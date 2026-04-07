"""PowerPoint operations for BISSI.

Provides functionality to read, create, and manipulate PPTX presentations.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


class PPTXAgent:
    """Agent for PowerPoint presentation operations."""
    
    def __init__(self, file_path: Optional[Union[str, Path]] = None):
        """Initialize PPTX agent.
        
        Args:
            file_path: Path to existing presentation, or None for new
        """
        self.file_path = file_path
        if file_path and Path(file_path).exists():
            self.presentation = Presentation(file_path)
        else:
            self.presentation = Presentation()
    
    def read_slides(self) -> List[Dict[str, Any]]:
        """Extract text content from all slides.
        
        Returns:
            List of slides with text content
        """
        slides_content = []
        
        for i, slide in enumerate(self.presentation.slides, 1):
            slide_text = []
            
            # Extract from all shapes
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)
            
            slides_content.append({
                'slide_number': i,
                'content': '\n'.join(slide_text),
                'shapes_count': len(slide.shapes)
            })
        
        return slides_content
    
    def read_tables(self) -> List[List[List[str]]]:
        """Extract tables from all slides.
        
        Returns:
            List of tables per slide
        """
        all_tables = []
        
        for slide in self.presentation.slides:
            slide_tables = []
            
            for shape in slide.shapes:
                if shape.has_table:
                    table = shape.table
                    table_data = []
                    
                    for row in table.rows:
                        row_data = [cell.text for cell in row.cells]
                        table_data.append(row_data)
                    
                    slide_tables.append(table_data)
            
            all_tables.append(slide_tables)
        
        return all_tables
    
    def add_slide(self, title: str, content: str, layout_idx: int = 1) -> Any:
        """Add new slide with title and content.
        
        Args:
            title: Slide title
            content: Slide body content
            layout_idx: Slide layout index (1 = Title and Content)
            
        Returns:
            The created slide object
        """
        slide_layout = self.presentation.slide_layouts[layout_idx]
        slide = self.presentation.slides.add_slide(slide_layout)
        
        # Set title
        if slide.shapes.title:
            slide.shapes.title.text = title
        
        # Set content in body placeholder
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 1:  # Body placeholder
                shape.text = content
                break
        
        return slide
    
    def add_image_slide(self, 
                       title: str, 
                       image_path: Union[str, Path],
                       left: float = 1,
                       top: float = 1.5,
                       width: float = 8,
                       height: float = 5) -> Any:
        """Add slide with image.
        
        Args:
            title: Slide title
            image_path: Path to image file
            left: Left position in inches
            top: Top position in inches
            width: Width in inches
            height: Height in inches
            
        Returns:
            The created slide object
        """
        slide_layout = self.presentation.slide_layouts[5]  # Blank layout
        slide = self.presentation.slides.add_slide(slide_layout)
        
        if title:
            # Add title textbox
            title_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(0.5), Inches(9), Inches(0.5)
            )
            title_frame = title_box.text_frame
            title_frame.text = title
            title_para = title_frame.paragraphs[0]
            title_para.font.size = Pt(24)
            title_para.font.bold = True
        
        # Add image
        slide.shapes.add_picture(
            str(image_path),
            Inches(left), Inches(top),
            Inches(width), Inches(height)
        )
        
        return slide
    
    def add_table_slide(self,
                       title: str,
                       data: List[List[str]],
                       rows: int,
                       cols: int,
                       left: float = 1,
                       top: float = 2,
                       width: float = 8,
                       height: float = 4) -> Any:
        """Add slide with table.
        
        Args:
            title: Slide title
            data: 2D list of table data
            rows: Number of rows
            cols: Number of columns
            left: Left position in inches
            top: Top position in inches
            width: Table width in inches
            height: Table height in inches
            
        Returns:
            The created slide object
        """
        slide_layout = self.presentation.slide_layouts[5]  # Blank layout
        slide = self.presentation.slides.add_slide(slide_layout)
        
        # Add title
        if title:
            title_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(0.5), Inches(9), Inches(0.5)
            )
            title_frame = title_box.text_frame
            title_frame.text = title
            title_para = title_frame.paragraphs[0]
            title_para.font.size = Pt(24)
            title_para.font.bold = True
        
        # Add table
        table = slide.shapes.add_table(
            rows, cols,
            Inches(left), Inches(top),
            Inches(width), Inches(height)
        ).table
        
        # Fill data
        for i, row_data in enumerate(data):
            if i < rows:
                for j, cell_text in enumerate(row_data):
                    if j < cols:
                        table.cell(i, j).text = str(cell_text)
        
        return slide
    
    def get_slide_count(self) -> int:
        """Get number of slides in presentation."""
        return len(self.presentation.slides)
    
    def get_slide_layouts(self) -> List[str]:
        """Get available slide layout names."""
        return [layout.name for layout in self.presentation.slide_layouts]
    
    def save(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """Save presentation to file.
        
        Args:
            file_path: Output path, or original path if None
        """
        save_path = file_path or self.file_path
        if not save_path:
            raise ValueError("No file path specified for saving")
        
        self.presentation.save(str(save_path))
        self.file_path = str(save_path)


def read_presentation(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Read and extract all content from PowerPoint file.
    
    Args:
        file_path: Path to .pptx file
        
    Returns:
        List of slides with content
    """
    agent = PPTXAgent(file_path)
    return agent.read_slides()


def get_presentation_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get metadata about PowerPoint presentation.
    
    Args:
        file_path: Path to .pptx file
        
    Returns:
        Dictionary with presentation info
    """
    agent = PPTXAgent(file_path)
    
    # Count shapes and content
    total_shapes = 0
    text_shapes = 0
    table_shapes = 0
    image_shapes = 0
    
    for slide in agent.presentation.slides:
        for shape in slide.shapes:
            total_shapes += 1
            
            if hasattr(shape, "text") and shape.text.strip():
                text_shapes += 1
            if shape.has_table:
                table_shapes += 1
            if shape.shape_type == 13:  # Picture type
                image_shapes += 1
    
    return {
        'slide_count': len(agent.presentation.slides),
        'total_shapes': total_shapes,
        'text_shapes': text_shapes,
        'table_shapes': table_shapes,
        'image_shapes': image_shapes,
        'layouts': agent.get_slide_layouts()
    }


def create_presentation(title: str = "New Presentation") -> PPTXAgent:
    """Create new presentation with title slide.
    
    Args:
        title: Presentation title
        
    Returns:
        PPTXAgent instance with new presentation
    """
    agent = PPTXAgent()
    
    # Add title slide
    slide_layout = agent.presentation.slide_layouts[0]  # Title slide layout
    slide = agent.presentation.slides.add_slide(slide_layout)
    
    # Set title and subtitle
    title_shape = slide.shapes.title
    subtitle_shape = slide.placeholders[1]
    
    title_shape.text = title
    subtitle_shape.text = f"Created by BISSI - {Path.cwd().name}"
    
    return agent
