"""Test note-taking functionality"""
import sys
sys.path.insert(0, '.')

from src.notes.note_manager import NoteSession

def main():
    print("CHIEF Note-Taking Test")
    print("=" * 40)
    
    notes = NoteSession()
    
    # Start a session
    print("\n1. Starting note session...")
    session_id = notes.start_session("Test Meeting", workspace="operations")
    print(f"   Session ID: {session_id}")
    
    # Add entries
    print("\n2. Adding note entries...")
    
    entry1 = "Discussed the new Everbridge rollout. John will send the contract by Friday."
    actions1, msg = notes.add_entry(session_id, entry1)
    print(f"   Entry 1 added. Actions found: {len(actions1)}")
    for a in actions1:
        print(f"   - {a['description']}")
    
    entry2 = "Training scheduled for Jan 15. Need 20 seats reserved. Maria to confirm attendees by Monday."
    actions2, msg = notes.add_entry(session_id, entry2)
    print(f"   Entry 2 added. Actions found: {len(actions2)}")
    for a in actions2:
        print(f"   - {a['description']}")
    
    # End session
    print("\n3. Ending session...")
    summary, msg = notes.end_session(session_id)
    print(f"   Summary:\n{summary}")
    
    # Get pending actions
    print("\n4. All pending actions:")
    pending = notes.get_pending_actions()
    for action in pending:
        print(f"   - {action['description']} (Due: {action.get('due_date', 'None')})")
    
    print("\n✅ Note-taking test complete!")

if __name__ == "__main__":
    main()
