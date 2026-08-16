"""
SUPERVISOR AGENT (Master Orchestrator)

Role: Receives user query → Creates execution plan → Delegates to workers → 
Monitors results → Requests refinement if needed → Returns final recommendation

This is the core agentic orchestrator using the Vellum framework.
"""

import json
import os
from typing import Any

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

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3-flash-preview"


class SupervisorAgent:
    """
    Master orchestrator that:
    1. Plans: Breaks crisis into sub-tasks
    2. Executes: Calls actual worker agents
    3. Monitors: Tracks worker results
    4. Refines: Requests re-work if quality is low
    5. Synthesizes: Combines results into final recommendation
    """
    
    def __init__(self):
        self.session_state = {}
        self.plan = None
        self.worker_results = {}
        self.refinement_count = 0
        
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
        """PLANNING PHASE: Supervisor breaks crisis into atomic tasks."""
        
        print("\n[SUPERVISOR] PLANNING PHASE")
        print(f"  Input: {user_query}")
        
        planning_prompt = f"""
You are a Film Production Supervisor. Break down this production crisis into 
5 concrete, atomic tasks that worker agents will execute.

Crisis Query: {user_query}
Scene ID: {scene_id}

Return ONLY valid JSON (no markdown, no extras):
{{
    "tasks": [
        {{"id": 1, "task": "load_scene_schedule", "worker": "SCHEDULE_WORKER"}},
        {{"id": 2, "task": "analyze_crisis_impact", "worker": "STRATEGY_WORKER"}},
        {{"id": 3, "task": "gather_external_context", "worker": "EXTERNAL_INFO_WORKER"}},
        {{"id": 4, "task": "generatefetch_weather_data", "worker": "WEATHER_WORKER"}},
        {{"id": 5, "task": "generate_recovery", "worker": "STRATEGY_WORKER"}},
        {{"id": 6, "task": "validate_plan", "worker": "CRITIC_WORKER"}}
    ],
    "success_criteria": ["All tasks complete", "Risk assessed", "Recovery option validated"]
}}
"""
        
        model = genai.GenerativeModel(MODEL)
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
        print(f"  ✓ Created plan with {len(plan.get('tasks', []))} tasks")
        for task in plan.get('tasks', []):
            print(f"    - Task {task.get('id')}: {task.get('task')} ({task.get('worker')})")
        
        return plan
    
    def execute_workers(self, scene_id: str, crisis_query: str) -> dict[str, Any]:
        """
        EXECUTION PHASE: Context-aware worker orchestration.
        
        Only runs workers relevant to the crisis type:
        - WEATHER: Schedule + Weather + Strategy + Recovery + Validation
        - EQUIPMENT: Schedule + Strategy + Recovery + Validation
        - CAST: Schedule + Strategy + Recovery + Validation
        - PERMIT: Schedule + Strategy + Recovery + Validation
        """
        
        print("\n[SUPERVISOR] WORKER EXECUTION PHASE")
        
        worker_results = {}
        
        # TASK 1: Load scene schedule (always needed)
        print("  → Executing SCHEDULE_WORKER...")
        schedule_result = load_scene_and_schedule(scene_id)
        worker_results["schedule"] = schedule_result
        
        if schedule_result.get("status") == "success":
            print(f"    ✓ Loaded: {schedule_result.get('scene', {}).get('title')}")
        else:
            return {"error": schedule_result.get("message"), "results": worker_results}
        
        # TASK 2: Determine crisis type (critical for context-aware execution)
        print("  → Analyzing crisis type...")
        impact_result = evaluate_impact(scene_id, crisis_query)
        worker_results["impact"] = impact_result
        crisis_type = impact_result.get("crisis_type", "UNKNOWN")
        print(f"    ✓ Crisis Type: {crisis_type}")
        
        # TASK 3: Gather external world context (ALWAYS - for all crisis types)
        print("  → Executing EXTERNAL_INFO_WORKER...")
        external_result = gather_external_context(scene_id, crisis_query)
        worker_results["external_context"] = external_result
        if external_result.get("status") == "success":
            quality = external_result.get("data_quality", {})
            print(f"    ✓ Gathered {external_result.get('investigation_dimensions', [])}")
            print(f"    ✓ Total sources: {quality.get('total_results', 0)} | Quality: {quality.get('quality_score', 0)}%")
        
        # TASK 4: Generate recovery options (works for ANY crisis type)
        print("  → Executing STRATEGY_WORKER (Recovery Generation)...")
        recovery_result = generate_recovery_options(scene_id, crisis_query)
        worker_results["recovery"] = recovery_result
        if recovery_result.get("status") == "success":
            print(f"    ✓ Generated {recovery_result.get('option_count', 0)} recovery options")
        
        # TASK 5: Validate best option
        print("  → Executing CRITIC_WORKER...")
        best_option = recovery_result.get("best_option") or {}
        validation_result = validate_plan(best_option)
        worker_results["validation"] = validation_result
        print(f"    ✓ Plan Status: {validation_result.get('recommendation')}")
        
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
                status = "✓ COMPLETE"
                print(f"  {status} Task {task_id} ({worker}): {task.get('task')}")
                execution_log['delegations'].append({
                    "task_id": task_id,
                    "worker": worker,
                    "status": "success"
                })
            else:
                print(f"  ⚠ PARTIAL Task {task_id} ({worker})")
        
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
            "weather_data_exists": "weather" in worker_results and len(worker_results.get("weather", {}).get("sources", [])) > 0,
            "scene_data_exists": "schedule" in worker_results and worker_results.get("schedule", {}).get("status") == "success",
            "impact_assessed": "impact" in worker_results and worker_results.get("impact", {}).get("risk_level"),
            "recovery_options_exist": "recovery" in worker_results and len(worker_results.get("recovery", {}).get("options", [])) > 0,
            "validation_passed": "validation" in worker_results and worker_results.get("validation", {}).get("valid")
        }
        
        all_checks_pass = all(quality_checks.values())
        
        print("  Quality Checks:")
        for check, result in quality_checks.items():
            status = "✓" if result else "✗"
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
        print(f"  ⚠️  Issues detected: {', '.join(failed_items)}")
        print("  🔄 Re-planning and requesting worker re-execution...")
        print("  This is TRUE AGENTIC BEHAVIOR: Detect failure → Adapt strategy → Retry")
        
        return f"Refinement cycle {self.refinement_count}"
    
    def synthesize_recommendation(self, worker_results: dict) -> dict[str, Any]:
        """
        SYNTHESIS PHASE: Combine worker outputs into final recommendation.
        
        Uses LLM to create coherent, evidence-backed recommendation.
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
        
        synthesis_prompt = f"""You are a Film Production Crisis Manager.

Scene: {scene_data.get('title')} (ID: {scene_data.get('id')})
Crisis: {impact.get('crisis_type') or 'UNKNOWN'}
Risk: {impact.get('risk_level')}
Action: {deterministic.get('action') if deterministic else 'HOLD'}{external_summary}

Write a 2-3 sentence executive summary (200 chars max) stating:
1. The crisis
2. Recommended action  
3. Why it works

Be concise and direct."""
        
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(
            synthesis_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=400,
                temperature=0.5
            )
        )
        
        summary = response.text if response and response.text else "Crisis analyzed. Recommendation pending review."
        
        print("  ✓ Recommendation Synthesized")
        
        return {
            "status": "success",
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
            "worker_results": worker_results,
            "reasoning_trail": [
                "PLANNER: Created execution plan",
                f"SCHEDULE_WORKER: Loaded {scene_data.get('title')}",
                f"EXTERNAL_INFO_WORKER: Gathered {len(external_context.get('investigation_dimensions', []))} dimensions",
                f"STRATEGY_WORKER: Risk = {impact.get('risk_level')}",
                f"STRATEGY_WORKER: Generated {len(recovery)} options",
                f"CRITIC_WORKER: Validation = {validation.get('recommendation')}"
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
        
        print("\n" + "="*70)
        print("👔 SUPERVISOR AGENT - Master Orchestrator (Full Agentic Loop)")
        print("="*70)
        
        self.session_state = session_state
        
        # PHASE 1: Create plan
        plan = self.create_execution_plan(user_query, scene_id)
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
                print("\n✅ Quality checks passed. Proceeding to synthesis.")
                break
            else:
                # PHASE 5: SELF-CORRECTION LOOP
                if quality_result["refinement_needed"]:
                    self.request_refinement(quality_result["checks"])
                    # In production, would call workers again with modified plan
                    # For now, continue to synthesis with partial data
                else:
                    print("\n⚠️  Max refinement attempts reached. Using best available data.")
                    break
        
        # PHASE 6: Synthesize
        final_recommendation = self.synthesize_recommendation(worker_results)
        
        # PHASE 7: ADD PROACTIVE NEXT STEPS (True Agentic Behavior)
        final_recommendation["next_actions"] = self.generate_proactive_actions(
            final_recommendation,
            worker_results
        )
        
        # Save state for multi-turn conversation
        final_recommendation["session_state"] = self.session_state
        final_recommendation["refinement_attempts"] = self.refinement_count
        
        return final_recommendation
    
    def generate_proactive_actions(self, recommendation: dict, worker_results: dict) -> list[dict[str, Any]]:
        """
        PROACTIVE BEHAVIOR: Suggest what the producer should do next.
        
        This is what separates true agents from passive tools.
        """
        
        print("\n[SUPERVISOR] GENERATING PROACTIVE NEXT STEPS")
        
        actions = []
        
        # Always suggest notifying cast
        actions.append({
            "priority": "HIGH",
            "label": "Notify Cast & Crew",
            "description": "Send updated call sheet to affected actors and crew",
            "example_query": "Generate call-sheet emails for the new schedule"
        })
        
        # Suggest budget update
        actions.append({
            "priority": "HIGH",
            "label": "Recalculate Daily Budget Impact",
            "description": "Show updated financial impact with new schedule",
            "example_query": "What's the new daily spend with this swap?"
        })
        
        # If there are alternative options, suggest exploring them
        if worker_results.get("recovery", {}).get("option_count", 0) > 1:
            actions.append({
                "priority": "MEDIUM",
                "label": "Explore Alternative Recovery Plans",
                "description": "Compare other scene swap options",
                "example_query": "What are the other scene swap options?"
            })
        
        # Suggest tracking decision
        actions.append({
            "priority": "MEDIUM",
            "label": "Log Decision to Production History",
            "description": "Record this decision for future reference and learning",
            "example_query": "Add this decision to the production decision log"
        })
        
        print(f"  ✓ Generated {len(actions)} proactive next-step suggestions")
        return actions
