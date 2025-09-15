# Meeting Title Auto-Generation Enhancement

## Current Issue
The meeting scheduler currently requires `meeting_title` as a mandatory field, creating unnecessary friction for users in simple scheduling scenarios.

## Proposed Solution
Implement smart auto-generation of meeting titles when not explicitly provided by the user.

## Auto-Generation Logic

### Priority Order:
1. **User-provided title** (highest priority)
2. **Context-based title** (extracted from conversation)
3. **Attendee-based title** (generated from attendees)
4. **Default title** (fallback)

### Title Generation Rules:

```python
def generate_meeting_title(data: dict) -> str:
    """Auto-generate meeting title based on available information"""
    
    # If user provided a title, use it
    if data.get('meeting_title'):
        return data['meeting_title']
    
    # Extract context clues from description or conversation
    description = data.get('meeting_description', '').lower()
    if 'review' in description:
        return "Project Review"
    elif 'standup' in description or 'daily' in description:
        return "Daily Standup"
    elif 'planning' in description:
        return "Planning Session"
    elif 'demo' in description:
        return "Demo Session"
    
    # Generate based on attendees
    attendees = data.get('attendees', [])
    if attendees:
        if len(attendees) == 1:
            # Extract name from email if possible
            attendee = attendees[0]
            if '@' in attendee:
                name = attendee.split('@')[0].replace('.', ' ').title()
                return f"Meeting with {name}"
            else:
                return f"Meeting with {attendee}"
        elif len(attendees) <= 3:
            names = []
            for attendee in attendees:
                if '@' in attendee:
                    name = attendee.split('@')[0].replace('.', ' ').title()
                    names.append(name)
                else:
                    names.append(attendee)
            return f"Meeting with {', '.join(names)}"
        else:
            return f"Team Meeting ({len(attendees)} attendees)"
    
    # Time-based titles
    start_time = data.get('start_datetime')
    if start_time:
        try:
            dt = datetime.fromisoformat(start_time)
            hour = dt.hour
            if 6 <= hour < 12:
                return "Morning Meeting"
            elif 12 <= hour < 17:
                return "Afternoon Meeting"
            else:
                return "Evening Meeting"
        except:
            pass
    
    # Default fallback
    return "Scheduled Meeting"
```

## Updated Mandatory Fields Logic

```python
def check_mandatory_fields(self, data: Dict[str, Any]) -> List[str]:
    """Check which mandatory fields are missing for meeting scheduling"""
    # Remove meeting_title from mandatory fields
    mandatory_fields = ['start_datetime', 'duration_minutes', 'attendees']
    missing = []
    
    for field in mandatory_fields:
        if field not in data or not data[field]:
            # Special case for attendees - empty list is okay (solo meeting)
            if field == 'attendees' and field in data:
                continue
            missing.append(field)
    
    return missing
```

## Benefits

### 1. **Reduced User Friction**
- Fewer questions asked
- Faster meeting scheduling
- More natural conversation flow

### 2. **Better User Experience**
```
Before:
User: Schedule a call with shreysoni009@gmail.com at 2 PM
Bot: What's the meeting about?
User: Just a regular call
Bot: How long should it be?
User: 1 hour

After:
User: Schedule a call with shreysoni009@gmail.com at 2 PM
Bot: Perfect! I've scheduled "Meeting with Shreysoni009" for today at 2 PM (1 hour)
```

### 3. **Smart Context Understanding**
- Extracts meaning from user input
- Uses conversation history
- Generates meaningful titles

## Updated Test Scenarios

### Easy Level - No Title Required
```
User: Schedule a meeting with shreysoni009@gmail.com tomorrow at 2 PM for 1 hour
Expected: Auto-generate title "Meeting with Shreysoni009", schedule successfully
```

### Medium Level - Context-Based Title
```
User: Set up our weekly standup with the team
Bot: [Asks for time and attendees]
User: Tomorrow 9 AM with shreysoni009@gmail.com and kushal.multiqos@gmail.com
Expected: Auto-generate title "Weekly Standup", schedule successfully
```

### Hard Level - Multiple Context Clues
```
User: I need to schedule the quarterly review we discussed
Bot: [Asks for specifics]
User: Next Friday with shreysoni009@gmail.com and the management team
Expected: Auto-generate title "Quarterly Review", handle complex scheduling
```

## Implementation Steps

1. **Update `check_mandatory_fields()`** - Remove meeting_title requirement
2. **Add `generate_meeting_title()`** - Smart title generation function
3. **Modify scheduling logic** - Auto-generate titles before creating events
4. **Update conversation handler** - Don't ask for title unless needed
5. **Test thoroughly** - Ensure all scenarios work with auto-generated titles

## Fallback Strategy
- Always allow users to override auto-generated titles
- Provide option to specify custom titles
- Maintain backward compatibility

This enhancement will make your meeting scheduler much more user-friendly and natural! 🚀 