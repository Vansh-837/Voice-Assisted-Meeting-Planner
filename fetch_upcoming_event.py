from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('token.json')
service = build('calendar', 'v3', credentials=creds)

events_result = service.events().list(
    calendarId='primary', maxResults=5, singleEvents=True,
    orderBy='startTime').execute()

events = events_result.get('items', [])
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(start, event['summary'])
