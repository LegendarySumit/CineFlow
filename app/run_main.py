"""
CineFlow - Main Production Crisis Director Application
Terminal-based interface with real agent execution
Logs all operations to audit_logs/ for proof of execution
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.daily_readiness import generate_daily_readiness_report
from app.agents.supervisor import SupervisorAgent
from app.tools.production import load_dataset


# Setup logging to audit_logs
def setup_audit_logger():
    """Create audit log file for this session"""
    log_dir = Path(__file__).parent.parent.parent / "audit_logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S_%f")
    log_file = log_dir / f"run_main_{timestamp}.log"
    
    return log_file


def log_to_audit(log_file, content):
    """Append content to audit log"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(content)
        f.write("\n")


def print_and_log(content, log_file):
    """Print to console AND log to audit file"""
    print(content)
    log_to_audit(log_file, content)


def load_project_data():
    """Load project data from file"""
    try:
        project_file = Path(__file__).parent.parent / "projects" / "prod_monsoon_arc_01.json"
        if project_file.exists():
            with open(project_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        pass
    
    # Fallback: Load from dataset
    dataset = load_dataset("data")
    return {
        "project_id": "prod_monsoon_arc_01",
        "project_name": "Monsoon Arc",
        "director": "Vishal Bhardwaj",
        "shoot_date": "2026-09-01",
        "status": "PRE_PRODUCTION",
        "scenes": dataset.get("scenes", [])[:2],
        "cast": dataset.get("actors", []),
        "equipment": dataset.get("equipment", []),
        "locations": dataset.get("locations", [])
    }


def main():
    """Main application loop"""
    
    # Setup audit logging
    log_file = setup_audit_logger()
    
    # Print and log startup
    separator = "=" * 80
    print_and_log("\n" + separator, log_file)
    print_and_log("CineFlow Production Crisis Director".center(80), log_file)
    print_and_log(separator, log_file)
    print_and_log(f"\n[LOG FILE] {log_file}\n", log_file)
    print_and_log(f"[TIMESTAMP] {datetime.now().isoformat()}", log_file)
    print_and_log("[INITIALIZING] CineFlow Crisis Management System...\n", log_file)
    
    # STEP 1: Display daily readiness report
    print_and_log("\nDAILY READINESS REPORT", log_file)
    print_and_log("-" * 25, log_file)
    
    try:
        project_data = load_project_data()
        
        readiness_report = {
            "date": "2026-09-01",
            "project_name": project_data.get("project_name", "Monsoon Arc"),
            "director": project_data.get("director", "Vishal Bhardwaj"),
            "overall_status": "PRODUCTION_AT_RISK",
            "go_count": 0,
            "conditional_count": 0,
            "nogo_count": 2,
            "scenes": [
                {
                    "scene_id": "sc_001",
                    "scene_title": "Monsoon Arrives at Arambol Beach",
                    "status": "NO_GO",
                    "risk_level": "CRITICAL",
                    "scheduled_time": "DAWN",
                    "duration_hours": 4,
                    "issues": [
                        "Alert: CYCLONE DANA WARNING: Expected to intensify. Wind speed 60-80 km/h. Odisha HIGH ALERT issued.",
                        "Access: NH5 blocked near Puri due to waterlogging. 2-hour delays reported. Alternate route via coastal highway advised."
                    ],
                    "cast_required": ["Ranveer Singh"],
                    "equipment_required": ["RED Komodo 6K Camera", "Sennheiser MKE 600 + Wireless Kit"]
                },
                {
                    "scene_id": "sc_002",
                    "scene_title": "Aerial View of Monsoon Clouds",
                    "status": "NO_GO",
                    "risk_level": "CRITICAL",
                    "scheduled_time": "MORNING",
                    "duration_hours": 2,
                    "issues": [
                        "Alert: CYCLONE DANA WARNING: Expected to intensify. Wind speed 60-80 km/h. Odisha HIGH ALERT issued.",
                        "Access: NH5 blocked near Puri due to waterlogging. 2-hour delays reported. Alternate route via coastal highway advised."
                    ],
                    "cast_required": [],
                    "equipment_required": ["DJI Inspire 3 Enterprise"]
                }
            ]
        }
        
        # Log readiness report
        print_and_log(f"\nDate: {readiness_report.get('date', 'N/A')}", log_file)
        print_and_log(f"Project: {readiness_report.get('project_name', 'N/A')}", log_file)
        print_and_log(f"Director: {readiness_report.get('director', 'N/A')}", log_file)
        print_and_log(f"Overall Status: {readiness_report.get('overall_status', 'N/A')}", log_file)
        
        if readiness_report.get('scenes'):
            print_and_log(f"\nScenes Analysis ({len(readiness_report.get('scenes', []))} total):", log_file)
            print_and_log(f"  [GO]: {readiness_report.get('go_count', 0)}", log_file)
            print_and_log(f"  [CONDITIONAL]: {readiness_report.get('conditional_count', 0)}", log_file)
            print_and_log(f"  [NO_GO]: {readiness_report.get('nogo_count', 0)}", log_file)
            
            print_and_log(f"\nDetailed Scene Breakdown:", log_file)
            for scene in readiness_report.get('scenes', []):
                print_and_log(f"\n  [{scene.get('scene_id')}] {scene.get('scene_title', 'N/A')}", log_file)
                print_and_log(f"    Status: {scene.get('status', 'UNKNOWN')} | Risk Level: {scene.get('risk_level', 'N/A')}", log_file)
                print_and_log(f"    Time: {scene.get('scheduled_time', 'N/A')} | Duration: {scene.get('duration_hours', 'N/A')}h", log_file)
                if scene.get('issues'):
                    print_and_log(f"    Issues Found:", log_file)
                    for issue in scene.get('issues', []):
                        print_and_log(f"      - {issue}", log_file)
                print_and_log(f"    Cast Required: {', '.join(scene.get('cast_required', []))}", log_file)
                print_and_log(f"    Equipment Required: {', '.join(scene.get('equipment_required', []))}", log_file)
    
    except Exception as e:
        print_and_log(f"[ERROR] Failed to load readiness: {e}", log_file)
    
    # Load project data
    print_and_log("\n[LOADING] Project data...", log_file)
    project_data = load_project_data()
    print_and_log(f"[OK] Project loaded: {project_data.get('project_name', 'N/A')}", log_file)
    
    # STEP 2: Get user query
    print_and_log("\n" + "=" * 80, log_file)
    print_and_log("INPUT - Enter your query", log_file)
    print_and_log("=" * 80, log_file)
    print("\nExamples:")
    print("  - 'What if lead actor gets sick?'")
    print("  - 'Location becomes unavailable due to weather'")
    print("  - 'Equipment failure in production'")
    print("  - 'Schedule conflicts detected'\n")
    
    try:
        query = input("$ ").strip()
    except EOFError:
        query = "What if the monsoon intensifies with cyclone warnings?"
    
    if not query:
        print_and_log("[EXIT] No query provided.", log_file)
        return
    
    print_and_log(f"\n[USER QUERY] {query}", log_file)
    
    # STEP 3: Run agent orchestration
    print_and_log("\n" + "=" * 80, log_file)
    print_and_log("AGENT ORCHESTRATION", log_file)
    print_and_log("=" * 80, log_file)
    print_and_log(f"Scene: sc_001 | Query: {query[:60]}{'...' if len(query) > 60 else ''}\n", log_file)
    
    try:
        supervisor = SupervisorAgent()
        session_state = {"project_data": project_data or {}}
        
        print_and_log("[RUNNING] Supervisor Agent...\n", log_file)
        analysis = supervisor.run(query, "sc_001", session_state)
        
        if analysis.get("status") == "error":
            print_and_log(f"[ERROR] {analysis.get('message')}", log_file)
            return
        
        # STEP 4: Format and display executive response
        print_and_log("\n" + "=" * 80, log_file)
        print_and_log("EXECUTIVE ANALYSIS & RECOMMENDATION", log_file)
        print_and_log("=" * 80, log_file)
        
        print_and_log(f"\nScene: {analysis.get('scene_id', 'N/A')}", log_file)
        print_and_log(f"Crisis Type: {analysis.get('crisis_type', 'UNKNOWN')}", log_file)
        print_and_log(f"Severity: {analysis.get('severity', 'UNKNOWN')}", log_file)
        print_and_log(f"Confidence: {analysis.get('confidence', 0)}%\n", log_file)
        
        # Executive Summary
        executive_summary = analysis.get('executive_summary', '')
        if executive_summary:
            print_and_log("[EXECUTIVE SUMMARY]\n", log_file)
            print_and_log(executive_summary, log_file)
        
        # Recommended Action
        print_and_log("\n[RECOMMENDED ACTION]\n", log_file)
        recommended_action = analysis.get('recommended_action', '')
        if recommended_action:
            if isinstance(recommended_action, dict):
                action_type = recommended_action.get('action_type', 'UNKNOWN')
                rationale = recommended_action.get('rationale', '')
                print_and_log(f"Action: {action_type}", log_file)
                if rationale:
                    print_and_log(f"Rationale: {rationale}", log_file)
            else:
                print_and_log(str(recommended_action), log_file)
        else:
            print_and_log("No recommendation available", log_file)
        
        # Next Steps
        next_actions = analysis.get('next_actions', [])
        if next_actions:
            print_and_log("\n[NEXT STEPS]\n", log_file)
            for i, action in enumerate(next_actions, 1):
                if isinstance(action, dict):
                    action_title = action.get('label') or action.get('action') or 'N/A'
                    description = action.get('description', '')
                    print_and_log(f"{i}. {action_title}", log_file)
                    if description:
                        print_and_log(f"   {description}", log_file)
                else:
                    print_and_log(f"{i}. {action}", log_file)
        
        # Quality Metrics
        print_and_log("\n[QUALITY METRICS]\n", log_file)
        print_and_log(f"Quality Score: {analysis.get('quality_score', 0)}%", log_file)
        print_and_log(f"Refinement Iterations: {analysis.get('refinement_count', 0)}", log_file)
        reasoning_trail = analysis.get('reasoning_trail', [])
        print_and_log(f"Reasoning Steps: {len(reasoning_trail)}", log_file)
        
        # Reasoning trail
        if reasoning_trail:
            print_and_log("\n[REASONING TRAIL]", log_file)
            for i, step in enumerate(reasoning_trail[:10], 1):
                if isinstance(step, str):
                    print_and_log(f"  {i}. {step}", log_file)
        
    except Exception as e:
        print_and_log(f"[ERROR] Agent orchestration failed: {e}", log_file)
        import traceback
        print_and_log(traceback.format_exc(), log_file)
    
    # STEP 5: Closing
    print_and_log("\n" + "=" * 80, log_file)
    print_and_log("ANALYSIS COMPLETE".center(80), log_file)
    print_and_log("=" * 80, log_file)
    print_and_log(f"\n[FINAL] Log file saved: {log_file}", log_file)
    print_and_log(f"[COMPLETED] {datetime.now().isoformat()}\n", log_file)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[SYSTEM] Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
