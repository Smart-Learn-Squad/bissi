"""Image processing for BISSI.

Provides image manipulation, conversion, and metadata extraction.
"""
from pathlib import Path
from typing import Union, Optional, Tuple
from PIL import Image
import io


def resize_image(input_path: Union[str, Path],
                 output_path: Union[str, Path],
                 size: Tuple[int, int],
                 maintain_aspect: bool = True) -> Path:
    """Resize image to specified dimensions.
    
    Args:
        input_path: Source image path
        output_path: Output image path
        size: Target size (width, height)
        maintain_aspect: Keep aspect ratio and fit within size
        
    Returns:
        Path to resized image
    """
    with Image.open(input_path) as img:
        if maintain_aspect:
            img.thumbnail(size, Image.Resampling.LANCZOS)
        else:
            img = img.resize(size, Image.Resampling.LANCZOS)
        
        img.save(output_path)
    
    return Path(output_path)


def convert_format(input_path: Union[str, Path],
                   output_path: Union[str, Path],
                   quality: int = 95) -> Path:
    """Convert image to different format.
    
    Args:
        input_path: Source image path
        output_path: Output path with target extension
        quality: JPEG quality (1-100)
        
    Returns:
        Path to converted image
    """
    with Image.open(input_path) as img:
        # Convert RGBA to RGB for JPEG
        if output_path.lower().endswith(('.jpg', '.jpeg')) and img.mode == 'RGBA':
            img = img.convert('RGB')
        
        save_kwargs = {}
        if output_path.lower().endswith(('.jpg', '.jpeg')):
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True
        elif output_path.lower().endswith('.png'):
            save_kwargs['optimize'] = True
        
        img.save(output_path, **save_kwargs)
    
    return Path(output_path)


def get_image_info(image_path: Union[str, Path]) -> dict:
    """Get image metadata.
    
    Args:
        image_path: Path to image
        
    Returns:
        Dictionary with image info
    """
    with Image.open(image_path) as img:
        info = {
            'format': img.format,
            'mode': img.mode,
            'width': img.width,
            'height': img.height,
            'size': img.size,
            'file_size': Path(image_path).stat().st_size
        }
        
        # Extract EXIF data if available
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            info['exif'] = {str(k): str(v) for k, v in exif.items()}
        
        return info


def create_thumbnail(input_path: Union[str, Path],
                     output_path: Union[str, Path],
                     size: Tuple[int, int] = (128, 128)) -> Path:
    """Create square thumbnail.
    
    Args:
        input_path: Source image
        output_path: Output thumbnail path
        size: Thumbnail dimensions
        
    Returns:
        Path to thumbnail
    """
    with Image.open(input_path) as img:
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(output_path)
    
    return Path(output_path)


def crop_image(input_path: Union[str, Path],
               output_path: Union[str, Path],
               box: Tuple[int, int, int, int]) -> Path:
    """Crop image to specified box.
    
    Args:
        input_path: Source image
        output_path: Output path
        box: Crop box (left, top, right, bottom)
        
    Returns:
        Path to cropped image
    """
    with Image.open(input_path) as img:
        cropped = img.crop(box)
        cropped.save(output_path)
    
    return Path(output_path)


def rotate_image(input_path: Union[str, Path],
                 output_path: Union[str, Path],
                 angle: int) -> Path:
    """Rotate image by specified angle.
    
    Args:
        input_path: Source image
        output_path: Output path
        angle: Rotation angle in degrees
        
    Returns:
        Path to rotated image
    """
    with Image.open(input_path) as img:
        rotated = img.rotate(angle, expand=True)
        rotated.save(output_path)
    
    return Path(output_path)


def compress_image(input_path: Union[str, Path],
                   output_path: Union[str, Path],
                   max_size_kb: int = 500,
                   quality_step: int = 5) -> Path:
    """Compress image to target file size.
    
    Args:
        input_path: Source image
        output_path: Output path
        max_size_kb: Maximum file size in KB
        quality_step: Quality reduction step
        
    Returns:
        Path to compressed image
    """
    max_bytes = max_size_kb * 1024
    quality = 95
    
    with Image.open(input_path) as img:
        # Convert to RGB if necessary
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Try decreasing quality until size is acceptable
        while quality > 10:
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            
            if buffer.tell() <= max_bytes:
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return Path(output_path)
            
            quality -= quality_step
    
    raise ValueError(f"Cannot compress image to {max_size_kb}KB")


class ImageBatchProcessor:
    """Batch image processing handler."""
    
    def __init__(self, input_dir: Union[str, Path], output_dir: Union[str, Path]):
        """Initialize batch processor.
        
        Args:
            input_dir: Directory with source images
            output_dir: Directory for output images
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def resize_all(self, size: Tuple[int, int], pattern: str = '*.jpg'):
        """Resize all matching images.
        
        Args:
            size: Target size (width, height)
            pattern: File pattern to match
        """
        for img_path in self.input_dir.glob(pattern):
            output_path = self.output_dir / f"resized_{img_path.name}"
            resize_image(img_path, output_path, size)
    
    def convert_all(self, target_format: str = '.jpg', pattern: str = '*.*'):
        """Convert all images to target format.
        
        Args:
            target_format: Target file extension
            pattern: File pattern to match
        """
        for img_path in self.input_dir.glob(pattern):
            if img_path.suffix.lower() != target_format:
                output_path = self.output_dir / img_path.with_suffix(target_format).name
                convert_format(img_path, output_path)
    
    def create_thumbnails(self, size: Tuple[int, int] = (128, 128)):
        """Create thumbnails for all images."""
        for img_path in self.input_dir.iterdir():
            if img_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.bmp'):
                output_path = self.output_dir / f"thumb_{img_path.name}"
                create_thumbnail(img_path, output_path, size)


# Convenience functions
def quick_resize(image_path: str, width: int, height: int) -> Path:
    """Quick resize with auto output name."""
    path = Path(image_path)
    output = path.parent / f"{path.stem}_resized{path.suffix}"
    return resize_image(path, output, (width, height))


def quick_convert(image_path: str, target_format: str) -> Path:
    """Quick format conversion."""
    path = Path(image_path)
    output = path.with_suffix(target_format)
    return convert_format(path, output)
