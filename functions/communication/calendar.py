"""Google Calendar integration for BISSI.

Provides calendar read/write operations using Google Calendar API.
Note: Requires OAuth2 setup and credentials file.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json

from utils.helpers import expand_path, ensure_dir


class GoogleCalendarClient:
    """Google Calendar API client."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize Google Calendar client.
        
        Args:
            credentials_path: Path to OAuth2 credentials JSON file
        """
        self.credentials_path = credentials_path or '~/.bissi/google_credentials.json'
        self.service = None
        self.token_path = expand_path('~/.bissi/google_token.json')
        ensure_dir(self.token_path.parent)
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Google API libraries required. Install with:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.token_path), self.SCOPES
            )
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not expand_path(self.credentials_path).exists():
                    raise FileNotFoundError(
                        f"Google credentials file not found: {self.credentials_path}\n"
                        "Download from Google Cloud Console and save to this location."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(expand_path(self.credentials_path)),
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save token for future runs
            ensure_dir(self.token_path.parent)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def list_calendars(self) -> List[Dict[str, str]]:
        """List all accessible calendars.
        
        Returns:
            List of calendar dictionaries
        """
        calendars = []
        page_token = None
        
        while True:
            calendar_list = self.service.calendarList().list(
                pageToken=page_token
            ).execute()
            
            for calendar in calendar_list['items']:
                calendars.append({
                    'id': calendar['id'],
                    'name': calendar.get('summary', 'Unnamed'),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False)
                })
            
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        
        return calendars
    
    def list_events(self,
                    calendar_id: str = 'primary',
                    days: int = 7,
                    max_results: int = 100) -> List[Dict[str, Any]]:
        """List upcoming events.
        
        Args:
            calendar_id: Calendar to query
            days: Number of days to look ahead
            max_results: Maximum events to return
            
        Returns:
            List of event dictionaries
        """
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days)).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = []
        for event in events_result.get('items', []):
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            events.append({
                'id': event['id'],
                'summary': event.get('summary', 'No title'),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'location': event.get('location', ''),
                'link': event.get('htmlLink', '')
            })
        
        return events
    
    def create_event(self,
                     summary: str,
                     start_time: datetime,
                     end_time: datetime,
                     description: str = '',
                     location: str = '',
                     calendar_id: str = 'primary') -> Dict[str, str]:
        """Create new calendar event.
        
        Args:
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime
            description: Event description
            location: Event location
            calendar_id: Target calendar
            
        Returns:
            Created event info
        """
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            }
        }
        
        result = self.service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        
        return {
            'id': result['id'],
            'summary': result['summary'],
            'link': result.get('htmlLink', '')
        }
    
    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """Delete calendar event.
        
        Args:
            event_id: Event to delete
            calendar_id: Calendar containing event
            
        Returns:
            True if deleted
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False
    
    def quick_add(self, text: str, calendar_id: str = 'primary') -> Dict[str, str]:
        """Quick add event using natural language.
        
        Args:
            text: Event description (e.g., "Meeting tomorrow at 3pm")
            calendar_id: Target calendar
            
        Returns:
            Created event info
        """
        result = self.service.events().quickAdd(
            calendarId=calendar_id,
            text=text
        ).execute()
        
        return {
            'id': result['id'],
            'summary': result['summary'],
            'start': result['start'].get('dateTime', result['start'].get('date'))
        }


def get_upcoming_events(days: int = 7) -> List[Dict[str, Any]]:
    """Convenience function to get upcoming events.
    
    Args:
        days: Number of days to look ahead
        
    Returns:
        List of events
    """
    client = GoogleCalendarClient()
    return client.list_events(days=days)


def add_event(summary: str,
              start: datetime,
              end: datetime,
              description: str = '') -> Dict[str, str]:
    """Convenience function to add event.
    
    Args:
        summary: Event title
        start: Start datetime
        end: End datetime
        description: Event description
        
    Returns:
        Created event info
    """
    client = GoogleCalendarClient()
    return client.create_event(summary, start, end, description)


def is_configured() -> bool:
    """Check if Google Calendar is configured."""
    cred_path = expand_path('~/.bissi/google_credentials.json')
    token_path = expand_path('~/.bissi/google_token.json')
    return cred_path.exists() or token_path.exists()
