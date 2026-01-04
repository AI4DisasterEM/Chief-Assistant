"""State management for CHIEF Agent"""
from typing import TypedDict, Optional, List, Annotated
from datetime import datetime


class ActionItem(TypedDict):
    item_id: str
    description: str
    assignee: Optional[str]
    due_date: Optional[str]
    priority: str
    status: str
    workspace: str
    source_session: Optional[str]


class NoteSession(TypedDict):
    session_id: str
    workspace: str
    title: str
    started_at: str
    entries: List[str]
    action_items: List[ActionItem]


class AgentState(TypedDict):
    """Main state for the CHIEF agent"""
    user_input: str
    intent: str
    workspace: str  # command | operations | planning | logistics | personal
    priority_level: int  # 1-5 (family=1, phd=2, sunrise=3, conference=4, other=5)
    requires_approval: bool
    context: List[str]
    actions_taken: List[str]
    pending_notifications: List[str]
    active_note_session: Optional[NoteSession]
    response: str
    messages: List[dict]


# Workspace detection keywords
WORKSPACE_RULES = {
    "command": {
        "keywords": ["city manager", "council", "union", "cba", "policy", "strategic", "budget approval", "commission"],
        "priority": 1
    },
    "operations": {
        "keywords": ["sunrise", "station", "crr", "mih", "everbridge", "shift", "response", "apparatus", "overtime"],
        "priority": 2
    },
    "planning": {
        "keywords": ["efo", "phd", "dissertation", "paper", "class", "ucf", "nfa", "leadership broward", "research"],
        "priority": 3
    },
    "logistics": {
        "keywords": ["conference", "ftfc", "eagles", "speakers", "sponsors", "vendor", "procurement"],
        "priority": 4
    },
    "personal": {
        "keywords": ["family", "kids", "home", "personal", "vacation", "appointment"],
        "priority": 5
    }
}


def detect_workspace(text: str) -> str:
    """Detect workspace from text content"""
    text_lower = text.lower()
    
    matches = []
    for workspace, rules in WORKSPACE_RULES.items():
        for keyword in rules["keywords"]:
            if keyword in text_lower:
                matches.append((workspace, rules["priority"]))
                break
    
    if matches:
        # Return highest priority (lowest number) workspace
        matches.sort(key=lambda x: x[1])
        return matches[0][0]
    
    return "operations"  # Default workspace


def get_priority_for_workspace(workspace: str) -> int:
    """Get priority level for a workspace"""
    return WORKSPACE_RULES.get(workspace, {}).get("priority", 5)
