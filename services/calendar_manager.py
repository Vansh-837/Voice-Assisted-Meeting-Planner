import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from config.settings import Config
from models.meeting import Meeting, TimeSlot

# Import our tracing system
from config.logger import trace_function, trace_api_call, logger

class CalendarManager:
    @trace_function
    def __init__(self):
        self.config = Config()
        self.service = None
        self.timezone = pytz.timezone(self.config.DEFAULT_TIMEZONE)
        self._authenticate()
    
    @trace_function
    @trace_api_call("Google_Auth", "authenticate")
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.config.TOKEN_PATH):
            try:
                with open(self.config.TOKEN_PATH, 'r') as token:
                    token_data = json.load(token)
                    creds = Credentials.from_authorized_user_info(token_data, self.config.SCOPES)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading token file: {e}")
                # Delete corrupted token file
                os.remove(self.config.TOKEN_PATH)
                creds = None
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.GOOGLE_CREDENTIALS_PATH, self.config.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.config.TOKEN_PATH, 'w') as token:
                token_data = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                json.dump(token_data, token, indent=2)
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    @trace_function
    @trace_api_call("Google_Calendar", "list_events")
    def get_events(self, start_date: datetime, end_date: datetime) -> List[Meeting]:
        """Get events between start and end dates"""
        try:
            # Ensure dates are timezone-aware and convert to UTC
            if start_date.tzinfo is None:
                start_date = self.timezone.localize(start_date)
            if end_date.tzinfo is None:
                end_date = self.timezone.localize(end_date)
            
            # Convert to UTC for API request
            start_utc = start_date.astimezone(pytz.UTC)
            end_utc = end_date.astimezone(pytz.UTC)
            
            # Format as RFC3339 strings
            start_time = start_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            end_time = end_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            events_result = self.service.events().list(
                calendarId=self.config.CALENDAR_ID,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            meetings = []
            
            for event in events:
                meeting = self._event_to_meeting(event)
                if meeting:
                    meetings.append(meeting)
            
            return meetings
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    @trace_function
    @trace_api_call("Google_Calendar", "create_event")
    def create_event(self, meeting: Meeting) -> bool:
        """Create a new calendar event"""
        try:
            # Ensure meeting times are timezone-aware
            start_time = meeting.start_time
            end_time = meeting.end_time
            
            if start_time.tzinfo is None:
                start_time = self.timezone.localize(start_time)
            if end_time.tzinfo is None:
                end_time = self.timezone.localize(end_time)
            
            event_body = {
                'summary': meeting.title,
                'description': meeting.description or '',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': str(start_time.tzinfo),
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': str(end_time.tzinfo),
                },
            }
            
            # Add attendees if provided
            if meeting.attendees:
                event_body['attendees'] = [{'email': email} for email in meeting.attendees]
            
            # Add location if provided
            if meeting.location:
                event_body['location'] = meeting.location
            
            event = self.service.events().insert(
                calendarId=self.config.CALENDAR_ID,
                body=event_body
            ).execute()
            
            print(f"Event created: {event.get('htmlLink')}")
            return True
            
        except HttpError as error:
            print(f"An error occurred while creating event: {error}")
            return False
    
    @trace_function
    @trace_api_call("Google_Calendar", "delete_event")
    def delete_event(self, meeting: Meeting) -> bool:
        """Delete a calendar event"""
        try:
            if not hasattr(meeting, 'event_id') or not meeting.event_id:
                print("Cannot delete event: No event ID available")
                return False
            
            self.service.events().delete(
                calendarId=self.config.CALENDAR_ID,
                eventId=meeting.event_id
            ).execute()
            
            print(f"Event '{meeting.title}' deleted successfully")
            return True
            
        except HttpError as error:
            print(f"An error occurred while deleting event: {error}")
            return False
    
    @trace_function
    def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if a time slot is available"""
        # Ensure times are timezone-aware
        if start_time.tzinfo is None:
            start_time = self.timezone.localize(start_time)
        if end_time.tzinfo is None:
            end_time = self.timezone.localize(end_time)
            
        existing_events = self.get_events(start_time, end_time)
        return len(existing_events) == 0
    
    @trace_function
    def find_available_slots(self, date: datetime, duration: timedelta, 
                           num_suggestions: int = 3) -> List[TimeSlot]:
        """Find available time slots on a given date"""
        available_slots = []
        
        # Ensure the input date is timezone-aware
        if date.tzinfo is None:
            date = self.timezone.localize(date)
        
        # Create timezone-aware start and end of day
        start_of_day = date.replace(hour=self.config.BUSINESS_HOURS_START, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=self.config.BUSINESS_HOURS_END, minute=0, second=0, microsecond=0)
        
        # Get existing events for the day
        existing_events = self.get_events(start_of_day, end_of_day)
        existing_events.sort(key=lambda x: x.start_time)
        
        current_time = start_of_day
        
        for event in existing_events:
            # Check if there's a gap before this event
            if current_time + duration <= event.start_time:
                available_slots.append(TimeSlot(current_time, current_time + duration))
                if len(available_slots) >= num_suggestions:
                    break
            current_time = max(current_time, event.end_time)
        
        # Check if there's time after the last event
        if len(available_slots) < num_suggestions and current_time + duration <= end_of_day:
            available_slots.append(TimeSlot(current_time, current_time + duration))
        
        return available_slots[:num_suggestions]
    
    @trace_function
    def get_todays_events(self) -> List[Meeting]:
        """Get today's events"""
        now = datetime.now(self.timezone)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return self.get_events(start_of_day, end_of_day)
    
    def get_events_with_person(self, person_email: str, days_ahead: int = 7) -> List[Meeting]:
        """Get events with a specific person in the coming days"""
        start_date = datetime.now(self.timezone)
        end_date = start_date + timedelta(days=days_ahead)
        all_events = self.get_events(start_date, end_date)
        
        return [event for event in all_events 
                if event.attendees and person_email in event.attendees]
    
    @trace_function
    def find_meetings(self, identifier: str, query_date: str = None) -> List[Meeting]:
        """Find meetings that match the given identifier (title, time, etc.)"""
        try:
            # Determine search date range
            if query_date:
                start_date = datetime.fromisoformat(query_date)
                end_date = start_date + timedelta(days=1)
            else:
                # Search from beginning of today to 30 days ahead
                now = datetime.now(self.timezone)
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=30)
            
            all_meetings = self.get_events(start_date, end_date)
            matching_meetings = []
            
            identifier_lower = identifier.lower()
            
            # Extract potential email addresses from the identifier
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            extracted_emails = re.findall(email_pattern, identifier)
            
            for meeting in all_meetings:
                match_found = False
                
                # Check if identifier matches title
                if identifier_lower in meeting.title.lower():
                    matching_meetings.append(meeting)
                    match_found = True
                
                # Check if any extracted email addresses match meeting attendees
                if not match_found and extracted_emails and meeting.attendees:
                    for email in extracted_emails:
                        if email.lower() in [attendee.lower() for attendee in meeting.attendees]:
                            matching_meetings.append(meeting)
                            match_found = True
                            break
                
                # Check if identifier matches a time pattern
                if not match_found and any(time_part in identifier_lower for time_part in 
                        [meeting.start_time.strftime('%H:%M').lower(), 
                         meeting.start_time.strftime('%I:%M %p').lower(),
                         meeting.start_time.strftime('%Y-%m-%d').lower()]):
                    matching_meetings.append(meeting)
            
            return matching_meetings
        except Exception as e:
            print(f"Error finding meetings: {e}")
            return []
    
    @trace_function
    def find_similar_meetings(self, identifier: str, query_date: str = None, similarity_threshold: float = 0.6) -> List[Meeting]:
        """Find meetings with similar titles using fuzzy matching"""
        try:
            # Determine search date range
            if query_date:
                start_date = datetime.fromisoformat(query_date)
                end_date = start_date + timedelta(days=1)
            else:
                # Search from beginning of today to 30 days ahead
                now = datetime.now(self.timezone)
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=30)
            
            all_meetings = self.get_events(start_date, end_date)
            similar_meetings = []
            
            identifier_lower = identifier.lower()
            identifier_words = set(identifier_lower.split())
            
            for meeting in all_meetings:
                meeting_title_lower = meeting.title.lower()
                meeting_words = set(meeting_title_lower.split())
                
                # Calculate similarity based on common words
                if identifier_words and meeting_words:
                    common_words = identifier_words.intersection(meeting_words)
                    similarity = len(common_words) / len(identifier_words.union(meeting_words))
                    
                    if similarity >= similarity_threshold:
                        similar_meetings.append((meeting, similarity))
                
                # Also check for partial word matches (e.g., "review" in "project review")
                elif any(word in meeting_title_lower for word in identifier_words if len(word) > 2):
                    similar_meetings.append((meeting, 0.5))  # Lower similarity for partial matches
            
            # Sort by similarity score (descending) and return just the meetings
            similar_meetings.sort(key=lambda x: x[1], reverse=True)
            return [meeting for meeting, _ in similar_meetings[:5]]  # Return top 5 similar meetings
            
        except Exception as e:
            print(f"Error finding similar meetings: {e}")
            return []
    
    def _event_to_meeting(self, event: Dict[str, Any]) -> Optional[Meeting]:
        """Convert Google Calendar event to Meeting object"""
        try:
            # Handle different datetime formats
            start = event['start']
            end = event['end']
            
            if 'dateTime' in start:
                # Parse timezone-aware datetime
                start_time_str = start['dateTime']
                end_time_str = end['dateTime']
                
                # Handle different timezone formats
                if start_time_str.endswith('Z'):
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                else:
                    start_time = datetime.fromisoformat(start_time_str)
                    end_time = datetime.fromisoformat(end_time_str)
                
                # Convert to local timezone
                start_time = start_time.astimezone(self.timezone)
                end_time = end_time.astimezone(self.timezone)
            else:
                # All-day event - create timezone-aware datetime
                start_date = datetime.fromisoformat(start['date'])
                end_date = datetime.fromisoformat(end['date'])
                
                start_time = self.timezone.localize(start_date)
                end_time = self.timezone.localize(end_date)
            
            attendees = []
            if 'attendees' in event:
                attendees = [attendee.get('email', '') for attendee in event['attendees']]
            
            return Meeting(
                title=event.get('summary', 'No Title'),
                start_time=start_time,
                end_time=end_time,
                description=event.get('description', ''),
                attendees=attendees,
                location=event.get('location', ''),
                event_id=event.get('id', '')  # Store the Google Calendar event ID
            )
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None