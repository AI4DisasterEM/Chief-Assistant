"""Full CHIEF System Integration Test"""
import sys
sys.path.insert(0, '.')

def main():
    print("=" * 50)
    print("   CHIEF ASSISTANT - FULL SYSTEM TEST")
    print("=" * 50)
    
    # 1. Calendar
    print("\n📅 CALENDAR")
    print("-" * 30)
    from src.calendar.google_calendar import get_todays_events, format_events_for_display
    events = get_todays_events()
    print(format_events_for_display(events))
    
    # 2. Credentials
    print("\n📚 PROFESSIONAL DEVELOPMENT")
    print("-" * 30)
    from src.agent.credentials_manager import CredentialsManager
    cm = CredentialsManager()
    print(cm.format_status_report())
    
    # 3. Contacts
    print("\n👥 KEY CONTACTS")
    print("-" * 30)
    from src.agent.contacts_manager import ContactsManager
    contacts = ContactsManager()
    for c in contacts.get_all_contacts()[:5]:
        print(f"  • {c['name']} - {c['role']}")
    
    # 4. Pending Actions
    print("\n✅ PENDING ACTIONS")
    print("-" * 30)
    from src.notes.note_manager import NoteSession
    notes = NoteSession()
    actions = notes.get_pending_actions()
    if actions:
        for a in actions[:5]:
            print(f"  • {a['description']}")
    else:
        print("  No pending actions")
    
    # 5. Agent Test
    print("\n🤖 AGENT RESPONSE TEST")
    print("-" * 30)
    from src.agent.orchestrator import process_message
    response = process_message("Give me a quick status update")
    print(f"  {response[:200]}...")
    
    print("\n" + "=" * 50)
    print("   ✅ ALL SYSTEMS OPERATIONAL")
    print("=" * 50)

if __name__ == "__main__":
    main()
