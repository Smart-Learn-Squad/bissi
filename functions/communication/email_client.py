"""Email client for BISSI.

Provides IMAP/SMTP email operations.
"""
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.parser import BytesParser
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


class EmailClient:
    """IMAP/SMTP email client."""
    
    def __init__(self,
                 imap_server: str,
                 smtp_server: str,
                 username: str,
                 password: str,
                 imap_port: int = 993,
                 smtp_port: int = 587):
        """Initialize email client.
        
        Args:
            imap_server: IMAP server address
            smtp_server: SMTP server address
            username: Email address
            password: Email password
            imap_port: IMAP port (default 993)
            smtp_port: SMTP port (default 587)
        """
        self.imap_server = imap_server
        self.smtp_server = smtp_server
        self.username = username
        self.password = password
        self.imap_port = imap_port
        self.smtp_port = smtp_port
        
        self.imap_conn: Optional[imaplib.IMAP4_SSL] = None
        self.smtp_conn: Optional[smtplib.SMTP] = None
    
    def connect_imap(self) -> bool:
        """Connect to IMAP server."""
        try:
            self.imap_conn = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap_conn.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"IMAP connection error: {e}")
            return False
    
    def connect_smtp(self) -> bool:
        """Connect to SMTP server."""
        try:
            self.smtp_conn = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.smtp_conn.starttls()
            self.smtp_conn.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"SMTP connection error: {e}")
            return False
    
    def disconnect(self):
        """Close all connections."""
        if self.imap_conn:
            try:
                self.imap_conn.logout()
            except:
                pass
            self.imap_conn = None
        
        if self.smtp_conn:
            try:
                self.smtp_conn.quit()
            except:
                pass
            self.smtp_conn = None
    
    def list_folders(self) -> List[str]:
        """List email folders/mailboxes."""
        if not self.imap_conn:
            if not self.connect_imap():
                return []
        
        _, folders = self.imap_conn.list()
        return [f.decode().split('"/"')[-1].strip().strip('"') for f in folders]
    
    def search_emails(self,
                   folder: str = 'INBOX',
                   criteria: str = 'ALL',
                   limit: int = 50) -> List[Dict[str, Any]]:
        """Search emails by criteria.
        
        Args:
            folder: Mailbox folder
            criteria: Search criteria (ALL, UNSEEN, FROM, SUBJECT, etc.)
            limit: Maximum results
            
        Returns:
            List of email summaries
        """
        if not self.imap_conn:
            if not self.connect_imap():
                return []
        
        self.imap_conn.select(folder)
        
        _, messages = self.imap_conn.search(None, criteria)
        email_ids = messages[0].split()
        
        # Get last N emails
        email_ids = email_ids[-limit:]
        
        emails = []
        for eid in reversed(email_ids):
            _, msg_data = self.imap_conn.fetch(eid, '(RFC822)')
            
            msg = BytesParser().parsebytes(msg_data[0][1])
            
            emails.append({
                'id': eid.decode(),
                'subject': msg.get('Subject', 'No Subject'),
                'from': msg.get('From', 'Unknown'),
                'to': msg.get('To', ''),
                'date': msg.get('Date', ''),
                'body': self._get_body(msg)
            })
        
        return emails
    
    def _get_body(self, msg) -> str:
        """Extract email body."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == 'text/html':
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        return ''
    
    def send_email(self,
                   to: Union[str, List[str]],
                   subject: str,
                   body: str,
                   html: bool = False) -> bool:
        """Send email.
        
        Args:
            to: Recipient email(s)
            subject: Email subject
            body: Email body
            html: Send as HTML
            
        Returns:
            True if sent
        """
        if not self.smtp_conn:
            if not self.connect_smtp():
                return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to) if isinstance(to, list) else to
            msg['Subject'] = subject
            
            content_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, content_type))
            
            self.smtp_conn.send_message(msg)
            return True
            
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def mark_as_read(self, email_id: str, folder: str = 'INBOX') -> bool:
        """Mark email as read."""
        if not self.imap_conn:
            if not self.connect_imap():
                return False
        
        try:
            self.imap_conn.select(folder)
            self.imap_conn.store(email_id.encode(), '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            print(f"Mark read error: {e}")
            return False
    
    def delete_email(self, email_id: str, folder: str = 'INBOX') -> bool:
        """Delete email."""
        if not self.imap_conn:
            if not self.connect_imap():
                return False
        
        try:
            self.imap_conn.select(folder)
            self.imap_conn.store(email_id.encode(), '+FLAGS', '\\Deleted')
            self.imap_conn.expunge()
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# Common email providers presets
EMAIL_PROVIDERS = {
    'gmail': {
        'imap': 'imap.gmail.com',
        'smtp': 'smtp.gmail.com',
        'imap_port': 993,
        'smtp_port': 587
    },
    'outlook': {
        'imap': 'outlook.office365.com',
        'smtp': 'smtp.office365.com',
        'imap_port': 993,
        'smtp_port': 587
    },
    'yahoo': {
        'imap': 'imap.mail.yahoo.com',
        'smtp': 'smtp.mail.yahoo.com',
        'imap_port': 993,
        'smtp_port': 587
    }
}


def create_client(provider: str, username: str, password: str) -> EmailClient:
    """Create client for common provider.
    
    Args:
        provider: Provider name (gmail, outlook, yahoo)
        username: Email address
        password: Password
        
    Returns:
        Configured EmailClient
    """
    if provider not in EMAIL_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    
    settings = EMAIL_PROVIDERS[provider]
    
    return EmailClient(
        imap_server=settings['imap'],
        smtp_server=settings['smtp'],
        username=username,
        password=password,
        imap_port=settings['imap_port'],
        smtp_port=settings['smtp_port']
    )
