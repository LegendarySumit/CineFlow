"""
SESSION MANAGER - Multi-Turn Conversation State Management

Implements TRUE AGENTIC BEHAVIOR:
- Remembers past decisions
- Maintains schedule state across turns
- Enables reflection and self-correction loops
- Provides proactive next-step suggestions
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class SessionManager:
    """
    Manages conversation state, schedule mutations, and decision history.
    
    Each session is a persistent context where:
    - User can ask follow-up questions
    - Agent remembers past decisions
    - Schedule state is mutated and persisted
    - All decisions are logged
    """
    
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid4())
        self.created_at = datetime.now(timezone.utc)
        self.last_interaction = datetime.now(timezone.utc)
        
        # Event log: Every user input, agent action, tool execution
        self.events = []
        
        # Working state: Active schedule with mutations
        self.state = {
            "active_schedule": None,  # Mutable copy of production schedule
            "approved_swaps": [],      # List of executed decisions
            "pending_swaps": [],       # Unapproved plan drafts
            "actor_availability": {},  # Dynamic actor status
            "location_status": {},     # Real-time location access
            "equipment_status": {}     # Equipment availability
        }
    
    def log_user_input(self, query: str, scene_id: str) -> None:
        """Record user's input to conversation history."""
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "user_input",
            "query": query,
            "scene_id": scene_id
        })
        self.last_interaction = datetime.now(timezone.utc)
    
    def log_agent_action(self, action: str, details: dict[str, Any]) -> None:
        """Record agent's action (plan, execution, validation)."""
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "agent_action",
            "action": action,
            "details": details
        })
    
    def log_tool_execution(self, tool_name: str, input_args: dict, result: dict) -> None:
        """Record tool execution and results."""
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "tool_execution",
            "tool": tool_name,
            "input": input_args,
            "result": result
        })
    
    def get_conversation_context(self) -> dict[str, Any]:
        """
        Generate a summary of past interactions for the agent to read.
        Returns both text summary and structured data.
        """
        
        context_lines = [
            f"Session ID: {self.session_id}",
            f"Total interactions: {len(self.events)}",
            "",
            "CONVERSATION HISTORY:",
        ]
        
        for event in self.events[-10:]:  # Last 10 events for context
            if event["type"] == "user_input":
                context_lines.append(f"  User: {event['query']}")
            elif event["type"] == "agent_action":
                context_lines.append(f"  Agent Action: {event['action']}")
            elif event["type"] == "tool_execution":
                context_lines.append(f"  Tool: {event['tool']}")
        
        context_lines.append("")
        context_lines.append("CURRENT SCHEDULE STATE:")
        if self.state.get("approved_swaps"):
            context_lines.append("  Approved Swaps:")
            for swap in self.state.get("approved_swaps", []):
                context_lines.append(f"    - {swap}")
        
        return {
            "session_id": self.session_id,
            "total_interactions": len(self.events),
            "events": self.events[-10:],  # Last 10 events
            "text_summary": "\n".join(context_lines),
            "approved_swaps": self.state["approved_swaps"]
        }
    
    def apply_schedule_mutation(self, mutation: dict[str, Any]) -> bool:
        """
        Apply a schedule change (scene swap) to the session state.
        
        Returns True if successful, False if violates constraints.
        """
        
        mutation_type = mutation.get("type")
        
        if mutation_type == "swap_scenes":
            source_scene = mutation.get("source_scene")
            target_scene = mutation.get("target_scene")
            
            # Validate the swap doesn't violate constraints
            if not self._validate_swap(source_scene, target_scene):
                return False
            
            # Record the approval
            self.state["approved_swaps"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "swap",
                "source": source_scene,
                "target": target_scene,
                "reason": mutation.get("reason")
            })
            
            # Log the action
            self.log_agent_action("schedule_mutation", {
                "type": "swap",
                "source": source_scene,
                "target": target_scene
            })
            
            return True
        
        return False
    
    def _validate_swap(self, source_scene: str | None, target_scene: str | None) -> bool:
        """
        Check if a scene swap violates union rules, budget constraints, etc.
        
        In production, this would check against live databases.
        """
        if not source_scene or not target_scene:
            return False
        return source_scene != target_scene
    
    def get_proposed_plans(self) -> list[dict[str, Any]]:
        """Return any unapproved plans pending user decision."""
        return self.state.get("pending_swaps", [])
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize session for storage or API response."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_interaction": self.last_interaction.isoformat(),
            "event_count": len(self.events),
            "state": self.state,
            "approved_swaps": self.state["approved_swaps"]
        }


class SessionStore:
    """
    In-memory session storage.
    In production, replace with Redis or database.
    """
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self) -> SessionManager:
        """Create a new session."""
        session = SessionManager()
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> SessionManager | None:
        """Retrieve an existing session."""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def list_sessions(self) -> list[str]:
        """List all active sessions."""
        return list(self.sessions.keys())


# Global session store
session_store = SessionStore()


def get_or_create_session(session_id: str | None = None) -> SessionManager:
    """
    Retrieve an existing session or create a new one.
    Used in FastAPI endpoints.
    """
    if session_id:
        existing_session = session_store.get_session(session_id)
        if existing_session:
            return existing_session
    return session_store.create_session()
