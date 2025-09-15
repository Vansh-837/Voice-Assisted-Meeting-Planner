from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.meeting import Meeting, TimeSlot
from services.calendar_manager import CalendarManager

# Import our tracing system
from config.logger import trace_function, logger

class SchedulerLogic:
    @trace_function
    def __init__(self, calendar_manager: CalendarManager):
        self.calendar_manager = calendar_manager
    
    @trace_function
    def schedule_meeting(self, meeting_data: dict) -> Tuple[bool, str, List[TimeSlot]]:
        """
        Attempt to schedule a meeting, return success status, message, and alternatives if needed
        """
        try:
            # Check if this is a recurring meeting
            recurrence_pattern = meeting_data.get('recurrence_pattern')
            recurrence_count = meeting_data.get('recurrence_count')
            recurrence_days = meeting_data.get('recurrence_days', [])
            
            if recurrence_pattern and recurrence_count:
                # Handle recurring meeting
                return self._schedule_recurring_meeting(meeting_data)
            else:
                # Handle single meeting
                return self._schedule_single_meeting(meeting_data)
                
        except Exception as e:
            return False, f"Error scheduling meeting: {str(e)}", []
    
    @trace_function
    def _schedule_single_meeting(self, meeting_data: dict) -> Tuple[bool, str, List[TimeSlot]]:
        """Schedule a single meeting"""
        try:
            # Parse meeting data
            title = meeting_data.get('meeting_title', 'Untitled Meeting')
            start_time = datetime.fromisoformat(meeting_data.get('start_datetime'))
            
            # Ensure start_time is timezone-aware
            if start_time.tzinfo is None:
                start_time = self.calendar_manager.timezone.localize(start_time)
            
            duration_minutes = meeting_data.get('duration_minutes', 60)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Create meeting object
            meeting = Meeting(
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=meeting_data.get('meeting_description', ''),
                attendees=meeting_data.get('attendees', []),
                location=meeting_data.get('location', '')
            )
            
            # Check availability
            if self.calendar_manager.check_availability(start_time, end_time):
                # Time slot is available, create the meeting
                success = self.calendar_manager.create_event(meeting)
                if success:
                    return True, "Meeting scheduled successfully!", []
                else:
                    return False, "Failed to create the meeting.", []
            else:
                # Time slot is not available, find better alternatives
                alternatives = self.find_nearby_available_slots(
                    start_time, 
                    timedelta(minutes=duration_minutes)
                )
                return False, "Time slot is already booked.", alternatives
                
        except Exception as e:
            return False, f"Error scheduling single meeting: {str(e)}", []
    
    @trace_function
    def _schedule_recurring_meeting(self, meeting_data: dict) -> Tuple[bool, str, List[TimeSlot]]:
        """Schedule recurring meetings"""
        try:
            # Parse meeting data
            title = meeting_data.get('meeting_title', 'Untitled Meeting')
            start_time = datetime.fromisoformat(meeting_data.get('start_datetime'))
            
            # Ensure start_time is timezone-aware
            if start_time.tzinfo is None:
                start_time = self.calendar_manager.timezone.localize(start_time)
            
            duration_minutes = meeting_data.get('duration_minutes', 60)
            recurrence_pattern = meeting_data.get('recurrence_pattern')
            recurrence_count = meeting_data.get('recurrence_count')
            recurrence_days = meeting_data.get('recurrence_days', [])
            
            # Generate all meeting dates
            meeting_dates = self._generate_recurring_dates(
                start_time, recurrence_pattern, recurrence_count, recurrence_days
            )
            
            if not meeting_dates:
                return False, "Could not generate recurring meeting dates.", []
            
            # Check availability for all dates
            conflicts = []
            for meeting_date in meeting_dates:
                end_time = meeting_date + timedelta(minutes=duration_minutes)
                if not self.calendar_manager.check_availability(meeting_date, end_time):
                    conflicts.append(meeting_date)
            
            if conflicts:
                # Some dates have conflicts
                conflict_dates = [dt.strftime('%B %d, %Y at %I:%M %p') for dt in conflicts[:3]]
                return False, f"Some meeting times conflict with existing events: {', '.join(conflict_dates)}", []
            
            # All dates are available, create all meetings
            created_count = 0
            for i, meeting_date in enumerate(meeting_dates):
                end_time = meeting_date + timedelta(minutes=duration_minutes)
                
                # Create individual meeting with original title (no occurrence number)
                meeting = Meeting(
                    title=title,
                    start_time=meeting_date,
                    end_time=end_time,
                    description=meeting_data.get('meeting_description', ''),
                    attendees=meeting_data.get('attendees', []),
                    location=meeting_data.get('location', '')
                )
                
                if self.calendar_manager.create_event(meeting):
                    created_count += 1
                else:
                    print(f"Failed to create meeting for {meeting_date}")
            
            if created_count == len(meeting_dates):
                return True, f"Successfully scheduled {created_count} recurring meetings!", []
            elif created_count > 0:
                return True, f"Successfully scheduled {created_count} out of {len(meeting_dates)} meetings.", []
            else:
                return False, "Failed to create any recurring meetings.", []
                
        except Exception as e:
            return False, f"Error scheduling recurring meeting: {str(e)}", []
    
    @trace_function
    def _generate_recurring_dates(self, start_time: datetime, pattern: str, count: int, days: List[str]) -> List[datetime]:
        """Generate list of dates for recurring meetings"""
        try:
            dates = []
            current_date = start_time
            
            if pattern == "daily":
                for i in range(count):
                    dates.append(current_date + timedelta(days=i))
            
            elif pattern == "weekly":
                if days:
                    # Specific days of the week
                    day_mapping = {
                        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                        'friday': 4, 'saturday': 5, 'sunday': 6
                    }
                    target_weekdays = [day_mapping.get(day.lower()) for day in days if day.lower() in day_mapping]
                    
                    if target_weekdays:
                        # Check if the start_time is already on the correct day
                        start_weekday = current_date.weekday()
                        if start_weekday in target_weekdays:
                            # Start_time is already on the correct day, use it directly
                            first_occurrence = current_date
                        else:
                            # Find the first occurrence (next occurrence of the target day)
                            first_target_day = min(target_weekdays)
                            
                            # Calculate days until the next occurrence of the target day
                            if first_target_day > start_weekday:
                                # Target day is later this week
                                days_until_first = first_target_day - start_weekday
                            elif first_target_day < start_weekday:
                                # Target day is next week
                                days_until_first = 7 - (start_weekday - first_target_day)
                            else:
                                # Today is the target day - check if we can schedule today or need next week
                                # For now, always schedule for next week if it's the same day
                                days_until_first = 7
                            
                            first_occurrence = current_date + timedelta(days=days_until_first)
                        
                        # Generate occurrences
                        for i in range(count):
                            occurrence_date = first_occurrence + timedelta(weeks=i)
                            dates.append(occurrence_date)
                else:
                    # Weekly on the same day as start_time
                    for i in range(count):
                        dates.append(current_date + timedelta(weeks=i))
            
            elif pattern == "monthly":
                for i in range(count):
                    # Add months (approximate - may need more sophisticated date handling)
                    month_offset = i
                    year_offset = month_offset // 12
                    month_offset = month_offset % 12
                    
                    new_year = current_date.year + year_offset
                    new_month = current_date.month + month_offset
                    if new_month > 12:
                        new_year += 1
                        new_month -= 12
                    
                    try:
                        new_date = current_date.replace(year=new_year, month=new_month)
                        dates.append(new_date)
                    except ValueError:
                        # Handle cases like Feb 31st -> Feb 28th
                        import calendar
                        last_day = calendar.monthrange(new_year, new_month)[1]
                        if current_date.day > last_day:
                            new_date = current_date.replace(year=new_year, month=new_month, day=last_day)
                        else:
                            new_date = current_date.replace(year=new_year, month=new_month)
                        dates.append(new_date)
            
            return dates
            
        except Exception as e:
            print(f"Error generating recurring dates: {e}")
            return []
    
    @trace_function
    def find_nearby_available_slots(self, preferred_time: datetime, 
                                  duration: timedelta, num_suggestions: int = 3) -> List[TimeSlot]:
        """Find available slots near the preferred time, checking same day first, then adjacent days"""
        all_alternatives = []
        
        # Ensure preferred_time is timezone-aware
        if preferred_time.tzinfo is None:
            preferred_time = self.calendar_manager.timezone.localize(preferred_time)
        
        # First, check the same day
        same_day_slots = self.calendar_manager.find_available_slots(
            preferred_time, duration, num_suggestions
        )
        
        # Prioritize slots closer to the preferred time
        for slot in same_day_slots:
            time_diff = abs((slot.start_time - preferred_time).total_seconds())
            all_alternatives.append((slot, time_diff))
        
        # If we need more suggestions, check the next day
        if len(all_alternatives) < num_suggestions:
            next_day = preferred_time + timedelta(days=1)
            next_day_preferred = next_day.replace(hour=preferred_time.hour, minute=preferred_time.minute)
            next_day_slots = self.calendar_manager.find_available_slots(
                next_day_preferred, duration, num_suggestions - len(all_alternatives)
            )
            
            for slot in next_day_slots:
                time_diff = abs((slot.start_time - preferred_time).total_seconds())
                all_alternatives.append((slot, time_diff))
        
        # If still need more, check the previous day
        if len(all_alternatives) < num_suggestions:
            prev_day = preferred_time - timedelta(days=1)
            # Only suggest previous day if it's not in the past
            current_date = datetime.now(self.calendar_manager.timezone).date()
            if prev_day.date() >= current_date:
                prev_day_preferred = prev_day.replace(hour=preferred_time.hour, minute=preferred_time.minute)
                prev_day_slots = self.calendar_manager.find_available_slots(
                    prev_day_preferred, duration, num_suggestions - len(all_alternatives)
                )
                
                for slot in prev_day_slots:
                    time_diff = abs((slot.start_time - preferred_time).total_seconds())
                    all_alternatives.append((slot, time_diff))
        
        # Sort by time difference (closest first) and return top suggestions
        all_alternatives.sort(key=lambda x: x[1])
        return [slot for slot, _ in all_alternatives[:num_suggestions]]
    
    @trace_function
    def find_next_available_slot(self, preferred_date: datetime, 
                                duration: timedelta) -> Optional[TimeSlot]:
        """Find the next available slot on or after the preferred date"""
        current_date = preferred_date.date()
        
        # Check up to 7 days ahead
        for i in range(7):
            check_date = datetime.combine(current_date + timedelta(days=i), 
                                        datetime.min.time())
            available_slots = self.calendar_manager.find_available_slots(
                check_date, duration, num_suggestions=1
            )
            
            if available_slots:
                return available_slots[0]
        
        return None
    
    @trace_function
    def detect_scheduling_conflicts(self, start_time: datetime, 
                                  end_time: datetime) -> List[Meeting]:
        """Detect conflicts with existing meetings"""
        return self.calendar_manager.get_events(start_time, end_time)
    
    @trace_function
    def suggest_optimal_meeting_times(self, date: datetime, duration: timedelta,
                                    num_suggestions: int = 3) -> List[TimeSlot]:
        """Suggest optimal meeting times considering existing schedule"""
        return self.calendar_manager.find_available_slots(date, duration, num_suggestions)
    

    