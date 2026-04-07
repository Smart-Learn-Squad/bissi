"""Audio processing for BISSI.

Provides audio transcription (Whisper) and text-to-speech capabilities.
"""
from pathlib import Path
from typing import Optional, Union, List
import tempfile
import subprocess


class AudioProcessor:
    """Audio transcription and TTS handler."""
    
    def __init__(self, whisper_model: str = 'base'):
        """Initialize audio processor.
        
        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
        """
        self.whisper_model = whisper_model
        self._check_whisper()
    
    def _check_whisper(self):
        """Check if Whisper is available."""
        try:
            import whisper
            self.whisper_available = True
        except ImportError:
            self.whisper_available = False
    
    def transcribe(self,
                   audio_path: Union[str, Path],
                   language: Optional[str] = None) -> str:
        """Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language code (e.g., 'fr', 'en'), auto-detect if None
            
        Returns:
            Transcribed text
        """
        if not self.whisper_available:
            raise ImportError(
                "Whisper not installed. Install with: pip install openai-whisper"
            )
        
        import whisper
        
        model = whisper.load_model(self.whisper_model)
        
        result = model.transcribe(
            str(audio_path),
            language=language,
            fp16=False
        )
        
        return result['text']
    
    def transcribe_with_timestamps(self,
                                    audio_path: Union[str, Path],
                                    language: Optional[str] = None) -> List[dict]:
        """Transcribe with word-level timestamps.
        
        Returns:
            List of segments with start, end, and text
        """
        if not self.whisper_available:
            raise ImportError("Whisper not installed")
        
        import whisper
        
        model = whisper.load_model(self.whisper_model)
        result = model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            fp16=False
        )
        
        return result.get('segments', [])


def text_to_speech(text: str,
                   output_path: Union[str, Path],
                   voice: str = 'default') -> Path:
    """Convert text to speech audio file.
    
    Args:
        text: Text to convert
        output_path: Output audio file path
        voice: Voice selection (platform-dependent)
        
    Returns:
        Path to generated audio file
    """
    output_path = Path(output_path)
    
    # Try gTTS first (Google Text-to-Speech)
    try:
        from gtts import gTTS
        
        lang = 'fr' if any(ord(c) > 127 for c in text[:100]) else 'en'
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(output_path))
        
        return output_path
        
    except ImportError:
        pass
    
    # Fallback to pyttsx3 (offline)
    try:
        import pyttsx3
        
        engine = pyttsx3.init()
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        
        return output_path
        
    except ImportError:
        raise ImportError(
            "TTS library not available. Install with:\n"
            "pip install gTTS  # for online\n"
            "pip install pyttsx3  # for offline"
        )


def extract_audio_from_video(video_path: Union[str, Path],
                              output_path: Optional[Union[str, Path]] = None) -> Path:
    """Extract audio track from video file.
    
    Args:
        video_path: Path to video file
        output_path: Output audio path, or auto-generated if None
        
    Returns:
        Path to extracted audio
    """
    video_path = Path(video_path)
    
    if output_path is None:
        output_path = video_path.with_suffix('.mp3')
    else:
        output_path = Path(output_path)
    
    # Use ffmpeg
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path),
        '-vn', '-acodec', 'libmp3lame', '-q:a', '2',
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not installed. Install with: sudo apt install ffmpeg")


def get_audio_duration(audio_path: Union[str, Path]) -> float:
    """Get audio file duration in seconds.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    try:
        from mutagen.mp3 import MP3
        from mutagen.wave import WAVE
        
        path = Path(audio_path)
        
        if path.suffix.lower() == '.mp3':
            audio = MP3(path)
        elif path.suffix.lower() == '.wav':
            audio = WAVE(path)
        else:
            # Use ffprobe
            cmd = [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                str(path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        
        return audio.info.length
        
    except ImportError:
        raise ImportError("mutagen not installed. Install with: pip install mutagen")


# Convenience functions
def transcribe_file(audio_path: Union[str, Path]) -> str:
    """Quick transcribe audio file."""
    processor = AudioProcessor()
    return processor.transcribe(audio_path)


def speak(text: str, output_path: str = 'output.mp3') -> Path:
    """Quick text-to-speech."""
    return text_to_speech(text, output_path)
