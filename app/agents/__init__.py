"""
CineFlow Multi-Agent Orchestration System

Agents:
- SUPERVISOR: Master orchestrator that coordinates all workers
- WORKERS: Specialized agents for schedule, weather, strategy, and validation
"""

from app.agents.supervisor import SupervisorAgent

__all__ = ["SupervisorAgent"]
