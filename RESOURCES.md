# Ressources Documentation - BISSI Development

## Core AI / LLM
- **Ollama Python SDK** - https://github.com/ollama/ollama-python
- **Ollama API Docs** - https://github.com/ollama/ollama/blob/main/docs/api.md

## Available Tools

### Core Functions

1. **read_word** - Read Microsoft Word documents
2. **read_excel** - Read Microsoft Excel spreadsheets  
3. **read_pdf** - Read PDF documents
4. **read_text_file** - Read text files (.py, .md, .txt)
5. **search_files** - Search for files by pattern (includes root directory)
6. **search_by_content** - Search files containing specific text
7. **list_directory** - List directory contents with file sizes
8. **get_file_info** - Get detailed file information
9. **get_directory_tree** - Get hierarchical directory structure
10. **get_recent_files** - Get recently modified files
11. **safe_operator** - Get Python version and working directory

### Multi-Step Reasoning

The agent now supports up to **7 iterations** of tool calls for complex tasks, enabling:
- Audit → Action → Calculation → Language synthesis workflow
- Cross-verification of file searches with directory listings
- Automatic retry on tool failures with alternative approaches

## Office Suite
- **python-docx** (Word) - https://python-docx.readthedocs.io/
- **openpyxl** (Excel) - https://openpyxl.readthedocs.io/
- **python-pptx** (PowerPoint) - https://python-pptx.readthedocs.io/

## PDF Processing
- **PyPDF2** - https://pypdf2.readthedocs.io/
- **pdfplumber** (extraction tables/texte) - https://github.com/jsvine/pdfplumber

## OCR
- **pytesseract** - https://github.com/madmaze/pytesseract
- **Tesseract OCR** (engine) - https://github.com/tesseract-ocr/tesseract
- **pdf2image** - https://github.com/Belval/pdf2image

## UI (PyQt6)
- **PyQt6 Docs** - https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Qt6 Official** - https://doc.qt.io/qt-6/
- **PyQt6 Tutorial** - https://www.pythonguis.com/pyqt6-tutorial/

## Data Processing
- **pandas** - https://pandas.pydata.org/docs/
- **numpy** - https://numpy.org/doc/
- **matplotlib** - https://matplotlib.org/stable/

## Vector Store / RAG (Future)
- **ChromaDB** - https://docs.trychroma.com/
- **sentence-transformers** - https://www.sbert.net/

## Web & API
- **requests** - https://docs.python-requests.org/
- **beautifulsoup4** - https://www.crummy.com/software/BeautifulSoup/bs4/doc/

## System Integration
- **pyperclip** (clipboard) - https://github.com/asweigart/pyperclip
- **pyautogui** (automation) - https://pyautogui.readthedocs.io/
- **pynput** (keyboard/mouse control) - https://pynput.readthedocs.io/

## System Dependencies
- **Tesseract OCR** (install with: `sudo apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng`)
- **poppler-utils** (for pdf2image: `sudo apt install poppler-utils`)

## Best Practices
- **Python Type Hints** - https://docs.python.org/3/library/typing.html
- **pathlib** (file paths) - https://docs.python.org/3/library/pathlib.html
