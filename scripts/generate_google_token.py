"""Generate Google OAuth refresh token"""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
import boto3

SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    # Check for credentials file
    creds_file = 'credentials.json'
    if not os.path.exists(creds_file):
        print(f"ERROR: {creds_file} not found!")
        print("Download OAuth credentials from Google Cloud Console")
        return
    
    # Run OAuth flow
    print("Opening browser for Google authorization...")
    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
    credentials = flow.run_local_server(port=8080)
    
    # Read client ID and secret from credentials file
    with open(creds_file, 'r') as f:
        client_config = json.load(f)
    
    installed = client_config.get('installed', client_config.get('web', {}))
    client_id = installed['client_id']
    client_secret = installed['client_secret']
    
    # Prepare secret value
    secret_value = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': credentials.refresh_token,
        'access_token': credentials.token
    }
    
    print("\n✅ Authorization successful!\n")
    print("Refresh Token:", credentials.refresh_token[:50] + "...")
    
    # Update AWS Secrets Manager
    update = input("\nUpdate AWS Secrets Manager? (yes/no): ").strip().lower()
    if update == 'yes':
        secrets = boto3.client('secretsmanager', region_name='us-east-1')
        secrets.update_secret(
            SecretId='chief/google-oauth',
            SecretString=json.dumps(secret_value)
        )
        print("✅ Secret updated in AWS!")
    else:
        print("\nManual update - save this JSON:")
        print(json.dumps(secret_value, indent=2))
    
    print("\n🎉 Google Calendar is now connected!")

if __name__ == "__main__":
    main()
