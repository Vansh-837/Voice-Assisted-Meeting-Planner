# Meeting Scheduler Bot - Comprehensive Test Conversation Scenarios

This document contains 3 levels of conversation complexity for each scenario in the meeting scheduler solution to thoroughly test accuracy and robustness.

## 1. ADD_MEETING (Schedule New Meetings)

### 🟢 Easy Level Conversations
**Simple, direct requests with all information provided**

**Test Case 1.1: Complete Information**
```
User: Schedule a project review meeting with shreysoni009@gmail.com tomorrow at 2 PM for 1 hour
Expected: Successfully schedule meeting with all details extracted
```

**Test Case 1.2: Basic Meeting**
```
User: Book a team standup meeting for today at 9 PM with shreysoni009@gmail.com
Expected: Schedule meeting with default 60-minute duration
```

**Test Case 1.3: Simple Time Format**
```
User: Add a lunch meeting with shreysoni009@gmail.com at 12:30 PM tomorrow
Expected: Parse time correctly and schedule meeting
```

### 🟡 Medium Level Conversations
**Multi-turn conversations with some missing information**

**Test Case 1.4: Missing Duration and Title**
```
User: I need to schedule a meeting with the marketing team tomorrow at 3 PM
Bot: [Asks for meeting title, duration and attendees]
User: Make it a quarterly planning meeting for 90 minutes with shreysoni009@gmail.com and kushal.multiqos@gmail.com  
Expected: Multi-turn conversation handling, successful scheduling
```

**Test Case 1.5: Missing Title and Time**
```
User: Can you set up a meeting with shreysoni009@gmail.com and kushal.multiqos@gmail.com next Tuesday?
Bot: [Asks for meeting title, time, duration]
User: A project review meeting at 10 AM for 2 hours
Expected: Parse "next Tuesday" correctly, handle follow-up info
```

**Test Case 1.6: Conflict Resolution with Title**
```
User: Schedule a client call meeting with shreysoni009@gmail.com tomorrow at 12:30 PM
Bot: [Detects conflict, offers alternatives]
User: The 11 AM slot works perfect
Expected: Handle time conflicts, accept alternative suggestion
```

### 🔴 Hard Level Conversations
**Complex scenarios with ambiguity, conflicts, and edge cases**

**Test Case 1.7: Complex Time Zones with Missing Title**
```
User: I need to meet with the London team next Friday
Bot: [Asks for meeting title, time, duration, attendees]
User: Q4 planning session at 3 PM EST with shreysoni009@gmail.com
Bot: [Asks for duration]
User: 2 hours should be enough
Expected: Handle timezone conversion, multi-turn context retention
```

**Test Case 1.8: Ambiguous References**
```
User: Set up that important meeting we discussed
Bot: [Asks for clarification on meeting title, time, attendees]
User: The client proposal review with shreysoni009@gmail.com
Bot: [Asks for more details like time]
User: Tomorrow afternoon around 3-ish for about an hour
Expected: Handle vague references, extract informal time expressions
```

**Test Case 1.9: Multiple Conflicts & Preferences**
```
User: I need to schedule a board meeting with all executives next week
Bot: [Asks for specifics including time, attendees]
User: Executive quarterly review on Tuesday or Wednesday, preferably morning, 3 hours with shreysoni009@gmail.com, kushal.multiqos@gmail.com, and ceo@company.com
Bot: [Checks availability, finds conflicts]
User: Wednesday morning is more important, can we move the other meeting?
Expected: Handle complex scheduling preferences, multiple attendees, rescheduling suggestions
```

## 2. DELETE_MEETING (Cancel/Remove Meetings)

### 🟢 Easy Level Conversations

**Test Case 2.1: Specific Meeting Title**
```
User: Cancel my project review meeting
Expected: Find and cancel the specific meeting
```

**Test Case 2.2: Time-based Deletion**
```
User: Delete my 2 PM meeting today  
Expected: Identify meeting by time and cancel it
```

**Test Case 2.3: Direct Cancellation**
```
User: Remove the standup meeting tomorrow
Expected: Locate and cancel the specified meeting
```

### 🟡 Medium Level Conversations

**Test Case 2.4: Multiple Matches**
```
User: Cancel my meeting with Shrey
Bot: [Shows multiple meetings with Shrey]
User: The project review one scheduled for Thursday at 3 PM
Expected: Handle multiple matches, allow user selection
```

**Test Case 2.5: Partial Information**
```
User: I need to cancel a meeting
Bot: [Asks which meeting]
User: The client call this week
Bot: [Shows matching meetings]
User: The one with shreysoni009@gmail.com
Expected: Multi-turn clarification process
```

**Test Case 2.6: Date Range Confusion**
```
User: Cancel my morning meeting
Bot: [Asks which day]
User: Tomorrow morning
Bot: [Shows tomorrow's morning meetings]
User: The 9 AM standup meeting
Expected: Handle ambiguous time references
```

### 🔴 Hard Level Conversations

**Test Case 2.7: Complex Meeting Description**
```
User: I need to cancel that recurring weekly sync we have
Bot: [Asks for clarification]
User: The weekly team standup every Tuesday with the dev team
Bot: [Shows options]
User: Just this week's instance, not the whole series
Expected: Handle recurring meetings, partial cancellation
```

**Test Case 2.8: Ambiguous References**
```
User: Cancel the meeting with the difficult client
Bot: [Asks for more details]
User: You know, the contract negotiation meeting where we discussed the issues
Bot: [Asks for specific identifiers]
User: It's the client review meeting with shreysoni009@gmail.com next week sometime
Expected: Handle vague descriptions, extract meaningful identifiers
```

**Test Case 2.9: Emergency Cancellation**
```
User: I need to cancel everything tomorrow, family emergency
Bot: [Shows all tomorrow's meetings]
User: Yes, cancel all of them and send apologies
Expected: Bulk cancellation handling, context understanding
```

## 3. VIEW_SCHEDULE/VIEW_CALENDAR (View Calendar Events)

### 🟢 Easy Level Conversations

**Test Case 3.1: Today's Schedule**
```
User: What's on my calendar today?
Expected: Display today's meetings clearly formatted
```

**Test Case 3.2: Specific Date**
```
User: Show me my schedule for tomorrow
Expected: Display tomorrow's meetings
```

**Test Case 3.3: Simple Date Format**
```
User: What meetings do I have on Friday?
Expected: Show Friday's schedule
```

### 🟡 Medium Level Conversations

**Test Case 3.4: Date Range**
```
User: What's my schedule like this week?
Expected: Show weekly overview or ask for specific day
```

**Test Case 3.5: Relative Dates**
```
User: Show me next Monday's calendar
Expected: Parse "next Monday" and display schedule
```

**Test Case 3.6: Empty Schedule**
```
User: What do I have on Saturday?
Expected: Handle empty schedule gracefully
```

### 🔴 Hard Level Conversations

**Test Case 3.7: Complex Date Parsing**
```
User: What's happening on the 20th of next month?
Expected: Parse complex date reference accurately
```

**Test Case 3.8: Contextual Follow-up**
```
User: Show my calendar
Bot: [Shows today's calendar]
User: What about tomorrow?
Expected: Understand contextual reference to calendar viewing
```

**Test Case 3.9: Detailed Information Request**
```
User: I need a detailed breakdown of my meetings this week including attendees and locations
Expected: Provide comprehensive meeting details
```

## 4. CHECK_AVAILABILITY (Check Free Time)

### 🟢 Easy Level Conversations

**Test Case 4.1: Simple Time Check**
```
User: Am I free at 3 PM today?
Expected: Check availability and respond clearly
```

**Test Case 4.2: Tomorrow's Availability**
```
User: Do I have anything at 10 AM tomorrow?
Expected: Check specific time slot
```

**Test Case 4.3: Basic Time Range**
```
User: Am I available from 2 to 4 PM today?
Expected: Check time range for conflicts
```

### 🟡 Medium Level Conversations

**Test Case 4.4: Multiple Time Options**
```
User: When am I free tomorrow morning?
Expected: Provide available time slots in morning
```

**Test Case 4.5: Duration-Specific Check**
```
User: Do I have 2 hours free this afternoon?
Expected: Find 2-hour blocks of free time
```

**Test Case 4.6: Best Time Suggestion**
```
User: When's the best time to schedule a 1-hour meeting today?
Expected: Suggest optimal available slots
```

### 🔴 Hard Level Conversations

**Test Case 4.7: Complex Scheduling Constraints**
```
User: I need to find time for a 3-hour workshop next week, preferably not on Monday or Friday
Expected: Handle complex constraints and preferences
```

**Test Case 4.8: Recurring Availability**
```
User: When am I consistently free every Tuesday for the next month?
Expected: Analyze recurring availability patterns
```

**Test Case 4.9: Priority-Based Scheduling**
```
User: I need to fit in an urgent 30-minute call today, what's my most flexible time slot?
Expected: Identify best time considering existing meeting importance
```

## 5. RESCHEDULE_MEETING (Change Meeting Times)

### 🟢 Easy Level Conversations

**Test Case 5.1: Simple Reschedule**
```
User: Move my 2 PM meeting to 3 PM
Expected: Identify meeting and reschedule successfully
```

**Test Case 5.2: Specific Meeting**
```
User: Reschedule the client call to tomorrow at the same time
Expected: Find specific meeting and move to new date
```

**Test Case 5.3: Direct Time Change**
```
User: Change my morning standup from 9 AM to 10 AM
Expected: Update meeting time
```

### 🟡 Medium Level Conversations

**Test Case 5.4: Multiple Options**
```
User: I need to reschedule my meeting with Shrey
Bot: [Shows multiple meetings with Shrey]
User: The project review one, move it to Friday at 2 PM
Expected: Handle multiple matches, execute reschedule
```

**Test Case 5.5: Conflict Resolution**
```
User: Move my lunch meeting to 1 PM
Bot: [Detects conflict at 1 PM]
User: How about 1:30 PM then?
Expected: Handle rescheduling conflicts
```

**Test Case 5.6: Partial Information**
```
User: I need to reschedule tomorrow's important meeting
Bot: [Asks which meeting]
User: The board presentation, move it to next week
Bot: [Asks for specific time]
User: Same time, just next Wednesday
Expected: Multi-turn rescheduling process
```

### 🔴 Hard Level Conversations

**Test Case 5.7: Complex Rescheduling**
```
User: The quarterly review needs to move because half the team is traveling
Bot: [Identifies meeting]
User: Find a time next week when everyone's available
Bot: [Checks attendee availability]
User: Tuesday afternoon looks good for everyone
Expected: Handle complex attendee availability checking
```

**Test Case 5.8: Cascading Changes**
```
User: If I move my 10 AM meeting to 11 AM, will that conflict with anything?
Bot: [Checks for conflicts]
User: Yes, then move that conflicting meeting too
Expected: Handle cascading schedule changes
```

**Test Case 5.9: Recurring Meeting Changes**
```
User: I need to permanently change our weekly standup time
Bot: [Identifies recurring meeting]
User: Move the whole series from 9 AM to 8:30 AM starting next week
Expected: Handle recurring meeting modifications
```

## 6. FIND_MEETINGS (Search for Specific Meetings)

### 🟢 Easy Level Conversations

**Test Case 6.1: Find by Person**
```
User: Show me all meetings with shreysoni009@gmail.com
Expected: List all meetings with specified person
```

**Test Case 6.2: Find by Title**
```
User: Find my project review meetings
Expected: Search meetings by title keyword
```

**Test Case 6.3: Find by Date**
```
User: What meetings do I have with clients this week?
Expected: Search by criteria and date range
```

### 🟡 Medium Level Conversations

**Test Case 6.4: Multiple Criteria**
```
User: Find meetings with the marketing team about the campaign
Expected: Search by both attendee and topic
```

**Test Case 6.5: Date Range Search**
```
User: Show me all my external meetings from last week
Expected: Search by meeting type and date range
```

**Test Case 6.6: Partial Matches**
```
User: Find meetings with anyone from the development team
Expected: Search by team or department name
```

### 🔴 Hard Level Conversations

**Test Case 6.7: Complex Search Criteria**
```
User: Find all recurring meetings I have with external stakeholders that are longer than 1 hour
Expected: Handle multiple complex search parameters
```

**Test Case 6.8: Fuzzy Matching**
```
User: Show me meetings related to the new product launch initiative
Expected: Use semantic search for related topics
```

**Test Case 6.9: Historical Analysis**
```
User: How many meetings did I have with shreysoni009@gmail.com last month compared to this month?
Expected: Provide analytical comparison of meeting patterns
```

## 7. CONFIRMATION (Yes/No Responses)

### 🟢 Easy Level Conversations

**Test Case 7.1: Simple Yes**
```
User: Schedule a meeting tomorrow at 2 PM with shreysoni009@gmail.com
Bot: [Asks for confirmation after detecting conflict]
User: Yes
Expected: Execute the confirmed action
```

**Test Case 7.2: Clear No**
```
User: Cancel my 3 PM meeting
Bot: [Asks for confirmation]
User: No, actually keep it
Expected: Abort the cancellation
```

**Test Case 7.3: Okay Confirmation**
```
User: Am I free at 4 PM?
Bot: [Shows conflict, suggests alternative]
User: Okay, that works
Expected: Accept the suggestion
```

### 🟡 Medium Level Conversations

**Test Case 7.4: Contextual Confirmation**
```
User: I need to schedule a client meeting
Bot: [Asks for details]
User: Tomorrow at 3 PM with shreysoni009@gmail.com
Bot: [Detects conflict, offers alternatives]
User: The 4 PM slot sounds good
Expected: Understand confirmation in context
```

**Test Case 7.5: Partial Agreement**
```
User: Reschedule my morning meetings
Bot: [Shows multiple meetings]
User: Just the first two, keep the others
Expected: Handle partial confirmations
```

**Test Case 7.6: Clarification Needed**
```
User: Set up a team meeting
Bot: [Asks for details]
User: Sure, make it for the whole dev team
Bot: [Asks for time]
User: Whatever works best for everyone
Expected: Handle confirmations that need more clarification
```

### 🔴 Hard Level Conversations

**Test Case 7.7: Ambiguous Confirmation**
```
User: I might need to cancel some meetings next week
Bot: [Asks which ones]
User: The non-essential ones
Bot: [Asks for clarification]
User: You decide based on priority
Expected: Handle ambiguous confirmations requiring judgment
```

**Test Case 7.8: Conditional Confirmation**
```
User: Schedule the board meeting if everyone's available
Bot: [Checks availability]
User: Only if we can get at least 80% attendance
Expected: Handle conditional confirmations
```

**Test Case 7.9: Context-Dependent Response**
```
User: What do you think about moving the sprint planning?
Bot: [Provides analysis]
User: That makes sense, let's do it
Expected: Understand confirmation in conversational context
```

## 8. PROVIDE_INFO (Providing Missing Information)

### 🟢 Easy Level Conversations

**Test Case 8.1: Simple Follow-up**
```
User: Schedule a meeting tomorrow
Bot: [Asks for time and attendees]
User: 2 PM with shreysoni009@gmail.com
Expected: Merge new information with existing request
```

**Test Case 8.2: Duration Clarification**
```
User: Book a client call
Bot: [Asks for details]
User: 1 hour with shreysoni009@gmail.com at 3 PM tomorrow
Expected: Extract all missing information at once
```

**Test Case 8.3: Attendee Addition**
```
User: Set up a project meeting
Bot: [Asks for attendees]
User: shreysoni009@gmail.com and kushal.multiqos@gmail.com
Expected: Add attendee information to pending meeting
```

### 🟡 Medium Level Conversations

**Test Case 8.4: Incremental Information**
```
User: I need a meeting scheduled
Bot: [Asks for details]
User: Tomorrow afternoon
Bot: [Asks for specific time]
User: 3 PM
Bot: [Asks for attendees]
User: The marketing team
Expected: Handle multi-step information gathering
```

**Test Case 8.5: Correction and Addition**
```
User: Schedule a meeting at 2 PM
Bot: [Asks for more details]
User: Actually make it 3 PM with shreysoni009@gmail.com about the proposal
Expected: Handle corrections while adding information
```

**Test Case 8.6: Timezone Clarification**
```
User: Book a call with the London office
Bot: [Asks for time]
User: 10 AM EST with shreysoni009@gmail.com
Expected: Handle timezone specifications
```

### 🔴 Hard Level Conversations

**Test Case 8.7: Complex Information Merge**
```
User: Set up the quarterly review
Bot: [Asks for details]
User: Next Friday, 2 hours, with all department heads and the CEO, make it a video call
Bot: [Asks for specific time]
User: Morning works best, maybe 9 or 10 AM, check everyone's availability
Expected: Handle complex information with preferences
```

**Test Case 8.8: Conflicting Information**
```
User: Schedule a team meeting tomorrow
Bot: [Asks for time]
User: 2 PM
Bot: [Detects conflict]
User: Oh right, I have that client call, make it 3 PM instead
Bot: [Asks for attendees]
User: The whole development team except Shrey, he's out sick
Expected: Handle information updates and exceptions
```

**Test Case 8.9: Context-Rich Follow-up**
```
User: I need to organize the product launch meeting we discussed
Bot: [Asks for specifics]
User: You know, the big one with marketing, sales, and engineering, probably need 3 hours
Bot: [Asks for timing]
User: Sometime next week when everyone's back from the conference, preferably not Monday
Expected: Handle rich contextual information with constraints
```

## 9. GREETING (Initial Interactions)

### 🟢 Easy Level Conversations

**Test Case 9.1: Simple Hello**
```
User: Hello
Expected: Friendly greeting with feature overview
```

**Test Case 9.2: Good Morning**
```
User: Good morning
Expected: Time-appropriate greeting
```

**Test Case 9.3: Hi There**
```
User: Hi there
Expected: Casual friendly response
```

### 🟡 Medium Level Conversations

**Test Case 9.4: Greeting with Intent**
```
User: Hi, I need help with my calendar
Expected: Greeting combined with readiness to help
```

**Test Case 9.5: Return Greeting**
```
User: Hey, I'm back
Expected: Welcome back message
```

**Test Case 9.6: Casual Start**
```
User: What's up?
Expected: Casual response with availability to help
```

### 🔴 Hard Level Conversations

**Test Case 9.7: Emotional Context**
```
User: Hi, I'm having a crazy day with all these meetings
Expected: Empathetic response with offer to help organize
```

**Test Case 9.8: Specific Situation**
```
User: Hello, I just got back from vacation and my calendar is a mess
Expected: Contextual greeting with specific assistance offer
```

**Test Case 9.9: Urgent Greeting**
```
User: Hi! I need immediate help, everything's double-booked
Expected: Recognize urgency and offer immediate assistance
```

## 10. HELP (Help and Information Requests)

### 🟢 Easy Level Conversations

**Test Case 10.1: Simple Help**
```
User: Help
Expected: Comprehensive feature list and usage guide
```

**Test Case 10.2: What Can You Do**
```
User: What can you do?
Expected: Clear capability overview
```

**Test Case 10.3: How Do I**
```
User: How do I schedule a meeting?
Expected: Step-by-step scheduling guidance
```

### 🟡 Medium Level Conversations

**Test Case 10.4: Specific Feature Help**
```
User: How do I check my availability?
Expected: Detailed explanation of availability checking
```

**Test Case 10.5: Troubleshooting**
```
User: I'm having trouble canceling a meeting
Expected: Troubleshooting steps for cancellation
```

**Test Case 10.6: Feature Comparison**
```
User: What's the difference between viewing my calendar and checking availability?
Expected: Clear explanation of feature differences
```

### 🔴 Hard Level Conversations

**Test Case 10.7: Complex Workflow Help**
```
User: How do I handle recurring meetings and exceptions?
Expected: Advanced feature explanation with examples
```

**Test Case 10.8: Integration Questions**
```
User: How does this work with my Google Calendar and timezone settings?
Expected: Technical integration details
```

**Test Case 10.9: Best Practices**
```
User: What's the best way to manage a busy calendar with lots of conflicts?
Expected: Strategic advice and workflow recommendations
```

---

## Testing Guidelines

### Evaluation Criteria

1. **Intent Recognition Accuracy**: Does the bot correctly identify the user's intent?
2. **Data Extraction Precision**: Are all relevant details extracted accurately?
3. **Context Retention**: Does the bot maintain conversation context across turns?
4. **Error Handling**: How gracefully does the bot handle ambiguous or incomplete requests?
5. **Response Quality**: Are responses helpful, natural, and appropriate?
6. **Edge Case Handling**: Does the bot handle unusual scenarios properly?

### Success Metrics

- **Easy Level**: 95%+ success rate expected
- **Medium Level**: 85%+ success rate expected  
- **Hard Level**: 70%+ success rate expected

### Testing Process

1. Run each conversation scenario
2. Record bot responses
3. Evaluate against expected outcomes
4. Note any failures or unexpected behaviors
5. Identify patterns in failures for improvement

This comprehensive test suite covers all major scenarios and complexity levels to thoroughly evaluate your meeting scheduler bot's accuracy and robustness! 🚀 