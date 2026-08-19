"""
Real-time progress streamer for WebSocket clients.
Emits worker execution updates as they happen.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EventType(str, Enum):
    """Event types for WebSocket streaming."""
    PHASE_START = "phase_start"
    PHASE_PROGRESS = "phase_progress"
    WORKER_START = "worker_start"
    WORKER_RESULT = "worker_result"
    SYNTHESIS = "synthesis"
    RESPONSE = "response"
    ERROR = "error"
    COMPLETE = "complete"


class StreamMessage:
    """Structured message for WebSocket streaming."""
    
    def __init__(
        self,
        event_type: EventType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        phase: Optional[int] = None,
        worker_name: Optional[str] = None,
        duration_ms: Optional[int] = None,
        severity: str = "info"
    ):
        self.event_type = event_type
        self.title = title
        self.message = message
        self.data = data or {}
        self.phase = phase
        self.worker_name = worker_name
        self.duration_ms = duration_ms
        self.severity = severity
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "phase": self.phase,
            "worker_name": self.worker_name,
            "duration_ms": self.duration_ms,
            "severity": self.severity,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class ProgressStreamer:
    """Manages progress streaming for a single crisis analysis session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: list[StreamMessage] = []
        self.current_phase = 0
    
    def emit_phase_start(self, phase_num: int, phase_name: str, description: str) -> StreamMessage:
        """Emit when a new analysis phase begins."""
        msg = StreamMessage(
            event_type=EventType.PHASE_START,
            title=f"Phase {phase_num}: {phase_name}",
            message=description,
            phase=phase_num,
            severity="info"
        )
        self.messages.append(msg)
        self.current_phase = phase_num
        return msg
    
    def emit_phase_progress(self, status: str, details: str, data: Optional[Dict] = None) -> StreamMessage:
        """Emit progress update within current phase."""
        msg = StreamMessage(
            event_type=EventType.PHASE_PROGRESS,
            title="Analyzing...",
            message=f"{status}: {details}",
            phase=self.current_phase,
            data=data or {},
            severity="info"
        )
        self.messages.append(msg)
        return msg
    
    def emit_worker_start(self, worker_name: str, description: str) -> StreamMessage:
        """Emit when a worker begins execution."""
        msg = StreamMessage(
            event_type=EventType.WORKER_START,
            title=f"Executing {worker_name}",
            message=description,
            worker_name=worker_name,
            phase=self.current_phase,
            severity="info"
        )
        self.messages.append(msg)
        return msg
    
    def emit_worker_result(
        self,
        worker_name: str,
        result: str,
        data: Dict[str, Any],
        duration_ms: int = 0
    ) -> StreamMessage:
        """Emit when a worker completes execution."""
        msg = StreamMessage(
            event_type=EventType.WORKER_RESULT,
            title=f"✓ {worker_name} Complete",
            message=result,
            worker_name=worker_name,
            data=data,
            duration_ms=duration_ms,
            phase=self.current_phase,
            severity="success"
        )
        self.messages.append(msg)
        return msg
    
    def emit_synthesis(self, title: str, summary: str, data: Dict[str, Any]) -> StreamMessage:
        """Emit during response synthesis phase."""
        msg = StreamMessage(
            event_type=EventType.SYNTHESIS,
            title=title,
            message=summary,
            data=data,
            phase=4,
            severity="info"
        )
        self.messages.append(msg)
        return msg
    
    def emit_response(
        self,
        title: str,
        narrative: str,
        financial_metrics: Dict[str, Any],
        alternatives: list[Dict[str, Any]],
        recommendations: list[str]
    ) -> StreamMessage:
        """Emit final formatted response."""
        msg = StreamMessage(
            event_type=EventType.RESPONSE,
            title=title,
            message=narrative,
            data={
                "financial_metrics": financial_metrics,
                "alternatives": alternatives,
                "recommendations": recommendations
            },
            severity="success"
        )
        self.messages.append(msg)
        return msg
    
    def emit_error(self, title: str, error_message: str, recovery_suggestion: Optional[str] = None) -> StreamMessage:
        """Emit error message with optional recovery suggestion."""
        data = {}
        if recovery_suggestion:
            data["recovery_suggestion"] = recovery_suggestion
        
        msg = StreamMessage(
            event_type=EventType.ERROR,
            title=title,
            message=error_message,
            data=data,
            severity="error"
        )
        self.messages.append(msg)
        return msg
    
    def emit_complete(self, summary: str) -> StreamMessage:
        """Emit analysis complete signal."""
        msg = StreamMessage(
            event_type=EventType.COMPLETE,
            title="Analysis Complete",
            message=summary,
            severity="success"
        )
        self.messages.append(msg)
        return msg
    
    def get_all_messages(self) -> list[StreamMessage]:
        """Get all messages emitted so far."""
        return self.messages
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []


# Global streamer instance (could be replaced with Redis for distributed systems)
_streamers: Dict[str, ProgressStreamer] = {}


def get_or_create_streamer(session_id: str) -> ProgressStreamer:
    """Get or create a progress streamer for a session."""
    if session_id not in _streamers:
        _streamers[session_id] = ProgressStreamer(session_id)
    return _streamers[session_id]


def clear_streamer(session_id: str) -> None:
    """Clear a streamer after session complete."""
    if session_id in _streamers:
        del _streamers[session_id]
