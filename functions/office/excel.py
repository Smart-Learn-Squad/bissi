"""Excel operations for BISSI.

Provides functionality to read, write, and manipulate XLSX files.
"""
import openpyxl
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from openpyxl.chart import BarChart, LineChart, PieChart, Reference


def read_excel(file_path: Union[str, Path], 
               sheet_name: Optional[str] = None,
               header: int = 0) -> pd.DataFrame:
    """Read Excel file into pandas DataFrame.
    
    Args:
        file_path: Path to the .xlsx file
        sheet_name: Name of sheet to read, or None for first sheet
        header: Row to use as column headers
        
    Returns:
        DataFrame with Excel data
    """
    if sheet_name:
        return pd.read_excel(file_path, sheet_name=sheet_name, header=header)
    return pd.read_excel(file_path, header=header)


def get_sheet_names(file_path: Union[str, Path]) -> List[str]:
    """Get list of all sheet names in Excel file.
    
    Args:
        file_path: Path to the .xlsx file
        
    Returns:
        List of sheet names
    """
    workbook = openpyxl.load_workbook(file_path, read_only=True)
    sheets = workbook.sheetnames
    workbook.close()
    return sheets


def get_sheet_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get metadata about all sheets in Excel file.
    
    Args:
        file_path: Path to the .xlsx file
        
    Returns:
        Dictionary with sheet names and row counts
    """
    workbook = openpyxl.load_workbook(file_path)
    info = {
        'sheets': {},
        'total_sheets': len(workbook.sheetnames)
    }
    
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        info['sheets'][sheet_name] = {
            'rows': sheet.max_row,
            'columns': sheet.max_column
        }
    
    workbook.close()
    return info


def write_excel(file_path: Union[str, Path],
                data: Union[pd.DataFrame, List[List[Any]], Dict[str, List[List[Any]]],
                sheet_name: str = "Sheet1",
                index: bool = False) -> None:
    """Write data to Excel file.
    
    Args:
        file_path: Path for output .xlsx
        data: DataFrame, 2D list, or dict mapping sheet names to 2D lists
        sheet_name: Sheet name for single sheet output
        index: Whether to include DataFrame index
    """
    if isinstance(data, pd.DataFrame):
        data.to_excel(file_path, sheet_name=sheet_name, index=index)
    elif isinstance(data, dict):
        # Multiple sheets
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet, sheet_data in data.items():
                if isinstance(sheet_data, pd.DataFrame):
                    sheet_data.to_excel(writer, sheet_name=sheet, index=index)
                else:
                    pd.DataFrame(sheet_data).to_excel(writer, sheet_name=sheet, index=index)
    else:
        # Single 2D list
        pd.DataFrame(data).to_excel(file_path, sheet_name=sheet_name, index=index)


def add_formula(file_path: Union[str, Path],
                cell: str,
                formula: str,
                sheet_name: Optional[str] = None) -> None:
    """Add formula to specific cell in Excel file.
    
    Args:
        file_path: Path to the .xlsx file
        cell: Cell reference (e.g., 'B5')
        formula: Excel formula string
        sheet_name: Target sheet, or active sheet if None
    """
    workbook = openpyxl.load_workbook(file_path)
    
    if sheet_name and sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
    else:
        sheet = workbook.active
    
    sheet[cell] = formula
    workbook.save(file_path)
    workbook.close()


def create_chart(file_path: Union[str, Path],
                 chart_type: str,
                 data_range: str,
                 title: str,
                 sheet_name: Optional[str] = None,
                 position: str = "E2") -> None:
    """Create chart in Excel file.
    
    Args:
        file_path: Path to the .xlsx file
        chart_type: 'bar', 'line', or 'pie'
        data_range: Cell range for data (e.g., 'A1:B10')
        title: Chart title
        sheet_name: Target sheet, or active sheet if None
        position: Cell position for chart
    """
    workbook = openpyxl.load_workbook(file_path)
    
    if sheet_name and sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
    else:
        sheet = workbook.active
    
    # Create chart
    chart_types = {
        'bar': BarChart,
        'line': LineChart,
        'pie': PieChart
    }
    
    chart_class = chart_types.get(chart_type.lower(), BarChart)
    chart = chart_class()
    chart.title = title
    
    # Parse data range and add data
    # Simple range parsing for now
    data = Reference(sheet, min_col=1, min_row=1, max_col=2, max_row=10)
    cats = Reference(sheet, min_col=1, min_row=2, max_row=10)
    
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    
    sheet.add_chart(chart, position)
    workbook.save(file_path)
    workbook.close()


def get_formulas(file_path: Union[str, Path], 
                 sheet_name: Optional[str] = None) -> Dict[str, str]:
    """Extract all formulas from Excel sheet.
    
    Args:
        file_path: Path to the .xlsx file
        sheet_name: Target sheet, or active sheet if None
        
    Returns:
        Dictionary mapping cell references to formulas
    """
    workbook = openpyxl.load_workbook(file_path, data_only=False)
    
    if sheet_name and sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
    else:
        sheet = workbook.active
    
    formulas = {}
    for row in sheet.iter_rows():
        for cell in row:
            if cell.value and str(cell.value).startswith('='):
                formulas[cell.coordinate] = cell.value
    
    workbook.close()
    return formulas


def to_dataframe(file_path: Union[str, Path],
                 sheet_name: Optional[str] = None) -> pd.DataFrame:
    """Convert Excel sheet to pandas DataFrame.
    
    Args:
        file_path: Path to the .xlsx file
        sheet_name: Target sheet, or first sheet if None
        
    Returns:
        DataFrame with sheet data
    """
    return read_excel(file_path, sheet_name=sheet_name)


def summarize_sheet(file_path: Union[str, Path],
                    sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """Generate summary statistics for Excel sheet.
    
    Args:
        file_path: Path to the .xlsx file
        sheet_name: Target sheet, or first sheet if None
        
    Returns:
        Dictionary with summary statistics
    """
    df = read_excel(file_path, sheet_name=sheet_name)
    
    summary = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.to_dict(),
        'numeric_summary': df.describe().to_dict() if df.select_dtypes(include=['number']).shape[1] > 0 else {},
        'missing_values': df.isnull().sum().to_dict()
    }
    
    return summary
