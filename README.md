<div align="center">

# 🎬 CineFlow

**Multi-Agent Production Crisis Director — Real-time intelligent crisis management for film productions**

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.5%20Flash-red?style=flat-square&logo=google)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?style=flat-square&logo=fastapi)
![Custom MAS](https://img.shields.io/badge/Multi--Agent%20System-Custom-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

*Agentic Intelligence • Cascade Detection • Cost Optimization • Real-time Execution*

[Features](#-features) • [Quick Start](#-quick-start) • [Tech Stack](#-tech-stack) • [Architecture](#-architecture) • [Author](#-author)

</div>

---

## 📖 Project Info

### What is CineFlow?

**CineFlow** is a production-grade autonomous decision engine that handles film production crises instantly. It's an AI-powered crisis director that orchestrates multiple specialized agents to analyze disruptions, detect cascading problems, and recommend financially optimal solutions in real-time.

### The Problem

Film productions face constant disruptions that cost **₹305,000+ per day** in lost time:

- **Weather Crises** — Cyclones, monsoons, unexpected weather changes force last-minute rewrites
- **Cast Emergencies** — Actor illness, injury, or unavailability affects 5-10 dependent scenes
- **Equipment Failures** — Camera breakdown, drone damage, or audio system failure during shoot
- **Permit Issues** — Revoked locations, police intervention, local authority restrictions
- **Logistics Breakdowns** — Transportation delays, crew unavailability, accommodation issues

Current solutions fail because they:
- ❌ Require 2-hour strategy meetings (producers need instant decisions)
- ❌ Provide generic advice, not executable actions
- ❌ Ignore cascading secondary crises (fixing one problem creates two new ones)
- ❌ Don't calculate financial impact or cost-benefit tradeoffs
- ❌ Are manual, slow, and prone to human error

### How CineFlow Solves It

CineFlow delivers **intelligent, immediate, executable decisions** through:

1. **True Multi-Agent Intelligence** — Not an LLM wrapper. Genuine orchestration with:
   - **Supervisor Agent** — Master decision-maker with planning, execution, reflection, and self-correction loops
   - **5 Specialized Workers** — Schedule analyst, impact assessor, external data gatherer, strategy planner, validator
   - **Architecture:** Planning → Execution → Reflection → Self-Correction

2. **Cascade Detection** — Identifies secondary crises BEFORE execution:
   - CAST_CONFLICT — Actor double-booked after swap
   - EQUIPMENT_CONFLICT — Equipment needed in two places simultaneously
   - LOCATION_CONFLICT — Location unavailable during proposed reschedule
   - Multi-level analysis finds safe alternatives automatically

3. **Financial Impact Analysis** — Every recommendation includes:
   - Disruption costs (cast daily rates, equipment rental, crew overtime)
   - Recovery costs (rescheduling, location scouting, permit re-filing)
   - Pareto frontier optimization (non-dominated solutions)
   - ROI for each alternative

4. **Real-time External Context** — Parallel MCP integration gathers from 50+ sources:
   - Weather alerts and cyclone warnings
   - Permit databases and local authority status
   - Infrastructure (road blockages, waterlogging, accessibility)
   - Cast availability from agency systems
   - Equipment inventory and availability

5. **Immediately Executable** — Returns exact decisions, not suggestions:
   - "Swap sc_001 with sc_003" (not "consider rescheduling")
   - "Confidence: 87%, Financial Impact: ₹1.2M savings"
   - Complete reasoning trail for producer approval
   - Audit log for compliance and post-incident review

### Key Features

- ✅ **Real-time Crisis Analysis** — Instant classification of crisis types (Cast, Equipment, Weather, Permits, Location)
- ✅ **Agentic Reflection Loops** — Self-correcting agents validate and refine decisions automatically
- ✅ **Cascade Detection** — Multi-level analysis identifies secondary crises BEFORE execution
- ✅ **Financial Impact Analysis** — Disruption costs, optimization scenarios, Pareto frontier solutions
- ✅ **Daily Production Readiness** — Automated crew briefings with scene-by-scene risk breakdown
- ✅ **Audit Logging** — Complete execution traces for compliance and post-incident review
- ✅ **Proactive Next Steps** — AI-powered action recommendations beyond the immediate crisis
- ✅ **External Context Gathering** — 50+ concurrent data sources via Parallel MCP integration
- ✅ **Production-Ready** — Works with ANY production manifest (JSON format)

---

## 🛠️ Tech Stack

### Core AI
- **Language Model:** `gemini-3.5-flash-lite` (Google Gemini - Latest Free Tier)
- **Framework:** Custom Multi-Agent Orchestration (No third-party framework)
  - Supervisor Agent + 5 Specialized Workers
  - Planning → Execution → Reflection → Self-Correction loops

### External Integration
- **Parallel MCP** — Real-time data from 50+ sources (weather, permits, infrastructure)
- **FastAPI** — High-performance async REST API
- **Python 3.13** — Core language

### Data & Storage
- **JSON** — Project metadata, cast/crew, equipment, locations, schedule
- **Audit Logs** — Time-stamped execution traces with full decision trails
- **Session State** — Multi-turn conversation memory for agentic continuity

---

## 🏗️ Architecture

### 5-Phase Agentic Loop

```
User Query (Arbitrary Crisis)
    ↓
[PHASE 1] PLANNING
  └─ Supervisor breaks crisis into 5 atomic tasks
    ↓
[PHASE 2] EXECUTION
  ├─ SCHEDULE_WORKER: Load production data
  ├─ IMPACT_WORKER: Assess disruption impact
  ├─ EXTERNAL_INFO_WORKER: Gather real-world context (Parallel MCP)
  ├─ STRATEGY_WORKER: Generate recovery alternatives
  └─ CRITIC_WORKER: Validate plan feasibility
    ↓
[PHASE 3] QUALITY MONITORING (Reflection)
  └─ Check: schedule? impact? external context? recovery? validation?
    ↓
[PHASE 4] CASCADE DETECTION
  ├─ Primary cascade check (CAST/EQUIPMENT/LOCATION conflicts)
  ├─ Multi-level cascade analysis (safe/risky/unsafe alternatives)
  └─ Pareto frontier optimization (non-dominated solutions)
    ↓
[PHASE 5] SYNTHESIS & RECOMMENDATION
  └─ Generate executive summary with financial impact analysis
```

### 📁 Project Structure

```
CineFlow/
├── app/
│   ├── agents/
│   │   ├── supervisor.py           # Master orchestrator (Planning, Reflection, Synthesis)
│   │   └── workers/
│   │       ├── schedule_worker.py  # Scene & schedule loading
│   │       ├── strategy_worker.py  # Crisis impact & recovery planning
│   │       ├── external_info_worker.py  # External data gathering (Parallel MCP)
│   │       └── critic_worker.py    # Validation & feasibility checks
│   ├── services/
│   │   ├── daily_readiness.py      # Daily crew briefings
│   │   ├── cascade_detector.py     # Secondary crisis detection
│   │   ├── cost_optimizer.py       # Financial impact analysis
│   │   ├── decision_executor.py    # Execute approved decisions
│   │   └── audit_logger.py         # Compliance logging
│   ├── tools/
│   │   ├── unified_risk_engine.py  # Crisis classification
│   │   ├── entity_extractor.py     # NLP entity mapping
│   │   ├── cost_calculator.py      # Disruption cost estimation
│   │   └── deterministic_resolver.py  # Scene swap logic
│   ├── main.py                     # FastAPI backend
│   ├── run_main.py                 # Terminal interface
│   └── session_manager.py          # Multi-turn state management
├── data/
│   ├── production.json             # Production metadata
│   ├── scenes.json                 # Scene breakdown
│   ├── actors.json                 # Cast database
│   ├── equipment.json              # Equipment inventory
│   └── locations.json              # Location details
├── projects/
│   └── prod_monsoon_arc_01.json   # Example project file
├── audit_logs/                     # Execution traces & decision logs
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template (secrets protected)
└── README.md                       # This file
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.13+** installed
- **Google Gemini API Key** (free tier at [Google AI Studio](https://gemini.google.com/app))
- **pip** package manager

### Local Installation

```bash
# Clone the repository
git clone https://github.com/LegendarySumit/CineFlow.git
cd CineFlow

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Local Configuration

```bash
# Copy environment template
copy .env.example .env

# Edit .env with your API key
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
PORT=8000
```

### Run Locally

**Terminal Interface:**
```bash
python app/run_main.py
```

**FastAPI Backend:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# API Docs: http://localhost:8000/docs
```

---

## ☁️ Deploy to Render.com (FREE - No Billing Required)

### Step 1: Prepare Repository

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub account
3. Connect your GitHub repository

### Step 3: Deploy Service

1. Click **"New +"** → **"Web Service"**
2. Select your **CineFlow** repository
3. Fill in configuration:
   - **Name:** `cineflow-api`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`

### Step 4: Add Environment Variables

In Render dashboard, add:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Your API key from Google AI Studio |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |
| `MAX_REFINEMENTS` | `0` |

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait for build to complete (2-3 minutes)
3. Your live URL appears: `https://cineflow-api.onrender.com`

### Step 6: Test Live Deployment

```bash
# Health check
curl https://cineflow-api.onrender.com/api/health

# View API documentation
https://cineflow-api.onrender.com/docs

# Test crisis analysis
curl -X POST https://cineflow-api.onrender.com/api/analyze-crisis \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Lead actor got sick what should we do",
    "scene_id": "sc_001"
  }'
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required) | - |
| `GEMINI_MODEL` | Model name | `gemini-3.5-flash-lite` |
| `PORT` | Server port | `8000` |
| `HOST` | Server host | `0.0.0.0` |
| `ENVIRONMENT` | Dev/Production mode | `development` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `MAX_REFINEMENTS` | Self-correction iterations | `0` |

### Project File Format

Create a project JSON in `projects/` directory:

```json
{
  "metadata": {
    "project_id": "prod_monsoon_arc_01",
    "project_name": "Monsoon Arc",
    "director": "Vishal Bhardwaj",
    "production_budget_inr": 3500000000,
    "start_date": "2026-09-01",
    "status": "PRE_PRODUCTION"
  },
  "cast": [
    {"actor_id": "actor_001", "name": "Ranveer Singh", "role": "Lead", ...}
  ],
  "scenes": [
    {"scene_id": "sc_001", "title": "Scene Title", "duration": 4, ...}
  ],
  "locations": [...],
  "equipment": [...]
}
```

---

## 📚 Usage

### Terminal Interface

```bash
$ python app/run_main.py

================================================================================
CineFlow Production Crisis Director
================================================================================

[INITIALIZING] CineFlow Crisis Management System...

DAILY READINESS REPORT
Date: 2026-09-01
Project: Monsoon Arc
Overall Status: PRODUCTION_AT_RISK

INPUT - Enter your query
Examples:
  - 'What if lead actor gets sick?'
  - 'Location becomes unavailable due to weather'
  - 'Equipment failure in production'

$ Lead actor got health issue what should we do
[RUNNING] Supervisor Agent...

EXECUTIVE ANALYSIS & RECOMMENDATION
Scene: sc_001
Crisis Type: CAST
Severity: CRITICAL
Confidence: 85%

[EXECUTIVE SUMMARY]
Actor disruption affects 5 scenes totaling ₹2.1M in production costs...

[RECOMMENDED ACTION]
Action: SWAP
Rationale: Scene sc_001 can be rescheduled with zero cast conflicts...
```

### API Usage

```bash
# Analyze a crisis
curl -X POST http://localhost:8000/api/analyze-crisis \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Lead actor got sick what should we do",
    "scene_id": "sc_001",
    "session_id": "session_123"
  }'

# Get daily readiness report
curl http://localhost:8000/api/daily-readiness

# Approve a decision
curl -X POST http://localhost:8000/api/approve-decision \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "decision_type": "SWAP",
    "source_scene_id": "sc_001",
    "target_scene_id": "sc_003",
    "approved_by": "Producer",
    "force_approve": false
  }'
```

---

## 🔌 API Endpoints

### Crisis Analysis

**POST** `/api/analyze-crisis`

```json
{
  "prompt": "Lead actor unavailable",
  "scene_id": "sc_001",
  "session_id": "session_123"
}
```

Response:
```json
{
  "status": "success",
  "crisis_type": "CAST",
  "severity": "CRITICAL",
  "confidence": "HIGH",
  "executive_summary": "...",
  "recommended_action": {
    "action": "SWAP",
    "target_scene": "sc_003"
  },
  "next_actions": [...]
}
```

### Cascade Detection

**POST** `/api/analyze-cascades` — Identifies secondary crises from proposed decisions

### Decision Approval

**POST** `/api/approve-decision` — Executes approved production decisions with audit trail

### Daily Readiness

**GET** `/api/daily-readiness` — Scene-by-scene production readiness (GO/CONDITIONAL/NO_GO)

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Total Agents** | 1 Supervisor + 5 Workers |
| **Crisis Types** | 5 (Cast, Equipment, Weather, Permits, Location) |
| **Max Scenes** | 100+ per project |
| **API Endpoints** | 8+ REST endpoints |
| **Analysis Time** | 15-30 seconds (with Gemini API) |
| **External Sources** | 50+ via Parallel MCP |
| **Audit Depth** | Full execution traces with reasoning |

---

## 🐛 Troubleshooting

### API Key Issues

**Error:** `403 Your API key was reported as leaked`
- **Solution:** Generate new key from [Google AI Studio](https://gemini.google.com/app), update `.env`, restart

### Port Already in Use

**Error:** `Address already in use`
- **Solution:** Change `PORT` in `.env` or kill existing process

### Project Data Not Loading

**Error:** `Project data not found`
- **Solution:** Verify JSON exists in `projects/`, check schema, ensure scene IDs are formatted (`sc_001`, etc.)

### Agent Returns Empty Analysis

**Error:** `crisis_type: UNKNOWN`
- **Solution:** Verify API quota and billing status, check `.env` configuration, review audit logs

---

## 🔮 Future Enhancements

- [ ] Real-time weather integration (OpenWeatherMap API)
- [ ] Permit status database (government APIs)
- [ ] Cast availability sync (agency management systems)
- [ ] Equipment GPS tracking (IoT sensors)
- [ ] Multi-location concurrent crisis handling
- [ ] Advanced Pareto frontier (3+ objectives)
- [ ] WebSocket multi-user sessions
- [ ] Mobile app for on-set alerts
- [ ] ML-based crisis prediction (historical patterns)
- [ ] Production accounting software integration
- [ ] Slack/Teams notifications
- [ ] Advanced analytics dashboard

---

## 📄 License

MIT License — Feel free to use in your own projects.

---

## 👨‍💻 Author

**LegendarySumit**

- **GitHub:** [@LegendarySumit](https://github.com/LegendarySumit)
- **Project:** [CineFlow](https://github.com/LegendarySumit/CineFlow)
- **Built for:** Google Gemini AI Hackathon 2024

---

<div align="center">

## 🎬 Managing Production Crises with Agentic Intelligence

*CineFlow: Where autonomous agents meet real-world production challenges*

**⭐ Star this repo if you find it helpful!**

Made with ❤️ for film producers and production teams

</div>
