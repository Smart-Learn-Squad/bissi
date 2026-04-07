"""PDF operations for BISSI.

Provides functionality to read, extract text/tables, merge, and split PDF files.
"""
import PyPDF2
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


def read_pdf(file_path: Union[str, Path], 
             pages: Optional[List[int]] = None) -> str:
    """Extract text from PDF file using pdfplumber.
    
    Args:
        file_path: Path to the PDF file
        pages: List of page numbers (0-indexed), or None for all pages
        
    Returns:
        Extracted text content
    """
    text_content = []
    
    with pdfplumber.open(file_path) as pdf:
        page_range = pages if pages else range(len(pdf.pages))
        
        for i in page_range:
            if 0 <= i < len(pdf.pages):
                page = pdf.pages[i]
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Page {i+1} ---\n{text}")
    
    return '\n\n'.join(text_content)


def read_pdf_simple(file_path: Union[str, Path]) -> str:
    """Extract text using PyPDF2 (fallback method).
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    text_content = []
    
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_content.append(f"--- Page {i+1} ---\n{text}")
    
    return '\n\n'.join(text_content)


def extract_tables(file_path: Union[str, Path], 
                    page_number: Optional[int] = None) -> List[List[List[str]]]:
    """Extract tables from PDF pages.
    
    Args:
        file_path: Path to the PDF file
        page_number: Specific page (0-indexed), or all pages if None
        
    Returns:
        List of tables (each table is list of rows, each row is list of cells)
    """
    all_tables = []
    
    with pdfplumber.open(file_path) as pdf:
        if page_number is not None:
            if 0 <= page_number < len(pdf.pages):
                page = pdf.pages[page_number]
                tables = page.extract_tables()
                all_tables.extend(tables)
        else:
            for page in pdf.pages:
                tables = page.extract_tables()
                all_tables.extend(tables)
    
    return all_tables


def get_pdf_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get metadata and information about PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dictionary with PDF metadata
    """
    with pdfplumber.open(file_path) as pdf:
        info = {
            'pages': len(pdf.pages),
            'metadata': dict(pdf.metadata) if pdf.metadata else {},
            'file_size': Path(file_path).stat().st_size
        }
    
    return info


def merge_pdfs(file_paths: List[Union[str, Path]], 
               output_path: Union[str, Path]) -> None:
    """Merge multiple PDF files into one.
    
    Args:
        file_paths: List of PDF files to merge (in order)
        output_path: Path for merged output file
    """
    merger = PyPDF2.PdfMerger()
    
    try:
        for file_path in file_paths:
            merger.append(str(file_path))
        
        merger.write(str(output_path))
    finally:
        merger.close()


def split_pdf(file_path: Union[str, Path],
              page_ranges: List[tuple],
              output_prefix: Union[str, Path]) -> List[str]:
    """Split PDF into multiple files based on page ranges.
    
    Args:
        file_path: Path to source PDF
        page_ranges: List of (start, end) tuples, 1-indexed, inclusive
        output_prefix: Prefix for output files
        
    Returns:
        List of created file paths
    """
    output_files = []
    reader = PyPDF2.PdfReader(str(file_path))
    prefix_path = Path(output_prefix)
    
    for i, (start, end) in enumerate(page_ranges):
        writer = PyPDF2.PdfWriter()
        
        # Convert to 0-indexed and clamp to valid range
        start_idx = max(0, start - 1)
        end_idx = min(end, len(reader.pages))
        
        for page_num in range(start_idx, end_idx):
            writer.add_page(reader.pages[page_num])
        
        output_file = f"{prefix_path}_part{i+1}.pdf"
        with open(output_file, 'wb') as output_pdf:
            writer.write(output_pdf)
        
        output_files.append(output_file)
    
    return output_files


def extract_images(file_path: Union[str, Path],
                   page_number: Optional[int] = None) -> List[Any]:
    """Extract images from PDF pages.
    
    Args:
        file_path: Path to the PDF file
        page_number: Specific page (0-indexed), or all pages if None
        
    Returns:
        List of image objects
    """
    images = []
    
    with pdfplumber.open(file_path) as pdf:
        if page_number is not None:
            if 0 <= page_number < len(pdf.pages):
                page = pdf.pages[page_number]
                images.extend(page.images)
        else:
            for page in pdf.pages:
                images.extend(page.images)
    
    return images


def search_text(file_path: Union[str, Path], 
                query: str,
                case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """Search for text in PDF.
    
    Args:
        file_path: Path to the PDF file
        query: Text to search for
        case_sensitive: Whether search is case sensitive
        
    Returns:
        List of matches with page number and context
    """
    matches = []
    
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            search_text = text if case_sensitive else text.lower()
            search_query = query if case_sensitive else query.lower()
            
            if search_query in search_text:
                # Find context around match
                idx = search_text.find(search_query)
                context_start = max(0, idx - 50)
                context_end = min(len(text), idx + len(query) + 50)
                context = text[context_start:context_end]
                
                matches.append({
                    'page': i + 1,
                    'context': context,
                    'match': text[idx:idx + len(query)] if case_sensitive else query
                })
    
    return matches
