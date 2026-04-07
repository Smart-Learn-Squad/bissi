"""Office module for BISSI.

Provides unified interface for Word, Excel, PowerPoint, PDF, and OCR operations.
"""

# Word processing
from .word import DocxAgent, read_document, read_with_structure, create_document

# Excel processing  
from .excel import (
    read_excel, write_excel, get_sheet_names, get_sheet_info,
    add_formula, create_chart, get_formulas, summarize_sheet
)

# PowerPoint processing
from .powerpoint import PPTXAgent, read_presentation, get_presentation_info, create_presentation

# PDF processing
from .pdf import (
    read_pdf, read_pdf_simple, extract_tables, get_pdf_info,
    merge_pdfs, split_pdf, search_text
)

# OCR processing
from .ocr import (
    image_to_text, image_to_data, is_scanned_pdf,
    pdf_to_text, smart_pdf_extract, extract_tables_ocr
)

__all__ = [
    # Word
    'DocxAgent',
    'read_document',
    'read_with_structure',
    'create_document',
    # Excel
    'read_excel',
    'write_excel',
    'get_sheet_names',
    'get_sheet_info',
    'add_formula',
    'create_chart',
    'get_formulas',
    'summarize_sheet',
    # PowerPoint
    'PPTXAgent',
    'read_presentation',
    'get_presentation_info',
    'create_presentation',
    # PDF
    'read_pdf',
    'read_pdf_simple',
    'extract_tables',
    'get_pdf_info',
    'merge_pdfs',
    'split_pdf',
    'search_text',
    # OCR
    'image_to_text',
    'image_to_data',
    'is_scanned_pdf',
    'pdf_to_text',
    'smart_pdf_extract',
    'extract_tables_ocr',
]
