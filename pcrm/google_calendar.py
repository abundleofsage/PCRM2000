import os.path
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_calendar_service():
    """
    Handles Google Calendar API authentication and returns a service object.

    This function manages the OAuth 2.0 flow. It looks for a `token.json`
    file which stores the user's access and refresh tokens, and is created
    automatically when the authorization flow completes for the first time.

    It requires a `credentials.json` file from a Google Cloud project with the
    OAuth 2.0 Client ID enabled. The user must provide this file.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                # Potentially corrupted token.json, force re-login
                creds = None

        if not creds:
            if not os.path.exists("credentials.json"):
                print("\n--- Google Calendar Integration Setup ---")
                print("ERROR: `credentials.json` not found.")
                print("To use Google Calendar integration, you must enable the Google Calendar API")
                print("in your Google Cloud project and download your OAuth 2.0 Client ID")
                print("credentials. Save the file as `credentials.json` in the same directory")
                print("as this application.")
                print("-------------------------------------------\n")
                return None

            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred building the service: {error}")
        return None

def create_calendar_event(summary, start_datetime, end_datetime):
    """
    Creates an event on the user's primary Google Calendar.

    Args:
        summary (str): The title of the event.
        start_datetime (datetime.datetime): The start time of the event.
        end_datetime (datetime.datetime): The end time of the event.
    """
    service = get_calendar_service()
    if not service:
        print("Could not connect to Google Calendar. Event not created.")
        return

    event = {
        'summary': summary,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'America/Los_Angeles', # TODO: Make this configurable
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'America/Los_Angeles', # TODO: Make this configurable
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except HttpError as error:
        print(f"An error occurred creating the event: {error}")
