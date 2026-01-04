"""Google Calendar integration for CHIEF Assistant"""
import os
import json
import boto3
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_google_credentials():
    """Retrieve Google OAuth credentials from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='chief/google-oauth')
    secret = json.loads(response['SecretString'])
    
    credentials = Credentials(
        token=secret.get('access_token'),
        refresh_token=secret.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=secret.get('client_id'),
        client_secret=secret.get('client_secret')
    )
    return credentials


def get_calendar_service():
    """Build and return Google Calendar service"""
    credentials = get_google_credentials()
    service = build('calendar', 'v3', credentials=credentials)
    return service


def get_todays_events():
    """Get all events for today"""
    service = get_calendar_service()
    
    now = datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_of_day.isoformat() + 'Z',
        timeMax=end_of_day.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])


def get_upcoming_events(days=7):
    """Get events for the next N days"""
    service = get_calendar_service()
    
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now.isoformat() + 'Z',
        timeMax=end_date.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])


def create_event(summary, start_time, end_time, description=None, location=None):
    """Create a new calendar event"""
    service = get_calendar_service()
    
    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/New_York',
        },
    }
    
    if description:
        event['description'] = description
    if location:
        event['location'] = location
    
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event


def find_free_time(duration_minutes=60, days_ahead=7):
    """Find available time slots"""
    events = get_upcoming_events(days=days_ahead)
    
    # Simple implementation - find gaps between events
    free_slots = []
    now = datetime.utcnow()
    
    # Business hours: 8 AM - 6 PM
    for day_offset in range(days_ahead):
        day = now + timedelta(days=day_offset)
        day_start = day.replace(hour=13, minute=0, second=0, microsecond=0)  # 8 AM EST in UTC
        day_end = day.replace(hour=23, minute=0, second=0, microsecond=0)    # 6 PM EST in UTC
        
        # Get events for this day
        day_events = [e for e in events if e.get('start', {}).get('dateTime', '').startswith(day.strftime('%Y-%m-%d'))]
        
        if not day_events:
            free_slots.append({
                'start': day_start,
                'end': day_end,
                'duration_minutes': (day_end - day_start).seconds // 60
            })
    
    return free_slots


def format_events_for_display(events):
    """Format events list for SMS/display"""
    if not events:
        return "No events scheduled."
    
    lines = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if 'T' in start:
            dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            time_str = dt.strftime('%I:%M %p')
        else:
            time_str = 'All day'
        
        summary = event.get('summary', 'No title')
        location = event.get('location', '')
        
        line = f"• {time_str} - {summary}"
        if location:
            line += f" @ {location}"
        lines.append(line)
    
    return "\n".join(lines)
