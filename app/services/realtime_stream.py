"""
REALTIME STREAM - WebSocket support for streaming analysis progress.

Sends live updates as agent works:
- "Agent starting analysis..."
- "Gathering external intelligence..."
- "Analyzing cascades..."
- "Computing optimal solutions..."
- "Complete: Recommending SWAP with sc_18"

This gives transparent visibility into agentic thinking.
"""

import json
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any


class StreamMessage:
    """Structured message sent over WebSocket."""
    
    def __init__(self, event_type: str, status: str, message: str, data: dict[str, Any] | None = None):
        self.event_type = event_type  # "ANALYSIS", "CASCADE", "OPTIMIZATION", "COMPLETE", "ERROR"
        self.status = status  # "in_progress", "complete", "warning", "error"
        self.message = message
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.data = data or {}
    
    def to_json(self) -> str:
        """Convert to JSON for WebSocket transmission."""
        return json.dumps({
            "event_type": self.event_type,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data
        })


async def stream_crisis_analysis(
    session_id: str,
    scene_id: str,
    user_query: str
) -> AsyncGenerator[StreamMessage, None]:
    """
    Stream crisis analysis progress in real-time.
    
    Yields progress updates as analysis proceeds.
    """
    
    # Phase 1: Planning
    yield StreamMessage(
        "ANALYSIS",
        "in_progress",
        "📋 Creating execution plan...",
        {"phase": "planning", "step": 1, "total_steps": 5}
    )
    
    # Phase 2: Load schedule
    yield StreamMessage(
        "ANALYSIS",
        "in_progress",
        "📅 Loading production schedule...",
        {"phase": "schedule_loading", "step": 2, "total_steps": 5, "scene_id": scene_id}
    )
    
    # Phase 3: External intelligence
    yield StreamMessage(
        "ANALYSIS",
        "in_progress",
        "🌐 Gathering external intelligence (7 dimensions)...",
        {
            "phase": "external_intelligence",
            "step": 3,
            "total_steps": 5,
            "dimensions": ["WEATHER", "LOCATION_ACCESS", "VENUE_STATUS", "LOCAL_EVENTS", "PUBLIC_ALERTS", "DAMAGE_NEWS", "INFRASTRUCTURE"]
        }
    )
    
    # Phase 4: Cascade detection
    yield StreamMessage(
        "CASCADE",
        "in_progress",
        "⚠️  Analyzing cascading crises...",
        {"phase": "cascade_detection", "step": 4, "total_steps": 5}
    )
    
    # Phase 5: Synthesis
    yield StreamMessage(
        "OPTIMIZATION",
        "in_progress",
        "💡 Synthesizing recommendations...",
        {"phase": "synthesis", "step": 5, "total_steps": 5}
    )
    
    # Completion with summary
    yield StreamMessage(
        "COMPLETE",
        "complete",
        "✅ Analysis complete. Recommendation ready.",
        {
            "phase": "complete",
            "ready_for_approval": True,
            "session_id": session_id
        }
    )


async def stream_cascade_analysis(
    decision_type: str,
    source_scene_id: str,
    target_scene_id: str,
    cascade_count: int = 0
) -> AsyncGenerator[StreamMessage, None]:
    """
    Stream cascade detection progress.
    """
    
    yield StreamMessage(
        "CASCADE",
        "in_progress",
        f"🔍 Checking cascades for {decision_type}: {source_scene_id} → {target_scene_id}...",
        {"source": source_scene_id, "target": target_scene_id}
    )
    
    yield StreamMessage(
        "CASCADE",
        "in_progress",
        "📊 Analyzing cast conflicts...",
        {"check": "cast_conflicts"}
    )
    
    yield StreamMessage(
        "CASCADE",
        "in_progress",
        "🔧 Analyzing equipment dependencies...",
        {"check": "equipment_conflicts"}
    )
    
    yield StreamMessage(
        "CASCADE",
        "in_progress",
        "📍 Analyzing location availability...",
        {"check": "location_conflicts"}
    )
    
    if cascade_count > 0:
        yield StreamMessage(
            "CASCADE",
            "warning",
            f"⚠️  Found {cascade_count} secondary crisis(es). Computing safe alternatives...",
            {"cascades_detected": cascade_count}
        )
    else:
        yield StreamMessage(
            "CASCADE",
            "complete",
            "✅ No cascading crises detected. Safe to execute.",
            {"cascades_detected": 0}
        )


async def stream_optimization(
    source_scene_id: str,
    alternative_count: int = 0
) -> AsyncGenerator[StreamMessage, None]:
    """
    Stream cost optimization progress.
    """
    
    yield StreamMessage(
        "OPTIMIZATION",
        "in_progress",
        f"💰 Analyzing {alternative_count} alternative solutions...",
        {"alternatives": alternative_count}
    )
    
    yield StreamMessage(
        "OPTIMIZATION",
        "in_progress",
        "📈 Computing financial impact for each option...",
        {"metric": "financial"}
    )
    
    yield StreamMessage(
        "OPTIMIZATION",
        "in_progress",
        "⏱️  Calculating setup time requirements...",
        {"metric": "setup_time"}
    )
    
    yield StreamMessage(
        "OPTIMIZATION",
        "in_progress",
        "🎯 Identifying Pareto frontier (optimal solutions)...",
        {"metric": "pareto"}
    )
    
    yield StreamMessage(
        "OPTIMIZATION",
        "complete",
        "✅ Optimization complete. Ready to choose.",
        {"ready": True}
    )


async def stream_decision_execution(
    decision_type: str,
    source_scene_id: str,
    target_scene_id: str
) -> AsyncGenerator[StreamMessage, None]:
    """
    Stream decision execution progress.
    """
    
    yield StreamMessage(
        "EXECUTION",
        "in_progress",
        f"⚙️  Executing {decision_type} decision...",
        {"decision_type": decision_type}
    )
    
    yield StreamMessage(
        "EXECUTION",
        "in_progress",
        "📅 Updating production schedule...",
        {"step": "schedule_update"}
    )
    
    yield StreamMessage(
        "EXECUTION",
        "in_progress",
        "📧 Preparing crew notifications...",
        {"step": "notifications"}
    )
    
    yield StreamMessage(
        "EXECUTION",
        "in_progress",
        "📋 Logging decision to audit trail...",
        {"step": "audit_logging"}
    )
    
    yield StreamMessage(
        "COMPLETE",
        "complete",
        f"✅ Decision executed successfully. {source_scene_id} & {target_scene_id} swapped.",
        {
            "decision_type": decision_type,
            "source": source_scene_id,
            "target": target_scene_id,
            "status": "executed"
        }
    )


def get_progress_percentage(current_step: int, total_steps: int) -> int:
    """Calculate progress percentage."""
    return int((current_step / total_steps) * 100)


async def stream_with_actual_data(
    session_id: str,
    analysis_result: dict[str, Any]
) -> AsyncGenerator[StreamMessage, None]:
    """
    Stream using actual analysis results (for real WebSocket integration).
    """
    
    # Start
    yield StreamMessage(
        "ANALYSIS",
        "in_progress",
        "🚀 Crisis analysis started...",
        {"session_id": session_id, "progress": 0}
    )
    
    # Get actual recommendations
    crisis_type = analysis_result.get("worker_results", {}).get("impact", {}).get("crisis_type", "UNKNOWN")
    recommended_action = analysis_result.get("recommended_action", {}).get("action", "HOLD")
    confidence = analysis_result.get("recommended_action", {}).get("confidence", "MEDIUM")
    
    yield StreamMessage(
        "ANALYSIS",
        "in_progress",
        f"🔍 Detected {crisis_type} crisis",
        {"crisis_type": crisis_type, "progress": 40}
    )
    
    # Check cascades
    cascade_count = len(analysis_result.get("worker_results", {}).get("impact", {}).get("cascades", []))
    if cascade_count > 0:
        yield StreamMessage(
            "CASCADE",
            "warning",
            f"⚠️  Detected {cascade_count} cascading crisis(es)",
            {"cascade_count": cascade_count, "progress": 60}
        )
    
    # Recommendation
    yield StreamMessage(
        "RECOMMENDATION",
        "in_progress",
        f"💡 Recommending: {recommended_action}",
        {
            "action": recommended_action,
            "confidence": confidence,
            "progress": 80
        }
    )
    
    # Complete
    yield StreamMessage(
        "COMPLETE",
        "complete",
        "✅ Analysis complete. Ready for approval.",
        {
            "session_id": session_id,
            "action": recommended_action,
            "progress": 100
        }
    )
