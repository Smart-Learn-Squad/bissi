"""Contact management for BISSI.

Provides vCard handling and contact storage.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from utils.helpers import expand_path, ensure_dir, generate_id, save_json, load_json


@dataclass
class Contact:
    """Contact information."""
    name: str
    email: str = ''
    phone: str = ''
    organization: str = ''
    title: str = ''
    address: str = ''
    notes: str = ''
    id: str = ''
    
    def __post_init__(self):
        if not self.id:
            self.id = generate_id(self.name, self.email)


class ContactManager:
    """Contact storage and management."""
    
    def __init__(self, db_path: Union[str, Path] = '~/.bissi/contacts.json'):
        """Initialize contact manager.
        
        Args:
            db_path: Path to contacts database
        """
        self.db_path = expand_path(db_path)
        ensure_dir(self.db_path.parent)
        self.contacts: List[Contact] = []
        self._load()
    
    def _load(self):
        """Load contacts from database."""
        data = load_json(self.db_path)
        if data:
            self.contacts = [Contact(**c) for c in data]
    
    def _save(self):
        """Save contacts to database."""
        data = [asdict(c) for c in self.contacts]
        save_json(data, self.db_path)
    
    def add(self, contact: Contact) -> bool:
        """Add contact.
        
        Args:
            contact: Contact to add
            
        Returns:
            True if added
        """
        # Check for duplicates
        for c in self.contacts:
            if c.id == contact.id:
                return False
        
        self.contacts.append(contact)
        self._save()
        return True
    
    def get(self, contact_id: str) -> Optional[Contact]:
        """Get contact by ID.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Contact or None
        """
        for c in self.contacts:
            if c.id == contact_id:
                return c
        return None
    
    def find_by_name(self, name: str) -> List[Contact]:
        """Find contacts by name.
        
        Args:
            name: Name to search
            
        Returns:
            Matching contacts
        """
        return [c for c in self.contacts if name.lower() in c.name.lower()]
    
    def find_by_email(self, email: str) -> Optional[Contact]:
        """Find contact by email.
        
        Args:
            email: Email to search
            
        Returns:
            Contact or None
        """
        for c in self.contacts:
            if c.email.lower() == email.lower():
                return c
        return None
    
    def update(self, contact_id: str, **kwargs) -> bool:
        """Update contact.
        
        Args:
            contact_id: Contact ID
            **kwargs: Fields to update
            
        Returns:
            True if updated
        """
        contact = self.get(contact_id)
        if not contact:
            return False
        
        for key, value in kwargs.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        
        self._save()
        return True
    
    def delete(self, contact_id: str) -> bool:
        """Delete contact.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            True if deleted
        """
        original_len = len(self.contacts)
        self.contacts = [c for c in self.contacts if c.id != contact_id]
        
        if len(self.contacts) < original_len:
            self._save()
            return True
        return False
    
    def list_all(self) -> List[Contact]:
        """List all contacts."""
        return sorted(self.contacts, key=lambda c: c.name.lower())
    
    def export_vcard(self, contact_id: str, output_path: str) -> bool:
        """Export contact to vCard.
        
        Args:
            contact_id: Contact ID
            output_path: Output vCard path
            
        Returns:
            True if exported
        """
        contact = self.get(contact_id)
        if not contact:
            return False
        
        vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact.name}
N:{contact.name};;;
EMAIL:{contact.email}
TEL:{contact.phone}
ORG:{contact.organization}
TITLE:{contact.title}
ADR:;;{contact.address};;;
NOTE:{contact.notes}
END:VCARD"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vcard)
        
        return True
    
    def import_vcard(self, vcard_path: str) -> bool:
        """Import contact from vCard.
        
        Args:
            vcard_path: Path to vCard file
            
        Returns:
            True if imported
        """
        try:
            import vobject
            
            with open(vcard_path, 'r', encoding='utf-8') as f:
                vcard = vobject.readOne(f.read())
            
            contact = Contact(
                name=str(vcard.fn.value) if hasattr(vcard, 'fn') else '',
                email=str(vcard.email.value) if hasattr(vcard, 'email') else '',
                phone=str(vcard.tel.value) if hasattr(vcard, 'tel') else '',
                organization=str(vcard.org.value[0]) if hasattr(vcard, 'org') else '',
                title=str(vcard.title.value) if hasattr(vcard, 'title') else '',
            )
            
            return self.add(contact)
            
        except ImportError:
            # Simple parser fallback
            with open(vcard_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.strip().split(':', 1)
                    if key == 'FN':
                        data['name'] = value
                    elif key == 'EMAIL':
                        data['email'] = value
                    elif key == 'TEL':
                        data['phone'] = value
                    elif key == 'ORG':
                        data['organization'] = value
            
            contact = Contact(**data)
            return self.add(contact)
    
    def search(self, query: str) -> List[Contact]:
        """Search contacts.
        
        Args:
            query: Search string
            
        Returns:
            Matching contacts
        """
        query = query.lower()
        results = []
        
        for c in self.contacts:
            if (query in c.name.lower() or 
                query in c.email.lower() or
                query in c.organization.lower()):
                results.append(c)
        
        return results


# Convenience functions
def quick_add(name: str, email: str = '', phone: str = '') -> bool:
    """Quick add contact."""
    manager = ContactManager()
    return manager.add(Contact(name=name, email=email, phone=phone))


def find_contact(name: str) -> List[Contact]:
    """Find contacts by name."""
    return ContactManager().find_by_name(name)


def list_contacts() -> List[Contact]:
    """List all contacts."""
    return ContactManager().list_all()
