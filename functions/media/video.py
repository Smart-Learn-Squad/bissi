"""Video processing for BISSI.

Provides video frame extraction and basic video operations.
"""
from pathlib import Path
from typing import Union, Optional, List
import subprocess
import tempfile
from utils.security import validate_path_safety

def extract_frames(video_path: Union[str, Path],
                   output_dir: Union[str, Path],
                   fps: float = 1.0,
                   start_time: Optional[float] = None,
                   duration: Optional[float] = None) -> List[Path]:
    """Extract frames from video at specified FPS.
    
    Args:
        video_path: Path to video file
        output_dir: Directory for extracted frames
        fps: Frames per second to extract
        start_time: Start time in seconds (None for beginning)
        duration: Duration to extract in seconds (None for all)
        
    Returns:
        List of paths to extracted frames
    """
    validate_path_safety(video_path)
    validate_path_safety(output_dir)
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build ffmpeg command
    cmd = ['ffmpeg', '-y', '-i', str(video_path)]
    
    if start_time is not None:
        cmd.extend(['-ss', str(start_time)])
    
    if duration is not None:
        cmd.extend(['-t', str(duration)])
    
    cmd.extend([
        '-vf', f'fps={fps}',
        '-q:v', '2',
        str(output_dir / 'frame_%04d.jpg')
    ])
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        
        # Return list of extracted frames
        frames = sorted(output_dir.glob('frame_*.jpg'))
        return frames
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg a dépassé le temps limite (60s)")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not installed. Install with: sudo apt install ffmpeg")


def get_video_info(video_path: Union[str, Path]) -> dict:
    """Get video file metadata.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary with video info
    """
    try:
        # Use ffprobe to get info
        validate_path_safety(video_path)
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration,size,bit_rate:stream=width,height,codec_name',
            '-of', 'json', str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        import json
        data = json.loads(result.stdout)
        
        info = {
            'duration': float(data['format'].get('duration', 0)),
            'size': int(data['format'].get('size', 0)),
            'bit_rate': int(data['format'].get('bit_rate', 0))
        }
        
        # Get video stream info
        from fractions import Fraction
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                info['width'] = stream.get('width')
                info['height'] = stream.get('height')
                info['codec'] = stream.get('codec_name')
                
                r_frame_rate = stream.get('r_frame_rate', '0/1')
                try:
                    if '/' in r_frame_rate:
                        num, den = r_frame_rate.split('/')
                        fps = float(Fraction(int(num), int(den)))
                    else:
                        fps = float(r_frame_rate)
                except (ValueError, ZeroDivisionError):
                    fps = 0.0
                info['fps'] = fps
                break
        
        return info
        
    except FileNotFoundError:
        raise RuntimeError("ffprobe not installed. Install with: sudo apt install ffmpeg")


def extract_thumbnail(video_path: Union[str, Path],
                      output_path: Union[str, Path],
                      time_offset: float = 0.0) -> Path:
    """Extract single frame as thumbnail.
    
    Args:
        video_path: Path to video file
        output_path: Output image path
        time_offset: Time in seconds for frame extraction
        
    Returns:
        Path to thumbnail image
    """
    validate_path_safety(video_path)
    validate_path_safety(output_path)
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path),
        '-ss', str(time_offset),
        '-vframes', '1',
        '-q:v', '2',
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return Path(output_path)
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg a dépassé le temps limite (30s)")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")


def convert_video(input_path: Union[str, Path],
                  output_path: Union[str, Path],
                  video_codec: str = 'libx264',
                  audio_codec: str = 'aac') -> Path:
    """Convert video to different format.
    
    Args:
        input_path: Source video
        output_path: Output video path
        video_codec: Video codec
        audio_codec: Audio codec
        
    Returns:
        Path to converted video
    """
    validate_path_safety(input_path)
    validate_path_safety(output_path)
    cmd = [
        'ffmpeg', '-y', '-i', str(input_path),
        '-c:v', video_codec,
        '-c:a', audio_codec,
        '-strict', 'experimental',
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return Path(output_path)
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg a dépassé le temps limite (300s)")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")


def trim_video(input_path: Union[str, Path],
               output_path: Union[str, Path],
               start_time: float,
               end_time: float) -> Path:
    """Trim video to specified time range.
    
    Args:
        input_path: Source video
        output_path: Output video
        start_time: Start time in seconds
        end_time: End time in seconds
        
    Returns:
        Path to trimmed video
    """
    validate_path_safety(input_path)
    validate_path_safety(output_path)
    duration = end_time - start_time
    
    cmd = [
        'ffmpeg', '-y', '-i', str(input_path),
        '-ss', str(start_time),
        '-t', str(duration),
        '-c', 'copy',
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        return Path(output_path)
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg a dépassé le temps limite (60s)")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")


# Convenience functions
def get_duration(video_path: Union[str, Path]) -> float:
    """Get video duration in seconds."""
    info = get_video_info(video_path)
    return info.get('duration', 0)


def quick_thumbnail(video_path: str, time_sec: float = 0) -> Path:
    """Quick thumbnail extraction."""
    path = Path(video_path)
    output = path.parent / f"{path.stem}_thumb.jpg"
    return extract_thumbnail(path, output, time_sec)
