"""AWS Lambda handler for CHIEF Assistant"""
import json
import boto3
import urllib.parse
from src.agent.orchestrator import process_message


def get_twilio_client():
    """Get Twilio credentials from Secrets Manager"""
    secrets = boto3.client('secretsmanager', region_name='us-east-1')
    response = secrets.get_secret_value(SecretId='chief/twilio-credentials')
    return json.loads(response['SecretString'])


def send_sms(to_number: str, message: str):
    """Send SMS via Twilio"""
    from twilio.rest import Client
    
    creds = get_twilio_client()
    client = Client(creds['account_sid'], creds['auth_token'])
    
    client.messages.create(
        body=message,
        from_=creds['phone_number'],
        to=to_number
    )


def handle_incoming_sms(event, context):
    """Handle incoming SMS from Twilio webhook"""
    # Parse Twilio webhook body
    body = event.get('body', '')
    if event.get('isBase64Encoded'):
        import base64
        body = base64.b64decode(body).decode('utf-8')
    
    params = urllib.parse.parse_qs(body)
    
    from_number = params.get('From', [''])[0]
    message_body = params.get('Body', [''])[0]
    
    if not message_body:
        return {
            'statusCode': 400,
            'body': 'No message body'
        }
    
    # Process the message
    response_text = process_message(message_body)
    
    # Send response back via SMS
    send_sms(from_number, response_text)
    
    # Return TwiML response
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/xml'},
        'body': '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    }


def handle_scheduled_briefing(event, context):
    """Handle scheduled morning/EOD briefings"""
    from src.calendar.google_calendar import get_todays_events, format_events_for_display
    
    briefing_type = event.get('briefing_type', 'morning')
    
    # Get today's events
    events = get_todays_events()
    events_text = format_events_for_display(events)
    
    if briefing_type == 'morning':
        message = f"""Good morning, Chief.

📅 TODAY'S CALENDAR:
{events_text}

Reply with any questions or 'note' to start taking notes."""
    else:
        message = f"""EOD Summary

📅 TOMORROW'S PREVIEW:
{events_text}

Anything else to capture before end of day?"""
    
    # Get user phone number from environment or secrets
    creds = get_twilio_client()
    user_phone = creds.get('user_phone_number', '')
    
    if user_phone:
        send_sms(user_phone, message)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Briefing sent'})
    }


def lambda_handler(event, context):
    """Main Lambda entry point - routes to appropriate handler"""
    
    # Check if this is a scheduled event
    if event.get('source') == 'aws.events':
        return handle_scheduled_briefing(event, context)
    
    # Check if this is an API Gateway event (SMS webhook)
    if event.get('httpMethod') == 'POST':
        return handle_incoming_sms(event, context)
    
    return {
        'statusCode': 400,
        'body': json.dumps({'error': 'Unknown event type'})
    }
