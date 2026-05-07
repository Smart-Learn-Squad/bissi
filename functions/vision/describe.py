"""Vision capabilities for BISSI using Gemma 4 multimodal.

Provides image description using Gemma 4's vision capabilities.
"""
import ollama
from pathlib import Path
from typing import Union, Optional

from core.types import ToolResult


def describe_image(
    file_path: str,
    prompt: str = "Describe this image in detail.",
    detail: str = "high",
    model: str = "gemma4:4b",
) -> ToolResult:
    """Analyze an image using Gemma 4's multimodal capabilities.

    Args:
        file_path: Path to the image file (PNG, JPG, WEBP, etc.)
        prompt: Question or instruction about the image
        detail: Detail level 'low', 'high', or 'auto'
        model: Model to use (default: gemma4:4b)

    Returns:
        ToolResult with description

    Example:
        describe_image("screenshot.png", "What UI elements are in this screenshot?")
        describe_image("chart.png", "What data does this chart show?")
    """
    path = Path(file_path)

    if not path.exists():
        return ToolResult.fail(f"Image not found: {file_path}")

    # Check file extension
    valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
    if path.suffix.lower() not in valid_exts:
        return ToolResult.fail(f"Unsupported image format: {path.suffix}")

    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            images=[str(path.absolute())],
            stream=False,
        )

        description = response.get('response', '').strip()

        return ToolResult.ok(
            output={
                'description': description,
                'model': model,
                'detail': detail,
            },
            message=f"Image analyzed: {path.name}",
            path=str(path.absolute()),
        )

    except ollama.ResponseError as e:
        return ToolResult.fail(f"Ollama error: {e}")
    except Exception as e:
        return ToolResult.fail(f"Failed to analyze image: {e}")


def extract_text_from_image(
    file_path: str,
    language: str = "eng",
) -> ToolResult:
    """Extract text from an image (OCR-like) using vision model.

    Args:
        file_path: Path to the image
        language: Language code (eng, fra, etc.)

    Returns:
        ToolResult with extracted text
    """
    prompt = f"Extract ALL text from this image. Return only the text, nothing else."

    result = describe_image(
        file_path=file_path,
        prompt=prompt,
        detail="high",
    )

    if result.success:
        # Transform to text extraction format
        return ToolResult.ok(
            output={'text': result.output['description']},
            message=f"Extracted {len(result.output['description'])} characters",
            path=result.path,
        )
    return result


def analyze_screenshot(
    file_path: str,
) -> ToolResult:
    """Analyze a screenshot (UI elements, text, layout).

    Args:
        file_path: Path to the screenshot

    Returns:
        ToolResult with analysis
    """
    prompt = """Analyze this screenshot. Identify:
1. UI elements (buttons, inputs, menus)
2. Text content visible
3. Layout structure
4. Any interactive elements

Be specific and detailed."""

    result = describe_image(
        file_path=file_path,
        prompt=prompt,
        detail="high",
    )

    if result.success:
        return ToolResult.ok(
            output={'analysis': result.output['description']},
            message="Screenshot analyzed",
            path=result.path,
        )
    return result


def analyze_chart(
    file_path: str,
) -> ToolResult:
    """Analyze a chart or graph, extracting data and insights.

    Args:
        file_path: Path to chart image

    Returns:
        ToolResult with chart analysis
    """
    prompt = """Analyze this chart or graph. Extract:
1. Chart type (bar, line, pie, etc.)
2. X and Y axis labels/values
3. Key data points visible
4. Trends or patterns
5. Any annotations or legends

Be precise about the data you can see."""

    result = describe_image(
        file_path=file_path,
        prompt=prompt,
        detail="high",
    )

    if result.success:
        return ToolResult.ok(
            output={'chart_analysis': result.output['description']},
            message="Chart analyzed",
            path=result.path,
        )
    return result