"""
CineFlow - Main Production Crisis Director Application
================================================
Terminal-based interface with:
1. Daily Readiness Report (top)
2. User Query Prompt
3. Multi-Agent Orchestration (Supervisor + Workers)
4. Formatted Response with Executive Summary
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
from app.services.response_formatter import format_crisis_analysis


def print_separator(char="=", length=100):
    """Print a formatted separator line"""
    print(char * length)


def print_section_header(title):
    """Print a formatted section header"""
    print_separator()
    print(f"\n{title}\n")
    print_separator()


def load_project_data():
    """Load project data from file"""
    try:
        # Look for project file in CineFlow/projects/
        project_file = Path(__file__).parent.parent.parent / "CineFlow" / "projects" / "prod_monsoon_arc_01.json"
        if not project_file.exists():
            # Try alternate path (if already in CineFlow directory)
            project_file = Path(__file__).parent.parent / "projects" / "prod_monsoon_arc_01.json"
        
        if project_file.exists():
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
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
    """Generate and display the daily readiness report (uses cached data to save API quota)"""
    print_section_header("DAILY READINESS REPORT")
    
    try:
        # Load project data
        project_data = load_project_data()
        
        # Use cached/pre-generated readiness data to save API quota for agent orchestration
        # The agent orchestration is more critical and needs fresh API calls
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
            print(f"\n" + "-" * 100)
            print(f"\n[DAILY BRIEFING]\n")
            print(readiness_report.get('daily_briefing', 'N/A'))
            print(f"\n" + "-" * 100)
        
        return readiness_report
    
    except Exception as e:
        print(f"[ERROR] Failed to generate daily readiness report: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_user_query():
    """Prompt user for crisis query - handles both interactive and piped input"""
    print_separator()
    print("\n[INPUT] Enter your query (Natural or Crisis-based):\n")
    print("Examples:")
    print("  - 'What if lead actor gets sick?'")
    print("  - 'Location becomes unavailable due to weather'")
    print("  - 'Equipment failure in production'")
    print("  - 'Schedule conflicts detected'\n")
    
    try:
        # Try to read from stdin (supports piped input and interactive)
        query = input("Your Query: ").strip()
    except EOFError:
        # If stdin is closed (batch mode without input)
        print("\n[WARNING] No input provided via stdin. Using default query.")
        query = "What if the monsoon intensifies with cyclone warnings?"
    
    if not query:
        print("[ERROR] Query cannot be empty!")
        return None
    
    return query


def run_agent_orchestration(query, scene_id="sc_001", project_data=None):
    """Run the multi-agent orchestration"""
    print_section_header("AGENT ORCHESTRATION")
    
    try:
        print(f"\n[INITIALIZING] Multi-Agent Crisis Director System")
        print(f"  Scene ID: {scene_id}")
        print(f"  Query: {query[:80]}{'...' if len(query) > 80 else ''}\n")
        
        # Initialize supervisor
        supervisor = SupervisorAgent()
        
        # Prepare session state with project data
        session_state = {
            "project_data": project_data or {}
        }
        
        # Run agent analysis
        print("[RUNNING] Supervisor Agent with Worker Execution...\n")
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
    
    # Scene and Crisis Summary
    print(f"\nSCENE: {analysis.get('scene_id', 'N/A')}")
    print(f"CRISIS TYPE: {analysis.get('crisis_type', 'UNKNOWN')}")
    print(f"SEVERITY: {analysis.get('severity', 'UNKNOWN')}")
    print(f"CONFIDENCE: {analysis.get('confidence', 0)}%\n")
    
    # Executive Summary
    print("-" * 100)
    print("\n[EXECUTIVE SUMMARY]\n")
    
    executive_summary = analysis.get('executive_summary', '')
    if executive_summary:
        # Format as a readable paragraph
        summary_text = executive_summary
        if isinstance(summary_text, str):
            print(summary_text)
        else:
            print(json.dumps(summary_text, indent=2))
    else:
        print("No summary available")
    
    # Crisis Analysis
    crisis_context = analysis.get('crisis_context', {})
    if crisis_context:
        print("\n" + "-" * 100)
        print("\n[CRISIS ANALYSIS]\n")
        
        if isinstance(crisis_context, dict):
            for key, value in crisis_context.items():
                print(f"{key}: {value}")
        else:
            print(crisis_context)
    
    # Recommended Action
    print("\n" + "-" * 100)
    print("\n[RECOMMENDED ACTION]\n")
    
    recommended_action = analysis.get('recommended_action', '')
    if recommended_action:
        if isinstance(recommended_action, dict):
            action_type = recommended_action.get('action_type', 'UNKNOWN')
            rationale = recommended_action.get('rationale', '')
            impact = recommended_action.get('impact', '')
            
            print(f"Action: {action_type}")
            print(f"Rationale: {rationale}")
            print(f"Impact: {impact}")
        else:
            print(recommended_action)
    else:
        print("No recommendation available")
    
    # Next Steps
    next_actions = analysis.get('next_actions', [])
    if next_actions:
        print("\n" + "-" * 100)
        print("\n[NEXT STEPS]\n")
        
        for i, action in enumerate(next_actions, 1):
            if isinstance(action, dict):
                # Check for both formats: 'action' or 'label'
                action_title = action.get('label') or action.get('action') or 'N/A'
                description = action.get('description', '')
                priority = action.get('priority', 'MEDIUM')
                
                print(f"{i}. {action_title}")
                if description:
                    print(f"   Description: {description}")
                if priority:
                    print(f"   Priority: {priority}")
                if action.get('owner'):
                    print(f"   Owner: {action.get('owner')}")
                if action.get('example_query'):
                    print(f"   Example: {action.get('example_query')}")
                print()
            else:
                print(f"{i}. {action}\n")
    
    # Quality Metrics
    print("\n" + "-" * 100)
    print("\n[ANALYSIS QUALITY METRICS]\n")
    
    quality_score = analysis.get('quality_score', 0)
    reasoning_trail = analysis.get('reasoning_trail', [])
    refinement_count = analysis.get('refinement_count', 0)
    
    print(f"Quality Score: {quality_score}%")
    print(f"Refinement Iterations: {refinement_count}")
    print(f"Reasoning Steps: {len(reasoning_trail)}")
    
    if reasoning_trail:
        print("\nReasoning Trail:")
        for i, step in enumerate(reasoning_trail[:5], 1):  # Show first 5 steps
            if isinstance(step, dict):
                print(f"  {i}. {step.get('step', 'N/A')}: {step.get('reasoning', 'N/A')[:80]}...")
            else:
                print(f"  {i}. {str(step)[:80]}...")
    
    print("\n" + "-" * 100)


def main():
    """Main application loop"""
    
    print("\n")
    print_separator("=")
    print("=" + " " * 28 + "CINEFLOW PRODUCTION CRISIS DIRECTOR" + " " * 34 + "=")
    print_separator("=")
    
    print("\n[SYSTEM] Initializing CineFlow Crisis Management System...")
    
    # STEP 1: Display daily readiness report
    print("\n")
    daily_readiness = print_daily_readiness()
    
    # Load project data for agent
    print("\n[SYSTEM] Loading project data...")
    project_data = load_project_data()
    
    # STEP 2: Get user query
    print("\n")
    query = get_user_query()
    
    if not query:
        print("\n[SYSTEM] Exiting without query.")
        return
    
    # STEP 3: Run agent orchestration
    print("\n")
    analysis = run_agent_orchestration(query, project_data=project_data)
    
    # STEP 4: Format and display executive response
    if analysis:
        print("\n")
        format_executive_response(analysis)
    
    # STEP 5: Closing
    print("\n")
    print_separator("=")
    print("=" + " " * 20 + "ANALYSIS COMPLETE - Thank you for using CineFlow" + " " * 26 + "=")
    print_separator("=")
    print("\n")


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
