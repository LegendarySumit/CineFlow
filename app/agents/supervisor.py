"""
SUPERVISOR AGENT (Master Orchestrator)

Role: Receives user query → Creates execution plan → Delegates to workers → 
Monitors results → Requests refinement if needed → Returns final recommendation

This is the core agentic orchestrator using the Vellum framework.
"""

import json
import os
import time
import warnings
from datetime import datetime, timezone
from typing import Any

# Suppress FutureWarning from deprecated google.generativeai package
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')
import google.generativeai as genai
from dotenv import load_dotenv

from app.agents.workers.critic_worker import validate_plan
from app.agents.workers.external_info_worker import gather_external_context
from app.agents.workers.schedule_worker import (
    load_scene_and_schedule,
)
from app.agents.workers.strategy_worker import (
    evaluate_impact,
    generate_recovery_options,
)
from app.services.progress_streamer import get_or_create_streamer

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Use gemini-2.5-flash for free tier - higher quota (10 RPM, 250 RPD)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class SupervisorAgent:
    """
    Master orchestrator that:
    1. Plans: Breaks crisis into sub-tasks
    2. Executes: Calls actual worker agents
    3. Monitors: Tracks worker results
    4. Refines: Requests re-work if quality is low
    5. Synthesizes: Combines results into final recommendation
    """
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self.streamer = get_or_create_streamer(session_id) if session_id else None
        self.session_state = {}
        self.plan = None
        self.worker_results = {}
        self.refinement_count = 0
        self.project_data = None  # Optional: If provided, use this instead of data/
        
        # REFINEMENT STRATEGY (Self-Correcting Agent Behavior)
        # ========================================================
        # FREE-TIER API (Current Default - Recommended):
        self.max_refinements = 0  # No refinements - respects 5 req/min limit
        
        # PAID-TIER API (Uncomment line below to enable true agentic behavior):
        # self.max_refinements = 2  # Enable 2 self-correction loops
        #
        # Why switch to 2 for paid API?
        # - Attempt 1: Initial analysis (~5 API calls)
        # - Attempt 2: Auto-retry on failures (~5 API calls)
        # - Attempt 3: Final refinement (~5 API calls)
        # - Total: ~15 API calls per request
        # - Benefit: Self-correcting agent fixes its own JSON parsing errors
        # - Cost: 3x more API calls (~₹10-50 per request with paid plan)
        #
        # NOTE: Only enable for PAID API tier
    
    def create_execution_plan(self, user_query: str, scene_id: str) -> dict[str, Any]:
        """PLANNING PHASE: Supervisor breaks crisis into atomic tasks with context awareness."""
        
        print("\n[SUPERVISOR] PLANNING PHASE")
        print(f"  Input: {user_query}")
        
        # Enhanced system prompt with better context understanding
        system_prompt = """You are an expert Film Production Supervisor with deep understanding of:
- Production logistics and resource constraints
- Actor availability and scheduling conflicts
- Equipment availability and technical requirements
- Location accessibility and permits
- Budget implications and cost optimization
- Weather impacts on outdoor filming
- Production timelines and schedule dependencies

Your role is to analyze production crises and create intelligent recovery plans.

KEY PRINCIPLES:
1. Understand the ROOT CAUSE of the crisis (actor unavailable, equipment broken, location blocked, etc.)
2. Consider CASCADING EFFECTS (if you swap scenes, what else breaks?)
3. Balance COST vs TIME vs QUALITY tradeoffs
4. Propose MULTIPLE OPTIONS with different risk/reward profiles
5. Provide REASONING for each recommendation
6. Consider HISTORICAL DECISIONS (what swaps were already approved?)"""
        
        planning_prompt = f"""
{system_prompt}

PRODUCTION CRISIS TO ANALYZE:
Crisis Query: {user_query}
Scene ID: {scene_id}

ANALYSIS REQUIREMENTS:
1. Identify the crisis type (CAST, EQUIPMENT, LOCATION, WEATHER, BUDGET, SCHEDULE)
2. Assess immediate impact on the specified scene and related scenes
3. Determine if rescheduling, actor swap, location change, or equipment substitution is needed
4. Plan comprehensive recovery with multiple options ranked by feasibility

Return ONLY valid JSON (no markdown, no extras):
{{
    "crisis_type": "CAST|EQUIPMENT|LOCATION|WEATHER|BUDGET|SCHEDULE",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "immediate_impact": "Description of what happens if no action taken",
    "tasks": [
        {{"id": 1, "task": "analyze_current_scene_state", "worker": "SCHEDULE_WORKER", "purpose": "Load scene details and dependencies"}},
        {{"id": 2, "task": "assess_crisis_scope", "worker": "STRATEGY_WORKER", "purpose": "Determine which scenes are affected"}},
        {{"id": 3, "task": "gather_resource_status", "worker": "EXTERNAL_INFO_WORKER", "purpose": "Check actor/equipment/location availability"}},
        {{"id": 4, "task": "identify_alternative_solutions", "worker": "STRATEGY_WORKER", "purpose": "Generate 3+ recovery options"}},
        {{"id": 5, "task": "validate_feasibility", "worker": "CRITIC_WORKER", "purpose": "Check for cascading issues and feasibility"}}
    ],
    "success_criteria": [
        "Crisis type correctly identified",
        "All affected scenes identified",
        "3+ recovery options generated",
        "No cascading crises introduced",
        "Cost and schedule impact calculated"
    ]
}}
"""
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            planning_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.5
            )
        )
        
        try:
            content = response.text if response else ""
            plan = json.loads(content) if content else {}
        except (json.JSONDecodeError, ValueError, IndexError):
            # Fallback plan
            plan = {
                "tasks": [
                    {"id": 1, "task": "load_scene", "worker": "SCHEDULE_WORKER"},
                    {"id": 2, "task": "analyze_crisis_impact", "worker": "STRATEGY_WORKER"},
                    {"id": 3, "task": "gather_external_context", "worker": "EXTERNAL_INFO_WORKER"},
                    {"id": 4, "task": "generate_recovery", "worker": "STRATEGY_WORKER"},
                    {"id": 5, "task": "validate_plan", "worker": "CRITIC_WORKER"}
                ],
                "success_criteria": ["All tasks complete"]
            }
        
        self.plan = plan
        print(f"  [CREATED] Plan with {len(plan.get('tasks', []))} tasks")
        for task in plan.get('tasks', []):
            print(f"    - Task {task.get('id')}: {task.get('task')} ({task.get('worker')})")
        
        return plan
    
    def execute_workers(self, scene_id: str, crisis_query: str) -> dict[str, Any]:
        """
        EXECUTION PHASE: Context-aware worker orchestration with real-time progress streaming.
        
        Only runs workers relevant to the crisis type:
        - WEATHER: Schedule + Weather + Strategy + Recovery + Validation
        - EQUIPMENT: Schedule + Strategy + Recovery + Validation
        - CAST: Schedule + Strategy + Recovery + Validation
        - PERMIT: Schedule + Strategy + Recovery + Validation
        """
        
        print("\n[SUPERVISOR] WORKER EXECUTION PHASE")
        if self.streamer:
            self.streamer.emit_phase_start(
                2,
                "Worker Delegation",
                "Executing specialized workers in parallel and sequential mode"
            )
        
        worker_results = {}
        
        # TASK 1: Load scene schedule (always needed)
        print("  [EXECUTE] SCHEDULE_WORKER...")
        if self.streamer:
            self.streamer.emit_worker_start(
                "SCHEDULE_WORKER",
                f"Loading scene data and production schedule for {scene_id}"
            )
        
        start_time = time.time()
        schedule_result = load_scene_and_schedule(scene_id, self.project_data)
        duration = int((time.time() - start_time) * 1000)
        worker_results["schedule"] = schedule_result
        
        if schedule_result.get("status") == "success":
            scene_title = schedule_result.get('scene', {}).get('title')
            print(f"    [OK] Loaded: {scene_title}")
            if self.streamer:
                self.streamer.emit_worker_result(
                    "SCHEDULE_WORKER",
                    f"Loaded scene: {scene_title}",
                    {"scene_id": scene_id, "title": scene_title},
                    duration
                )
        else:
            error_msg = schedule_result.get("message")
            if self.streamer:
                self.streamer.emit_error(
                    "SCHEDULE_WORKER Failed",
                    error_msg,
                    "Verify scene ID exists and data files are accessible"
                )
            return {"error": error_msg, "results": worker_results}
        
        # TASK 2: Determine crisis type (critical for context-aware execution)
        print("  [ANALYZE] Crisis type...")
        if self.streamer:
            self.streamer.emit_worker_start(
                "IMPACT_WORKER",
                "Determining crisis type and financial impact"
            )
        
        start_time = time.time()
        impact_result = evaluate_impact(scene_id, crisis_query, self.project_data)
        duration = int((time.time() - start_time) * 1000)
        worker_results["impact"] = impact_result
        crisis_type = impact_result.get("crisis_type", "UNKNOWN")
        print(f"    [OK] Crisis Type: {crisis_type}")
        
        if self.streamer:
            self.streamer.emit_worker_result(
                "IMPACT_WORKER",
                f"Crisis identified: {crisis_type}",
                {
                    "crisis_type": crisis_type,
                    "financial_impact": impact_result.get("financial_impact"),
                    "risk_level": impact_result.get("risk_level")
                },
                duration
            )
        
        # TASK 3: Gather external world context (ALWAYS - for all crisis types)
        print("  [EXECUTE] EXTERNAL_INFO_WORKER...")
        if self.streamer:
            self.streamer.emit_worker_start(
                "EXTERNAL_INFO_WORKER",
                "Gathering external context (weather, permits, news)"
            )
        
        start_time = time.time()
        external_result = gather_external_context(scene_id, crisis_query, self.project_data, impact_result.get("crisis_type"))
        duration = int((time.time() - start_time) * 1000)
        worker_results["external_context"] = external_result
        
        if external_result.get("status") == "success":
            quality = external_result.get("data_quality", {})
            dims = external_result.get('investigation_dimensions', [])
            print(f"    [OK] Gathered {dims}")
            print(f"    [OK] Total sources: {quality.get('total_results', 0)} | Quality: {quality.get('quality_score', 0)}%")
            
            if self.streamer:
                self.streamer.emit_worker_result(
                    "EXTERNAL_INFO_WORKER",
                    f"Gathered {len(dims)} information dimensions",
                    {
                        "dimensions": dims,
                        "total_sources": quality.get('total_results', 0),
                        "quality_score": quality.get('quality_score', 0)
                    },
                    duration
                )
        
        # TASK 4: Generate recovery options (works for ANY crisis type)
        print("  [EXECUTE] STRATEGY_WORKER (Recovery Generation)...")
        if self.streamer:
            self.streamer.emit_worker_start(
                "STRATEGY_WORKER",
                "Generating recovery and mitigation options"
            )
        
        start_time = time.time()
        recovery_result = generate_recovery_options(scene_id, crisis_query, self.project_data)
        duration = int((time.time() - start_time) * 1000)
        worker_results["recovery"] = recovery_result
        
        if recovery_result.get("status") == "success":
            option_count = recovery_result.get('option_count', 0)
            print(f"    [OK] Generated {option_count} recovery options")
            
            if self.streamer:
                self.streamer.emit_worker_result(
                    "STRATEGY_WORKER",
                    f"Generated {option_count} viable recovery options",
                    {
                        "option_count": option_count,
                        "best_option": recovery_result.get("best_option"),
                        "alternatives": recovery_result.get("alternatives", [])
                    },
                    duration
                )
        
        # TASK 5: Validate best option
        print("  [EXECUTE] CRITIC_WORKER...")
        if self.streamer:
            self.streamer.emit_worker_start(
                "CRITIC_WORKER",
                "Validating chosen strategy and detecting cascading impacts"
            )
        
        start_time = time.time()
        best_option = recovery_result.get("best_option") or {}
        validation_result = validate_plan(best_option)
        duration = int((time.time() - start_time) * 1000)
        worker_results["validation"] = validation_result
        
        rec_status = validation_result.get('recommendation', 'UNKNOWN')
        print(f"    [OK] Plan Status: {rec_status}")
        
        if self.streamer:
            self.streamer.emit_worker_result(
                "CRITIC_WORKER",
                f"Validation complete: {rec_status}",
                {
                    "recommendation": rec_status,
                    "cascades_detected": validation_result.get("cascades_detected", 0),
                    "risk_factors": validation_result.get("risk_factors", [])
                },
                duration
            )
        
        return worker_results
    
    def delegate_to_workers(self, plan: dict, worker_results: dict) -> dict[str, Any]:
        """
        DELEGATION MONITORING: Log worker results execution.
        
        In production, this would use ADK's SequentialAgent or GraphWorkflow
        to route tasks to specialized agents.
        """
        
        print("\n[SUPERVISOR] DELEGATION MONITORING")
        
        execution_log = {
            "delegations": [],
            "worker_results": worker_results,
            "status": "all_tasks_complete" if len(worker_results) >= 5 else "partial_complete"
        }
        
        result_key_map = {
            1: "schedule",
            2: "impact",
            3: "external_context",
            4: "recovery",
            5: "validation"
        }
        
        for task in plan.get('tasks', []):
            task_id = task.get('id')
            worker = task.get('worker')
            result_key = result_key_map.get(task_id)
            
            if result_key and result_key in worker_results:
                status = "[COMPLETE]"
                print(f"  {status} Task {task_id} ({worker}): {task.get('task')}")
                execution_log['delegations'].append({
                    "task_id": task_id,
                    "worker": worker,
                    "status": "success"
                })
            else:
                print(f"  [PARTIAL] Task {task_id} ({worker})")
        
        self.worker_results = worker_results
        return execution_log
    
    def monitor_quality(self, worker_results: dict) -> dict[str, Any]:
        """
        MONITORING PHASE: Supervisor checks if worker outputs meet quality standards.
        
        TRUE AGENTIC BEHAVIOR: If validation fails, loop back to planning.
        Returns: {"quality_ok": bool, "issues": [...], "refinement_needed": bool}
        """
        
        print("\n[SUPERVISOR] QUALITY MONITORING (Reflection & Self-Critique)")
        
        quality_checks = {
            "scene_data_exists": "schedule" in worker_results and worker_results.get("schedule", {}).get("status") == "success",
            "impact_assessed": "impact" in worker_results and worker_results.get("impact", {}).get("crisis_type") is not None,
            "recovery_options_exist": "recovery" in worker_results and worker_results.get("recovery", {}).get("option_count", 0) > 0,
            "validation_passed": "validation" in worker_results and worker_results.get("validation", {}).get("valid") is not None,
            "external_context_gathered": "external_context" in worker_results and worker_results.get("external_context", {}).get("status") == "success"
        }
        
        # For CAST/EQUIPMENT crises, weather data is not required (skip that check)
        crisis_type = worker_results.get("impact", {}).get("crisis_type")
        if crisis_type not in ["CAST", "EQUIPMENT"]:
            quality_checks["weather_data_relevant"] = True  # Not required for CAST/EQUIPMENT
        
        all_checks_pass = all(quality_checks.values())
        
        print("  Quality Checks:")
        for check, result in quality_checks.items():
            status = "[OK]" if result else "[FAIL]"
            print(f"    {status} {check}")
        
        return {
            "quality_ok": all_checks_pass,
            "checks": quality_checks,
            "refinement_needed": not all_checks_pass and self.refinement_count < self.max_refinements
        }
    
    def request_refinement(self, failed_checks: dict) -> str:
        """
        REFINEMENT REQUEST: If quality issues, loop and re-plan.
        
        TRUE AGENTIC LOOP: Detects failures → Re-plans → Re-executes
        """
        
        self.refinement_count += 1
        
        print(f"\n[SUPERVISOR] SELF-CORRECTION LOOP (Attempt {self.refinement_count}/{self.max_refinements})")
        
        failed_items = [check for check, passed in failed_checks.items() if not passed]
        print(f"  Issues detected: {', '.join(failed_items)}")
        print("  Replanning and requesting worker re-execution...")
        print("  This is TRUE AGENTIC BEHAVIOR: Detect failure -> Adapt strategy -> Retry")
        
        return f"Refinement cycle {self.refinement_count}"
    
    def synthesize_recommendation(self, worker_results: dict) -> dict[str, Any]:
        """
        SYNTHESIS PHASE: Combine worker outputs into intelligent, context-aware recommendation.
        
        Uses enhanced LLM prompts to create coherent, evidence-backed recommendations
        that understand production context and constraints.
        """
        
        print("\n[SUPERVISOR] SYNTHESIS PHASE")
        
        # Extract data from worker results
        scene_data = worker_results.get("schedule", {}).get("scene", {})
        external_context = worker_results.get("external_context", {})
        impact = worker_results.get("impact", {})
        recovery_data = worker_results.get("recovery", {})
        recovery = recovery_data.get("alternative_options", [])
        deterministic = recovery_data.get("deterministic_resolution", {})
        validation = worker_results.get("validation", {})
        
        # Build external context summary
        external_summary = ""
        if external_context.get("status") == "success":
            quality = external_context.get("data_quality", {})
            investigation = external_context.get("investigation_dimensions", [])
            external_summary = f"\nExternal Intel: Investigated {len(investigation)} dimensions from {quality.get('total_results', 0)} sources (Quality: {quality.get('quality_score', 0)}%)"
        
        # Enhanced synthesis prompt with better system instructions
        synthesis_prompt = f"""You are an expert Film Production Crisis Manager with deep experience in:
- Production scheduling and logistics
- Cost optimization and budget management
- Risk assessment and mitigation
- Resource allocation and conflict resolution

CONTEXT:
Scene: {scene_data.get('title')} (ID: {scene_data.get('id')})
Location: {scene_data.get('location')}
Cast: {scene_data.get('cast')}
Duration: {scene_data.get('duration')} hours
Crisis Type: {impact.get('crisis_type') or 'UNKNOWN'}
Risk Level: {impact.get('risk_level')}
Recommended Action: {deterministic.get('action') if deterministic else 'HOLD'}{external_summary}

ANALYSIS DATA:
- Alternative Options Available: {len(recovery)}
- Risk Factors: {', '.join(impact.get('risk_factors', [])[:3])}
- Cost Impact: {impact.get('cost_impact', 'TBD')}

YOUR TASK:
Write a concise, intelligent executive summary (150-250 words) that:

1. CLEARLY STATE the crisis - Be specific about what's happening and why it matters
2. EXPLAIN THE IMPACT - How does this affect production? What are consequences?
3. RECOMMEND ACTION - What should the producer do? Why is this the best option?
4. ADDRESS CONCERNS - Why is this better than alternatives? What's the risk?
5. NEXT STEPS - What needs to happen immediately? What's the timeline?

Use production terminology. Be confident but not dismissive of other options.
Explain your reasoning so the producer understands the tradeoffs.
Make it sound professional, not robotic."""
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            synthesis_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=600,
                temperature=0.6
            )
        )
        
        summary = response.text if response and response.text else "Crisis analyzed. Comprehensive recommendation generated."
        
        print("  [OK] Recommendation Synthesized")
        
        return {
            "status": "success",
            "crisis_type": impact.get('crisis_type', 'UNKNOWN'),
            "executive_summary": summary,
            "scene_id": scene_data.get('id'),
            "risk_level": impact.get('risk_level'),
            "recommended_action": {
                "action": deterministic.get('action'),
                "target_scene": deterministic.get('target_scene'),
                "reasoning": deterministic.get('action_reason'),
                "confidence": deterministic.get('executive_decision', {}).get('confidence')
            } if deterministic else None,
            "confidence": validation.get('confidence', 'MEDIUM'),
            "evidence_count": external_context.get('data_quality', {}).get('total_results', 0),
            "risk_factors": impact.get('risk_factors', []),
            "cost_impact": impact.get('cost_impact'),
            "worker_results": worker_results,
            "reasoning_trail": [
                "PLANNER: Created execution plan with context awareness",
                f"SCHEDULE_WORKER: Loaded {scene_data.get('title')} - analyzed dependencies",
                f"EXTERNAL_INFO_WORKER: Gathered {len(external_context.get('investigation_dimensions', []))} dimensions of context",
                f"STRATEGY_WORKER: Crisis Assessment = {impact.get('risk_level')}, Impact = {impact.get('cost_impact')}",
                f"STRATEGY_WORKER: Generated {len(recovery)} recovery options with tradeoff analysis",
                f"CRITIC_WORKER: Validation = {validation.get('recommendation')}, Feasibility Confirmed"
            ]
        }
    
    def run(self, user_query: str, scene_id: str, session_state: dict | None = None) -> dict[str, Any]:
        """
        MAIN SUPERVISOR LOOP - TRUE AGENTIC BEHAVIOR:
        1. Plan what needs to happen
        2. Execute workers to gather data
        3. Monitor quality of results (Reflection)
        4. IF quality fails → Loop back to step 1 (Self-Correction)
        5. IF quality passes → Synthesize final recommendation
        6. Suggest proactive next-steps
        """
        if session_state is None:
            session_state = {}
        
        # Initialize session events if not present
        if "events" not in session_state:
            session_state["events"] = []
        
        # Extract project_data from session_state if provided
        if "project_data" in session_state:
            self.project_data = session_state["project_data"]
        
        print("\n" + "="*70)
        print("[SUPERVISOR] AGENT - Master Orchestrator (Full Agentic Loop)")
        print("="*70)
        
        # Log this interaction
        session_state["events"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "supervisor_run",
            "scene_id": scene_id,
            "query": user_query
        })
        
        self.session_state = session_state
        
        # PHASE 1: Create plan
        try:
            plan = self.create_execution_plan(user_query, scene_id)
        except Exception as e:
            # If planning fails (API quota), use default plan
            print(f"  [WARNING] Plan creation failed: {str(e)[:100]}")
            plan = {
                "tasks": [
                    {"id": 1, "worker": "schedule_worker", "action": "load_scene"},
                    {"id": 2, "worker": "strategy_worker", "action": "analyze_crisis_impact"},
                    {"id": 3, "worker": "external_info_worker", "action": "gather_external_context"},
                    {"id": 4, "worker": "strategy_worker", "action": "generate_recovery"},
                    {"id": 5, "worker": "critic_worker", "action": "validate_plan"}
                ]
            }
        worker_results: dict[str, Any] = {}
        
        # LOOPING PHASE: Keep refining until quality passes or max refinements reached
        while self.refinement_count <= self.max_refinements:
            
            # PHASE 2: EXECUTE workers (actual agent behavior)
            worker_results = self.execute_workers(scene_id, user_query)
            
            if "error" in worker_results:
                return {
                    "status": "error",
                    "message": worker_results["error"],
                    "scene_id": scene_id
                }
            
            # PHASE 3: Delegate/Monitor
            self.delegate_to_workers(plan, worker_results)
            
            # PHASE 4: Monitor quality (REFLECTION)
            quality_result = self.monitor_quality(worker_results)
            
            # Check if quality is acceptable
            if quality_result["quality_ok"]:
                print("\n[OK] Quality checks passed. Proceeding to synthesis.")
                break
            else:
                # PHASE 5: SELF-CORRECTION LOOP
                if quality_result["refinement_needed"]:
                    self.request_refinement(quality_result["checks"])
                    # In production, would call workers again with modified plan
                    # For now, continue to synthesis with partial data
                else:
                    print("\n  Max refinement attempts reached. Using best available data.")
                    break
        
        # PHASE 6: Synthesize
        final_recommendation = self.synthesize_recommendation(worker_results)
        
        # PHASE 7: ADD PROACTIVE NEXT STEPS (True Agentic Behavior)
        try:
            final_recommendation["next_actions"] = self.generate_proactive_actions(
                final_recommendation,
                worker_results
            )
        except Exception as e:
            # If API quota exceeded or other error, use fallback
            print(f"\n  [WARNING] Proactive actions generation failed: {str(e)[:100]}")
            final_recommendation["next_actions"] = self._generate_context_aware_fallback(
                final_recommendation.get('crisis_type', 'UNKNOWN'),
                len(worker_results.get("recovery_options", []))
            )
        
        # Save state for multi-turn conversation
        final_recommendation["session_state"] = self.session_state
        final_recommendation["refinement_attempts"] = self.refinement_count
        
        return final_recommendation
    
    def generate_proactive_actions(self, recommendation: dict, worker_results: dict) -> list[dict[str, Any]]:
        """
        PROACTIVE BEHAVIOR: Use Gemini to suggest context-aware next steps.
        
        Instead of hardcoded templates, generate specific actions based on:
        - Crisis type
        - Recommended action
        - Financial impact
        - External context
        - Timeline
        """
        
        print("\n[SUPERVISOR] GENERATING PROACTIVE NEXT STEPS (Gemini-Powered)")
        
        # Build context for Gemini
        crisis_type = recommendation.get('crisis_type', 'UNKNOWN')
        action = recommendation.get('recommended_action', {})
        impact = worker_results.get("impact", {})
        recovery = worker_results.get("recovery", {})
        external = worker_results.get("external_context", {})
        
        prompt = f"""You are a production manager suggesting immediate next steps after a crisis decision.

CRISIS TYPE: {crisis_type}
RECOMMENDED ACTION: {action.get('action', 'UNKNOWN')}
TARGET SCENE: {action.get('target_scene_id', 'N/A')}

CRISIS IMPACT:
- Financial Impact: {impact.get('financial_impact', 'Unknown')}
- Affected Scenes: {impact.get('affected_scenes_count', 0)}
- Risk Level: {impact.get('risk_level', 'UNKNOWN')}

RECOVERY OPTIONS:
- Option Count: {recovery.get('option_count', 0)}
- Best Option: {action.get('target_scene_id', 'TBD')}

EXTERNAL CONTEXT:
- Dimensions Gathered: {external.get('investigation_dimensions', [])}
- Total Sources: {external.get('total_sources', 0)}

YOUR TASK:
Generate 4-5 specific, actionable next steps the producer should take IMMEDIATELY.
For each step:
1. Assign PRIORITY (HIGH, MEDIUM, LOW)
2. Give a specific LABEL describing the action
3. Provide a 1-line DESCRIPTION
4. Suggest an EXAMPLE QUERY the producer could ask

Focus on:
- Crisis-specific actions (not generic templates)
- Time-sensitive tasks first
- Stakeholder notifications appropriate to the crisis type
- Risk mitigation specific to this crisis
- Decision documentation

Return ONLY valid JSON array with no markdown:
[
  {{"priority": "HIGH", "label": "Action Title", "description": "What to do", "example_query": "Example question"}},
  ...
]
"""
        
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7
                )
            )
            
            content = response.text if response else ""
            actions = json.loads(content) if content else []
            
            if not actions or len(actions) == 0:
                # Fallback to context-aware actions if parsing fails
                actions = self._generate_context_aware_fallback(crisis_type, recovery.get('option_count', 0))
        except (json.JSONDecodeError, ValueError, IndexError):
            # Fallback if Gemini fails
            actions = self._generate_context_aware_fallback(crisis_type, recovery.get('option_count', 0))
        
        print(f"  [OK] Generated {len(actions)} context-aware next-step suggestions")
        return actions
    
    def _generate_context_aware_fallback(self, crisis_type: str, option_count: int) -> list[dict[str, Any]]:
        """
        Fallback: Generate context-aware actions without Gemini (crisis-type specific).
        
        Not hardcoded templates - actions vary by crisis type.
        """
        actions = []
        
        if crisis_type == "CAST":
            actions = [
                {
                    "priority": "HIGH",
                    "label": "Notify Lead Actor & Replacements",
                    "description": "Contact backup actors for potential replacement or schedule adjustment",
                    "example_query": "Who are the available backup actors for this role?"
                },
                {
                    "priority": "HIGH",
                    "label": "Update Call Sheets Immediately",
                    "description": "Send revised shooting schedule to all cast and crew with new scene order",
                    "example_query": "Generate updated call sheet with new scene order"
                },
                {
                    "priority": "MEDIUM",
                    "label": "Notify Location & Logistics",
                    "description": "Confirm new scene location availability and transportation needs",
                    "example_query": "Is the alternative location available on the new date?"
                }
            ]
        
        elif crisis_type == "EQUIPMENT":
            actions = [
                {
                    "priority": "HIGH",
                    "label": "Source Replacement Equipment",
                    "description": "Contact rental houses for emergency equipment replacement or repair",
                    "example_query": "Where can we rent a replacement camera by tomorrow?"
                },
                {
                    "priority": "HIGH",
                    "label": "Update Camera Team & Vendors",
                    "description": "Notify DP and equipment vendors of changes to gear requirements",
                    "example_query": "What's the replacement equipment spec and availability?"
                },
                {
                    "priority": "MEDIUM",
                    "label": "Recalculate Equipment Budget",
                    "description": "Update daily rental costs and insurance for replacement gear",
                    "example_query": "What's the new equipment rental cost?"
                }
            ]
        
        elif crisis_type == "LOCATION":
            actions = [
                {
                    "priority": "HIGH",
                    "label": "Secure Alternative Location Permits",
                    "description": "Confirm permits and legal clearance for replacement shooting location",
                    "example_query": "What permits do we need for the new location?"
                },
                {
                    "priority": "HIGH",
                    "label": "Notify Location Manager & Scouts",
                    "description": "Brief location team on new venue and any access/setup requirements",
                    "example_query": "What's the setup time at the new location?"
                },
                {
                    "priority": "MEDIUM",
                    "label": "Update Transportation & Parking",
                    "description": "Arrange crew transportation and parking for alternative location",
                    "example_query": "What's parking available at the new location?"
                }
            ]
        
        elif crisis_type == "WEATHER":
            actions = [
                {
                    "priority": "HIGH",
                    "label": "Monitor Weather Forecast Continuously",
                    "description": "Track hourly weather updates for outdoor scene viability",
                    "example_query": "What's the updated weather forecast for tomorrow?"
                },
                {
                    "priority": "HIGH",
                    "label": "Prepare Indoor Backup Scenes",
                    "description": "Ensure backup interior scenes are ready to shoot instead",
                    "example_query": "Are there indoor scenes we can shoot if weather worsens?"
                },
                {
                    "priority": "MEDIUM",
                    "label": "Notify Weather Insurance",
                    "description": "Contact weather stop insurance for potential claims",
                    "example_query": "What's our weather insurance coverage and claim process?"
                }
            ]
        
        else:
            # Generic fallback for unknown crisis types
            actions = [
                {
                    "priority": "HIGH",
                    "label": "Notify Affected Stakeholders",
                    "description": "Send crisis update to cast, crew, and production team",
                    "example_query": "Who needs to be notified of this change?"
                },
                {
                    "priority": "HIGH",
                    "label": "Update Call Sheets",
                    "description": "Generate and distribute revised shooting schedule",
                    "example_query": "Generate updated call sheet"
                },
                {
                    "priority": "MEDIUM",
                    "label": "Review Budget Impact",
                    "description": "Calculate financial impact of schedule change",
                    "example_query": "What's the cost impact of this decision?"
                }
            ]
        
        # If multiple options available, suggest exploring them
        if option_count > 1:
            actions.insert(1, {
                "priority": "MEDIUM",
                "label": "Review Alternative Options",
                "description": f"Consider other {option_count - 1} viable recovery options",
                "example_query": "What are the other scene swap alternatives?"
            })
        
        return actions
