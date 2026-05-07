"""Data analysis and visualization for BISSI.

Provides statistical analysis and chart generation for Excel/CSV data.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json


def load_data(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load data from various file formats.
    
    Args:
        file_path: Path to data file (CSV, Excel, JSON)
        
    Returns:
        DataFrame with loaded data
    """
    path = Path(file_path)
    
    if path.suffix.lower() == '.csv':
        return pd.read_csv(file_path)
    elif path.suffix.lower() in ('.xlsx', '.xls'):
        return pd.read_excel(file_path)
    elif path.suffix.lower() == '.json':
        return pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Comprehensive analysis of DataFrame.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'memory_usage': df.memory_usage(deep=True).sum(),
        'missing_values': df.isnull().sum().to_dict(),
        'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict()
    }
    
    # Numeric columns analysis
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        analysis['numeric_columns'] = numeric_cols
        analysis['numeric_summary'] = df[numeric_cols].describe().to_dict()
        analysis['correlation'] = df[numeric_cols].corr().to_dict()
    
    # Categorical columns analysis
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if categorical_cols:
        analysis['categorical_columns'] = categorical_cols
        analysis['categorical_summary'] = {
            col: {
                'unique_values': df[col].nunique(),
                'top_values': df[col].value_counts().head(5).to_dict()
            }
            for col in categorical_cols
        }
    
    # Datetime columns
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    if datetime_cols:
        analysis['datetime_columns'] = datetime_cols
        analysis['datetime_summary'] = {
            col: {
                'min': str(df[col].min()),
                'max': str(df[col].max()),
                'range': str(df[col].max() - df[col].min())
            }
            for col in datetime_cols
        }
    
    return analysis


def generate_insights(df: pd.DataFrame) -> List[str]:
    """Generate automated insights from DataFrame.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        List of insight strings
    """
    insights = []
    
    # Basic info
    insights.append(f"Dataset contains {df.shape[0]} rows and {df.shape[1]} columns")
    
    # Missing data
    missing_cols = df.columns[df.isnull().any()].tolist()
    if missing_cols:
        insights.append(f"Missing data found in columns: {', '.join(missing_cols)}")
    else:
        insights.append("No missing data detected")
    
    # Numeric insights
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        mean_val = df[col].mean()
        std_val = df[col].std()
        min_val = df[col].min()
        max_val = df[col].max()
        
        insights.append(
            f"{col}: mean={mean_val:.2f}, std={std_val:.2f}, range=[{min_val:.2f}, {max_val:.2f}]"
        )
        
        # Detect outliers (values beyond 3 standard deviations)
        outliers = df[(df[col] < mean_val - 3*std_val) | (df[col] > mean_val + 3*std_val)]
        if len(outliers) > 0:
            insights.append(f"  → {len(outliers)} potential outliers detected in {col}")
    
    # Categorical insights
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        unique_count = df[col].nunique()
        top_val = df[col].value_counts().index[0] if unique_count > 0 else None
        top_count = df[col].value_counts().iloc[0] if unique_count > 0 else 0
        
        insights.append(
            f"{col}: {unique_count} unique values, most common is '{top_val}' ({top_count} occurrences)"
        )
    
    return insights


def create_chart(df: pd.DataFrame,
                chart_type: str,
                x_column: str,
                y_column: Optional[str] = None,
                title: str = "Chart",
                save_path: Optional[Union[str, Path]] = None) -> str:
    """Create chart from DataFrame data.
    
    Args:
        df: DataFrame with data
        chart_type: Type of chart (bar, line, scatter, histogram, pie)
        x_column: Column for x-axis or categories
        y_column: Column for y-axis (optional for histogram, pie)
        title: Chart title
        save_path: Path to save chart image
        
    Returns:
        Path to saved chart or "displayed"
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        raise ImportError("matplotlib and seaborn required for charting")
    
    plt.figure(figsize=(10, 6))
    
    if chart_type == 'bar':
        if y_column:
            df.plot(x=x_column, y=y_column, kind='bar', ax=plt.gca())
        else:
            df[x_column].value_counts().plot(kind='bar', ax=plt.gca())
    
    elif chart_type == 'line':
        if y_column:
            df.plot(x=x_column, y=y_column, kind='line', ax=plt.gca())
        else:
            df[x_column].plot(kind='line', ax=plt.gca())
    
    elif chart_type == 'scatter':
        if y_column:
            df.plot(x=x_column, y=y_column, kind='scatter', ax=plt.gca())
        else:
            raise ValueError("Scatter plot requires both x and y columns")
    
    elif chart_type == 'histogram':
        df[x_column].hist(bins=20, ax=plt.gca())
    
    elif chart_type == 'pie':
        df[x_column].value_counts().plot(kind='pie', ax=plt.gca())
    
    elif chart_type == 'box':
        if y_column:
            df.boxplot(column=y_column, by=x_column, ax=plt.gca())
        else:
            df[x_column].plot(kind='box', ax=plt.gca())
    
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")
    
    plt.title(title)
    plt.xlabel(x_column)
    if y_column:
        plt.ylabel(y_column)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        return str(save_path)
    else:
        plt.show()
        return "displayed"


def filter_dataframe(df: pd.DataFrame,
                    conditions: Dict[str, Any]) -> pd.DataFrame:
    """Filter DataFrame based on conditions.
    
    Args:
        df: Source DataFrame
        conditions: Dictionary mapping column names to filter values
        
    Returns:
        Filtered DataFrame
    """
    result = df.copy()
    
    for column, value in conditions.items():
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        if isinstance(value, dict):  # Range filter
            if 'min' in value:
                result = result[result[column] >= value['min']]
            if 'max' in value:
                result = result[result[column] <= value['max']]
        elif isinstance(value, list):  # Multiple values
            result = result[result[column].isin(value)]
        else:  # Exact match
            result = result[result[column] == value]
    
    return result


def aggregate_data(df: pd.DataFrame,
                  group_by: str,
                  aggregations: Dict[str, str]) -> pd.DataFrame:
    """Aggregate data by group.
    
    Args:
        df: Source DataFrame
        group_by: Column to group by
        aggregations: Dict mapping column to aggregation function (sum, mean, count, etc.)
        
    Returns:
        Aggregated DataFrame
    """
    agg_dict = {}
    for col, func in aggregations.items():
        agg_dict[col] = func
    
    return df.groupby(group_by).agg(agg_dict).reset_index()


def export_results(results: Dict[str, Any],
                  file_path: Union[str, Path],
                  format: str = 'json') -> None:
    """Export analysis results to file.
    
    Args:
        results: Analysis results dictionary
        file_path: Output file path
        format: Export format (json, csv)
    """
    path = Path(file_path)
    
    if format == 'json':
        # Convert non-serializable objects
        def serialize(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(path, 'w') as f:
            json.dump(results, f, indent=2, default=serialize)
    
    elif format == 'csv':
        # Convert to DataFrame if possible
        if isinstance(results, dict):
            df = pd.DataFrame(results)
            df.to_csv(path, index=False)
        else:
            raise ValueError("Results must be dict for CSV export")


def summarize_file(file_path: Union[str, Path]) -> str:
    """Generate human-readable summary of data file.
    
    Args:
        file_path: Path to data file
        
    Returns:
        Summary text
    """
    df = load_data(file_path)
    analysis = analyze_dataframe(df)
    insights = generate_insights(df)
    
    summary_lines = [
        f"=== Data Summary for {Path(file_path).name} ===",
        "",
        f"Dimensions: {analysis['shape'][0]} rows × {analysis['shape'][1]} columns",
        f"Columns: {', '.join(analysis['columns'][:10])}{'...' if len(analysis['columns']) > 10 else ''}",
        "",
        "Key Insights:",
    ]
    
    for insight in insights[:10]:
        summary_lines.append(f"  • {insight}")
    
    if analysis.get('numeric_columns'):
        summary_lines.extend([
            "",
            f"Numeric columns: {', '.join(analysis['numeric_columns'][:5])}"
        ])
    
    if analysis.get('categorical_columns'):
        summary_lines.extend([
            "",
            f"Categorical columns: {', '.join(analysis['categorical_columns'][:5])}"
        ])
    
    return '\n'.join(summary_lines)
