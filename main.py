import os
import sys
import json
import pytz
from datetime import datetime, timedelta
from colorama import init, Fore, Style
from services.calendar_manager import CalendarManager
from services.conversation_handler import ConversationHandler
from services.scheduler_logic import SchedulerLogic
import asyncio
from dotenv import load_dotenv

# Import our new logging system
from config.logger import request_tracer, trace_function, logger

# Load environment variables from .env file
load_dotenv()

# Initialize colorama for colored terminal output
init()

class MeetingSchedulerBot:
    @trace_function
    def __init__(self):
        print(f"{Fore.BLUE}🤖 Initializing Meeting Scheduler Bot...{Style.RESET_ALL}")
        
        # try:
        self.calendar_manager = CalendarManager()
        self.conversation_handler = ConversationHandler()
        self.scheduler = SchedulerLogic(self.calendar_manager)
        self.pending_context = {}  # Store context for multi-turn conversations
        print(f"{Fore.GREEN}✅ Bot initialized successfully!{Style.RESET_ALL}")
        # except Exception as e:
        #     print(f"{Fore.RED}❌ Failed to initialize bot: {e}{Style.RESET_ALL}")
        #     sys.exit(1)
    
    async def run(self):
        """Main bot loop"""
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"🗓️  MEETING SCHEDULER BOT")
        print(f"{'='*50}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Hey there! 👋 I'm your friendly meeting scheduler assistant!")
        print(f"I'm here to make managing your calendar super easy and fun!")
        print(f"\nHere's what I can help you with:")
        print(f"📅 'What's on my calendar today?' - Check your schedule")
        print(f"➕ 'Schedule a meeting with John tomorrow at 2 PM' - Add meetings")
        print(f"❌ 'Cancel my meeting with Sarah' - Delete meetings")
        print(f"🔍 'Am I free this Friday at 10 AM?' - Check availability")
        print(f"👥 'Show me meetings with john@example.com' - Find specific meetings")
        print(f"\n✨ I'll always ask for the essentials: meeting purpose, time, duration, and attendees!")
        print(f"💡 If your preferred time is busy, I'll suggest great alternatives nearby!")
        print(f"\nJust chat with me naturally - type 'exit' when you're done! 😊{Style.RESET_ALL}\n")
        
        while True:
            try:
                await self.conversation_handler.speak_response_in_terminal("How can I help you with your calendar?")
            
                # 🎤 Get user voice input
                user_input = self.conversation_handler.get_user_voice_input()
                print(f"{Fore.WHITE}You (spoken): {user_input}{Style.RESET_ALL}")

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print(f"\n{Fore.BLUE}👋 Thanks for using me! Hope I made your day a little easier! Take care! ✨{Style.RESET_ALL}")
                    break

                if not user_input.strip():
                    continue
                
                # Start request tracing
                request_id = request_tracer.start_request(user_input)
                
                # Process user input
                response = await self._process_user_request(user_input)
                
                # End request tracing
                request_tracer.end_request(response)
                
                print(f"{Fore.GREEN}Bot: {response}{Style.RESET_ALL}\n")
                await self.conversation_handler.speak_response_in_terminal(response)
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.BLUE}👋 Thanks for using me! Hope I made your day a little easier! Take care! ✨{Style.RESET_ALL}")
                break
            except Exception as e:
                request_tracer.log_error(e, "main_loop")
                print(f"{Fore.RED}❌ An error occurred: {e}{Style.RESET_ALL}")
    
    @trace_function
    async def _process_user_request(self, user_input: str) -> str:
        # Check for debug commands first
        if user_input.lower() in ['debug history', 'show history', 'chat history']:
            return self.conversation_handler.get_history_summary()
        
        if user_input.lower() in ['clear history', 'reset history']:
            self.conversation_handler.clear_history()
            return self.conversation_handler.generate_dynamic_response(
                situation="User requested to clear conversation history and it was successfully cleared",
                context_data={'action': 'clear_history'}
            )
        
        # Check if user is likely confirming something when we have pending context
        confirmation_words = ['yes', 'yeah', 'yep', 'ok', 'okay', 'sure', 'go ahead', 'proceed', 'correct', 'right']
        deletion_context_words = ['delete', 'cancel', 'remove', 'that', 'this', 'meeting']
        
        if self.pending_context:
            user_lower = user_input.lower()
            pending_action = self.pending_context.get('action')
            
            # Enhanced confirmation detection
            has_confirmation_word = any(word in user_lower.split() for word in confirmation_words)
            
            # For DELETE_MEETING actions, also look for deletion-related confirmations
            if pending_action == 'DELETE_MEETING':
                has_deletion_context = any(word in user_lower for word in deletion_context_words)
                is_likely_confirmation = (
                    has_confirmation_word or  # Contains yes/ok/sure etc.
                    (has_deletion_context and len(user_input.split()) <= 10) or  # Mentions delete/cancel with reasonable length
                    (user_lower.startswith(('yes', 'yeah', 'yep', 'ok', 'sure')) and 'delete' in user_lower)  # Starts with confirmation and mentions delete
                )
            else:
                # For other actions, use simpler confirmation detection
                is_likely_confirmation = has_confirmation_word and len(user_input.split()) <= 5
            
            if is_likely_confirmation:
                print(f"DEBUG: Detected likely confirmation: '{user_input}' with pending context for action: {pending_action}")
                # Force classification as CONFIRMATION
                result = {
                    'intent': 'CONFIRMATION',
                    'confidence': 0.9,
                    'extracted_data': {},
                    'missing_fields': [],
                    'context_understood': True,
                    'response': 'Got it!'
                }
            else:
                # Process the user input with conversation context normally
               result = await self.conversation_handler.process_user_input(user_input, self.pending_context)


        else:
            # Process the user input with conversation context normally
           result = await self.conversation_handler.process_user_input(user_input, self.pending_context)


        
        # Extract the intent and context_understood flag
        context_understood = result.get('context_understood', False)
        
        # Handle different intents
        if result['intent'] == 'ADD_MEETING':
            response = self._handle_add_meeting(result)
        elif result['intent'] == 'DELETE_MEETING':
            response = self._handle_delete_meeting(result)
        elif result['intent'] == 'VIEW_SCHEDULE':
            response = self._handle_view_schedule(result, user_input)
        elif result['intent'] == 'VIEW_CALENDAR':
            response = self._handle_view_schedule(result, user_input)
        elif result['intent'] == 'CHECK_AVAILABILITY':
            response = self._handle_check_availability(result)
        elif result['intent'] == 'RESCHEDULE_MEETING':
            response = self._handle_reschedule_meeting(result)
        elif result['intent'] == 'FIND_MEETINGS':
            response = self._handle_find_meetings(result)
        elif result['intent'] == 'CONFIRMATION':
            response = self._handle_confirmation(result)
        elif result['intent'] == 'PROVIDE_INFO':
            response = self._handle_provide_info(result)
        elif result['intent'] == 'GREETING':
            response = result.get('response', 'Hello! How can I help you with your schedule today?')
            # Clear any pending context on greeting
            self.pending_context = {}
        elif result['intent'] == 'HELP':
            response = self._get_help_message()
            # Clear any pending context on help request
            self.pending_context = {}
        else:
            response = result.get('response', 'I\'m not sure how to help with that. Try asking about your schedule, adding meetings, or say "help" for more options.')
            # Clear any pending context for unknown intents
            self.pending_context = {}
        
        # Add context information if it was understood and used
        if context_understood and self.pending_context:
            response += "\n\n💡 *Using conversation context to better understand your request.*"
        
        # Add the assistant's response to chat history for future context
        self.conversation_handler.add_to_history('assistant', response)
        
        return response
    
    @trace_function
    def _handle_view_schedule(self, result: dict, user_input: str) -> str:
        """Handle viewing schedule requests"""
        try:
            data = result.get('extracted_data', {})
            
            # Check if this is a weekly request - both from extracted data and user input text
            date_range = data.get('date_range', '')
            is_weekly_request = (
                date_range in ['this_week', 'next_week'] or
                any(phrase in user_input.lower() for phrase in [
                    'this week', 'weekly', 'week', 'entire week', 'whole week'
                ])
            )
            
            if is_weekly_request:
                # Calculate current week boundaries (Monday to Sunday)
                now = datetime.now()
                
                # Determine which week to show
                if date_range == 'next_week' or 'next week' in user_input.lower():
                    # Next week
                    now = now + timedelta(days=7)
                    week_label = "next week"
                else:
                    # This week (default)
                    week_label = "this week"
                
                # Find Monday of the target week (weekday() returns 0=Monday, 6=Sunday)
                days_since_monday = now.weekday()
                monday = now - timedelta(days=days_since_monday)
                
                # Set to start of Monday and end of Sunday
                start_of_week = monday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
                
                events = self.calendar_manager.get_events(start_of_week, end_of_week)
                date_str = f"{week_label} ({start_of_week.strftime('%B %d')} - {end_of_week.strftime('%B %d, %Y')})"
                
            elif 'query_date' in data:
                # Single day request
                query_date = datetime.fromisoformat(data['query_date'])
                end_date = query_date + timedelta(days=1)
                events = self.calendar_manager.get_events(query_date, end_date)
                date_str = query_date.strftime('%B %d, %Y')
            else:
                # Default to today
                events = self.calendar_manager.get_todays_events()
                date_str = "today"
            
            if not events:
                return self.conversation_handler.generate_dynamic_response(
                    situation="User requested to view schedule but no meetings found",
                    context_data={
                        'date_requested': date_str,
                        'events_count': 0,
                        'is_weekly': is_weekly_request
                    }
                )
            
            # Format events for context
            formatted_events = []
            for event in events:
                start_time = event.start_time.strftime('%I:%M %p')
                end_time = event.end_time.strftime('%I:%M %p')
                event_date = event.start_time.strftime('%B %d') if is_weekly_request else None
                event_info = {
                    'title': event.title,
                    'time': f"{start_time} - {end_time}",
                    'date': event_date,  # Include date for weekly view
                    'attendees': event.attendees[:3] if event.attendees else [],
                    'description': event.description[:100] if event.description else ""
                }
                formatted_events.append(event_info)
            
            return self.conversation_handler.generate_dynamic_response(
                situation="Showing user their schedule with meetings",
                context_data={
                    'date_requested': date_str,
                    'events_count': len(events),
                    'events': formatted_events,
                    'is_weekly': is_weekly_request
                }
            )
            
        except Exception as e:
            return self.conversation_handler.generate_dynamic_response(
                situation="Error occurred while trying to retrieve schedule",
                context_data={'error': str(e)}
            )
    
    @trace_function
    def _handle_add_meeting(self, result: dict) -> str:
        """Handle meeting creation requests"""
        try:
            data = result.get('extracted_data', {})
            print(f"DEBUG: ADD_MEETING data received: {data}")  # Debug print
            
            # Check if we have all mandatory fields
            missing_fields = self.conversation_handler.check_mandatory_fields(data)
            print(f"DEBUG: Missing fields: {missing_fields}")  # Debug print
            
            if missing_fields:
                # Store context for follow-up
                self.pending_context = {
                    'action': 'ADD_MEETING',
                    'data': data,
                    'context': {'missing_info': True, 'missing_fields': missing_fields}
                }
                
                # Generate dynamic response for missing information
                return self.conversation_handler.generate_dynamic_response(
                    situation="User wants to schedule a meeting but some required information is missing",
                    context_data={
                        'missing_fields': missing_fields,
                        'current_data': data,
                        'required_fields': ['meeting_title', 'start_datetime', 'duration_minutes', 'attendees']
                    }
                )
            
            # All required fields are present - try to schedule immediately
            print(f"DEBUG: All fields present, attempting to schedule...")  # Debug print
            success, message, alternatives = self.scheduler.schedule_meeting(data)
            print(f"DEBUG: Schedule result - Success: {success}, Message: {message}")  # Debug print
            
            if success:
                self.pending_context = {}  # Clear context after successful action
                return self.conversation_handler.generate_dynamic_response(
                    situation="Meeting was successfully scheduled",
                    context_data={
                        'meeting_title': data.get('meeting_title', 'Untitled Meeting'),
                        'start_time': data.get('start_datetime'),
                        'attendees': data.get('attendees', [])
                    }
                )
            elif alternatives:
                # Store context for potential confirmation
                self.pending_context = {
                    'action': 'ADD_MEETING',
                    'data': data,
                    'context': {'conflict': True, 'suggestions': alternatives}
                }
                
                return self.conversation_handler.generate_dynamic_response(
                    situation="Requested meeting time conflicts with existing schedule, offering alternatives",
                    context_data={
                        'requested_time': data.get('start_datetime'),
                        'meeting_title': data.get('meeting_title', 'meeting'),
                        'alternative_times': [alt.start_time.strftime('%I:%M %p on %B %d') for alt in alternatives[:3]]
                    }
                )
            else:
                self.pending_context = {}
                return self.conversation_handler.generate_dynamic_response(
                    situation="Failed to schedule meeting",
                    context_data={
                        'error_message': message,
                        'meeting_title': data.get('meeting_title', 'meeting')
                    }
                )
                
        except Exception as e:
            print(f"DEBUG: Exception in _handle_add_meeting: {e}")  # Debug print
            self.pending_context = {}
            return self.conversation_handler.generate_dynamic_response(
                situation="Error occurred while trying to schedule meeting",
                context_data={'error': str(e)}
            )
    
    @trace_function
    def _handle_delete_meeting(self, result: dict) -> str:
        """Handle meeting deletion requests"""
        try:
            data = result.get('extracted_data', {})
            meeting_identifier = data.get('meeting_identifier', '')
            query_date = data.get('query_date')
            
            if not meeting_identifier:
                # If no specific meeting identifier but we have a date, check what meetings exist on that date
                if query_date:
                    # Check meetings for the specific date
                    start_date = datetime.fromisoformat(query_date)
                    end_date = start_date + timedelta(days=1)
                    meetings_on_date = self.calendar_manager.get_events(start_date, end_date)
                    date_str = start_date.strftime('%B %d, %Y')
                    
                    if not meetings_on_date:
                        # No meetings on that date
                        self.pending_context = {}
                        return self.conversation_handler.generate_dynamic_response(
                            situation="User wants to cancel meetings on a specific date but no meetings exist on that date",
                            context_data={
                                'query_date': date_str,
                                'events_count': 0
                            }
                        )
                    else:
                        # Show actual meetings on that date
                        self.pending_context = {
                            'action': 'DELETE_MEETING',
                            'data': data,
                            'context': {'meetings_on_date': meetings_on_date, 'date': query_date}
                        }
                        
                        # Format meetings for context
                        meeting_list = []
                        for i, meeting in enumerate(meetings_on_date, 1):
                            meeting_info = {
                                'number': i,
                                'title': meeting.title,
                                'time': meeting.start_time.strftime('%I:%M %p'),
                                'attendees': meeting.attendees[:2] if meeting.attendees else []
                            }
                            meeting_list.append(meeting_info)
                        
                        return self.conversation_handler.generate_dynamic_response(
                            situation="User wants to cancel meetings on a specific date, showing actual meetings that exist",
                            context_data={
                                'query_date': date_str,
                                'meetings': meeting_list,
                                'events_count': len(meetings_on_date),
                                'action': 'delete_meeting'
                            }
                        )
                else:
                    # No date and no identifier - ask for clarification
                    self.pending_context = {
                        'action': 'DELETE_MEETING',
                        'data': data,
                        'context': {'needs_identifier': True}
                    }
                    return self.conversation_handler.generate_dynamic_response(
                        situation="User wants to cancel a meeting but didn't specify which one or when",
                        context_data={'action': 'delete_meeting'}
                    )
            
            # Search for meetings that match the identifier
            matching_meetings = self._find_meetings_by_identifier(meeting_identifier, query_date)
            
            if not matching_meetings:
                # Try fuzzy matching for similar meetings
                similar_meetings = self.calendar_manager.find_similar_meetings(meeting_identifier, query_date)
                
                if similar_meetings:
                    # Found similar meetings, ask user to clarify
                    self.pending_context = {
                        'action': 'DELETE_MEETING',
                        'data': data,
                        'context': {'similar_matches': similar_meetings}
                    }
                    
                    meeting_list = []
                    for i, meeting in enumerate(similar_meetings[:5], 1):
                        meeting_info = {
                            'number': i,
                            'title': meeting.title,
                            'time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                            'attendees': meeting.attendees[:2] if meeting.attendees else []
                        }
                        meeting_list.append(meeting_info)
                    
                    return self.conversation_handler.generate_dynamic_response(
                        situation="No exact matches found but found similar meetings, asking user to clarify",
                        context_data={
                            'search_term': meeting_identifier,
                            'similar_meetings': meeting_list,
                            'total_matches': len(similar_meetings)
                        }
                    )
                else:
                    self.pending_context = {}
                    return self.conversation_handler.generate_dynamic_response(
                        situation="No meetings found matching the user's description",
                        context_data={
                            'search_term': meeting_identifier,
                            'search_date': query_date
                        }
                    )
            elif len(matching_meetings) == 1:
                # Found exactly one meeting - ask for confirmation before deleting
                meeting = matching_meetings[0]
                self.pending_context = {
                    'action': 'DELETE_MEETING',
                    'data': data,
                    'context': {'meeting_to_delete': meeting, 'awaiting_confirmation': True}
                }
                
                return self.conversation_handler.generate_dynamic_response(
                    situation="Found specific meeting to delete, asking for user confirmation",
                    context_data={
                        'meeting_title': meeting.title,
                        'meeting_time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                        'attendees': meeting.attendees[:2] if meeting.attendees else [],
                        'action': 'delete'
                    }
                )
            else:
                # Multiple meetings found, ask for clarification
                self.pending_context = {
                    'action': 'DELETE_MEETING',
                    'data': data,
                    'context': {'multiple_matches': matching_meetings}
                }
                
                meeting_list = []
                for i, meeting in enumerate(matching_meetings[:5], 1):
                    meeting_info = {
                        'number': i,
                        'title': meeting.title,
                        'time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                        'attendees': meeting.attendees[:2] if meeting.attendees else []
                    }
                    meeting_list.append(meeting_info)
                
                return self.conversation_handler.generate_dynamic_response(
                    situation="Multiple meetings found matching user's description, need clarification",
                    context_data={
                        'search_term': meeting_identifier,
                        'matching_meetings': meeting_list,
                        'total_matches': len(matching_meetings)
                    }
                )
                
        except Exception as e:
            self.pending_context = {}
            return self.conversation_handler.generate_dynamic_response(
                situation="Error occurred while trying to cancel meeting",
                context_data={'error': str(e)}
            )
    
    @trace_function
    def _find_meetings_by_identifier(self, identifier: str, query_date: str = None) -> list:
        """Find meetings that match the given identifier (title, time, etc.)"""
        try:
            # Determine search date range
            if query_date:
                start_date = datetime.fromisoformat(query_date)
                end_date = start_date + timedelta(days=1)
            else:
                # Search from beginning of today to 30 days ahead
                now = datetime.now()
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=30)
            
            all_meetings = self.calendar_manager.get_events(start_date, end_date)
            matching_meetings = []
            
            identifier_lower = identifier.lower()
            
            # Extract potential email addresses from the identifier
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            extracted_emails = re.findall(email_pattern, identifier)
            
            # Extract potential time patterns from the identifier
            time_patterns = [
                r'\b(\d{1,2})\s*pm\b',     # "2 PM", "2PM", "12 pm"
                r'\b(\d{1,2})\s*am\b',     # "9 AM", "9AM", "10 am"
                r'\b(\d{1,2}):(\d{2})\s*pm\b',  # "2:30 PM", "2:30PM"
                r'\b(\d{1,2}):(\d{2})\s*am\b',  # "9:30 AM", "9:30AM"
            ]
            
            extracted_times = []
            for pattern in time_patterns:
                matches = re.findall(pattern, identifier_lower)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2:  # Hour and minute
                            hour, minute = match
                            extracted_times.append(f"{hour}:{minute}")
                        else:
                            extracted_times.append(match[0])
                    else:
                        extracted_times.append(match)
            
            print(f"DEBUG: Identifier: '{identifier}', Extracted times: {extracted_times}, Extracted emails: {extracted_emails}")
            
            for meeting in all_meetings:
                match_found = False
                
                # Check if identifier matches title
                if identifier_lower in meeting.title.lower():
                    matching_meetings.append(meeting)
                    match_found = True
                    print(f"DEBUG: Title match - Meeting: {meeting.title}")
                
                # Check if any extracted email addresses match meeting attendees
                if not match_found and extracted_emails and meeting.attendees:
                    for email in extracted_emails:
                        if email.lower() in [attendee.lower() for attendee in meeting.attendees]:
                            matching_meetings.append(meeting)
                            match_found = True
                            print(f"DEBUG: Attendee match - Meeting: {meeting.title}, matched email: {email}")
                            break
                
                # Check if extracted times match meeting time
                if not match_found and extracted_times:
                    meeting_time_12h = meeting.start_time.strftime('%I:%M %p').lower()  # "02:00 pm"
                    meeting_hour_12h = meeting.start_time.strftime('%I %p').lower()     # "02 pm"
                    meeting_time_24h = meeting.start_time.strftime('%H:%M')             # "14:00"
                    
                    for extracted_time in extracted_times:
                        # Handle different time formats
                        if ':' in extracted_time:
                            # Time with minutes (e.g., "2:30")
                            time_part = extracted_time
                            # Check if it matches the time part of the meeting
                            if (time_part in meeting_time_12h or 
                                time_part in meeting_time_24h):
                                matching_meetings.append(meeting)
                                match_found = True
                                print(f"DEBUG: Time match (with minutes) - Meeting: {meeting.title} at {meeting_time_12h}, matched: {time_part}")
                                break
                        else:
                            # Just hour (e.g., "2")
                            hour = extracted_time
                            # Convert to different formats for comparison
                            try:
                                hour_int = int(hour)
                                # Check 12-hour format matches
                                if (f"{hour_int:02d}" in meeting_time_12h.split(':')[0] or  # "02" in "02:00 pm"
                                    f"{hour_int}" == meeting.start_time.strftime('%I').lstrip('0')):  # "2" == "2" (no leading zero)
                                    matching_meetings.append(meeting)
                                    match_found = True
                                    print(f"DEBUG: Hour match - Meeting: {meeting.title} at {meeting_time_12h}, matched hour: {hour}")
                                    break
                            except ValueError:
                                continue
                
                if match_found:
                    continue
            
            print(f"DEBUG: Found {len(matching_meetings)} matching meetings")
            return matching_meetings
        except Exception as e:
            print(f"Error finding meetings: {e}")
            return []
    
    @trace_function
    def _handle_check_availability(self, result: dict) -> str:
        """Handle availability checking requests"""
        try:
            data = result.get('extracted_data', {})
            
            # Check if we have the required datetime information
            if 'start_datetime' not in data:
                return self.conversation_handler.generate_dynamic_response(
                    situation="User wants to check availability but didn't specify when",
                    context_data={'extracted_data': data}
                )
            
            start_time = datetime.fromisoformat(data['start_datetime'])
            
            # Determine end time - either from end_datetime or duration
            if 'end_datetime' in data and data['end_datetime']:
                end_time = datetime.fromisoformat(data['end_datetime'])
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
            else:
                duration_minutes = data.get('duration_minutes', 60)  # Default to 1 hour
                end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Check for conflicts
            conflicts = self.calendar_manager.get_events(start_time, end_time)
            available = len(conflicts) == 0
            
            if available:
                return self.conversation_handler.generate_dynamic_response(
                    situation="User checked availability and the time slot is free",
                    context_data={
                        'start_time': start_time.strftime('%I:%M %p'),
                        'end_time': end_time.strftime('%I:%M %p'),
                        'date': start_time.strftime('%B %d, %Y'),
                        'available': True
                    }
                )
            else:
                # Format conflicting meetings
                conflict_details = []
                for meeting in conflicts:
                    conflict_details.append({
                        'title': meeting.title,
                        'time': f"{meeting.start_time.strftime('%I:%M %p')} - {meeting.end_time.strftime('%I:%M %p')}"
                    })
                
                return self.conversation_handler.generate_dynamic_response(
                    situation="User checked availability but there are conflicting meetings",
                    context_data={
                        'start_time': start_time.strftime('%I:%M %p'),
                        'end_time': end_time.strftime('%I:%M %p'),
                        'date': start_time.strftime('%B %d, %Y'),
                        'available': False,
                        'conflicts': conflict_details,
                        'conflict_count': len(conflicts)
                    }
                )
                
        except Exception as e:
            return self.conversation_handler.generate_dynamic_response(
                situation="Error occurred while checking availability",
                context_data={'error': str(e)}
            )
    
    @trace_function
    def _handle_find_meetings(self, result: dict) -> str:
        """Handle finding specific meetings"""
        try:
            data = result.get('extracted_data', {})
            
            if 'person_email' in data:
                meetings = self.calendar_manager.get_events_with_person(data['person_email'])
                person_name = data['person_email'].split('@')[0]
                context_desc = f"with {person_name}"
            else:
                # Default to this week's meetings
                start_date = datetime.now()
                end_date = start_date + timedelta(days=7)
                meetings = self.calendar_manager.get_events(start_date, end_date)
                context_desc = "for this week"
            
            if not meetings:
                return f"🔍 I didn't find any meetings {context_desc}."
            
            response = f"🔍 **Found {len(meetings)} meeting{'s' if len(meetings) != 1 else ''} {context_desc}:**\n\n"
            for meeting in meetings[:10]:  # Show max 10 meetings
                meeting_time = meeting.start_time.strftime('%I:%M %p on %B %d')
                response += f"• **{meeting.title}** - {meeting_time}\n"
                if meeting.attendees:
                    attendee_names = [att.split('@')[0] for att in meeting.attendees[:2]]
                    response += f"  👥 With: {', '.join(attendee_names)}\n"
                response += "\n"
            
            if len(meetings) > 10:
                response += f"... and {len(meetings) - 10} more meetings."
            
            return response.strip()
            
        except Exception as e:
            return f"❌ Sorry, I couldn't search for meetings: {str(e)}"
    
    @trace_function
    def _handle_confirmation(self, result: dict) -> str:
        """Handle user confirmations (yes/no responses)"""
        try:
            print(f"DEBUG: CONFIRMATION - Pending context: {self.pending_context}")  # Debug print
            
            if not self.pending_context:
                return self.conversation_handler.generate_dynamic_response(
                    situation="User confirmed something but there's no pending action to confirm",
                    context_data={'user_input': result.get('extracted_data', {})}
                )
            
            pending_action = self.pending_context.get('action')
            pending_data = self.pending_context.get('data', {})
            pending_context_data = self.pending_context.get('context', {})
            new_data = result.get('extracted_data', {})  # Define new_data at the beginning
            
            print(f"DEBUG: CONFIRMATION - Action: {pending_action}, Data: {pending_data}")  # Debug print
            
            if pending_action == 'ADD_MEETING':
                # User confirmed they want to schedule the meeting
                if pending_context_data.get('conflict'):
                    return self.conversation_handler.generate_dynamic_response(
                        situation="User confirmed they want to schedule meeting despite conflict, but need to specify which alternative time",
                        context_data={
                            'meeting_title': pending_data.get('meeting_title', 'meeting'),
                            'alternative_times': pending_context_data.get('suggestions', [])
                        }
                    )
                elif pending_context_data.get('missing_info'):
                    # They confirmed they want to proceed, but check if we still actually need info
                    # Re-check missing fields in case they were provided in the conversation
                    current_missing_fields = self.conversation_handler.check_mandatory_fields(pending_data)
                    
                    if current_missing_fields:
                        # Still missing some fields, ask for them
                        return self.conversation_handler.generate_dynamic_response(
                            situation="User confirmed they want to schedule meeting but still missing required information",
                            context_data={
                                'missing_fields': current_missing_fields,
                                'current_data': pending_data
                            }
                        )
                    else:
                        # Try to schedule with current data - user has confirmed everything
                        print(f"DEBUG: CONFIRMATION - Attempting to schedule with data: {pending_data}")  # Debug print
                        success, message, alternatives = self.scheduler.schedule_meeting(pending_data)
                        self.pending_context = {}  # Clear context after action
                        
                        print(f"DEBUG: CONFIRMATION - Schedule result: Success={success}, Message={message}")  # Debug print
                        
                        if success:
                            return self.conversation_handler.generate_dynamic_response(
                                situation="Meeting successfully scheduled after user confirmation",
                                context_data={
                                    'meeting_title': pending_data.get('meeting_title', 'Untitled Meeting'),
                                    'meeting_time': pending_data.get('start_datetime')
                                }
                            )
                        elif alternatives:
                            # Store new context for alternatives
                            self.pending_context = {
                                'action': 'ADD_MEETING',
                                'data': pending_data,
                                'context': {'conflict': True, 'suggestions': alternatives}
                            }
                            
                            return self.conversation_handler.generate_dynamic_response(
                                situation="Still conflict after confirmation, offering new alternative times",
                                context_data={
                                    'meeting_title': pending_data.get('meeting_title', 'meeting'),
                                    'alternative_times': [alt.start_time.strftime('%I:%M %p on %B %d') for alt in alternatives[:3]]
                                }
                            )
                        else:
                            return self.conversation_handler.generate_dynamic_response(
                                situation="Failed to schedule meeting even after user confirmation",
                                context_data={
                                    'error_message': message,
                                    'meeting_title': pending_data.get('meeting_title', 'meeting')
                                }
                            )
                else:
                    # This else block handles the case where there's no missing_info and no conflict
                    # Try to schedule with current data - user has confirmed everything
                    print(f"DEBUG: CONFIRMATION - Attempting to schedule with data: {pending_data}")  # Debug print
                    success, message, alternatives = self.scheduler.schedule_meeting(pending_data)
                    self.pending_context = {}  # Clear context after action
                    
                    print(f"DEBUG: CONFIRMATION - Schedule result: Success={success}, Message={message}")  # Debug print
                    
                    if success:
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Meeting successfully scheduled after user confirmation",
                            context_data={
                                'meeting_title': pending_data.get('meeting_title', 'Untitled Meeting'),
                                'meeting_time': pending_data.get('start_datetime')
                            }
                        )
                    elif alternatives:
                        # Store new context for alternatives
                        self.pending_context = {
                            'action': 'ADD_MEETING',
                            'data': pending_data,
                            'context': {'conflict': True, 'suggestions': alternatives}
                        }
                        
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Still conflict after confirmation, offering new alternative times",
                            context_data={
                                'meeting_title': pending_data.get('meeting_title', 'meeting'),
                                'alternative_times': [alt.start_time.strftime('%I:%M %p on %B %d') for alt in alternatives[:3]]
                            }
                        )
                    else:
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Failed to schedule meeting even after user confirmation",
                            context_data={
                                'error_message': message,
                                'meeting_title': pending_data.get('meeting_title', 'meeting')
                            }
                        )
            
            elif pending_action == 'DELETE_MEETING':
                # Check if we have meetings on a specific date that user wants to delete all of
                if pending_context_data.get('meetings_on_date'):
                    meetings_to_delete = pending_context_data['meetings_on_date']
                    date_str = pending_context_data.get('date', 'the specified date')
                    
                    print(f"DEBUG: CONFIRMATION - Bulk deletion of {len(meetings_to_delete)} meetings for {date_str}")
                    
                    # Delete all meetings on that date
                    deleted_count = 0
                    failed_deletions = []
                    
                    for meeting in meetings_to_delete:
                        success = self.calendar_manager.delete_event(meeting)
                        if success:
                            deleted_count += 1
                            print(f"DEBUG: Successfully deleted meeting: {meeting.title}")
                        else:
                            failed_deletions.append(meeting.title)
                            print(f"DEBUG: Failed to delete meeting: {meeting.title}")
                    
                    self.pending_context = {}  # Clear context after action
                    
                    if deleted_count == len(meetings_to_delete):
                        # All meetings deleted successfully
                        return self.conversation_handler.generate_dynamic_response(
                            situation="All meetings successfully deleted for the specified date",
                            context_data={
                                'deleted_count': deleted_count,
                                'date': date_str,
                                'action': 'bulk_delete_success'
                            }
                        )
                    elif deleted_count > 0:
                        # Some meetings deleted, some failed
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Some meetings deleted successfully but some failed",
                            context_data={
                                'deleted_count': deleted_count,
                                'failed_count': len(failed_deletions),
                                'failed_meetings': failed_deletions,
                                'date': date_str,
                                'action': 'partial_delete'
                            }
                        )
                    else:
                        # All deletions failed
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Failed to delete any meetings",
                            context_data={
                                'failed_count': len(failed_deletions),
                                'failed_meetings': failed_deletions,
                                'date': date_str,
                                'action': 'delete_failed'
                            }
                        )
                
                # Check if we're awaiting final confirmation for deletion
                elif pending_context_data.get('awaiting_confirmation') and pending_context_data.get('meeting_to_delete'):
                    meeting = pending_context_data['meeting_to_delete']
                    print(f"DEBUG: CONFIRMATION - Attempting to delete meeting: {meeting.title}")
                    
                    # User confirmed deletion, proceed with deleting the meeting
                    success = self.calendar_manager.delete_event(meeting)
                    self.pending_context = {}  # Clear context after action
                    
                    if success:
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Meeting successfully deleted after user confirmation",
                            context_data={
                                'meeting_title': meeting.title,
                                'meeting_time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                                'action': 'deleted'
                            }
                        )
                    else:
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Failed to delete meeting despite user confirmation",
                            context_data={
                                'meeting_title': meeting.title,
                                'meeting_time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                                'action': 'delete'
                            }
                        )
                
                # Check if user is selecting from similar matches or multiple matches
                if (pending_context_data.get('similar_matches') or 
                    pending_context_data.get('multiple_matches')):
                    
                    meetings = (pending_context_data.get('similar_matches', []) or 
                               pending_context_data.get('multiple_matches', []))
                    
                    # Check if user is confirming they want to delete the suggested meeting
                    user_text = str(new_data.get('meeting_title', '') or 
                                  new_data.get('meeting_identifier', '') or 
                                  list(new_data.values())[0] if new_data else '').strip().lower()
                    
                    # Look for confirmation keywords in the user's response
                    confirmation_keywords = ['yes', 'yeah', 'yep', 'right', 'correct', 'that', 'this', 'delete', 'cancel', 'remove']
                    if any(keyword in user_text for keyword in confirmation_keywords):
                        # User is confirming they want to delete the suggested meeting
                        if len(meetings) == 1:
                            selected_meeting = meetings[0]
                            # Ask for final confirmation before deleting
                            self.pending_context = {
                                'action': 'DELETE_MEETING',
                                'data': pending_data,
                                'context': {'meeting_to_delete': selected_meeting, 'awaiting_confirmation': True}
                            }
                            return self.conversation_handler.generate_dynamic_response(
                                situation="User confirmed they want to delete the suggested meeting, asking for final confirmation",
                                context_data={
                                    'meeting_title': selected_meeting.title,
                                    'meeting_time': selected_meeting.start_time.strftime('%I:%M %p on %B %d'),
                                    'attendees': selected_meeting.attendees[:2] if selected_meeting.attendees else [],
                                    'action': 'delete'
                                }
                            )
                    
                    # Try to parse as a number selection (1, 2, 3, etc.)
                    try:
                        selection_number = int(user_text)
                        if 1 <= selection_number <= len(meetings):
                            selected_meeting = meetings[selection_number - 1]
                            # Ask for confirmation before deleting
                            self.pending_context = {
                                'action': 'DELETE_MEETING',
                                'data': pending_data,
                                'context': {'meeting_to_delete': selected_meeting, 'awaiting_confirmation': True}
                            }
                            return self.conversation_handler.generate_dynamic_response(
                                situation="User selected specific meeting from list, asking for confirmation before deletion",
                                context_data={
                                    'meeting_title': selected_meeting.title,
                                    'meeting_time': selected_meeting.start_time.strftime('%I:%M %p on %B %d'),
                                    'attendees': selected_meeting.attendees[:2] if selected_meeting.attendees else [],
                                    'action': 'delete'
                                }
                            )
                    except ValueError:
                        # Not a number, try to match by title
                        for meeting in meetings:
                            if user_text in meeting.title.lower():
                                # Ask for confirmation before deleting
                                self.pending_context = {
                                    'action': 'DELETE_MEETING',
                                    'data': pending_data,
                                    'context': {'meeting_to_delete': meeting, 'awaiting_confirmation': True}
                                }
                                return self.conversation_handler.generate_dynamic_response(
                                    situation="User selected specific meeting by name, asking for confirmation before deletion",
                                    context_data={
                                        'meeting_title': meeting.title,
                                        'meeting_time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                                        'attendees': meeting.attendees[:2] if meeting.attendees else [],
                                        'action': 'delete'
                                    }
                                )
                
                # Try to find meetings with the new information (fallback)
                identifier = new_data.get('meeting_title') or new_data.get('meeting_identifier')
                if identifier:
                    meetings = self.calendar_manager.find_meetings(identifier)
                    if len(meetings) == 1:
                        # Found exactly one meeting - ask for confirmation
                        self.pending_context['context'] = {'meeting_to_delete': meetings[0], 'awaiting_confirmation': True}
                        meeting = meetings[0]
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Found specific meeting to delete after user provided more information",
                            context_data={
                                'meeting_title': meeting.title,
                                'meeting_time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                                'attendees': meeting.attendees[:2] if meeting.attendees else [],
                                'action': 'delete'
                            }
                        )
                    elif len(meetings) > 1:
                        # Multiple meetings found
                        self.pending_context['context'] = {'multiple_matches': meetings}
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Found multiple meetings matching the information, need user to specify which one",
                            context_data={
                                'meetings': [
                                    {
                                        'title': m.title,
                                        'time': m.start_time.strftime('%I:%M %p on %B %d')
                                    } for m in meetings[:5]
                                ],
                                'action': 'delete'
                            }
                        )
                    else:
                        self.pending_context = {}  # Clear context if no meetings found
                        return self.conversation_handler.generate_dynamic_response(
                            situation="No meetings found matching the provided information",
                            context_data={
                                'search_term': identifier,
                                'action': 'delete'
                            }
                        )
                else:
                    return self.conversation_handler.generate_dynamic_response(
                        situation="User provided information but still need meeting identifier for deletion",
                        context_data={'provided_data': new_data}
                    )
            
            # For other actions or unknown actions
            return self.conversation_handler.generate_dynamic_response(
                situation="User provided information for unknown or unsupported action",
                context_data={
                    'pending_action': pending_action,
                    'provided_data': new_data
                }
            )
            
        except Exception as e:
            print(f"DEBUG: CONFIRMATION - Exception: {e}")  # Debug print
            self.pending_context = {}
            return self.conversation_handler.generate_dynamic_response(
                situation="Error occurred while processing user confirmation",
                context_data={'error': str(e)}
            )
    
    @trace_function
    def _handle_reschedule_meeting(self, result: dict) -> str:
        """Handle rescheduling requests"""
        try:
            data = result.get('extracted_data', {})
            meeting_identifier = data.get('meeting_identifier', '')
            new_time = data.get('new_datetime')
            
            if not meeting_identifier:
                return self.conversation_handler.generate_dynamic_response(
                    situation="User wants to reschedule a meeting but didn't specify which meeting",
                    context_data={'extracted_data': data}
                )
            
            # Find the meeting to reschedule
            meetings = self.calendar_manager.find_meetings(meeting_identifier)
            
            if not meetings:
                return self.conversation_handler.generate_dynamic_response(
                    situation="No meetings found matching the identifier for rescheduling",
                    context_data={'search_term': meeting_identifier}
                )
            elif len(meetings) > 1:
                return self.conversation_handler.generate_dynamic_response(
                    situation="Multiple meetings found for rescheduling, need user to specify which one",
                    context_data={
                        'meetings': [
                            {
                                'title': m.title,
                                'time': m.start_time.strftime('%I:%M %p on %B %d')
                            } for m in meetings[:5]
                        ],
                        'search_term': meeting_identifier,
                        'action': 'reschedule'
                    }
                )
            
            meeting = meetings[0]
            
            if not new_time:
                return self.conversation_handler.generate_dynamic_response(
                    situation="Found meeting to reschedule but no new time specified",
                    context_data={
                        'meeting_title': meeting.title,
                        'current_time': meeting.start_time.strftime('%I:%M %p on %B %d')
                    }
                )
            
            # Try to reschedule
            success = self.calendar_manager.reschedule_event(meeting, new_time)
            
            if success:
                return self.conversation_handler.generate_dynamic_response(
                    situation="Meeting successfully rescheduled",
                    context_data={
                        'meeting_title': meeting.title,
                        'old_time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                        'new_time': new_time.strftime('%I:%M %p on %B %d') if hasattr(new_time, 'strftime') else str(new_time)
                    }
                )
            else:
                return self.conversation_handler.generate_dynamic_response(
                    situation="Failed to reschedule meeting",
                    context_data={
                        'meeting_title': meeting.title,
                        'requested_time': new_time.strftime('%I:%M %p on %B %d') if hasattr(new_time, 'strftime') else str(new_time)
                    }
                )
                
        except Exception as e:
            return self.conversation_handler.generate_dynamic_response(
                situation="Error occurred while trying to reschedule meeting",
                context_data={'error': str(e)}
            )
    
    @trace_function
    def _get_help_message(self) -> str:
        """Generate help message using LLM"""
        return self.conversation_handler.generate_dynamic_response(
            situation="User requested help or general information about the meeting scheduler",
            context_data={
                'available_features': [
                    'Schedule meetings',
                    'View calendar and schedule',
                    'Cancel meetings',
                    'Find meetings',
                    'Reschedule meetings'
                ]
            }
        )

    @trace_function
    def _handle_provide_info(self, result: dict) -> str:
        """Handle additional information provided by the user"""
        try:
            if not self.pending_context:
                return self.conversation_handler.generate_dynamic_response(
                    situation="User provided information but there's no pending action that needs information",
                    context_data={'user_input': result.get('extracted_data', {})}
                )
            
            pending_action = self.pending_context.get('action')
            pending_data = self.pending_context.get('data', {})
            new_data = result.get('extracted_data', {})
            
            # Merge new data with existing data
            for key, value in new_data.items():
                if value:  # Only update if new value is not empty
                    pending_data[key] = value
            
            # Check if timezone info is provided in other fields and extract it
            if 'timezone' not in new_data and any(tz in str(new_data).upper() for tz in ['EST', 'PST', 'CST', 'MST', 'UTC', 'GMT', 'EASTERN', 'PACIFIC', 'CENTRAL', 'MOUNTAIN']):
                print(f"DEBUG: Detected timezone in new_data but no explicit timezone field: {new_data}")
                # Try to extract timezone from the input
                for field_name, field_value in new_data.items():
                    if isinstance(field_value, str):
                        field_upper = field_value.upper()
                        for tz_abbr in ['EST', 'PST', 'CST', 'MST', 'UTC', 'GMT', 'EASTERN', 'PACIFIC', 'CENTRAL', 'MOUNTAIN']:
                            if tz_abbr in field_upper:
                                new_data['timezone'] = tz_abbr
                                print(f"DEBUG: Extracted timezone '{tz_abbr}' from field '{field_name}': {field_value}")
                                break
                        if 'timezone' in new_data:
                            break
            
            # Process timezone if it exists and we have a start_datetime
            if 'timezone' in new_data and 'start_datetime' in pending_data:
                try:
                    print(f"DEBUG: Processing timezone - timezone: {new_data['timezone']}, start_datetime: {pending_data['start_datetime']}")
                    
                    # Parse the existing datetime
                    base_datetime = datetime.fromisoformat(pending_data['start_datetime'].replace('Z', '+00:00'))
                    timezone_str = new_data['timezone'].upper()
                    
                    # Map common timezone abbreviations to pytz timezones
                    timezone_mapping = {
                        'EST': 'US/Eastern',
                        'EDT': 'US/Eastern', 
                        'CST': 'US/Central',
                        'CDT': 'US/Central',
                        'MST': 'US/Mountain',
                        'MDT': 'US/Mountain',
                        'PST': 'US/Pacific',
                        'PDT': 'US/Pacific',
                        'UTC': 'UTC',
                        'GMT': 'GMT',
                        'EASTERN': 'US/Eastern',
                        'CENTRAL': 'US/Central',
                        'MOUNTAIN': 'US/Mountain',
                        'PACIFIC': 'US/Pacific'
                    }
                    
                    if timezone_str in timezone_mapping:
                        tz = pytz.timezone(timezone_mapping[timezone_str])
                        
                        # If the datetime is naive, localize it to the specified timezone
                        if base_datetime.tzinfo is None:
                            localized_datetime = tz.localize(base_datetime)
                        else:
                            # Convert to the specified timezone
                            localized_datetime = base_datetime.astimezone(tz)
                        
                        # Update the start_datetime with timezone information
                        pending_data['start_datetime'] = localized_datetime.isoformat()
                        print(f"DEBUG: Updated datetime with timezone: {pending_data['start_datetime']}")
                    else:
                        print(f"DEBUG: Unknown timezone: {timezone_str}")
                    
                except Exception as e:
                    print(f"DEBUG: Error processing timezone: {e}")
            
            # Update the pending context with new data
            self.pending_context['data'] = pending_data
            
            if pending_action == 'ADD_MEETING':
                # Check if we now have all required fields using the correct field names
                missing_fields = self.conversation_handler.check_mandatory_fields(pending_data)
                
                if missing_fields:
                    # Still missing some fields
                    self.pending_context['context'] = {'missing_info': True, 'missing_fields': missing_fields}
                    return self.conversation_handler.generate_dynamic_response(
                        situation="User provided some information but still missing required fields for meeting scheduling",
                        context_data={
                            'missing_fields': missing_fields,
                            'current_data': pending_data,
                            'recently_provided': list(new_data.keys())
                        }
                    )
                else:
                    # We have all required fields, try to schedule directly
                    print(f"DEBUG: Attempting to schedule meeting with data: {pending_data}")
                    success, message, alternatives = self.scheduler.schedule_meeting(pending_data)
                    print(f"DEBUG: Schedule result - Success: {success}, Message: {message}")
                    
                    if success:
                        self.pending_context = {}  # Clear context after success
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Meeting successfully scheduled after user provided missing information",
                            context_data={
                                'meeting_title': pending_data.get('meeting_title', 'Untitled Meeting'),
                                'meeting_time': pending_data.get('start_datetime'),
                                'attendees': pending_data.get('attendees', [])
                            }
                        )
                    elif alternatives:
                        # Store context for conflict resolution
                        self.pending_context['context'] = {'conflict': True, 'suggestions': alternatives}
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Meeting scheduling conflict detected after user provided information, offering alternatives",
                            context_data={
                                'meeting_title': pending_data.get('meeting_title', 'meeting'),
                                'alternative_times': [alt.start_time.strftime('%I:%M %p on %B %d') for alt in alternatives[:3]]
                            }
                        )
                    else:
                        self.pending_context = {}  # Clear context after failure
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Failed to schedule meeting after user provided all required information",
                            context_data={
                                'error_message': message,
                                'meeting_title': pending_data.get('meeting_title', 'meeting'),
                                'provided_data': pending_data
                            }
                        )
            
            elif pending_action == 'DELETE_MEETING':
                # Try to find meetings with the new information
                pending_context_data = self.pending_context.get('context', {})
                
                # Check if user is selecting from similar matches or multiple matches
                if (pending_context_data.get('similar_matches') or 
                    pending_context_data.get('multiple_matches')):
                    
                    meetings = (pending_context_data.get('similar_matches', []) or 
                               pending_context_data.get('multiple_matches', []))
                    
                    # Check if user is confirming they want to delete the suggested meeting
                    user_text = str(new_data.get('meeting_title', '') or 
                                  new_data.get('meeting_identifier', '') or 
                                  list(new_data.values())[0] if new_data else '').strip().lower()
                    
                    # Look for confirmation keywords in the user's response
                    confirmation_keywords = ['yes', 'yeah', 'yep', 'right', 'correct', 'that', 'this', 'delete', 'cancel', 'remove']
                    if any(keyword in user_text for keyword in confirmation_keywords):
                        # User is confirming they want to delete the suggested meeting
                        if len(meetings) == 1:
                            selected_meeting = meetings[0]
                            # Ask for final confirmation before deleting
                            self.pending_context = {
                                'action': 'DELETE_MEETING',
                                'data': pending_data,
                                'context': {'meeting_to_delete': selected_meeting, 'awaiting_confirmation': True}
                            }
                            return self.conversation_handler.generate_dynamic_response(
                                situation="User confirmed they want to delete the suggested meeting, asking for final confirmation",
                                context_data={
                                    'meeting_title': selected_meeting.title,
                                    'meeting_time': selected_meeting.start_time.strftime('%I:%M %p on %B %d'),
                                    'attendees': selected_meeting.attendees[:2] if selected_meeting.attendees else [],
                                    'action': 'delete'
                                }
                            )
                    
                    # Try to parse as a number selection (1, 2, 3, etc.)
                    try:
                        selection_number = int(user_text)
                        if 1 <= selection_number <= len(meetings):
                            selected_meeting = meetings[selection_number - 1]
                            # Ask for confirmation before deleting
                            self.pending_context = {
                                'action': 'DELETE_MEETING',
                                'data': pending_data,
                                'context': {'meeting_to_delete': selected_meeting, 'awaiting_confirmation': True}
                            }
                            return self.conversation_handler.generate_dynamic_response(
                                situation="User selected specific meeting from list, asking for confirmation before deletion",
                                context_data={
                                    'meeting_title': selected_meeting.title,
                                    'meeting_time': selected_meeting.start_time.strftime('%I:%M %p on %B %d'),
                                    'attendees': selected_meeting.attendees[:2] if selected_meeting.attendees else [],
                                    'action': 'delete'
                                }
                            )
                    except ValueError:
                        # Not a number, try to match by title
                        for meeting in meetings:
                            if user_text in meeting.title.lower():
                                # Ask for confirmation before deleting
                                self.pending_context = {
                                    'action': 'DELETE_MEETING',
                                    'data': pending_data,
                                    'context': {'meeting_to_delete': meeting, 'awaiting_confirmation': True}
                                }
                                return self.conversation_handler.generate_dynamic_response(
                                    situation="User selected specific meeting by name, asking for confirmation before deletion",
                                    context_data={
                                        'meeting_title': meeting.title,
                                        'meeting_time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                                        'attendees': meeting.attendees[:2] if meeting.attendees else [],
                                        'action': 'delete'
                                    }
                                )
                
                # Try to find meetings with the new information (fallback)
                identifier = new_data.get('meeting_title') or new_data.get('meeting_identifier')
                if identifier:
                    meetings = self.calendar_manager.find_meetings(identifier)
                    if len(meetings) == 1:
                        # Found exactly one meeting - ask for confirmation
                        self.pending_context['context'] = {'meeting_to_delete': meetings[0], 'awaiting_confirmation': True}
                        meeting = meetings[0]
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Found specific meeting to delete after user provided more information",
                            context_data={
                                'meeting_title': meeting.title,
                                'meeting_time': meeting.start_time.strftime('%I:%M %p on %B %d'),
                                'attendees': meeting.attendees[:2] if meeting.attendees else [],
                                'action': 'delete'
                            }
                        )
                    elif len(meetings) > 1:
                        # Multiple meetings found
                        self.pending_context['context'] = {'multiple_matches': meetings}
                        return self.conversation_handler.generate_dynamic_response(
                            situation="Found multiple meetings matching the information, need user to specify which one",
                            context_data={
                                'meetings': [
                                    {
                                        'title': m.title,
                                        'time': m.start_time.strftime('%I:%M %p on %B %d')
                                    } for m in meetings[:5]
                                ],
                                'action': 'delete'
                            }
                        )
                    else:
                        self.pending_context = {}  # Clear context if no meetings found
                        return self.conversation_handler.generate_dynamic_response(
                            situation="No meetings found matching the provided information",
                            context_data={
                                'search_term': identifier,
                                'action': 'delete'
                            }
                        )
                else:
                    return self.conversation_handler.generate_dynamic_response(
                        situation="User provided information but still need meeting identifier for deletion",
                        context_data={'provided_data': new_data}
                    )
            
            # For other actions or unknown actions
            return self.conversation_handler.generate_dynamic_response(
                situation="User provided information for unknown or unsupported action",
                context_data={
                    'pending_action': pending_action,
                    'provided_data': new_data
                }
            )
            
        except Exception as e:
            self.pending_context = {}
            return self.conversation_handler.generate_dynamic_response(
                situation="Error occurred while processing additional user information",
                context_data={'error': str(e)}
            )

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ['GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"{Fore.RED}❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print(f"\nPlease set these variables and try again.{Style.RESET_ALL}")
        return False
    
    return True

if __name__ == "__main__":
    if not check_environment():
        sys.exit(1)
    
    bot = MeetingSchedulerBot()
    asyncio.run(bot.run())
