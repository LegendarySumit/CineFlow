"""
CineFlow FastAPI Backend - UNIFIED Integration
REST API for Production Crisis Director Agent

Features:
- Multi-turn conversation with session state
- Reflection & self-correction loops
- Proactive next-step suggestions
- Financial impact analysis
- True agentic behavior: planning → execution → reflection → state mutation
"""

import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agents.supervisor import SupervisorAgent
from app.services.audit_logger import (
    get_scene_decision_history,
    get_session_audit_trail,
    log_crisis_analysis,
    log_decision_approval,
)
from app.services.cascade_detector import (
    detect_cascading_crises,
    detect_secondary_cascades,
    get_safe_alternatives,
)
from app.services.cost_optimizer import optimize_decision
from app.services.decision_executor import (
    execute_reschedule_decision,
    execute_swap_decision,
)
from app.services.notification_service import notify_schedule_change
from app.services.realtime_stream import stream_with_actual_data
from app.services.response_formatter import (
    format_approval_confirmation,
    format_cascade_warning,
    format_crisis_analysis,
    format_multi_cascade_analysis,
)
from app.session_manager import get_or_create_session, session_store
from app.tools.production import load_dataset

app = FastAPI(
    title="CineFlow API",
    description="Multi-Agent Crisis Director (Unified Agentic Loop)",
    version="1.0.0"
)

# CORS - Restrict origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

DATASET = load_dataset("data")

class CrisisRequest(BaseModel):
    prompt: str
    scene_id: str | None = "sc_42"
    session_id: str | None = None  # Multi-turn conversation support

class DecisionApprovalRequest(BaseModel):
    session_id: str
    decision_type: str  # SWAP or RESCHEDULE
    source_scene_id: str | None = None  # For SWAP
    target_scene_id: str | None = None  # For SWAP
    scene_id: str | None = None  # For RESCHEDULE
    new_day_number: int | None = None  # For RESCHEDULE
    new_date: str | None = None  # For RESCHEDULE
    approved_by: str = "Producer"
    reason: str | None = None
    notify_cast_crew: bool = True
    force_approve: bool = False  # Override cascade warnings if HIGH severity detected

class FormattingRequest(BaseModel):
    format_type: str = "conversational"  # conversational or json

@app.get("/api/production")
def get_production_state():
    """Get current production metadata"""
    return DATASET.get("production", {})

@app.get("/api/schedule")
def get_schedule():
    """Get complete schedule with cast/location/equipment details"""
    return {
        "schedule": DATASET.get("schedule", []),
        "scenes": DATASET.get("scenes", []),
        "actors": DATASET.get("actors", []),
        "locations": DATASET.get("locations", []),
        "equipment": DATASET.get("equipment", []),
    }

@app.post("/api/analyze-crisis")
def analyze_crisis(request: CrisisRequest):
    """
    Multi-Agent Orchestration with Session State Management.
    
    TRUE AGENTIC BEHAVIOR:
    1. Create/restore session (memory)
    2. Run multi-agent analysis with reflection loops
    3. Execute deterministic constraint validation
    4. Provide proactive next steps
    5. Persist state for multi-turn continuity
    """
    if not request.prompt or len(request.prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    try:
        # STEP 1: Multi-turn session management (MEMORY & STATE)
        session = get_or_create_session(request.session_id)
        session.log_user_input(request.prompt, request.scene_id or "sc_42")
        
        # STEP 2: Initialize Supervisor Agent
        supervisor = SupervisorAgent()
        
        # STEP 3: Run agent with session context (PLANNING + REFLECTION)
        result = supervisor.run(request.prompt, request.scene_id or "sc_42", session.state)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        # STEP 4: Log agent decision to session (STATE MUTATION)
        session.log_agent_action("crisis_analysis", result)
        
        # STEP 4b: Log to audit trail for compliance
        log_crisis_analysis(session.session_id, request.scene_id or "sc_42", request.prompt, result)
        
        # STEP 5: Return results with session info for multi-turn continuity
        return {
            "status": "success",
            "session_id": session.session_id,
            "scene_id": result.get("scene_id"),
            "analysis": result,
            "reasoning_trail": result.get("reasoning_trail"),
            "confidence": result.get("confidence"),
            "recommended_action": result.get("recommended_action"),
            "executive_summary": result.get("executive_summary"),
            "next_actions": result.get("next_actions", []),
            "conversation_context": session.get_conversation_context(),
            "approved_swaps": session.state.get("approved_swaps", []),
            "refinement_count": result.get("refinement_count", 0)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e!s}")
    except (RuntimeError, KeyError) as e:
        print(f"[ERROR] Supervisor Agent failed: {e!s}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Multi-agent analysis failed. Check logs.")

@app.post("/api/analyze-cascades")
def analyze_cascades(request: DecisionApprovalRequest):
    """
    ANALYZE cascading crises BEFORE executing a decision.
    
    Checks if a decision (SWAP/RESCHEDULE) creates secondary crises:
    - CAST_CONFLICT: Actor double-booked after swap
    - EQUIPMENT_CONFLICT: Equipment needed in two places
    - LOCATION_CONFLICT: Location unavailable
    
    Returns:
    - has_cascades: bool
    - safe_to_execute: bool
    - cascades: list of detected secondary crises
    - safe_alternatives: suggested target scenes with no cascades
    """
    
    try:
        # Build decision dict for cascade detection
        decision = {
            "decision_type": request.decision_type,
            "source_scene_id": request.source_scene_id,
            "target_scene_id": request.target_scene_id,
            "scene_id": request.scene_id,
            "new_date": request.new_date
        }
        
        # Analyze cascades
        cascade_result = detect_cascading_crises(decision, DATASET)
        
        # Get safe alternatives if cascades exist
        safe_alternatives = []
        if cascade_result.get("has_cascades"):
            safe_alternatives = get_safe_alternatives(decision, cascade_result.get("cascades", []), DATASET)
        
        return {
            "status": "success",
            "has_cascades": cascade_result.get("has_cascades"),
            "cascade_count": cascade_result.get("cascade_count", 0),
            "cascades": cascade_result.get("cascades", []),
            "safe_to_execute": cascade_result.get("safe_to_execute"),
            "warning": cascade_result.get("warning"),
            "safe_alternatives": safe_alternatives
        }
    
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise HTTPException(status_code=500, detail=f"Cascade analysis failed: {e!s}")

@app.post("/api/optimize-decision")
def optimize_decision_endpoint(request: dict):
    """
    COST OPTIMIZATION - Find multiple economically optimal solutions.
    
    Uses Pareto frontier analysis to identify non-dominated solutions.
    A solution is optimal if you can't improve one metric without degrading another.
    
    Request:
    {
        "source_scene_id": "sc_42",
        "alternative_targets": ["sc_09", "sc_14", "sc_18", "sc_25"]
    }
    
    Returns:
    {
        "optimal_solutions": [
            {
                "rank": 1,
                "scenario": "SWAP sc_42 ↔ sc_09",
                "rationale": "Best overall value",
                "metrics": {
                    "net_benefit": 245000,
                    "setup_hours": 2.5,
                    "risk_score": 0.3
                },
                "recommendation": "Recommended"
            }
        ],
        "decision_support": {
            "if_financial_priority": "Use this option",
            "if_speed_priority": "Use this option",
            "if_safety_priority": "Use this option"
        }
    }
    """
    
    try:
        source_scene = request.get("source_scene_id")
        alternatives = request.get("alternative_targets", [])
        
        if not source_scene or not alternatives:
            raise ValueError("source_scene_id and alternative_targets required")
        
        result = optimize_decision(source_scene, alternatives, DATASET)
        
        return {
            "status": "success",
            "optimization_result": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {e!s}")
    except (KeyError, TypeError, AttributeError):
        raise HTTPException(status_code=500, detail="Decision optimization failed")

@app.post("/api/analyze-multi-cascades")
def analyze_multi_cascades(request: DecisionApprovalRequest):
    """
    MULTI-LEVEL CASCADE ANALYSIS
    
    If primary decision creates cascades, check if safe alternatives create NEW cascades.
    This enables sophisticated crisis planning when options are limited.
    
    Returns:
    - safe_alternatives: Options with no cascades (BEST)
    - risky_alternatives: Options with mild cascades (MANAGEABLE)
    - unsafe_alternatives: Options with severe cascades (AVOID)
    - has_truly_safe_option: Whether any completely safe option exists
    - recommendation: Suggested course of action
    """
    
    try:
        # Step 1: Detect primary cascades
        decision = {
            "decision_type": request.decision_type,
            "source_scene_id": request.source_scene_id,
            "target_scene_id": request.target_scene_id,
            "scene_id": request.scene_id,
            "new_date": request.new_date
        }
        
        primary_result = detect_cascading_crises(decision, DATASET)
        
        # Step 2: If cascades detected, analyze safe alternatives
        if primary_result.get("has_cascades"):
            multi_result = detect_secondary_cascades(
                decision,
                primary_result.get("cascades", []),
                DATASET
            )
        else:
            # No cascades, just return single safe result
            multi_result = {
                "safe_alternatives": [],
                "risky_alternatives": [],
                "unsafe_alternatives": [],
                "has_truly_safe_option": True,
                "recommendation": "Primary decision is safe - no cascades detected",
                "total_safe": 0,
                "total_risky": 0,
                "total_unsafe": 0
            }
        
        return {
            "status": "success",
            "primary_decision": decision,
            "primary_cascade_result": {
                "has_cascades": primary_result.get("has_cascades"),
                "cascade_count": primary_result.get("cascade_count", 0)
            },
            "multi_level_analysis": multi_result
        }
    
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise HTTPException(status_code=500, detail=f"Multi-level cascade analysis failed: {e!s}")

@app.post("/api/approve-decision")
def approve_decision(request: DecisionApprovalRequest):
    """
    APPROVE & EXECUTE a production decision.
    
    TRUE AGENTIC BEHAVIOR:
    1. Validate decision
    2. Check for cascading crises (BEFORE execution)
    3. If HIGH severity cascades + no force_approve → return warning
    4. If safe or force_approved → execute schedule changes
    5. Notify affected cast/crew
    6. Log execution
    7. Update session state
    """
    
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        # STEP 1: Build decision dict
        decision = {
            "decision_type": request.decision_type,
            "source_scene_id": request.source_scene_id,
            "target_scene_id": request.target_scene_id,
            "scene_id": request.scene_id,
            "new_date": request.new_date
        }
        
        # STEP 2: Check for cascading crises BEFORE execution (multi-level analysis)
        cascade_result = detect_cascading_crises(decision, DATASET)
        
        # STEP 3: If HIGH severity cascades detected and not force-approved, return warning with multi-level analysis
        if cascade_result.get("has_cascades") and not cascade_result.get("safe_to_execute") and not request.force_approve:
            # Get both single-level and multi-level alternatives
            safe_alternatives = get_safe_alternatives(decision, cascade_result.get("cascades", []), DATASET)
            
            # Also run multi-level analysis for sophisticated decision support
            multi_result = detect_secondary_cascades(
                decision,
                cascade_result.get("cascades", []),
                DATASET
            )
            
            return {
                "status": "cascade_warning",
                "message": "Cascading crises detected. Review alternatives or approve with force_approve=true",
                "decision": decision,
                "cascades": cascade_result.get("cascades"),
                "single_level_alternatives": safe_alternatives,
                "multi_level_analysis": multi_result,
                "recommended_action": multi_result.get("recommendation"),
                "session_id": request.session_id
            }
        
        # STEP 4: Execute based on decision type
        if request.decision_type == "SWAP":
            if not request.source_scene_id or not request.target_scene_id:
                raise ValueError("SWAP requires source_scene_id and target_scene_id")
            
            execution_result = execute_swap_decision(
                session_id=request.session_id,
                source_scene_id=request.source_scene_id,
                target_scene_id=request.target_scene_id,
                approved_by=request.approved_by,
                reason=request.reason or "Producer approval"
            )
        
        elif request.decision_type == "RESCHEDULE":
            if not request.scene_id or request.new_day_number is None or not request.new_date:
                raise ValueError("RESCHEDULE requires scene_id, new_day_number, and new_date")
            
            execution_result = execute_reschedule_decision(
                session_id=request.session_id,
                scene_id=request.scene_id,
                new_day_number=request.new_day_number,
                new_date=request.new_date,
                approved_by=request.approved_by,
                reason=request.reason or "Producer approval"
            )
        
        else:
            raise ValueError(f"Unknown decision_type: {request.decision_type}")
        
        # STEP 5: Send notifications if requested
        notification_result = None
        if request.notify_cast_crew and execution_result.get("status") == "success":
            recipients = [
                {"type": "ACTOR", "id": "actor_1", "email": "actor@example.com"},
                {"type": "CREW", "id": "crew_1", "email": "crew@example.com"}
            ]
            notification_result = notify_schedule_change(execution_result, recipients)
        
        # STEP 6: Update session state with comprehensive cascade info
        session.state["approved_swaps"] = session.state.get("approved_swaps", []) + [{
            "decision_id": execution_result.get("execution_id"),
            "type": request.decision_type,
            "timestamp": execution_result.get("execution_timestamp"),
            "approved_by": request.approved_by,
            "cascades_detected": cascade_result.get("has_cascades", False),
            "cascade_count": cascade_result.get("cascade_count", 0),
            "force_approved": request.force_approve
        }]
        
        # STEP 6b: Log decision to audit trail
        log_decision_approval(
            session_id=request.session_id,
            decision_type=request.decision_type,
            source_scene_id=request.source_scene_id or request.scene_id or "unknown",
            target_scene_id=request.target_scene_id or "unknown",
            approved_by=request.approved_by,
            approval_reason=request.reason or "Producer approval",
            execution_result=execution_result,
            cascades_checked=cascade_result.get("has_cascades", False),
            force_approved=request.force_approve
        )
        
        return {
            "status": "success",
            "message": f"{request.decision_type} decision executed successfully",
            "execution_result": execution_result,
            "cascade_check": {
                "has_cascades": cascade_result.get("has_cascades", False),
                "safe_to_execute": cascade_result.get("safe_to_execute", True)
            },
            "notifications": notification_result,
            "session_id": request.session_id,
            "approved_swaps_count": len(session.state.get("approved_swaps", []))
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {e!s}")
    except (KeyError, TypeError, AttributeError):
        raise HTTPException(status_code=500, detail="Decision execution failed")

@app.post("/api/analyze-crisis-conversational")
def analyze_crisis_conversational(request: CrisisRequest):
    """
    Single endpoint: Analyze crisis AND return human-readable conversational format.
    Perfect for terminal/UI applications.
    """
    
    try:
        session = get_or_create_session(request.session_id)
        session.log_user_input(request.prompt, request.scene_id or "sc_42")
        
        supervisor = SupervisorAgent()
        analysis = supervisor.run(request.prompt, request.scene_id or "sc_42", session.state)
        
        if analysis.get("status") == "error":
            raise HTTPException(status_code=400, detail=analysis.get("message"))
        
        session.log_agent_action("crisis_analysis", analysis)
        
        # Format as conversational
        conversational = format_crisis_analysis(analysis)
        
        return {
            "status": "success",
            "session_id": session.session_id,
            "conversational_format": conversational
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e!s}")
    except (KeyError, TypeError, AttributeError):
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.post("/api/format-analysis")
def format_analysis_response(request: CrisisRequest):
    """
    Format crisis analysis as human-readable conversational text.
    Use this for terminal/UI display instead of raw JSON.
    """
    
    try:
        # Run analysis
        session = get_or_create_session(request.session_id)
        supervisor = SupervisorAgent()
        analysis = supervisor.run(request.prompt, request.scene_id or "sc_42", session.state)
        
        if analysis.get("status") == "error":
            raise HTTPException(status_code=400, detail=analysis.get("message"))
        
        # Format as conversational
        conversational = format_crisis_analysis(analysis)
        
        return {
            "status": "success",
            "session_id": session.session_id,
            "conversational_format": conversational,
            "json_format": analysis  # Also provide raw JSON for reference
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e!s}")
    except (KeyError, TypeError, AttributeError):
        raise HTTPException(status_code=500, detail="Analysis formatting failed")

@app.post("/api/format-approval")
def format_approval_response(execution_result: dict):
    """
    Format decision approval confirmation as human-readable text.
    """
    
    try:
        conversational = format_approval_confirmation(execution_result)
        
        return {
            "status": "success",
            "conversational_format": conversational,
            "json_format": execution_result
        }
    
    except (KeyError, TypeError, AttributeError):
        raise HTTPException(status_code=500, detail="Approval formatting failed")

@app.post("/api/format-cascades")
def format_cascades_response(cascade_result: dict):
    """
    Format cascade detection warning as human-readable text.
    """
    
    try:
        conversational = format_cascade_warning(cascade_result)
        
        return {
            "status": "success",
            "conversational_format": conversational,
            "json_format": cascade_result
        }
    
    except (KeyError, TypeError, AttributeError):
        raise HTTPException(status_code=500, detail="Cascade formatting failed")

@app.post("/api/format-multi-cascades")
def format_multi_cascades_response(multi_result: dict):
    """
    Format multi-level cascade analysis as human-readable text.
    Shows safe, risky, and unsafe alternatives clearly.
    """
    
    try:
        conversational = format_multi_cascade_analysis(multi_result)
        
        return {
            "status": "success",
            "conversational_format": conversational,
            "json_format": multi_result
        }
    
    except (KeyError, TypeError, AttributeError):
        raise HTTPException(status_code=500, detail="Multi-cascade formatting failed")

@app.get("/api/session/{session_id}")
def get_session_info(session_id: str):
    """
    Retrieve conversation history and state for a session.
    Enables multi-turn conversation continuity and state inspection.
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_interaction": session.last_interaction.isoformat(),
        "event_count": len(session.events),
        "approved_swaps": session.state.get("approved_swaps", []),
        "active_schedule": session.state.get("active_schedule", []),
        "recent_events": [
            {
                "timestamp": e.get("timestamp"),
                "type": e.get("type"),
                "summary": e.get("query") or e.get("action") or e.get("tool")
            }
            for e in session.events[-5:]
        ]
    }

@app.get("/api/audit-trail/{session_id}")
def get_audit_trail(session_id: str):
    """
    Retrieve decision audit trail for a session.
    Shows all crisis analyses, approvals, and executions in chronological order.
    """
    
    try:
        trail = get_session_audit_trail(session_id)
        
        return {
            "status": "success",
            "session_id": session_id,
            "audit_count": len(trail),
            "audit_trail": trail
        }
    
    except (OSError, json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=500, detail="Audit trail retrieval failed")

@app.get("/api/scene-history/{scene_id}")
def get_scene_history(scene_id: str):
    """
    Retrieve decision history for a specific scene.
    Shows all decisions that affected this scene.
    """
    
    try:
        history = get_scene_decision_history(scene_id)
        
        return {
            "status": "success",
            "scene_id": scene_id,
            "decision_count": len(history),
            "decision_history": history
        }
    
    except (OSError, json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=500, detail="Scene history retrieval failed")

@app.websocket("/ws/analyze-crisis")
async def websocket_analyze_crisis(websocket: WebSocket):
    """
    WebSocket endpoint for streaming crisis analysis progress in real-time.
    
    Client sends:
    {"session_id": "...", "prompt": "...", "scene_id": "sc_42"}
    
    Server streams: StreamMessage updates (event_type, status, message, data)
    """
    
    await websocket.accept()
    
    try:
        data = await websocket.receive_json()
        session_id = data.get("session_id")
        prompt = data.get("prompt")
        scene_id = data.get("scene_id", "sc_42")
        
        if not session_id or not prompt:
            await websocket.send_json({
                "event_type": "ERROR",
                "status": "error",
                "message": "Missing session_id or prompt"
            })
            await websocket.close(code=1000)
            return
        
        # Get or create session
        session = get_or_create_session(session_id)
        session.log_user_input(prompt, scene_id)
        
        # Run analysis and stream progress
        supervisor = SupervisorAgent()
        analysis_result = supervisor.run(prompt, scene_id, session.state)
        
        # Stream actual results with real data
        async for message in stream_with_actual_data(session_id, analysis_result):
            await websocket.send_text(message.to_json())
        
        # Log to audit trail
        log_crisis_analysis(session_id, scene_id, prompt, analysis_result)
        session.log_agent_action("crisis_analysis", analysis_result)
        
    except WebSocketDisconnect:
        pass
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        try:
            await websocket.send_json({
                "event_type": "ERROR",
                "status": "error",
                "message": str(e)
            })
        except (OSError, RuntimeError):
            pass

@app.get("/api/health")
def health_check():
    """Health check endpoint - verify agent operational status"""
    return {
        "status": "operational",
        "agent": "CineFlow Crisis Director (Unified Agentic Loop)",
        "version": "1.0.0",
        "features": [
            "Multi-agent orchestration (Planner, Researcher, Strategist, Critic)",
            "Reflection & self-correction loops",
            "Session state management (multi-turn)",
            "Proactive next-step suggestions",
            "Deterministic constraint validation",
            "Financial impact analysis",
            "State persistence across turns",
            "Conversation memory & context injection"
        ]
    }

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

@app.get("/")
def serve_ui():
    """Serve 4-screen dashboard UI"""
    ui_path = os.path.join(static_dir, "ui.html")
    if os.path.exists(ui_path):
        return FileResponse(ui_path)
    
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"message": "CineFlow API Running. UI at /static/ui.html"}

try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except (OSError, RuntimeError) as e:
    print(f"[WARNING] Static files mount failed: {e!s}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
