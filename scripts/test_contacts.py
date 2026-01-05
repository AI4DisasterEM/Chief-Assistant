"""Test Contact Management and Tone Modulation"""
import sys
sys.path.insert(0, '.')

from src.agent.contacts_manager import ContactsManager, seed_steven_contacts, TONE_PROFILES

def main():
    print("CHIEF Contact Management Test")
    print("=" * 40)
    
    # Seed contacts
    print("\n1. Seeding key contacts...")
    seed_steven_contacts()
    
    # Create manager
    cm = ContactsManager()
    
    # List all contacts
    print("\n2. Your contacts:")
    contacts = cm.get_all_contacts()
    for c in contacts:
        print(f"   - {c['name']} ({c['role']}) @ {c['organization']}")
    
    # Get tone guidelines
    print("\n3. Tone guidelines for City Manager:")
    guidelines = cm.get_tone_guidelines("City Manager")
    if guidelines:
        print(f"   Style: {guidelines['style']}")
        print(f"   Guidelines: {guidelines['guidelines']}")
    
    # Log an interaction
    print("\n4. Logging interaction with Union President...")
    result, msg = cm.log_interaction(
        "Union President",
        "meeting",
        "Discussed overtime scheduling concerns. Agreed to review CBA Article 12.",
        "positive"
    )
    print(f"   Logged: {result['type']} on {result['date']}")
    
    # Draft message context
    print("\n5. Getting context for drafting email to City Manager:")
    context = cm.draft_message("City Manager", "CRR Division Budget Request", "email")
    if context:
        print(f"   To: {context['recipient']} ({context['role']})")
        print(f"   Tone: {context['tone_style']}")
        print(f"   Guidelines: {context['guidelines']}")
    
    # Show tone profiles
    print("\n6. Available tone profiles:")
    for key, profile in TONE_PROFILES.items():
        print(f"   - {key}: {profile['description']}")
    
    print("\n✅ Contact Management test complete!")

if __name__ == "__main__":
    main()
