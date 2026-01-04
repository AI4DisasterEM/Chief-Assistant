"""Main orchestrator agent for CHIEF"""
import json
import boto3
from datetime import datetime
from anthropic import Anthropic
from typing import Optional

from .state import AgentState, detect_workspace, get_priority_for_workspace, NoteSession


def get_anthropic_client():
    """Get Anthropic client with API key from Secrets Manager"""
    secrets = boto3.client('secretsmanager', region_name='us-east-1')
    response = secrets.get_secret_value(SecretId='chief/anthropic-api-key')
    secret = json.loads(response['SecretString'])
    return Anthropic(api_key=secret['api_key'])


SYSTEM_PROMPT = """You are CHIEF (Contextual Helper for Integrated Executive Functions), a personal executive assistant for a Fire Rescue Chief Officer.

Your user is Steven, Chief of Community Risk Reduction at Sunrise Fire-Rescue in South Florida. He has 17+ years of emergency services experience, holds an MBA, is pursuing an MS in Disaster & Emergency Management, and is applying to PhD programs. His career goal is to become a fire chief within 3-5 years.

## Your Capabilities:
- Calendar management (view, create, modify events)
- Note-taking with action item extraction
- Morning briefings and EOD summaries
- Professional development tracking (EFO, certifications, CEUs)
- Wellness monitoring integration

## Workspace Context:
You operate across five domains:
1. COMMAND - City manager, council, union, strategic policy
2. OPERATIONS - Sunrise Fire-Rescue daily operations, CRR, MIH
3. PLANNING - Academic work, EFO, PhD, research
4. LOGISTICS - Conference planning, vendors, procurement
5. PERSONAL - Family, personal appointments

## Communication Style:
- Be concise and direct (SMS-friendly responses)
- Use professional but warm tone
- Always cite sources when referencing policies or documents
- Proactively surface conflicts and anomalies

## Current Context:
Workspace: {workspace}
Time: {current_time}
Active Note Session: {note_session}

Respond helpfully to the user's request."""


class ChiefOrchestrator:
    def __init__(self):
        self.client = get_anthropic_client()
        self.state: Optional[AgentState] = None
    
    def initialize_state(self, user_input: str) -> AgentState:
        """Initialize agent state from user input"""
        workspace = detect_workspace(user_input)
        
        return AgentState(
            user_input=user_input,
            intent="",
            workspace=workspace,
            priority_level=get_priority_for_workspace(workspace),
            requires_approval=False,
            context=[],
            actions_taken=[],
            pending_notifications=[],
            active_note_session=None,
            response="",
            messages=[]
        )
    
    def classify_intent(self, user_input: str) -> str:
        """Classify the user's intent"""
        input_lower = user_input.lower()
        
        # Calendar intents
        if any(word in input_lower for word in ["calendar", "schedule", "meeting", "event", "free", "busy", "block"]):
            if any(word in input_lower for word in ["what", "show", "today", "tomorrow", "week"]):
                return "calendar_query"
            elif any(word in input_lower for word in ["schedule", "create", "add", "block"]):
                return "calendar_create"
            elif any(word in input_lower for word in ["move", "reschedule", "cancel"]):
                return "calendar_modify"
        
        # Note intents
        if any(word in input_lower for word in ["note", "taking notes", "remember", "action item"]):
            if any(word in input_lower for word in ["start", "taking", "begin"]):
                return "note_start"
            elif any(word in input_lower for word in ["done", "end", "stop", "finish"]):
                return "note_end"
            else:
                return "note_add"
        
        # Briefing intents
        if any(word in input_lower for word in ["brief", "summary", "status", "update"]):
            return "briefing"
        
        # Default to conversation
        return "conversation"
    
    def process(self, user_input: str, conversation_history: list = None) -> str:
        """Process user input and return response"""
        self.state = self.initialize_state(user_input)
        self.state["intent"] = self.classify_intent(user_input)
        
        # Build messages
        messages = conversation_history or []
        messages.append({"role": "user", "content": user_input})
        
        # Format system prompt with context
        system = SYSTEM_PROMPT.format(
            workspace=self.state["workspace"].upper(),
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            note_session="None active"
        )
        
        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system,
            messages=messages
        )
        
        assistant_message = response.content[0].text
        self.state["response"] = assistant_message
        
        return assistant_message


def process_message(user_input: str, conversation_history: list = None) -> str:
    """Main entry point for processing messages"""
    orchestrator = ChiefOrchestrator()
    return orchestrator.process(user_input, conversation_history)
