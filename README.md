# BISSI (by Smart-Learn Squad)

> **"Optima, immo absoluta perfectio"**

## Vision
BISSI is the definitive answer to the digital divide. Where the cloud fails due to bandwidth constraints, BISSI excels through its local presence. We are reclaiming technological sovereignty by bringing world-class intelligence directly to the edge.

## Architecture

### BISSI Lite (Smartlearn)
**Target:** Students | **Model:** gemma4:e2b (2B parameters)

Designed for students with limited resources. Features AI tutoring and seamless Office document management for offline learning.

- AI Tutor with step-by-step explanations
- Office suite integration (Word, Excel, PowerPoint)
- Study planning and exam preparation
- Document analysis and summarization

### BISSI Hi
**Target:** Researchers | **Model:** gemma4:e4b (4B parameters)

Engineered for complex research tasks. Capable of advanced data analysis while ensuring total data sovereignty.

- DNA sequence analysis and bioinformatics
- Survival analysis and statistical modeling
- Research paper synthesis
- Advanced data visualization

## Why BISSI?

* **Zero Latency:** No server wait times; immediate inference.
* **Zero Data Cost:** Once downloaded, it remains free for life—no internet required.
* **Privacy First:** Your documents and research data never leave your local machine.
* **Modular Design:** Use only what you need.

## Project Structure

```
bissi/
│
├── main.py                    # Application entry point
├── manager.py                 # Central orchestrator (BissiManager)
│
├── core/                      # AI Engine & Memory
│   ├── bissi.py              # Ollama LLM interface (BissiEngine)
│   └── memory/
│       ├── conversation_store.py  # SQLite chat persistence
│       └── vector_store.py        # ChromaDB RAG system
│
├── functions/                 # Capabilities (28+ modules)
│   ├── office/               # Document processing
│   │   ├── word.py           # Word documents
│   │   ├── excel.py          # Spreadsheets & formulas
│   │   ├── powerpoint.py     # Presentations
│   │   ├── pdf.py            # PDF text extraction
│   │   └── ocr.py            # Tesseract OCR
│   ├── database/
│   │   └── access.py         # Microsoft Access via pyodbc
│   ├── communication/
│   │   ├── email_client.py   # IMAP/SMTP client
│   │   ├── calendar.py       # Google Calendar integration
│   │   └── contacts.py       # Contact management (vCard)
│   ├── media/
│   │   ├── audio.py          # Whisper transcription, TTS
│   │   ├── image.py          # PIL image processing
│   │   └── video.py          # FFmpeg frame extraction
│   ├── code/
│   │   └── python_runner.py  # RestrictedPython sandbox
│   ├── data/
│   │   └── analysis.py       # Pandas/NumPy analytics
│   ├── web/
│   │   └── search.py         # URL fetching, content extraction
│   ├── templates/
│   │   ├── engine.py         # Jinja2 template engine
│   │   └── repository.py     # Template storage
│   ├── finance/
│   │   └── expense_manager.py # Expense tracker integration
│   ├── filesystem/
│   │   └── explorer.py       # File navigation & search
│   └── system/
│       ├── operations.py     # Safe file operations
│       └── clipboard.py      # System clipboard access
│
├── workflows/                 # Automation (IFTTT-style)
│   ├── engine.py             # Workflow orchestrator
│   ├── triggers.py           # Event triggers (time, file, etc.)
│   └── actions.py            # Executable actions
│
├── configs/                   # Configuration & Personas
│   ├── settings.py           # Global settings manager
│   └── personas/
│       ├── researcher.py     # Research assistant persona
│       ├── student.py        # Study companion persona
│       └── office_assistant.py # Productivity persona
│
├── ui/                        # User Interface
│   ├── components/           # Atomic design system
│   │   ├── atoms.py         # Buttons, inputs, labels
│   │   ├── molecules.py     # Chat bubbles, cards
│   │   ├── organisms.py     # Sidebar, ChatArea
│   │   └── complex.py       # Code blocks, drop zones
│   └── styles/
│       └── theme.py         # Design tokens
│
└── utils/                     # Shared utilities
    └── helpers.py            # Common functions (JSON, paths, etc.)
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Ollama (required)
ollama pull gemma4:e2b  # For Bissi Lite
ollama pull gemma4:e4b  # For Bissi Hi

# Launch application
python -m bissi
```

## Key Features

### Document Intelligence
- Read/write Word, Excel, PowerPoint
- PDF text extraction and OCR
- Smart document summarization
- Template-based generation

### Communication Hub
- Email (IMAP/SMTP) with attachments
- Google Calendar event management
- Contact vCard import/export
- Meeting notes automation

### Data & Analysis
- Python sandbox for safe code execution
- Pandas/NumPy data analysis
- Automatic chart generation
- Statistical insights

### Media Processing
- Audio transcription (Whisper)
- Text-to-speech (gTTS)
- Image processing (resize, convert)
- Video frame extraction

### Workflow Automation
- File watchers (auto-backup, auto-process)
- Scheduled tasks
- Trigger-based actions
- Document conversion pipelines

## Configuration

```python
# ~/.bissi/config.json
{
    "model": "gemma4:e2b",
    "persona": "student",
    "memory": {
        "conversation_db": "~/.bissi/conversations.db",
        "vector_store": "~/.bissi/vector_store"
    },
    "office": {
        "auto_backup": true,
        "backup_dir": "~/.bissi/backups"
    }
}
```

## Dependencies

**Core:**
- `ollama` - Local LLM inference
- `chromadb` - Vector database
- `sqlite3` - Conversation storage

**Office:**
- `python-docx`, `openpyxl`, `python-pptx` - Document processing
- `PyPDF2`, `pdfplumber` - PDF handling
- `pytesseract`, `pdf2image` - OCR

**Media:**
- `whisper` - Audio transcription
- `Pillow` - Image processing

**Data:**
- `pandas`, `numpy`, `matplotlib` - Analytics
- `RestrictedPython` - Safe code execution

## Development

```bash
# Run tests
pytest tests/

# Code style
black bissi/
flake8 bissi/
```

## License

MIT License - Smart-Learn Squad

---

### 🛡️ The Smart-Learn Squad
*Refining intelligence through collective willpower.*

* **Lead Engineer:** [Sam (goldensam777)](https://github.com/goldensam777)
* **Core Architecture:** [Abdel](https://github.com/tarouwereabdelazim-arch)
* **Logic & Systems:** [Tobie](https://github.com/tobiamadou-eng)
* **UI/UX Design:** [Mauricia](https://github.com/neriah249-alt)
* **Research & Data:** [Frejus](https://github.com/AthindehouFrejus)