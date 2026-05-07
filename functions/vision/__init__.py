"""Vision module for BISSI.

Provides image analysis using Gemma 4 multimodal.

Functions:
- describe_image: General image description with vision
- extract_text_from_image: OCR-like text extraction
- analyze_screenshot: UI/screenshot analysis
- analyze_chart: Chart/graph data extraction
"""
from .describe import (
    describe_image,
    extract_text_from_image,
    analyze_screenshot,
    analyze_chart,
)

__all__ = [
    "describe_image",
    "extract_text_from_image",
    "analyze_screenshot",
    "analyze_chart",
]