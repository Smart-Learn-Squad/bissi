"""Template engine for BISSI.

Provides Jinja2-based document template processing.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Union
from jinja2 import Environment, FileSystemLoader, BaseLoader, Template
import json


class TemplateEngine:
    """Jinja2 template processing engine."""
    
    def __init__(self, templates_dir: Optional[Union[str, Path]] = None):
        """Initialize template engine.
        
        Args:
            templates_dir: Directory with template files, or None for string templates
        """
        if templates_dir:
            self.loader = FileSystemLoader(str(templates_dir))
            self.env = Environment(loader=self.loader)
        else:
            self.loader = None
            self.env = Environment(loader=BaseLoader())
        
        # Add custom filters
        self.env.filters['currency'] = self._format_currency
        self.env.filters['percentage'] = self._format_percentage
        self.env.filters['date'] = self._format_date
    
    @staticmethod
    def _format_currency(value: float, symbol: str = '€') -> str:
        """Format as currency."""
        return f"{value:,.2f} {symbol}"
    
    @staticmethod
    def _format_percentage(value: float) -> str:
        """Format as percentage."""
        return f"{value:.1f}%"
    
    @staticmethod
    def _format_date(value: str, format: str = '%d/%m/%Y') -> str:
        """Format date string."""
        from datetime import datetime
        try:
            dt = datetime.strptime(value, '%Y-%m-%d')
            return dt.strftime(format)
        except:
            return value
    
    def load_template(self, template_name: str) -> Template:
        """Load template from file.
        
        Args:
            template_name: Template file name
            
        Returns:
            Jinja2 Template object
        """
        return self.env.get_template(template_name)
    
    def load_template_from_string(self, template_string: str) -> Template:
        """Load template from string.
        
        Args:
            template_string: Template content
            
        Returns:
            Jinja2 Template object
        """
        return self.env.from_string(template_string)
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render template with context.
        
        Args:
            template_name: Template file name
            context: Variables for template
            
        Returns:
            Rendered output
        """
        template = self.load_template(template_name)
        return template.render(**context)
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render string template with context.
        
        Args:
            template_string: Template content
            context: Variables for template
            
        Returns:
            Rendered output
        """
        template = self.load_template_from_string(template_string)
        return template.render(**context)
    
    def render_to_file(self,
                       template_name: str,
                       context: Dict[str, Any],
                       output_path: Union[str, Path]) -> Path:
        """Render template and save to file.
        
        Args:
            template_name: Template file name
            context: Variables for template
            output_path: Output file path
            
        Returns:
            Path to rendered file
        """
        rendered = self.render(template_name, context)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered)
        
        return output_path


def process_document_template(template_path: Union[str, Path],
                              context: Dict[str, Any],
                              output_path: Union[str, Path]) -> Path:
    """Process a document template with variable substitution.
    
    Args:
        template_path: Path to template file
        context: Variables to substitute
        output_path: Output document path
        
    Returns:
        Path to generated document
    """
    template_path = Path(template_path)
    template_dir = template_path.parent
    template_name = template_path.name
    
    engine = TemplateEngine(template_dir)
    return engine.render_to_file(template_name, context, output_path)


def quick_render(template_string: str, **kwargs) -> str:
    """Quick render template string with variables.
    
    Args:
        template_string: Template content
        **kwargs: Template variables
        
    Returns:
        Rendered string
    """
    engine = TemplateEngine()
    return engine.render_string(template_string, kwargs)


# Common document templates
DOCUMENT_TEMPLATES = {
    'report': """
# {{ title }}

**Date:** {{ date }}
**Author:** {{ author }}

## Summary

{{ summary }}

## Details

{% for item in items %}
- {{ item }}
{% endfor %}

## Conclusion

{{ conclusion }}
""",

    'letter': """
{{ date }}

{{ recipient_name }}
{{ recipient_address }}

Dear {{ recipient_name }},

{{ body }}

Sincerely,

{{ sender_name }}
{{ sender_address }}
""",

    'meeting_notes': """
# Meeting: {{ title }}

**Date:** {{ date }}
**Attendees:** {{ attendees | join(', ') }}

## Agenda

{% for item in agenda %}
1. {{ item }}
{% endfor %}

## Notes

{{ notes }}

## Action Items

{% for item in action_items %}
- [ ] {{ item }}
{% endfor %}
"""
}


def get_template(name: str) -> str:
    """Get built-in template by name."""
    return DOCUMENT_TEMPLATES.get(name, '')
