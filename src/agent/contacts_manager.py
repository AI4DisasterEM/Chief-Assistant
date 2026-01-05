"""Contact & Relationship Manager for CHIEF"""
import json
import boto3
from datetime import datetime


def get_dynamodb():
    return boto3.resource('dynamodb', region_name='us-east-1')


# Communication style profiles
TONE_PROFILES = {
    "formal_analytical": {
        "description": "City Manager, Council - Data-driven, formal",
        "guidelines": "Use data and metrics. Formal tone. Lead with ROI/impact. Avoid jargon."
    },
    "professional_collaborative": {
        "description": "Union, Labor relations - Respectful, partnership-focused",
        "guidelines": "Acknowledge concerns. Reference CBA when relevant. Collaborative language."
    },
    "direct_supportive": {
        "description": "Staff, Direct reports - Clear, encouraging",
        "guidelines": "Be direct but supportive. Provide clear expectations. Recognize efforts."
    },
    "professional_diplomatic": {
        "description": "External partners, Other agencies - Professional, bridge-building",
        "guidelines": "Professional courtesy. Find common ground. Represent department well."
    },
    "formal_controlled": {
        "description": "Media, Public communications - Careful, on-message",
        "guidelines": "Stay on message. No speculation. Refer complex questions to PIO."
    }
}


class ContactsManager:
    def __init__(self, user_id="steven"):
        self.user_id = user_id
        self.dynamodb = get_dynamodb()
        self.table = self.dynamodb.Table('chief_contacts')
    
    def add_contact(self, name, role, organization, 
                    communication_style="professional_diplomatic",
                    email=None, phone=None, notes=None):
        """Add or update a contact"""
        
        self.table.put_item(Item={
            'PK': f'USER#{self.user_id}',
            'SK': f'CONTACT#{name.upper().replace(" ", "_")}',
            'name': name,
            'role': role,
            'organization': organization,
            'communication_style': communication_style,
            'email': email,
            'phone': phone,
            'notes': notes,
            'interactions': [],
            'updated_at': datetime.utcnow().isoformat()
        })
        
        return f"Added contact: {name}"
    
    def log_interaction(self, contact_name, interaction_type, summary, sentiment=None):
        """Log an interaction with a contact"""
        key = {
            'PK': f'USER#{self.user_id}',
            'SK': f'CONTACT#{contact_name.upper().replace(" ", "_")}'
        }
        
        response = self.table.get_item(Key=key)
        if 'Item' not in response:
            return None, "Contact not found"
        
        contact = response['Item']
        interactions = contact.get('interactions', [])
        
        interactions.append({
            'date': datetime.utcnow().isoformat()[:10],
            'type': interaction_type,  # meeting, email, call, text
            'summary': summary,
            'sentiment': sentiment  # positive, neutral, negative
        })
        
        # Keep last 10 interactions
        interactions = interactions[-10:]
        
        self.table.update_item(
            Key=key,
            UpdateExpression='SET interactions = :i, last_interaction = :l, updated_at = :ts',
            ExpressionAttributeValues={
                ':i': interactions,
                ':l': datetime.utcnow().isoformat()[:10],
                ':ts': datetime.utcnow().isoformat()
            }
        )
        
        return interactions[-1], "Interaction logged"
    
    def get_contact(self, contact_name):
        """Get a specific contact"""
        response = self.table.get_item(Key={
            'PK': f'USER#{self.user_id}',
            'SK': f'CONTACT#{contact_name.upper().replace(" ", "_")}'
        })
        return response.get('Item')
    
    def get_all_contacts(self):
        """Get all contacts"""
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'USER#{self.user_id}',
                ':sk': 'CONTACT#'
            }
        )
        return response.get('Items', [])
    
    def get_tone_guidelines(self, contact_name):
        """Get communication guidelines for a contact"""
        contact = self.get_contact(contact_name)
        if not contact:
            return None
        
        style = contact.get('communication_style', 'professional_diplomatic')
        profile = TONE_PROFILES.get(style, TONE_PROFILES['professional_diplomatic'])
        
        return {
            'contact': contact['name'],
            'role': contact.get('role'),
            'style': style,
            'guidelines': profile['guidelines'],
            'recent_interactions': contact.get('interactions', [])[-3:]
        }
    
    def draft_message(self, contact_name, topic, message_type="email"):
        """Get context for drafting a message to a contact"""
        contact = self.get_contact(contact_name)
        if not contact:
            return None
        
        style = contact.get('communication_style', 'professional_diplomatic')
        profile = TONE_PROFILES.get(style, TONE_PROFILES['professional_diplomatic'])
        
        context = {
            'recipient': contact['name'],
            'role': contact.get('role'),
            'organization': contact.get('organization'),
            'tone_style': style,
            'guidelines': profile['guidelines'],
            'topic': topic,
            'message_type': message_type,
            'notes': contact.get('notes'),
            'recent_interactions': contact.get('interactions', [])[-3:]
        }
        
        return context
    
    def search_contacts(self, query):
        """Search contacts by name or organization"""
        contacts = self.get_all_contacts()
        query_lower = query.lower()
        
        matches = []
        for contact in contacts:
            if (query_lower in contact.get('name', '').lower() or
                query_lower in contact.get('organization', '').lower() or
                query_lower in contact.get('role', '').lower()):
                matches.append(contact)
        
        return matches


def seed_steven_contacts():
    """Seed Steven's key contacts"""
    cm = ContactsManager()
    
    # City Leadership
    cm.add_contact(
        name="City Manager",
        role="City Manager",
        organization="City of Sunrise",
        communication_style="formal_analytical",
        notes="Prefers data-driven presentations. Focus on ROI and community impact."
    )
    
    cm.add_contact(
        name="Fire Chief",
        role="Fire Chief",
        organization="Sunrise Fire-Rescue",
        communication_style="direct_supportive",
        notes="Direct report. Weekly 1:1s on Mondays."
    )
    
    # Union
    cm.add_contact(
        name="Union President",
        role="IAFF Local President",
        organization="IAFF Local 2928",
        communication_style="professional_collaborative",
        notes="Good working relationship. Reference CBA Article 12 for scheduling issues."
    )
    
    # External
    cm.add_contact(
        name="Broward EOC Director",
        role="Emergency Management Director",
        organization="Broward County EOC",
        communication_style="professional_diplomatic",
        notes="Key partner for mutual aid and hurricane response."
    )
    
    # Academic
    cm.add_contact(
        name="UCF Advisor",
        role="PhD Program Advisor",
        organization="UCF",
        communication_style="professional_diplomatic",
        notes="Dissertation committee. Research focus on emergency management."
    )
    
    # Conference
    cm.add_contact(
        name="FTFC Chair",
        role="Conference Chair",
        organization="First There First Care",
        communication_style="professional_collaborative",
        notes="2026 conference planning. Monthly planning calls."
    )
    
    print("Contacts seeded!")
    return cm
