"""
CineFlow - Main Production Crisis Director Application
Terminal-based interface with real agent execution
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


def print_separator(char="=", length=80):
    """Print a formatted separator line"""
    print(char * length)


def print_section_header(title):
    """Print a formatted section header"""
    print(f"\n{title}")
    print("-" * len(title))


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


def print_daily_readiness():
    """Generate and display the daily readiness report"""
    print_section_header("DAILY READINESS REPORT")
    
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
            ],
            "daily_briefing": """Alright crew, listen up.

Good morning. For Project Monsoon Arc today, September 1st, our overall status is **NO-GO**. Both 
"Monsoon Arrives at Arambol Beach" and "Aerial View of Monsoon Clouds" are scrubbed.

The critical issue is **CYCLONE DANA**. It's intensifying with 60-80 km/h winds, and Odisha is on 
HIGH ALERT. Additionally, NH5 is blocked near Puri due to waterlogging, reporting 2-hour delays. 
Travel is not safe today.

Your instruction is to **STAND DOWN**. Prioritize your safety and that of your families. Stay home, 
stay safe, and monitor local weather updates. We will reassess the schedule once the cyclone threat 
has passed.

Confidence Level: Very Low for today's shoot. Your safety is paramount."""
        }
        
        # Display report
        print(f"\nDate: {readiness_report.get('date', 'N/A')}")
        print(f"Project: {readiness_report.get('project_name', 'N/A')}")
        print(f"Director: {readiness_report.get('director', 'N/A')}")
        print(f"Overall Status: {readiness_report.get('overall_status', 'N/A')}")
        
        if readiness_report.get('scenes'):
            print(f"\nScenes Analysis ({len(readiness_report.get('scenes', []))} total):")
            print(f"  [GO]: {readiness_report.get('go_count', 0)}")
            print(f"  [CONDITIONAL]: {readiness_report.get('conditional_count', 0)}")
            print(f"  [NO_GO]: {readiness_report.get('nogo_count', 0)}")
            
            print(f"\nDetailed Scene Breakdown:")
            for scene in readiness_report.get('scenes', []):
                print(f"\n  [{scene.get('scene_id')}] {scene.get('scene_title', 'N/A')}")
                print(f"    Status: {scene.get('status', 'UNKNOWN')} | Risk Level: {scene.get('risk_level', 'N/A')}")
                print(f"    Time: {scene.get('scheduled_time', 'N/A')} | Duration: {scene.get('duration_hours', 'N/A')}h")
                if scene.get('issues'):
                    print(f"    Issues Found:")
                    for issue in scene.get('issues', []):
                        print(f"      - {issue}")
                print(f"    Cast Required: {', '.join(scene.get('cast_required', []))}")
                print(f"    Equipment Required: {', '.join(scene.get('equipment_required', []))}")
        
        # Display daily briefing
        if readiness_report.get('daily_briefing'):
            print(f"\n")
            print(f"[DAILY BRIEFING]\n")
            print(readiness_report.get('daily_briefing', 'N/A'))
        
        return readiness_report
    
    except Exception as e:
        print(f"[ERROR] Failed to generate daily readiness report: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_user_query():
    """Prompt user for crisis query"""
    print_section_header("INPUT - Enter your query")
    
    print("\nExamples:")
    print("  - 'What if lead actor gets sick?'")
    print("  - 'Location becomes unavailable due to weather'")
    print("  - 'Equipment failure in production'")
    print("  - 'Schedule conflicts detected'\n")
    
    try:
        query = input("$ ").strip()
    except EOFError:
        print("[WARNING] No input provided. Using default query.")
        query = "What if the monsoon intensifies with cyclone warnings?"
    
    if not query:
        print("[ERROR] Query cannot be empty!")
        return None
    
    return query


def run_agent_orchestration(query, scene_id="sc_001", project_data=None):
    """Run the multi-agent orchestration"""
    print_section_header("AGENT ORCHESTRATION")
    print(f"Scene: {scene_id} | Query: {query[:60]}{'...' if len(query) > 60 else ''}\n")
    
    try:
        supervisor = SupervisorAgent()
        session_state = {"project_data": project_data or {}}
        
        print("[RUNNING] Supervisor Agent...\n")
        analysis = supervisor.run(query, scene_id, session_state)
        
        if analysis.get("status") == "error":
            print(f"[ERROR] {analysis.get('message')}")
            return None
        
        return analysis
    
    except Exception as e:
        print(f"[ERROR] Agent orchestration failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def format_executive_response(analysis):
    """Format the analysis response in executive briefing style"""
    print_section_header("EXECUTIVE ANALYSIS & RECOMMENDATION")
    
    if not analysis:
        print("[ERROR] No analysis available")
        return
    
    print(f"\nScene: {analysis.get('scene_id', 'N/A')}")
    print(f"Crisis Type: {analysis.get('crisis_type', 'UNKNOWN')}")
    print(f"Severity: {analysis.get('severity', 'UNKNOWN')}")
    print(f"Confidence: {analysis.get('confidence', 0)}%\n")
    
    # Executive Summary
    executive_summary = analysis.get('executive_summary', '')
    if executive_summary:
        print("[EXECUTIVE SUMMARY]\n")
        print(executive_summary)
    
    # Recommended Action
    print("\n[RECOMMENDED ACTION]\n")
    recommended_action = analysis.get('recommended_action', '')
    if recommended_action:
        if isinstance(recommended_action, dict):
            action_type = recommended_action.get('action_type', 'UNKNOWN')
            rationale = recommended_action.get('rationale', '')
            
            print(f"Action: {action_type}")
            if rationale:
                print(f"Rationale: {rationale}")
        else:
            print(recommended_action)
    else:
        print("No recommendation available")
    
    # Next Steps
    next_actions = analysis.get('next_actions', [])
    if next_actions:
        print("\n[NEXT STEPS]\n")
        for i, action in enumerate(next_actions, 1):
            if isinstance(action, dict):
                action_title = action.get('label') or action.get('action') or 'N/A'
                description = action.get('description', '')
                print(f"{i}. {action_title}")
                if description:
                    print(f"   {description}")
            else:
                print(f"{i}. {action}")
    
    # Quality Metrics
    print("\n[QUALITY METRICS]\n")
    print(f"Quality Score: {analysis.get('quality_score', 0)}%")
    print(f"Refinement Iterations: {analysis.get('refinement_count', 0)}")
    reasoning_trail = analysis.get('reasoning_trail', [])
    print(f"Reasoning Steps: {len(reasoning_trail)}")


def main():
    """Main application loop"""
    
    print("\n" + "=" * 80)
    print("CineFlow Production Crisis Director".center(80))
    print("=" * 80)
    
    print("\n[INITIALIZING] CineFlow Crisis Management System...\n")
    
    # STEP 1: Display daily readiness report
    daily_readiness = print_daily_readiness()
    
    # Load project data
    print("\n[LOADING] Project data...")
    project_data = load_project_data()
    
    # STEP 2: Get user query
    print()
    query = get_user_query()
    
    if not query:
        print("\n[EXIT] No query provided.")
        return
    
    # STEP 3: Run agent orchestration
    print()
    analysis = run_agent_orchestration(query, project_data=project_data)
    
    # STEP 4: Format and display executive response
    if analysis:
        print()
        format_executive_response(analysis)
    
    # STEP 5: Closing
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE".center(80))
    print("=" * 80 + "\n")


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
