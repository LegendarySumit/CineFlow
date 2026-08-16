"""
AUDIT LOGGER - Tracks all production decisions with full context.

Logs:
- Decision metadata (who, when, what, why)
- Agent analysis (reasoning, confidence)
- Cascades detected
- Approval details
- Execution results
- Outcomes

Purpose:
- Compliance/Legal: Prove decisions were made with due diligence
- Learning: Understand which strategies work
- Analytics: Identify patterns in production crises
- Debugging: Trace issues back to decisions
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_DIR = Path("audit_logs")
AUDIT_LOG_DIR.mkdir(exist_ok=True)


def log_crisis_analysis(
    session_id: str,
    scene_id: str,
    user_query: str,
    analysis_result: dict[str, Any]
) -> str:
    """
    Log crisis analysis event with full context.
    
    Returns: audit_id for reference
    """
    
    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "_")
    audit_id = f"analysis_{session_id}_{timestamp}"
    now = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "audit_id": audit_id,
        "event_type": "CRISIS_ANALYSIS",
        "timestamp": now,
        "session_id": session_id,
        "scene_id": scene_id,
        "user_query": user_query,
        "agent_result": {
            "status": analysis_result.get("status"),
            "risk_level": analysis_result.get("risk_level"),
            "confidence": analysis_result.get("confidence"),
            "recommended_action": analysis_result.get("recommended_action"),
            "evidence_count": analysis_result.get("evidence_count", 0)
        },
        "reasoning_trail": analysis_result.get("reasoning_trail", []),
        "worker_results_summary": {
            "schedule": "success" if analysis_result.get("worker_results", {}).get("schedule", {}).get("status") == "success" else "failed",
            "impact": "success" if analysis_result.get("worker_results", {}).get("impact", {}).get("status") == "success" else "failed",
            "external_context": "success" if analysis_result.get("worker_results", {}).get("external_context", {}).get("status") == "success" else "failed",
            "recovery": "success" if analysis_result.get("worker_results", {}).get("recovery", {}).get("status") == "success" else "failed"
        }
    }
    
    _write_audit_log(audit_id, log_entry)
    return audit_id


def log_cascade_detection(
    session_id: str,
    decision: dict[str, Any],
    cascade_result: dict[str, Any]
) -> str:
    """
    Log cascade detection event.
    
    Returns: audit_id for reference
    """
    
    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "_")
    audit_id = f"cascade_{session_id}_{timestamp}"
    now = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "audit_id": audit_id,
        "event_type": "CASCADE_DETECTION",
        "timestamp": now,
        "session_id": session_id,
        "decision": decision,
        "cascade_result": {
            "has_cascades": cascade_result.get("has_cascades"),
            "cascade_count": cascade_result.get("cascade_count", 0),
            "safe_to_execute": cascade_result.get("safe_to_execute"),
            "cascade_types": [c.get("type") for c in cascade_result.get("cascades", [])],
            "safe_alternatives_count": len(cascade_result.get("safe_alternatives", []))
        }
    }
    
    _write_audit_log(audit_id, log_entry)
    return audit_id


def log_decision_approval(
    session_id: str,
    decision_type: str,
    source_scene_id: str,
    target_scene_id: str,
    approved_by: str,
    approval_reason: str,
    execution_result: dict[str, Any],
    cascades_checked: bool = False,
    force_approved: bool = False
) -> str:
    """
    Log decision approval and execution.
    
    Returns: audit_id for reference
    """
    
    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "_")
    audit_id = f"approval_{session_id}_{timestamp}"
    now = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "audit_id": audit_id,
        "event_type": "DECISION_APPROVAL",
        "timestamp": now,
        "session_id": session_id,
        "decision": {
            "type": decision_type,
            "source_scene": source_scene_id,
            "target_scene": target_scene_id
        },
        "approval": {
            "approved_by": approved_by,
            "approval_time": now,
            "reason": approval_reason,
            "cascades_checked": cascades_checked,
            "force_approved": force_approved
        },
        "execution": {
            "status": execution_result.get("status"),
            "execution_id": execution_result.get("execution_id"),
            "affected_resources": execution_result.get("affected_resources", {})
        },
        "chain_of_command": {
            "approved_by": approved_by,
            "decision_timestamp": execution_result.get("execution_timestamp")
        }
    }
    
    _write_audit_log(audit_id, log_entry)
    return audit_id


def log_optimization_decision(
    session_id: str,
    source_scene_id: str,
    optimization_result: dict[str, Any],
    chosen_solution: dict[str, Any] | None = None
) -> str:
    """
    Log cost optimization analysis and chosen solution.
    
    Returns: audit_id for reference
    """
    
    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "_")
    audit_id = f"optimization_{session_id}_{timestamp}"
    now = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "audit_id": audit_id,
        "event_type": "COST_OPTIMIZATION",
        "timestamp": now,
        "session_id": session_id,
        "source_scene": source_scene_id,
        "optimization": {
            "scenarios_analyzed": optimization_result.get("scenarios_analyzed", 0),
            "frontier_count": optimization_result.get("frontier_count", 0),
            "optimal_solutions": len(optimization_result.get("optimal_solutions", []))
        },
        "top_solution": {
            "scenario": optimization_result.get("optimal_solutions", [{}])[0].get("scenario") if optimization_result.get("optimal_solutions") else None,
            "benefit": optimization_result.get("optimal_solutions", [{}])[0].get("financial", {}).get("net_benefit") if optimization_result.get("optimal_solutions") else None,
            "risk_score": optimization_result.get("optimal_solutions", [{}])[0].get("metrics", {}).get("risk_score") if optimization_result.get("optimal_solutions") else None
        },
        "chosen_solution": chosen_solution or "Not yet chosen"
    }
    
    _write_audit_log(audit_id, log_entry)
    return audit_id


def get_audit_log(audit_id: str) -> dict[str, Any] | None:
    """
    Retrieve a specific audit log entry.
    """
    
    log_file = AUDIT_LOG_DIR / f"{audit_id}.json"
    
    if not log_file.exists():
        return None
    
    with open(log_file, "r") as f:
        return json.load(f)


def get_session_audit_trail(session_id: str) -> list[dict[str, Any]]:
    """
    Retrieve all audit logs for a session (decision history).
    """
    
    trail = []
    
    if not AUDIT_LOG_DIR.exists():
        return trail
    
    for filename in sorted(AUDIT_LOG_DIR.iterdir()):
        # Only include audit log files
        if not any(filename.name.startswith(prefix) for prefix in ["analysis_", "cascade_", "approval_", "optimization_"]):
            continue
        
        if session_id not in filename.name:
            continue
        
        filepath = filename
        try:
            with open(filepath, "r") as f:
                entry = json.load(f)
                trail.append(entry)
        except (json.JSONDecodeError, OSError):
            pass
    
    # Sort by timestamp
    trail.sort(key=lambda x: x.get("timestamp", ""))
    return trail


def get_scene_decision_history(scene_id: str) -> list[dict[str, Any]]:
    """
    Retrieve all decisions affecting a specific scene.
    """
    
    history = []
    
    if not AUDIT_LOG_DIR.exists():
        return history
    
    for filepath in AUDIT_LOG_DIR.iterdir():
        try:
            with open(filepath, "r") as f:
                entry = json.load(f)
                
                # Check if scene involved in this decision
                if (entry.get("scene_id") == scene_id or 
                    entry.get("decision", {}).get("source_scene") == scene_id or
                    entry.get("decision", {}).get("target_scene") == scene_id):
                    history.append(entry)
        except (json.JSONDecodeError, OSError):
            pass
    
    history.sort(key=lambda x: x.get("timestamp", ""))
    return history


def _write_audit_log(audit_id: str, entry: dict[str, Any]) -> None:
    """
    Write audit log entry to file.
    """
    
    log_file = AUDIT_LOG_DIR / f"{audit_id}.json"
    
    with open(log_file, "w") as f:
        json.dump(entry, f, indent=2, default=str)


def cleanup_old_logs(days_old: int = 30) -> int:
    """
    Delete audit logs older than specified days.
    
    Returns: count of deleted logs
    """
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_old)
    deleted_count = 0
    
    if not AUDIT_LOG_DIR.exists():
        return 0
    
    for filepath in AUDIT_LOG_DIR.iterdir():
        try:
            with open(filepath, "r") as f:
                entry = json.load(f)
                log_time = datetime.fromisoformat(entry.get("timestamp", ""))
                
                if log_time < cutoff_time:
                    filepath.unlink()
                    deleted_count += 1
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    
    return deleted_count
