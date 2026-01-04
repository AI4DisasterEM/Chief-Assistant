"""Test Google Calendar connection"""
import sys
sys.path.insert(0, '.')

from src.calendar.google_calendar import get_todays_events, get_upcoming_events, format_events_for_display

def main():
    print("Testing Google Calendar Connection...\n")
    
    print("📅 TODAY'S EVENTS:")
    print("-" * 40)
    events = get_todays_events()
    print(format_events_for_display(events))
    
    print("\n📅 NEXT 7 DAYS:")
    print("-" * 40)
    upcoming = get_upcoming_events(days=7)
    print(format_events_for_display(upcoming))
    
    print("\n✅ Calendar connection working!")

if __name__ == "__main__":
    main()
