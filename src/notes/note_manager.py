"""Note-taking and action item extraction for CHIEF"""
import json
import boto3
import uuid
from datetime import datetime
from anthropic import Anthropic


def get_secret(secret_id):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_id)
    return json.loads(response['SecretString'])


def get_dynamodb():
    return boto3.resource('dynamodb', region_name='us-east-1')


class NoteSession:
    def __init__(self, user_id="steven"):
        self.user_id = user_id
        self.dynamodb = get_dynamodb()
        self.sessions_table = self.dynamodb.Table('chief_note_sessions')
        self.actions_table = self.dynamodb.Table('chief_action_items')
    
    def start_session(self, title, workspace="operations"):
        """Start a new note-taking session"""
        session_id = str(uuid.uuid4())[:8]
        
        self.sessions_table.put_item(Item={
            'PK': f'SESSION#{session_id}',
            'SK': 'META',
            'user_id': self.user_id,
            'title': title,
            'workspace': workspace,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'active',
            'entries': []
        })
        
        return session_id
    
    def add_entry(self, session_id, content, input_type="text"):
        """Add an entry to an active session"""
        timestamp = datetime.utcnow().isoformat()
        
        # Get current session
        response = self.sessions_table.get_item(
            Key={'PK': f'SESSION#{session_id}', 'SK': 'META'}
        )
        
        if 'Item' not in response:
            return None, "Session not found"
        
        session = response['Item']
        entries = session.get('entries', [])
        
        # Add new entry
        entry = {
            'timestamp': timestamp,
            'content': content,
            'input_type': input_type
        }
        entries.append(entry)
        
        # Extract action items
        actions = self.extract_actions(content, session['workspace'])
        
        # Update session
        self.sessions_table.update_item(
            Key={'PK': f'SESSION#{session_id}', 'SK': 'META'},
            UpdateExpression='SET entries = :e',
            ExpressionAttributeValues={':e': entries}
        )
        
        return actions, "Entry added"
    
    def extract_actions(self, content, workspace):
        """Use Claude to extract action items from note content"""
        try:
            creds = get_secret('chief/anthropic-api-key')
            client = Anthropic(api_key=creds['api_key'])
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system="""Extract action items from the note. Return JSON array:
[{"description": "task", "assignee": "name or null", "due_date": "date or null", "priority": "high/medium/low"}]
If no actions found, return empty array: []
Only return valid JSON, nothing else.""",
                messages=[{"role": "user", "content": content}]
            )
            
            result = response.content[0].text.strip()
            actions = json.loads(result)
            
            # Save action items
            for action in actions:
                self.save_action(action, workspace)
            
            return actions
        except:
            return []
    
    def save_action(self, action, workspace):
        """Save an action item to DynamoDB"""
        item_id = str(uuid.uuid4())[:8]
        
        self.actions_table.put_item(Item={
            'PK': f'ACTION#{item_id}',
            'SK': f'USER#{self.user_id}',
            'GSI1PK': 'STATUS#pending',
            'GSI1SK': f'DUE#{action.get("due_date", "none")}',
            'description': action['description'],
            'assignee': action.get('assignee'),
            'due_date': action.get('due_date'),
            'priority': action.get('priority', 'medium'),
            'status': 'pending',
            'workspace': workspace,
            'created_at': datetime.utcnow().isoformat()
        })
    
    def end_session(self, session_id):
        """End a note session and generate summary"""
        response = self.sessions_table.get_item(
            Key={'PK': f'SESSION#{session_id}', 'SK': 'META'}
        )
        
        if 'Item' not in response:
            return None, "Session not found"
        
        session = response['Item']
        
        # Generate summary
        all_content = '\n'.join([e['content'] for e in session.get('entries', [])])
        summary = self.generate_summary(all_content)
        
        # Update session
        self.sessions_table.update_item(
            Key={'PK': f'SESSION#{session_id}', 'SK': 'META'},
            UpdateExpression='SET #s = :s, ended_at = :e, summary = :sum',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'closed',
                ':e': datetime.utcnow().isoformat(),
                ':sum': summary
            }
        )
        
        return summary, "Session closed"
    
    def generate_summary(self, content):
        """Generate a summary of the note session"""
        try:
            creds = get_secret('chief/anthropic-api-key')
            client = Anthropic(api_key=creds['api_key'])
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                system="Summarize these notes in 2-3 bullet points. Be concise.",
                messages=[{"role": "user", "content": content}]
            )
            
            return response.content[0].text
        except:
            return "Summary unavailable"
    
    def get_pending_actions(self):
        """Get all pending action items"""
        response = self.actions_table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :status',
            ExpressionAttributeValues={':status': 'STATUS#pending'}
        )
        return response.get('Items', [])
