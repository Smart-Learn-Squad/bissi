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