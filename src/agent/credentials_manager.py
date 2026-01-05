"""Professional Development & Credentials Manager for CHIEF"""
import json
import boto3
from datetime import datetime, timedelta


def get_dynamodb():
    return boto3.resource('dynamodb', region_name='us-east-1')


class CredentialsManager:
    def __init__(self, user_id="steven"):
        self.user_id = user_id
        self.dynamodb = get_dynamodb()
        self.table = self.dynamodb.Table('chief_credentials')
    
    def add_credential(self, name, credential_type, status="active", 
                       expiration_date=None, ceu_required=0, ceu_earned=0,
                       issuing_body=None, credential_id=None):
        self.table.put_item(Item={
            'PK': f'USER#{self.user_id}',
            'SK': f'CRED#{name.upper().replace(" ", "_")}',
            'GSI1PK': f'TYPE#{credential_type}',
            'GSI1SK': f'EXP#{expiration_date or "none"}',
            'name': name,
            'credential_type': credential_type,
            'status': status,
            'expiration_date': expiration_date,
            'ceu_required': ceu_required,
            'ceu_earned': ceu_earned,
            'issuing_body': issuing_body,
            'credential_id': credential_id,
            'updated_at': datetime.utcnow().isoformat()
        })
        return f"Added: {name}"
    
    def update_ceu(self, credential_name, ceu_to_add, description=None):
        key = {
            'PK': f'USER#{self.user_id}',
            'SK': f'CRED#{credential_name.upper().replace(" ", "_")}'
        }
        response = self.table.get_item(Key=key)
        if 'Item' not in response:
            return None, "Credential not found"
        
        current = response['Item']
        new_total = int(current.get('ceu_earned', 0)) + ceu_to_add
        
        self.table.update_item(
            Key=key,
            UpdateExpression='SET ceu_earned = :ceu, updated_at = :ts',
            ExpressionAttributeValues={
                ':ceu': new_total,
                ':ts': datetime.utcnow().isoformat()
            }
        )
        
        required = int(current.get('ceu_required', 0))
        remaining = max(0, required - new_total)
        
        return {
            'credential': credential_name,
            'ceu_earned': new_total,
            'ceu_required': required,
            'remaining': remaining,
            'complete': new_total >= required
        }, "CEUs updated"
    
    def get_credential(self, credential_name):
        response = self.table.get_item(Key={
            'PK': f'USER#{self.user_id}',
            'SK': f'CRED#{credential_name.upper().replace(" ", "_")}'
        })
        return response.get('Item')
    
    def get_all_credentials(self):
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'USER#{self.user_id}',
                ':sk': 'CRED#'
            }
        )
        return response.get('Items', [])
    
    def get_expiring_soon(self, days=90):
        credentials = self.get_all_credentials()
        expiring = []
        today = datetime.utcnow().date()
        threshold = today + timedelta(days=days)
        
        for cred in credentials:
            exp_date = cred.get('expiration_date')
            if exp_date and exp_date != 'none':
                try:
                    exp = datetime.fromisoformat(exp_date).date()
                    if exp <= threshold:
                        days_left = (exp - today).days
                        cred['days_until_expiration'] = days_left
                        expiring.append(cred)
                except:
                    pass
        
        return sorted(expiring, key=lambda x: x.get('days_until_expiration', 999))
    
    def get_ceu_status(self):
        credentials = self.get_all_credentials()
        ceu_status = []
        
        for cred in credentials:
            required = int(cred.get('ceu_required', 0))
            if required > 0:
                earned = int(cred.get('ceu_earned', 0))
                ceu_status.append({
                    'name': cred['name'],
                    'earned': earned,
                    'required': required,
                    'remaining': max(0, required - earned),
                    'percent': min(100, int((earned / required) * 100))
                })
        
        return ceu_status
    
    def add_milestone(self, credential_name, milestone, date_achieved=None):
        key = {
            'PK': f'USER#{self.user_id}',
            'SK': f'CRED#{credential_name.upper().replace(" ", "_")}'
        }
        response = self.table.get_item(Key=key)
        if 'Item' not in response:
            return None, "Credential not found"
        
        current = response['Item']
        milestones = current.get('milestones', [])
        milestones.append({
            'description': milestone,
            'date': date_achieved or datetime.utcnow().isoformat()[:10]
        })
        
        self.table.update_item(
            Key=key,
            UpdateExpression='SET milestones = :m, updated_at = :ts',
            ExpressionAttributeValues={
                ':m': milestones,
                ':ts': datetime.utcnow().isoformat()
            }
        )
        return milestones, "Milestone added"
    
    def format_status_report(self):
        credentials = self.get_all_credentials()
        active = len([c for c in credentials if c.get('status') == 'active'])
        in_progress = len([c for c in credentials if c.get('status') == 'in_progress'])
        
        lines = [
            "PROFESSIONAL DEVELOPMENT STATUS",
            "=" * 35,
            f"Active Credentials: {active}",
            f"In Progress: {in_progress}",
            "",
            "CEU PROGRESS:"
        ]
        
        for ceu in self.get_ceu_status():
            bar = "#" * (ceu['percent'] // 10) + "-" * (10 - ceu['percent'] // 10)
            lines.append(f"  {ceu['name']}: [{bar}] {ceu['earned']}/{ceu['required']}")
        
        expiring = self.get_expiring_soon(90)
        if expiring:
            lines.append("")
            lines.append("EXPIRING SOON:")
            for cred in expiring[:3]:
                lines.append(f"  - {cred['name']}: {cred['days_until_expiration']} days")
        
        return '\n'.join(lines)


def seed_steven_credentials():
    cm = CredentialsManager()
    
    cm.add_credential(
        name="Executive Fire Officer",
        credential_type="certification",
        status="in_progress",
        issuing_body="National Fire Academy"
    )
    cm.add_milestone("Executive Fire Officer", "EFO I - Complete", "2024-06-15")
    
    cm.add_credential(
        name="EMT-P",
        credential_type="license",
        status="active",
        expiration_date="2026-03-31",
        ceu_required=40,
        ceu_earned=28,
        issuing_body="Florida DOH"
    )
