"""Test Professional Development tracking"""
import sys
sys.path.insert(0, '.')

from src.agent.credentials_manager import CredentialsManager, seed_steven_credentials

def main():
    print("CHIEF Professional Development Test")
    print("=" * 40)
    
    # Seed credentials
    print("\n1. Seeding your credentials...")
    seed_steven_credentials()
    
    # Create manager
    cm = CredentialsManager()
    
    # Get status report
    print("\n2. Status Report:")
    print(cm.format_status_report())
    
    # Add some CEUs
    print("\n3. Adding 4 CEUs to EMT-P...")
    result, msg = cm.update_ceu("EMT-P", 4, "ACLS Refresher")
    if result:
        print(f"   Now: {result['ceu_earned']}/{result['ceu_required']} ({result['remaining']} remaining)")
    
    # Check expiring
    print("\n4. Credentials expiring in 90 days:")
    expiring = cm.get_expiring_soon(90)
    if expiring:
        for cred in expiring:
            print(f"   - {cred['name']}: {cred['days_until_expiration']} days left")
    else:
        print("   None expiring soon!")
    
    # Final summary
    print("\n5. Updated Status Report:")
    print(cm.format_status_report())
    
    print("\n✅ Professional Development tracking complete!")

if __name__ == "__main__":
    main()
