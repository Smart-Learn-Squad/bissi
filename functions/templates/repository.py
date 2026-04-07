"""Template repository for BISSI.

Provides storage and management for document templates.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class TemplateRepository:
    """Storage and management for document templates."""
    
    def __init__(self, repo_dir: Union[str, Path] = '~/.bissi/templates'):
        """Initialize template repository.
        
        Args:
            repo_dir: Directory for template storage
        """
        self.repo_dir = Path(repo_dir).expanduser()
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.repo_dir / 'index.json'
        self._load_index()
    
    def _load_index(self):
        """Load template index."""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
        else:
            self.index = {}
            self._save_index()
    
    def _save_index(self):
        """Save template index."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2)
    
    def add_template(self,
                     name: str,
                     content: str,
                     description: str = '',
                     variables: Optional[List[str]] = None,
                     category: str = 'general') -> bool:
        """Add template to repository.
        
        Args:
            name: Template name
            content: Template content
            description: Template description
            variables: List of required variables
            category: Template category
            
        Returns:
            True if added successfully
        """
        try:
            # Save template file
            template_file = self.repo_dir / f'{name}.j2'
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update index
            self.index[name] = {
                'description': description,
                'variables': variables or [],
                'category': category,
                'created': datetime.now().isoformat(),
                'updated': datetime.now().isoformat(),
                'file': str(template_file)
            }
            self._save_index()
            
            return True
            
        except Exception as e:
            print(f"Error adding template: {e}")
            return False
    
    def get_template(self, name: str) -> Optional[str]:
        """Get template content by name.
        
        Args:
            name: Template name
            
        Returns:
            Template content or None
        """
        if name not in self.index:
            return None
        
        template_file = Path(self.index[name]['file'])
        
        if not template_file.exists():
            return None
        
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get template metadata.
        
        Args:
            name: Template name
            
        Returns:
            Template info or None
        """
        return self.index.get(name)
    
    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all templates.
        
        Args:
            category: Filter by category
            
        Returns:
            List of template info
        """
        templates = []
        
        for name, info in self.index.items():
            if category is None or info.get('category') == category:
                templates.append({
                    'name': name,
                    **info
                })
        
        return sorted(templates, key=lambda x: x['name'])
    
    def delete_template(self, name: str) -> bool:
        """Delete template from repository.
        
        Args:
            name: Template name
            
        Returns:
            True if deleted
        """
        if name not in self.index:
            return False
        
        try:
            # Remove file
            template_file = Path(self.index[name]['file'])
            if template_file.exists():
                template_file.unlink()
            
            # Remove from index
            del self.index[name]
            self._save_index()
            
            return True
            
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
    
    def update_template(self,
                       name: str,
                       content: Optional[str] = None,
                       description: Optional[str] = None,
                       variables: Optional[List[str]] = None) -> bool:
        """Update existing template.
        
        Args:
            name: Template name
            content: New content (optional)
            description: New description (optional)
            variables: New variables list (optional)
            
        Returns:
            True if updated
        """
        if name not in self.index:
            return False
        
        try:
            # Update content if provided
            if content is not None:
                template_file = Path(self.index[name]['file'])
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Update metadata
            if description is not None:
                self.index[name]['description'] = description
            
            if variables is not None:
                self.index[name]['variables'] = variables
            
            self.index[name]['updated'] = datetime.now().isoformat()
            self._save_index()
            
            return True
            
        except Exception as e:
            print(f"Error updating template: {e}")
            return False
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """Search templates by name or description.
        
        Args:
            query: Search string
            
        Returns:
            Matching templates
        """
        results = []
        query_lower = query.lower()
        
        for name, info in self.index.items():
            if (query_lower in name.lower() or 
                query_lower in info.get('description', '').lower()):
                results.append({
                    'name': name,
                    **info
                })
        
        return results
    
    def export_template(self, name: str, output_path: Union[str, Path]) -> bool:
        """Export template to file.
        
        Args:
            name: Template name
            output_path: Export file path
            
        Returns:
            True if exported
        """
        content = self.get_template(name)
        if content is None:
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error exporting template: {e}")
            return False
    
    def import_template(self, file_path: Union[str, Path],
                       name: Optional[str] = None,
                       description: str = '') -> bool:
        """Import template from file.
        
        Args:
            file_path: Source file
            name: Template name (default: filename)
            description: Template description
            
        Returns:
            True if imported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            template_name = name or file_path.stem
            
            # Extract variables from template
            import re
            variables = list(set(re.findall(r'\{\{\s*(\w+)\s*\}\}', content)))
            
            return self.add_template(
                template_name,
                content,
                description,
                variables
            )
            
        except Exception as e:
            print(f"Error importing template: {e}")
            return False


# Convenience functions
def get_repo() -> TemplateRepository:
    """Get default template repository."""
    return TemplateRepository()


def list_all_templates() -> List[Dict[str, Any]]:
    """List all templates in default repository."""
    return get_repo().list_templates()


def quick_add_template(name: str, content: str) -> bool:
    """Quick add template."""
    return get_repo().add_template(name, content)
