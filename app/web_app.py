"""
CineFlow Web Interface for Render.com Deployment
Wraps the terminal-based agent in a Flask web interface
"""

from flask import Flask, render_template, request, jsonify
import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.supervisor import SupervisorAgent
from app.tools.production import load_dataset
from app.services.daily_readiness import generate_daily_readiness_report

app = Flask(__name__)

# Setup logging
log_dir = Path(__file__).parent.parent.parent / "audit_logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("cineflow_web")


def load_project_data():
    """Load project data"""
    try:
        project_file = Path(__file__).parent.parent.parent / "projects" / "prod_monsoon_arc_01.json"
        if project_file.exists():
            with open(project_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load project: {e}")
    
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


@app.route('/')
def index():
    """Main page"""
    logger.info("Web interface accessed")
    return render_template('index.html')


@app.route('/api/daily-readiness', methods=['GET'])
def get_daily_readiness():
    """Get daily readiness report"""
    logger.info("Fetching daily readiness report")
    
    try:
        project_data = load_project_data()
        
        readiness = {
            "date": "2026-09-01",
            "project_name": project_data.get("project_name"),
            "director": project_data.get("director"),
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
                    "issues": [
                        "Alert: CYCLONE DANA WARNING: Expected to intensify. Wind speed 60-80 km/h.",
                        "Access: NH5 blocked near Puri due to waterlogging. 2-hour delays reported."
                    ]
                },
                {
                    "scene_id": "sc_002",
                    "scene_title": "Aerial View of Monsoon Clouds",
                    "status": "NO_GO",
                    "risk_level": "CRITICAL",
                    "issues": [
                        "Alert: CYCLONE DANA WARNING: Expected to intensify. Wind speed 60-80 km/h.",
                        "Access: NH5 blocked near Puri due to waterlogging. 2-hour delays reported."
                    ]
                }
            ]
        }
        
        logger.info(f"Daily readiness retrieved: {readiness['overall_status']}")
        return jsonify(readiness)
    
    except Exception as e:
        logger.error(f"Error getting daily readiness: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_crisis():
    """Analyze crisis query"""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        logger.info(f"Analyzing crisis query: {query[:100]}...")
        
        # Log to file
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S_%f")
        log_file = Path(__file__).parent.parent.parent / "audit_logs" / f"web_request_{timestamp}.log"
        
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"WEB REQUEST - {datetime.now().isoformat()}\n")
            f.write(f"Query: {query}\n")
            f.write(f"{'='*80}\n")
        
        # Load project data
        project_data = load_project_data()
        
        # Initialize supervisor
        supervisor = SupervisorAgent()
        session_state = {"project_data": project_data}
        
        # Run analysis
        logger.info("Running supervisor agent")
        analysis = supervisor.run(query, "sc_001", session_state)
        
        # Log result
        with open(log_file, 'a') as f:
            f.write(f"\nCrisis Type: {analysis.get('crisis_type')}\n")
            f.write(f"Severity: {analysis.get('severity')}\n")
            f.write(f"Confidence: {analysis.get('confidence')}%\n")
            f.write(f"Status: {analysis.get('status')}\n")
        
        logger.info(f"Analysis complete: {analysis.get('crisis_type')}")
        
        return jsonify({
            "status": "success",
            "scene_id": analysis.get('scene_id'),
            "crisis_type": analysis.get('crisis_type'),
            "severity": analysis.get('severity'),
            "confidence": analysis.get('confidence'),
            "executive_summary": analysis.get('executive_summary', 'N/A')[:500],
            "recommended_action": analysis.get('recommended_action'),
            "next_actions": analysis.get('next_actions', [])[:3],
            "quality_score": analysis.get('quality_score'),
            "log_file": str(log_file)
        })
    
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent logs"""
    try:
        log_dir = Path(__file__).parent.parent.parent / "audit_logs"
        logs = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        
        log_files = []
        for log in logs:
            log_files.append({
                "name": log.name,
                "size": log.stat().st_size,
                "modified": datetime.fromtimestamp(log.stat().st_mtime).isoformat()
            })
        
        logger.info(f"Retrieved {len(log_files)} log files")
        return jsonify({"logs": log_files, "log_dir": str(log_dir)})
    
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    logger.info("Health check")
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "project": "CineFlow Production Crisis Director"
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting CineFlow Web App on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
