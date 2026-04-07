"""Configuration settings for BISSI.

Global settings and configuration management.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict


@dataclass
class ModelConfig:
    """LLM model configuration."""
    name: str = 'gemma4:e2b'
    temperature: float = 0.7
    context_window: int = 8192
    max_tokens: int = 2048


@dataclass
class MemoryConfig:
    """Memory and storage configuration."""
    conversation_db: str = '~/.bissi/conversations.db'
    vector_store_path: str = '~/.bissi/vector_store'
    max_history: int = 100
    backup_enabled: bool = True


@dataclass
class OfficeConfig:
    """Office suite configuration."""
    default_word_template: Optional[str] = None
    default_excel_sheet: str = 'Sheet1'
    ocr_language: str = 'fra+eng'
    ocr_dpi: int = 300


@dataclass
class SystemConfig:
    """System integration configuration."""
    clipboard_enabled: bool = True
    screenshot_enabled: bool = False
    notifications_enabled: bool = True


class Settings:
    """BISSI global settings manager."""
    
    CONFIG_FILE = '~/.bissi/config.json'
    
    def __init__(self):
        """Initialize settings with defaults."""
        self.model = ModelConfig()
        self.memory = MemoryConfig()
        self.office = OfficeConfig()
        self.system = SystemConfig()
        
        # Load saved settings if exist
        self._load()
    
    def _get_config_path(self) -> Path:
        """Get configuration file path."""
        return Path(self.CONFIG_FILE).expanduser()
    
    def _load(self):
        """Load settings from config file."""
        config_path = self._get_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                
                # Update configurations
                if 'model' in data:
                    self.model = ModelConfig(**data['model'])
                if 'memory' in data:
                    self.memory = MemoryConfig(**data['memory'])
                if 'office' in data:
                    self.office = OfficeConfig(**data['office'])
                if 'system' in data:
                    self.system = SystemConfig(**data['system'])
                    
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
    
    def save(self):
        """Save current settings to config file."""
        config_path = self._get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'model': asdict(self.model),
            'memory': asdict(self.memory),
            'office': asdict(self.office),
            'system': asdict(self.system)
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value by key path.
        
        Args:
            key: Dot-notation key (e.g., 'model.name', 'memory.max_history')
            default: Default value if not found
            
        Returns:
            Setting value
        """
        parts = key.split('.')
        
        if len(parts) != 2:
            return default
        
        section, setting = parts
        config = getattr(self, section, None)
        
        if config and hasattr(config, setting):
            return getattr(config, setting)
        
        return default
    
    def set(self, key: str, value: Any):
        """Set setting value by key path.
        
        Args:
            key: Dot-notation key
            value: Value to set
        """
        parts = key.split('.')
        
        if len(parts) != 2:
            raise ValueError(f"Invalid key format: {key}")
        
        section, setting = parts
        config = getattr(self, section, None)
        
        if config and hasattr(config, setting):
            setattr(config, setting, value)
            self.save()
        else:
            raise ValueError(f"Unknown setting: {key}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings as dictionary."""
        return {
            'model': asdict(self.model),
            'memory': asdict(self.memory),
            'office': asdict(self.office),
            'system': asdict(self.system)
        }
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.model = ModelConfig()
        self.memory = MemoryConfig()
        self.office = OfficeConfig()
        self.system = SystemConfig()
        self.save()


# Global settings instance
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def get_model_name() -> str:
    """Get configured model name."""
    return get_settings().model.name


def get_model_temperature() -> float:
    """Get configured model temperature."""
    return get_settings().model.temperature
