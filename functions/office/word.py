"""
A lib for agent to exploit docx documents
"""
from docx import Document

class DocxAgent:
    """A simple agent to read and manipulate docx documents."""
    def __init__(self, file_path):
        """Initialize the agent with the path to the docx file."""
        self.file_path = file_path
        self.document = Document(file_path)

    def read_paragraphs(self):
        """"Read and return the text of all paragraphs in the document."""
        return [para.text for para in self.document.paragraphs]

    def read_tables(self):
        """Read and return the data from all tables in the document."""
        tables_data = []
        for table in self.document.tables:
            table_data = []
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                table_data.append(row_data)
            tables_data.append(table_data)
        return tables_data

    def save(self, new_file_path=None):
        """Save the document. If new_file_path is provided, save to that path; otherwise, overwrite the original file."""
        if new_file_path:
            self.document.save(new_file_path)
        else:
            self.document.save(self.file_path)


# Module-level convenience functions
def read_document(file_path: str) -> str:
    """Read all text from a Word document."""
    agent = DocxAgent(file_path)
    return "\n".join(agent.read_paragraphs())


def read_with_structure(file_path: str) -> dict:
    """Read document with structure (paragraphs and tables)."""
    agent = DocxAgent(file_path)
    return {
        "paragraphs": agent.read_paragraphs(),
        "tables": agent.read_tables()
    }


def create_document() -> DocxAgent:
    """Create a new empty Word document."""
    from docx import Document
    from pathlib import Path
    import tempfile
    
    # Create temp file
    temp_path = Path(tempfile.gettempdir()) / "new_document.docx"
    doc = Document()
    doc.save(str(temp_path))
    return DocxAgent(str(temp_path))