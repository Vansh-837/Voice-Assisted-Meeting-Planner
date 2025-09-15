import google.generativeai as genai
from datetime import datetime, timedelta
import re
from typing import Dict, Any, Optional, List
from config.settings import Config
from models.meeting import Meeting
from fastapi import WebSocket
import json
import os
import uuid
from real_time_tts_version2.app.tts_engine import synthesize_text
# Import our tracing system
from config.logger import trace_function, trace_api_call, logger
from stt import RealTimeSTT

class ConversationHandler:
    @trace_function
    def __init__(self):
        self.config = Config()
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.config.GEMINI_MODEL)
        self.pending_meetings = {}  # Store meetings pending complete information
        self.chat_history = []  # Store conversation history
        
    @trace_function
    def add_to_history(self, role: str, message: str):
        """Add a message to chat history and maintain only last 6 messages (3 user + 3 assistant)"""
        self.chat_history.append({
            'role': role,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only the last 6 messages (3 pairs of user-assistant)
        if len(self.chat_history) > 6:
            self.chat_history = self.chat_history[-6:]
    
    @trace_function
    def get_conversation_context(self) -> str:
        """Format chat history for LLM context - includes both user and assistant messages"""
        if not self.chat_history:
            return "No previous conversation history."
        
        context_lines = ["Recent conversation history:"]
        for entry in self.chat_history:
            role_label = "User" if entry['role'] == 'user' else "Assistant"
            # Truncate very long messages for context
            message = entry['message']
            if len(message) > 150:
                message = message[:150] + "..."
            context_lines.append(f"{role_label}: {message}")
        
        return "\n".join(context_lines)

    @trace_function
    def get_user_voice_input(self) -> str:
        print("🎤 Listening for your reply...")
        stt = RealTimeSTT(model_size="large-v3", device="cpu")
        result = stt.start_recording_for_public_environment()  # Use public environment settings
        if result and 'transcription' in result:
            return result['transcription']
        return ""
    

    
    def clean_text_for_tts(self,text: str) -> str:
        # Remove markdown characters
        text = re.sub(r'[*_`~]', '', text)
        
        # Remove bullet points and extra spacing
        text = re.sub(r'^[\s•*-]+\s*', '', text, flags=re.MULTILINE)

        # Remove emojis (Unicode emoji pattern)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)

        # Normalize excessive whitespace
        text = re.sub(r'\s{2,}', ' ', text).strip()

        return text
        

    async def speak_response_in_terminal(self, text: str):
        cleaned_text = self.clean_text_for_tts(text)  # 👈 Clean before speaking

        filename = f"terminal_response_{uuid.uuid4()}.wav"
        output_path = f"temp_audio/{filename}"
        speaker_wav = "/home/multiqos/vansh/MeetingScheduler/meeting-schedular/real_time_tts_version2/my/cloning_Male.wav"

        language = "en"

        success = await synthesize_text(cleaned_text, speaker_wav, language, output_path)
        if success:
            os.system(f"ffplay -nodisp -autoexit {output_path} >/dev/null 2>&1")
        else:
            print(f"❌ TTS failed for: {cleaned_text}")

        
    @trace_function
    @trace_api_call("Gemini", "process_user_input")
    async def process_user_input(self,user_input: str, context: Dict[str, Any], websocket: Optional[WebSocket] = None) -> Dict[str, Any]:
        """Process user input and determine intent and extract information"""
        
        # Add user message to history
        self.add_to_history('user', user_input)
        
        # Get conversation context
        conversation_context = self.get_conversation_context()

        prompt = f"""
        You are a friendly meeting scheduler assistant. Analyze the user's message and determine their intent.
        Be warm, conversational, and helpful - like talking to a good friend, not a strict teacher.
        
        {conversation_context}
        
        Current user message: "{user_input}"
        
        Current context:
        - Today's date: {datetime.now().strftime('%Y-%m-%d')}
        - Current time: {datetime.now().strftime('%H:%M')}
        
        IMPORTANT: Use the conversation history to understand:
        1. If the user is continuing a previous request (like providing missing meeting details)
        2. If they're referring to something mentioned earlier
        3. If they're confirming or canceling a previous action
        4. Context about meetings they've discussed before
        
        Possible intents:
        1. VIEW_CALENDAR - User wants to see their schedule
        2. ADD_MEETING - User wants to schedule a new meeting
        3. DELETE_MEETING - User wants to cancel/delete a meeting
        4. CHECK_AVAILABILITY - User wants to check if they're free at a specific time
        5. FIND_MEETINGS - User wants to find meetings with specific people or criteria
        6. CONFIRMATION - User is confirming a previous action (like "yes" to schedule a meeting)
        7. PROVIDE_INFO - User is providing missing information for a previous request
        8. GENERAL_QUERY - General questions about their calendar
        
        For ADD_MEETING intent, extract:
        - meeting_title (the purpose/title of the meeting - MANDATORY)
        - meeting_description (optional subtitle/additional details)
        - start_datetime (convert relative times like "tomorrow at 2pm" to specific datetime - MANDATORY)
        - duration_minutes (how long the meeting should be in minutes - MANDATORY, only include if user specifies duration)
        - attendees (email addresses or names if mentioned - MANDATORY, only include if user mentions attendees, do not default to empty list)
            Note: This includes team references like "marketing team", "dev team", specific names, or email addresses
        - location (if mentioned, optional)
        - timezone (if user mentions timezone like EST, PST, UTC, etc.)
        - recurrence_pattern (if user mentions recurring meetings - values: "daily", "weekly", "monthly", "yearly")
        - recurrence_count (number of occurrences for recurring meetings - e.g., "5 weeks" = 5, "3 months" = 3)
        - recurrence_days (for weekly patterns, which days - e.g., ["tuesday"] for "every tuesday", ["monday", "friday"] for "mondays and fridays")
        
        For VIEW_CALENDAR intent, extract:
        - query_date (convert dates like "20th june", "june 20th", "tomorrow", "today" to ISO format YYYY-MM-DD)
        - date_range (for weekly/range requests like "this week", "next week", "this month" - use values like "this_week", "next_week", "this_month")
        
        For DELETE_MEETING intent, extract:
        - meeting_identifier (title, time, or other identifying info)
        - query_date (if specific date mentioned)
        
        For PROVIDE_INFO intent, extract whatever information the user is providing based on conversation history.
        This includes:
        - timezone (if user mentions EST, PST, UTC, etc.)
        - Any other missing fields they're providing
        
        For CHECK_AVAILABILITY intent, extract:
        - start_datetime (the time to check availability for - MANDATORY)
        - duration_minutes (if checking for a specific duration, default 60)
        - end_datetime (if user specifies a time range like "3 to 4pm")
        
        DATE PARSING RULES:
        - Convert ordinal dates like "20th june", "1st july", "3rd december" to ISO format
        - For dates without year, assume current year (2025)
        - Convert relative dates like "today", "tomorrow", "next week" to specific dates
        - For weekly requests like "this week", "next week", set date_range to "this_week", "next_week" respectively
        - Examples: "20th june" -> "2025-06-20", "tomorrow" -> actual tomorrow's date, "this week" -> date_range: "this_week"
        - Always use YYYY-MM-DD format for query_date
        - For start_datetime, use full ISO format: YYYY-MM-DDTHH:MM:SS
        
        RECURRING MEETING START DATE RULES:
        - For recurring meetings like "every tuesday for 5 weeks", the start_datetime should be the NEXT occurrence of that day
        - If today is Friday June 20, 2025, and user says "every tuesday", start_datetime should be Tuesday June 24, 2025 (the very next Tuesday)
        - Do NOT set start dates weeks or months in the future unless explicitly specified
        - Examples: 
          * "every tuesday for 5 weeks" on Friday -> start next Tuesday (not 5 weeks from now)
          * "every monday starting next month" -> start first Monday of next month
          * "daily for 2 weeks" -> start tomorrow (or today if time allows)
        
        TIMEZONE HANDLING:
        - If user mentions timezone abbreviations like EST, PST, CST, MST, UTC, GMT, etc., extract them as "timezone"
        - If user just says a timezone name like "Eastern", "Pacific", "Central", extract as "timezone"
        - Common patterns: "EST", "in EST", "Eastern time", "Pacific Standard Time", etc.
        
        RECURRING MEETING PATTERNS:
        - "every tuesday" or "every tuesday for 5 weeks" -> recurrence_pattern: "weekly", recurrence_days: ["tuesday"], recurrence_count: 5
        - "daily for 2 weeks" -> recurrence_pattern: "daily", recurrence_count: 14
        - "weekly for 3 weeks" -> recurrence_pattern: "weekly", recurrence_count: 3
        - "monthly for 6 months" -> recurrence_pattern: "monthly", recurrence_count: 6
        - "every monday and friday" -> recurrence_pattern: "weekly", recurrence_days: ["monday", "friday"]
        
        Respond in this exact JSON format:
        {{
            "intent": "INTENT_NAME",
            "confidence": 0.95,
            "extracted_data": {{
                "meeting_title": "title here",
                "meeting_description": "subtitle here",
                "start_datetime": "2024-01-15T14:00:00",
                "end_datetime": "2024-01-15T15:00:00",
                "duration_minutes": 60,
                "location": "location here",
                "timezone": "EST",
                "recurrence_pattern": "weekly",
                "recurrence_count": 5,
                "recurrence_days": ["tuesday"],
                "query_date": "2024-01-15",
                "person_email": "person@example.com",
                "meeting_identifier": "meeting title or time"
            }},
            "missing_fields": ["field1", "field2"],
            "context_understood": true/false,
            "response": "Natural, friendly language response to user"
        }}
        
        Only include relevant fields in extracted_data based on the intent.
        For ADD_MEETING, list any missing mandatory fields (meeting_title, start_datetime, duration_minutes, attendees) in "missing_fields".
        Set "context_understood" to true if you're using conversation history to understand the current message.
        Make responses conversational and friendly.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                print("⚠️ LLM response was not valid JSON, using fallback intent matcher.")
                result = {
                    "intent": "GENERAL_QUERY",
                    "confidence": 0.5,
                    "extracted_data": {},
                    "missing_fields": [],
                    "context_understood": False,
                    "response": "Hey! I'd love to help you with your calendar. Could you tell me a bit more about what you'd like to do? 😊"
                }

                user_lower = user_input.lower()
                if any(word in user_lower for word in ['schedule', 'add', 'create', 'book', 'meeting']):
                    result["intent"] = "ADD_MEETING"
                    result["response"] = "Awesome! I can help you schedule a meeting. Let me get the details I need from you."
                elif any(word in user_lower for word in ['delete', 'cancel', 'remove']):
                    result["intent"] = "DELETE_MEETING"
                    result["response"] = "No problem! I can help you cancel a meeting. Which meeting would you like to remove?"
                elif any(word in user_lower for word in ['view', 'show', 'list', 'today', 'tomorrow']):
                    result["intent"] = "VIEW_CALENDAR"
                    result["response"] = "Sure thing! Let me show you what's on your calendar."
                elif any(word in user_lower for word in ['free', 'available', 'busy']):
                    result["intent"] = "CHECK_AVAILABILITY"
                    result["response"] = "I can definitely check that for you! What date and time are you curious about?"
                elif any(word in user_lower for word in ['yes', 'ok', 'okay', 'confirm', 'go ahead']):
                    result["intent"] = "CONFIRMATION"
                    result["response"] = "Got it! Let me proceed with that for you."

            if websocket:
                await websocket.send_text(json.dumps({"type": "text", "content": result["response"]}))
            
            # REMOVED: Don't speak the LLM response here
            # final_response = self.generate_response(result["intent"], result.get("extracted_data", {}), context)
            # await self.speak_response_in_terminal(final_response)
            
            return result

        except Exception as e:
            print(f"❌ LLM processing failed: {e}")
            fallback = {
                "intent": "GENERAL_QUERY",
                "confidence": 0.5,
                "extracted_data": {},
                "missing_fields": [],
                "context_understood": False,
                "response": "Oops! I had a little hiccup understanding that. Mind rephrasing it for me? 🤔"
            }
            if websocket:
                await websocket.send_text(json.dumps({"type": "text", "content": fallback["response"]}))
            # REMOVED: Don't speak fallback response here
            # await self.speak_response_in_terminal(fallback["response"])
            return fallback
    


    
    @trace_function
    def generate_response(self, intent: str, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate a natural language response based on intent and data"""
        
        response = ""
        
        if intent == "VIEW_CALENDAR":
            if context.get('events'):
                events_count = len(context['events'])
                events_text = "\n".join([f"📅 {event}" for event in context['events']])
                response = f"Here's what you've got coming up! ({events_count} event{'s' if events_count != 1 else ''}):\n\n{events_text}"
            else:
                response = "Looks like you've got a clear schedule for that time! 🎉 Perfect opportunity to relax or tackle something new."
        
        elif intent == "ADD_MEETING":
            if context.get('success'):
                meeting_title = data.get('meeting_title', 'your meeting')
                start_time = data.get('start_datetime', '')
                response = f"Perfect! ✅ I've got '{meeting_title}' scheduled for {start_time}. You're all set!"
            elif context.get('conflict'):
                suggestions = context.get('suggestions', [])
                if suggestions:
                    suggestion_text = "\n".join([f"• {slot}" for slot in suggestions])
                    response = f"Ah, looks like that time's already taken! 😅 But no worries, I found some great alternatives nearby:\n\n{suggestion_text}\n\nWhich one works better for you? Just let me know!"
                else:
                    response = "Hmm, that time slot's busy and I couldn't find good alternatives right around then. How about suggesting another time that might work? 🤔"
            elif context.get('missing_info'):
                missing_fields = context.get('missing_fields', [])
                response = self._ask_for_missing_info(missing_fields, data)
            else:
                error_msg = context.get('message', context.get('error', ''))
                response = f"Oops! I ran into a little issue scheduling that meeting. {error_msg} Want to try again? 😊"
        
        elif intent == "DELETE_MEETING":
            if context.get('success'):
                response = "Done! ✅ I've removed that meeting from your calendar. One less thing to worry about!"
            elif context.get('meetings_found'):
                meetings = context.get('meetings', [])
                if len(meetings) == 1:
                    response = f"Found it! I can cancel '{meetings[0].title}' on {meetings[0].start_time.strftime('%Y-%m-%d at %H:%M')}. Should I go ahead and remove it?"
                else:
                    meetings_text = "\n".join([f"• {meeting.title} - {meeting.start_time.strftime('%Y-%m-%d at %H:%M')}" for meeting in meetings])
                    response = f"I found a few meetings that might match what you're looking for:\n\n{meetings_text}\n\nWhich one would you like me to cancel?"
            else:
                response = "Hmm, I couldn't find a meeting matching that description. Could you give me a bit more detail? Maybe the meeting title or when it's scheduled? 🔍"
        
        elif intent == "CHECK_AVAILABILITY":
            query_time = data.get('start_datetime', 'that time')
            if context.get('available'):
                response = f"Great news! You're completely free at {query_time}. Perfect timing! ✨"
            else:
                conflicting_event = context.get('conflicting_event', 'another meeting')
                response = f"Ah, you've got '{conflicting_event}' scheduled for {query_time}. Want me to check another time for you?"
        
        elif intent == "FIND_MEETINGS":
            if context.get('meetings'):
                meetings_count = len(context['meetings'])
                meetings_text = "\n".join([f"📅 {meeting}" for meeting in context['meetings']])
                response = f"Found {meetings_count} meeting{'s' if meetings_count != 1 else ''} matching what you're looking for:\n\n{meetings_text}"
            else:
                response = "I couldn't find any meetings matching those criteria. Maybe try different search terms? 🤷‍♀️"
        
        elif intent == "CONFIRMATION":
            response = context.get('response', "Thanks for confirming! Let me take care of that for you. ✨")
        
        elif intent == "PROVIDE_INFO":
            response = context.get('response', "Got it! Thanks for that information. Let me see what I can do with that. 😊")
        
        else:
            response = context.get('response', "Hey there! I'm here to help you manage your calendar like a pro. Feel free to ask me to check your schedule, set up meetings, or see if you're free at certain times! 😊")
        
        # Note: Assistant response is now added to history in main.py processing loop
        
        return response

    @trace_function
    def _ask_for_missing_info(self, missing_fields: List[str], current_data: Dict[str, Any]) -> str:
        """Generate friendly prompts for missing meeting information"""
        field_prompts = {
            'meeting_title': "What's this meeting about? Give me a quick title or purpose! 📝",
            'start_datetime': "When would you like to schedule this? (like 'tomorrow at 2pm' or 'Friday at 10:30am') ⏰",
            'duration_minutes': "How long should this meeting be? (I'll assume 1 hour if you don't specify) ⏱️",
            'attendees': "Who should I invite? You can give me email addresses, or just say 'just me' if it's a solo meeting! 👥"
        }
        
        # Special handling for start_datetime when we have a date but need a time
        if 'start_datetime' in missing_fields and current_data.get('start_datetime'):
            datetime_str = current_data['start_datetime']
            if isinstance(datetime_str, str) and 'T00:00:00' in datetime_str:
                # Extract the date part for a more specific prompt
                date_part = datetime_str.split('T')[0]
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_part)
                    day_name = date_obj.strftime('%A')  # e.g., "Friday"
                    formatted_date = date_obj.strftime('%B %d')  # e.g., "June 27"
                    field_prompts['start_datetime'] = f"What time on {day_name}, {formatted_date}? (like '3 PM EST' or '10:30 AM') ⏰"
                except:
                    field_prompts['start_datetime'] = "What time would work best? (like '3 PM EST' or '10:30 AM') ⏰"
        
        # Special handling for attendees with team references
        if 'attendees' in missing_fields and current_data.get('attendees'):
            attendees = current_data['attendees']
            has_team_references = any(
                any(team_word in str(attendee).lower() for team_word in ['team', 'group', 'department', 'staff'])
                and '@' not in str(attendee)
                for attendee in attendees
            )
            if has_team_references:
                team_names = [att for att in attendees if '@' not in str(att)]
                field_prompts['attendees'] = f"I see you want to invite the {', '.join(team_names)}! Could you give me the specific email addresses of the people you'd like to invite? 📧"
        
        if len(missing_fields) == 1:
            return f"Almost there! I just need one more thing: {field_prompts.get(missing_fields[0], f'the {missing_fields[0]}')} 😊"
        
        prompts = []
        for field in missing_fields:
            prompts.append(f"• {field_prompts.get(field, f'{field}')}")
        
        return f"I'm excited to help you schedule this! I just need a few more details:\n\n" + "\n".join(prompts) + "\n\nJust give me what you can, and we'll get this meeting set up! 🚀"

    @trace_function
    def confirm_meeting_details(self, meeting_data: Dict[str, Any]) -> str:
        """Generate a friendly confirmation message for meeting details"""
        title = meeting_data.get('meeting_title', 'Untitled Meeting')
        start_time = meeting_data.get('start_datetime', '')
        duration = meeting_data.get('duration_minutes', 60)
        attendees = meeting_data.get('attendees', [])
        location = meeting_data.get('location', '')
        description = meeting_data.get('meeting_description', '')
        
        confirmation = f"Perfect! Let me make sure I've got everything right:\n\n"
        confirmation += f"📅 **{title}**\n"
        if description:
            confirmation += f"📝 {description}\n"
        confirmation += f"🕒 {start_time}\n"
        confirmation += f"⏱️ {duration} minutes\n"
        
        if attendees:
            if len(attendees) == 1 and attendees[0].lower() in ['me', 'just me', 'myself']:
                confirmation += f"👤 Just you\n"
            else:
                confirmation += f"👥 {', '.join(attendees)}\n"
        
        if location:
            confirmation += f"📍 {location}\n"
        
        confirmation += "\nLooks good to go? Just say yes and I'll get it scheduled! ✨"
        
        return confirmation

    @trace_function
    def check_mandatory_fields(self, data: Dict[str, Any]) -> List[str]:
        """Check which mandatory fields are missing for meeting scheduling"""
        # All meetings need title, start time, and attendees
        mandatory_fields = ['meeting_title', 'start_datetime', 'attendees']

        # Check if this is a recurring meeting
        is_recurring = data.get('recurrence_pattern') and data.get('recurrence_count')
        
        # For non-recurring meetings, we also need duration
        if not is_recurring:
            mandatory_fields.append('duration_minutes')
        
        missing = []
        
        for field in mandatory_fields:
            if field not in data or not data[field]:
                # Special case for attendees - empty list is okay (solo meeting)
                if field == 'attendees' and field in data:
                    continue
                missing.append(field)
            elif field == 'start_datetime' and data[field]:
                # Check if start_datetime appears to be incomplete (e.g., midnight when user didn't specify time)
                datetime_str = data[field]
                if isinstance(datetime_str, str):
                    # Check if time is midnight (00:00:00) which often indicates missing time specification
                    if 'T00:00:00' in datetime_str:
                        missing.append('start_datetime')  # Need specific time
            elif field == 'attendees' and data[field]:
                # Check if attendees contains team references instead of email addresses
                attendees = data[field]
                has_team_references = any(
                    any(team_word in str(attendee).lower() for team_word in ['team', 'group', 'department', 'staff'])
                    and '@' not in str(attendee)
                    for attendee in attendees
                )
                if has_team_references:
                    missing.append('attendees')  # Need specific email addresses
        
        return missing

    @trace_function
    @trace_api_call("Gemini", "generate_dynamic_response")
    def generate_dynamic_response(self, situation: str, context_data: dict = None, user_message: str = "") -> str:
        """Generate dynamic responses using LLM instead of static strings"""
        
        # Get conversation context
        conversation_context = self.get_conversation_context()
        
        # Prepare context data as string
        context_str = ""
        if context_data:
            context_items = []
            for key, value in context_data.items():
                if isinstance(value, list) and value:
                    # Special handling for events/meetings - always show details
                    if key == 'events' and all(isinstance(item, dict) for item in value):
                        # Format meeting details properly
                        events_text = []
                        for event in value:
                            title = event.get('title', 'No Title')
                            time = event.get('time', 'No Time')
                            date = event.get('date', '')  # For weekly view
                            
                            if date:
                                # Weekly view - include date
                                event_line = f"• {title} on {date} from {time}"
                            else:
                                # Single day view
                                event_line = f"• {title} ({time})"
                            
                            if event.get('attendees'):
                                attendees_str = ', '.join(event['attendees'][:2])
                                if len(event['attendees']) > 2:
                                    attendees_str += f" +{len(event['attendees']) - 2} more"
                                event_line += f" - with {attendees_str}"
                            events_text.append(event_line)
                        context_items.append(f"{key}:\n" + "\n".join(events_text))
                    elif len(value) <= 3:
                        context_items.append(f"{key}: {', '.join(str(v) for v in value)}")
                    else:
                        # For other lists, provide both count and sample items
                        sample_items = ', '.join(str(v) for v in value[:3])
                        context_items.append(f"{key}: {len(value)} items (first 3: {sample_items}...)")
                elif value is not None:
                    context_items.append(f"{key}: {value}")
            context_str = "\n".join(context_items)
        
        prompt = f"""
        You are a friendly, conversational meeting scheduler assistant. Generate a natural response for this situation.
        Be warm, helpful, and personable - like talking to a good friend who's helping with your calendar.
        
        {conversation_context}
        
        Current situation: {situation}
        
        Additional context:
        {context_str}
        
        User's last message: "{user_message}"
        
        Current date/time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
        CRITICAL INSTRUCTIONS:
        - NEVER create, invent, or hallucinate fake meetings, events, or calendar data
        - ONLY use actual meeting/event information provided in the context above
        - If no meetings/events are provided in the context, the calendar is empty - acknowledge this clearly
        - If events_count is 0 or there are no events listed, say the calendar is free/empty
        - Do NOT create example meetings like "Project Brainstorm", "Client Presentation", etc.
        - When asking for clarification about which meeting to cancel, do NOT list fake meetings
        
        Generate a natural, conversational response that:
        1. Acknowledges the situation appropriately
        2. Uses the conversation context to maintain continuity
        3. Is helpful and friendly
        4. Uses emojis sparingly but effectively
        5. Matches the tone of a helpful assistant
        6. ONLY shows actual meeting details from the context if any exist
        
        When showing meetings/events, format them nicely with:
        - Meeting titles (only real ones from context)
        - Times (only real ones from context)
        - Attendees (only real ones from context)
        
        Keep the response conversational but informative. Don't include JSON or formatting instructions.
        Just return the natural response text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating dynamic response: {e}")
            # Fallback to a basic response
            return "I'm here to help! Let me know what you'd like to do with your calendar. 😊"
    
    def clear_history(self):
        """Clear the conversation history"""
        self.chat_history = []
        print("🔄 Chat history cleared!")
    
    def get_history_summary(self) -> str:
        """Get a summary of the current chat history for debugging"""
        if not self.chat_history:
            return "No chat history"
        
        summary = f"Chat history ({len(self.chat_history)} messages):\n"
        for i, entry in enumerate(self.chat_history, 1):
            role_emoji = "👤" if entry['role'] == 'user' else "🤖"
            summary += f"{i}. {role_emoji} {entry['role']}: {entry['message'][:50]}{'...' if len(entry['message']) > 50 else ''}\n"
        
        return summary







