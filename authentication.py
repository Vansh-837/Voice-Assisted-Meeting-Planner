# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

# SCOPES = ['https://www.googleapis.com/auth/calendar']

# # Run OAuth flow
# flow = InstalledAppFlow.from_client_secrets_file(
#     'client_secret_652953902856-vpttnqi41dlf2ta5pudb8q2dr8t8ts85.apps.googleusercontent.com.json', SCOPES)
# creds = flow.run_local_server(port=0)

# # Build the calendar service
# service = build('calendar', 'v3', credentials=creds)

# # Example: List upcoming events
# events_result = service.events().list(
#     calendarId='primary', maxResults=10).execute()

# for event in events_result.get('items', []):
#     print(event['summary'], event.get('start', {}).get('dateTime'))




from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        # Starts OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret_652953902856-vpttnqi41dlf2ta5pudb8q2dr8t8ts85.apps.googleusercontent.com.json', SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the token for future use
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    return creds

# Use the credentials
creds = get_credentials()
service = build('calendar', 'v3', credentials=creds)

# Test: List upcoming events
events_result = service.events().list(calendarId='primary', maxResults=5).execute()
for event in events_result.get('items', []):
    print(event['summary'], event.get('start', {}).get('dateTime'))
