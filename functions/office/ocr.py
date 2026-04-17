"""OCR operations for BISSI.

Provides Optical Character Recognition for images and scanned PDFs using Tesseract.
"""
import pytesseract
from PIL import Image
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import pdfplumber


def image_to_text(image_path: Union[str, Path], 
                  lang: str = 'fra+eng') -> str:
    """Extract text from image using OCR.
    
    Args:
        image_path: Path to image file (PNG, JPG, etc.)
        lang: Language code(s) for OCR (e.g., 'eng', 'fra', 'fra+eng')
        
    Returns:
        Extracted text content
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang=lang)
    return text.strip()


def image_to_data(image_path: Union[str, Path],
                  lang: str = 'fra+eng') -> Dict[str, Any]:
    """Extract detailed OCR data with bounding boxes.
    
    Args:
        image_path: Path to image file
        lang: Language code(s) for OCR
        
    Returns:
        Dictionary with text, coordinates, and confidence for each word
    """
    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
    
    # Filter out empty entries
    n_boxes = len(data['text'])
    results = []
    
    for i in range(n_boxes):
        if int(data['conf'][i]) > 0:  # Valid recognition
            results.append({
                'text': data['text'][i],
                'x': data['left'][i],
                'y': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i],
                'confidence': data['conf'][i]
            })
    
    return {
        'words': results,
        'total_words': len(results),
        'image_size': image.size
    }


def is_scanned_pdf(file_path: Union[str, Path], 
                   sample_pages: int = 2,
                   threshold: int = 50) -> bool:
    """Check if PDF is image-based (scanned) or text-based.
    
    Args:
        file_path: Path to PDF file
        sample_pages: Number of pages to check
        threshold: Minimum characters to consider as text-based
        
    Returns:
        True if PDF appears to be scanned/image-based
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            check_pages = min(sample_pages, len(pdf.pages))
            
            for i in range(check_pages):
                page = pdf.pages[i]
                text = page.extract_text()
                
                # If page has very little extractable text, likely scanned
                if not text or len(text.strip()) < threshold:
                    return True
        
        return False
    except Exception:
        # If we can't extract text at all, assume scanned
        return True


def pdf_to_text(file_path: Union[str, Path],
                lang: str = 'fra+eng',
                dpi: int = 300) -> str:
    """Extract text from scanned PDF using OCR.
    
    Requires pdf2image to convert PDF pages to images first.
    
    Args:
        file_path: Path to PDF file
        lang: Language code(s) for OCR
        dpi: Resolution for PDF to image conversion
        
    Returns:
        Extracted text content from all pages
    """
    try:
        import pdf2image
    except ImportError:
        raise ImportError("pdf2image is required for OCR on PDFs. Install with: pip install pdf2image")
    
    try:
        images = pdf2image.convert_from_path(file_path, dpi=dpi)
    except pdf2image.exceptions.PDFInfoNotInstalledError:
        # Poppler not installed — try pdfplumber as fallback
        with pdfplumber.open(file_path) as pdf:
            all_text = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ''
                if text.strip():
                    all_text.append(f"--- Page {i+1} ---\n{text}")
            if all_text:
                return '\n\n'.join(all_text)
        return "[OCR unavailable] Poppler is not installed. Install Poppler for Windows from https://github.com/oschwartz10612/poppler-windows/releases and add to PATH."
    
    all_text = []
    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image, lang=lang)
        if text.strip():
            all_text.append(f"--- Page {i+1} ---\n{text}")
    
    return '\n\n'.join(all_text)


def smart_pdf_extract(file_path: Union[str, Path],
                      lang: str = 'fra+eng') -> Dict[str, Any]:
    """Intelligently extract text from PDF - uses direct extraction if text-based, OCR if scanned.
    
    Args:
        file_path: Path to PDF file
        lang: Language for OCR if needed
        
    Returns:
        Dictionary with extracted text and method used
    """
    from .pdf import read_pdf
    
    if is_scanned_pdf(file_path):
        text = pdf_to_text(file_path, lang=lang)
        method = 'ocr' if not text.startswith('[OCR unavailable]') else 'fallback_extraction'
        return {
            'text': text,
            'method': method,
            'is_scanned': True
        }
    else:
        return {
            'text': read_pdf(file_path),
            'method': 'direct_extraction',
            'is_scanned': False
        }


def extract_tables_ocr(file_path: Union[str, Path],
                       page_number: int = 0,
                       lang: str = 'fra+eng') -> List[List[str]]:
    """Extract tables from scanned PDF using OCR and table detection.
    
    This is a simplified implementation. For production, consider using
    specialized table extraction libraries.
    
    Args:
        file_path: Path to PDF file
        page_number: Page to extract (0-indexed)
        lang: Language for OCR
        
    Returns:
        List of rows with cell values
    """
    try:
        import pdf2image
    except ImportError:
        raise ImportError("pdf2image is required. Install with: pip install pdf2image")
    
    try:
        images = pdf2image.convert_from_path(file_path, first_page=page_number+1, last_page=page_number+1)
    except pdf2image.exceptions.PDFInfoNotInstalledError:
        return [["[OCR unavailable] Poppler is not installed. Install from https://github.com/oschwartz10612/poppler-windows/releases"]]
    
    if not images:
        return []
    
    image = images[0]
    
    # Get OCR with bounding boxes
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
    
    # Group by lines (similar y-coordinates) to simulate rows
    lines = {}
    n_boxes = len(data['text'])
    
    for i in range(n_boxes):
        if int(data['conf'][i]) > 30:  # Filter low confidence
            y = data['top'][i]
            text = data['text'][i].strip()
            
            if text:
                # Group by line (within 10 pixels)
                line_key = round(y / 10) * 10
                if line_key not in lines:
                    lines[line_key] = []
                lines[line_key].append((data['left'][i], text))
    
    # Sort by y position and then x position within each line
    table = []
    for y in sorted(lines.keys()):
        row = lines[y]
        row.sort(key=lambda x: x[0])  # Sort by x position
        table.append([cell[1] for cell in row])
    
    return table
