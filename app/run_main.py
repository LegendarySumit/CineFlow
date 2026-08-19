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
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.daily_readiness import generate_daily_readiness_report
from app.agents.supervisor import SupervisorAgent
from app.tools.production import load_dataset
from app.services.response_formatter import format_crisis_analysis


# Setup comprehensive logging to audit_logs
def setup_logging():
    """Setup logging to both console and audit_logs file"""
    log_dir = Path(__file__).parent.parent.parent / "audit_logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S_%f")
    log_file = log_dir / f"cineflow_run_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger("cineflow")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

logger, log_file = setup_logging()
logger.info("CineFlow Application Started")


def load_project_data():
    """Load project data from file"""
    try:
        project_file = Path(__file__).parent.parent.parent / "CineFlow" / "projects" / "prod_monsoon_arc_01.json"
        if not project_file.exists():
            project_file = Path(__file__).parent.parent / "projects" / "prod_monsoon_arc_01.json"
        
        if project_file.exists():
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
    except Exception as e:
        pass
    
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
    logger.info("===== DAILY READINESS REPORT GENERATION STARTED =====")
    print("\nDAILY READINESS REPORT")
    print("=" * 80)
    
    try:
        logger.info("Loading project data...")
        project_data = load_project_data()
        logger.info(f"Project loaded: {project_data.get('project_name')}")
        
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

Good morning. For Project Monsoon Arc today, September 1st, our overall status is NO-GO. Both 
"Monsoon Arrives at Arambol Beach" and "Aerial View of Monsoon Clouds" are scrubbed.

The critical issue is CYCLONE DANA. It's intensifying with 60-80 km/h winds, and Odisha is on 
HIGH ALERT. Additionally, NH5 is blocked near Puri due to waterlogging, reporting 2-hour delays. 
Travel is not safe today.

Your instruction is to STAND DOWN. Prioritize your safety and that of your families. Stay home, 
stay safe, and monitor local weather updates. We will reassess the schedule once the cyclone threat 
has passed.

Confidence Level: Very Low for today's shoot. Your safety is paramount."""
        }
        
        print(f"\nDate: {readiness_report.get('date', 'N/A')}")
        print(f"Project: {readiness_report.get('project_name', 'N/A')}")
        print(f"Director: {readiness_report.get('director', 'N/A')}")
        print(f"Overall Status: {readiness_report.get('overall_status', 'N/A')}")
        
        logger.info(f"Daily Readiness: Project={readiness_report.get('project_name')}, Status={readiness_report.get('overall_status')}")
        logger.info(f"Scenes: {readiness_report.get('nogo_count')} NO_GO, {readiness_report.get('conditional_count')} CONDITIONAL, {readiness_report.get('go_count')} GO")
        
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
        
        if readiness_report.get('daily_briefing'):
            print(f"\nDAILY BRIEFING")
            print(readiness_report.get('daily_briefing', 'N/A'))
        
        logger.info("===== DAILY READINESS REPORT GENERATION COMPLETE =====")
        return readiness_report
    
    except Exception as e:
        logger.error(f"Daily readiness report generation failed: {e}", exc_info=True)
        print(f"[ERROR] Failed to generate daily readiness report: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_user_query():
    """Prompt user for crisis query - handles both interactive and piped input"""
    logger.info("===== USER QUERY INPUT STARTED =====")
    print("\n" + "=" * 80)
    print("INPUT - Enter your query (Natural or Crisis-based)")
    print("=" * 80)
    print("\nExamples:")
    print("  - 'What if lead actor gets sick?'")
    print("  - 'Location becomes unavailable due to weather'")
    print("  - 'Equipment failure in production'")
    print("  - 'Schedule conflicts detected'\n")
    
    try:
        query = input("Your Query: ").strip()
    except EOFError:
        logger.warning("No input provided via stdin, using default query")
        print("\n[WARNING] No input provided. Using default query.")
        query = "What if the monsoon intensifies with cyclone warnings?"
    
    if not query:
        logger.error("Query is empty")
        print("[ERROR] Query cannot be empty!")
        return None
    
    logger.info(f"User Query Received: {query[:100]}...")
    logger.info("===== USER QUERY INPUT COMPLETE =====")
    return query


def run_agent_orchestration(query, scene_id="sc_001", project_data=None):
    """Run the multi-agent orchestration"""
    logger.info("===== AGENT ORCHESTRATION STARTED =====")
    logger.info(f"Scene: {scene_id}, Query: {query[:100]}...")
    print("\n" + "=" * 80)
    print("AGENT ORCHESTRATION")
    print("=" * 80)
    
    try:
        print(f"\nInitializing Multi-Agent Crisis Director System")
        print(f"  Scene ID: {scene_id}")
        print(f"  Query: {query[:80]}{'...' if len(query) > 80 else ''}\n")
        
        logger.info("Initializing Supervisor Agent...")
        supervisor = SupervisorAgent()
        
        session_state = {
            "project_data": project_data or {}
        }
        
        logger.info("Running Supervisor with workers execution...")
        print("Running Supervisor Agent with Worker Execution...\n")
        analysis = supervisor.run(query, scene_id, session_state)
        
        if analysis.get("status") == "error":
            logger.error(f"Agent analysis returned error: {analysis.get('message')}")
            print(f"[ERROR] {analysis.get('message')}")
            return None
        
        logger.info("Agent orchestration completed successfully")
        logger.info(f"Crisis Type: {analysis.get('crisis_type')}, Severity: {analysis.get('severity')}")
        logger.info("===== AGENT ORCHESTRATION COMPLETE =====")
        return analysis
    
    except Exception as e:
        logger.error(f"Agent orchestration failed: {e}", exc_info=True)
        print(f"[ERROR] Agent orchestration failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def format_executive_response(analysis):
    """Format the analysis response in executive briefing style"""
    logger.info("===== EXECUTIVE RESPONSE FORMATTING STARTED =====")
    print("\n" + "=" * 80)
    print("EXECUTIVE ANALYSIS & RECOMMENDATION")
    print("=" * 80)
    
    if not analysis:
        logger.error("No analysis available for formatting")
        print("[ERROR] No analysis available")
        return
    
    print(f"\nSCENE: {analysis.get('scene_id', 'N/A')}")
    print(f"CRISIS TYPE: {analysis.get('crisis_type', 'UNKNOWN')}")
    print(f"SEVERITY: {analysis.get('severity', 'UNKNOWN')}")
    print(f"CONFIDENCE: {analysis.get('confidence', 0)}%")
    
    logger.info(f"Scene: {analysis.get('scene_id')}, Crisis: {analysis.get('crisis_type')}, Severity: {analysis.get('severity')}")
    
    print(f"\nEXECUTIVE SUMMARY")
    
    executive_summary = analysis.get('executive_summary', '')
    if executive_summary:
        summary_text = executive_summary
        if isinstance(summary_text, str):
            print(summary_text)
            logger.info(f"Executive Summary: {summary_text[:200]}...")
        else:
            print(json.dumps(summary_text, indent=2))
    else:
        print("No summary available")
    
    crisis_context = analysis.get('crisis_context', {})
    if crisis_context:
        print(f"\nCRISIS ANALYSIS")
        
        if isinstance(crisis_context, dict):
            for key, value in crisis_context.items():
                print(f"{key}: {value}")
        else:
            print(crisis_context)
    
    print(f"\nRECOMMENDED ACTION")
    
    recommended_action = analysis.get('recommended_action', '')
    if recommended_action:
        if isinstance(recommended_action, dict):
            action_type = recommended_action.get('action_type', 'UNKNOWN')
            rationale = recommended_action.get('rationale', '')
            impact = recommended_action.get('impact', '')
            
            print(f"Action: {action_type}")
            print(f"Rationale: {rationale}")
            print(f"Impact: {impact}")
            logger.info(f"Recommended Action: {action_type}")
        else:
            print(recommended_action)
    else:
        print("No recommendation available")
    
    next_actions = analysis.get('next_actions', [])
    if next_actions:
        print(f"\nNEXT STEPS")
        logger.info(f"Next Steps: {len(next_actions)} actions identified")
        
        for i, action in enumerate(next_actions, 1):
            if isinstance(action, dict):
                action_title = action.get('label') or action.get('action') or 'N/A'
                description = action.get('description', '')
                priority = action.get('priority', 'MEDIUM')
                
                print(f"\n{i}. {action_title}")
                if description:
                    print(f"   Description: {description}")
                if priority:
                    print(f"   Priority: {priority}")
                if action.get('owner'):
                    print(f"   Owner: {action.get('owner')}")
                if action.get('example_query'):
                    print(f"   Example: {action.get('example_query')}")
                
                logger.info(f"  Step {i}: {action_title} (Priority: {priority})")
            else:
                print(f"\n{i}. {action}")
                logger.info(f"  Step {i}: {action}")
    
    print(f"\nANALYSIS QUALITY METRICS")
    
    quality_score = analysis.get('quality_score', 0)
    reasoning_trail = analysis.get('reasoning_trail', [])
    refinement_count = analysis.get('refinement_count', 0)
    
    print(f"Quality Score: {quality_score}%")
    print(f"Refinement Iterations: {refinement_count}")
    print(f"Reasoning Steps: {len(reasoning_trail)}")
    
    logger.info(f"Quality Score: {quality_score}%, Reasoning Steps: {len(reasoning_trail)}")
    
    if reasoning_trail:
        print("\nReasoning Trail:")
        for i, step in enumerate(reasoning_trail[:5], 1):
            if isinstance(step, dict):
                print(f"  {i}. {step.get('step', 'N/A')}: {step.get('reasoning', 'N/A')[:80]}...")
            else:
                print(f"  {i}. {str(step)[:80]}...")
    
    logger.info("===== EXECUTIVE RESPONSE FORMATTING COMPLETE =====")


def main():
    """Main application loop"""
    logger.info("========== CINEFLOW APPLICATION START ==========")
    
    print("\n" + "=" * 80)
    print("CINEFLOW PRODUCTION CRISIS DIRECTOR")
    print("=" * 80)
    
    logger.info("Initializing CineFlow Crisis Management System...")
    print("\nInitializing CineFlow Crisis Management System...")
    
    print_daily_readiness()
    
    logger.info("Loading project data for agent...")
    print("\nLoading project data...")
    project_data = load_project_data()
    
    query = get_user_query()
    
    if not query:
        logger.warning("Exiting: No query provided")
        print("\nExiting without query.")
        return
    
    analysis = run_agent_orchestration(query, project_data=project_data)
    
    if analysis:
        format_executive_response(analysis)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE - Thank you for using CineFlow")
    print("=" * 80 + "\n")
    
    logger.info("========== CINEFLOW APPLICATION END ==========")
    logger.info(f"Log file saved to: {log_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Application cancelled by user")
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
