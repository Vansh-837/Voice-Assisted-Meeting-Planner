from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Meeting:
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    attendees: Optional[List[str]] = None
    location: Optional[str] = None
    event_id: Optional[str] = None  # Google Calendar event ID for deletion
    
    def __str__(self):
        return f"{self.title} ({self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')})"

@dataclass
class TimeSlot:
    start_time: datetime
    end_time: datetime
    
    def __str__(self):
        return f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"