# Meeting Scheduler Bot

An intelligent, voice-assisted conversational bot that manages your Google Calendar using natural language and Google Gemini AI. Schedule, view, and manage meetings hands-free—perfect for busy professionals!

---

## 🚀 Features

- **Natural Language Conversation**: Talk to the bot as you would to a human assistant.
- **Google Calendar Integration**: Add, view, delete and manage events directly in your Google Calendar.
- **Smart Scheduling**: Detects conflicts and suggests alternative times.
- **Context Awareness**: Understands phrases like "next Friday" or "tomorrow at 2 PM".
- **Recurring Meetings**: Easily set up weekly or daily meetings.
- **Voice and Text Support**: Use voice commands or type your requests.

---

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Voice-Assisted-Meeting-Planner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Google Calendar API Setup**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create/select a project
   - Enable the Google Calendar API
   - Go to "APIs & Services > Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Download the file and save as `credentials.json` in the project root
   - This file contains your app's client ID and secret. **Do not share it!**

4. **First Run: OAuth Token Generation**
   - On first run, the app will prompt you to log in with your Google account
   - It will generate a `token.json` file (your access/refresh token)
   - **Never commit `credentials.json` or `token.json` to git!**

5. **Gemini API Setup**
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Set it as an environment variable:
     ```bash
     export GEMINI_API_KEY="your-api-key-here"
     ```

6. **Optional Configuration**
   - Set your timezone:
     ```bash
     export TIMEZONE="America/New_York"
     ```
   - Set a custom calendar ID:
     ```bash
     export GOOGLE_CALENDAR_ID="your-email@gmail.com"
     ```

---

## 🗂️ Project Structure

```
Voice-Assisted-Meeting-Planner/
├── main.py                  # Main entry point
├── config/
│   ├── settings.py          # App configuration
│   └── logger.py            # Logging/tracing
├── models/
│   └── meeting.py           # Meeting data models
├── services/
│   ├── calendar_manager.py  # Google Calendar logic
│   ├── conversation_handler.py # Gemini AI logic
│   └── scheduler_logic.py   # Scheduling logic
├── real_time_tts_version2/  # Voice/Audio modules
├── temp_audio/              # Temporary audio files (gitignored)
├── credentials.json         # Google API credentials (DO NOT COMMIT)
├── token.json               # OAuth token (DO NOT COMMIT)
└── .gitignore               # Ignore sensitive & temp files
```

---

## 🔑 About `credentials.json` and `token.json`

- **`credentials.json`**: Downloaded from Google Cloud Console. Contains your app's OAuth client ID and secret. Required for authenticating with Google Calendar API. **Keep this file private!**
- **`token.json`**: Generated automatically after you authenticate on first run. Stores your access and refresh tokens so you don't have to log in every time. **Never share this file!**
- Both files are listed in `.gitignore` to prevent accidental commits.

---

## 📝 Example Usage

- "What are my meetings today?"
- "Schedule a meeting with John tomorrow at 2 PM"
- "Book a 1-hour call with sarah@company.com for Friday"
- "Show me all meetings with the word 'review'"
- "Am I free this Friday at 10 AM?"

---

## 🧠 Architecture Overview

- **CalendarManager**: Handles all Google Calendar API operations (auth, CRUD, etc.)
- **ConversationHandler**: Uses Gemini AI to process and understand user input
- **SchedulerLogic**: Handles conflict detection and smart suggestions
- **Meeting/TimeSlot Models**: Clean data structures for events
- **Logger**: Traces and logs all actions for debugging

---

## 🛡️ Security & Best Practices

- Never share or commit your `credentials.json` or `token.json`.
- Use environment variables for sensitive keys (like `GEMINI_API_KEY`).
- All temporary audio and cache files are ignored via `.gitignore`.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
