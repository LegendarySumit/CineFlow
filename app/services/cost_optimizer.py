"""
COST OPTIMIZER - Finds multiple economically optimal solutions.

Problem: Multiple valid alternatives exist (e.g., swap with sc_09, sc_14, sc_25)
Each has different financial/logistical tradeoffs.

Solution: Use Pareto frontier analysis to find non-dominated solutions.
A solution is "non-dominated" if you can't improve one metric without harming another.

Example:
- Option A: ₹245K benefit, 2 hours setup, 1 cascade
- Option B: ₹220K benefit, 1 hour setup, 0 cascades
- Option C: ₹100K benefit, 4 hours setup, 0 cascades

Pareto frontier: A & B (both optimal for different priorities)
Dominated: C (worse benefit and setup time than B)

This enables producers to choose based on their priorities.
"""

from typing import Any

from app.tools.production import load_dataset


def analyze_scenario_costs(
    decision: dict[str, Any],
    dataset: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Analyze financial & logistical costs of a single decision scenario.
    
    Returns:
    {
        "scenario": "SWAP sc_42 → sc_18",
        "metrics": {
            "net_benefit": 245000,
            "setup_hours": 2.5,
            "risk_score": 0.8,  # 0-1, lower is better
            "crew_disruption": "moderate"
        },
        "details": {...}
    }
    """
    
    if dataset is None:
        dataset = load_dataset("data")
    
    decision_type = decision.get("decision_type", "UNKNOWN")
    source_id = decision.get("source_scene_id")
    target_id = decision.get("target_scene_id")
    
    # Get scene details
    source_scene = next((s for s in dataset.get("scenes", []) if s["scene_id"] == source_id), None)
    target_scene = next((s for s in dataset.get("scenes", []) if s["scene_id"] == target_id), None)
    
    if not source_scene or not target_scene:
        return {}
    
    # Base metrics
    source_cast_count = len(source_scene.get("cast_ids", []))
    target_cast_count = len(target_scene.get("cast_ids", []))
    
    # Financial analysis
    daily_burn = 300000  # From test data
    idle_cost_saved = daily_burn  # 1 day saved if swap eliminates problem
    
    # Setup costs (estimated based on scene complexity)
    setup_cost = (source_cast_count * 5000) + (target_cast_count * 5000)
    
    net_benefit = idle_cost_saved - setup_cost
    
    # Setup time (hours)
    setup_hours = 1.0 + (source_cast_count * 0.3) + (target_cast_count * 0.3)
    
    # Risk score (0-1, lower is better)
    cast_overlap = len(set(source_scene.get("cast_ids", [])) & set(target_scene.get("cast_ids", [])))
    equipment_overlap = len(set(source_scene.get("equipment_ids", [])) & set(target_scene.get("equipment_ids", [])))
    location_same = source_scene.get("location_id") == target_scene.get("location_id")
    
    risk_score = 0.0
    risk_score += (cast_overlap / max(source_cast_count, target_cast_count, 1)) * 0.4  # Cast conflict weight
    risk_score += (equipment_overlap * 0.15)  # Equipment conflict weight
    risk_score += (0.1 if location_same else 0.0)  # Location complexity
    
    risk_score = min(risk_score, 1.0)
    
    # Crew disruption estimate
    if cast_overlap > 0:
        crew_disruption = "high"
    elif setup_hours > 3:
        crew_disruption = "moderate"
    else:
        crew_disruption = "low"
    
    return {
        "scenario": f"{decision_type} {source_id} ↔ {target_id}",
        "source_scene": source_scene.get("title", "Unknown"),
        "target_scene": target_scene.get("title", "Unknown"),
        "decision": decision,
        "metrics": {
            "net_benefit": net_benefit,
            "setup_hours": round(setup_hours, 1),
            "risk_score": round(risk_score, 2),
            "crew_disruption": crew_disruption,
            "cast_impact": cast_overlap,
            "equipment_impact": equipment_overlap
        },
        "financial": {
            "idle_cost_saved": idle_cost_saved,
            "setup_cost": setup_cost,
            "net_benefit": net_benefit,
            "roi_percentage": (net_benefit / setup_cost * 100) if setup_cost > 0 else 0
        },
        "logistics": {
            "setup_hours": setup_hours,
            "crew_disruption": crew_disruption,
            "cast_changes": cast_overlap,
            "equipment_changes": equipment_overlap
        }
    }


def find_pareto_frontier(
    scenarios: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Identify non-dominated solutions using Pareto frontier analysis.
    
    A solution is on the Pareto frontier if you can't improve one metric
    without making another metric worse.
    
    Returns:
    {
        "frontier_solutions": [...],  # Non-dominated options
        "dominated_solutions": [...],  # Options to avoid
        "summary": "Best value option", "Fastest option", "Lowest risk option"
    }
    """
    
    if not scenarios:
        return {
            "frontier_solutions": [],
            "dominated_solutions": [],
            "summary": "No scenarios to analyze"
        }
    
    # Extract metrics for comparison
    # Higher benefit = better, Lower risk/hours = better
    frontier = []
    dominated = []
    
    for i, scenario_a in enumerate(scenarios):
        is_dominated = False
        
        for scenario_b in scenarios:
            if scenario_a == scenario_b:
                continue
            
            metrics_a = scenario_a.get("metrics", {})
            metrics_b = scenario_b.get("metrics", {})
            
            # Check if B dominates A
            # B dominates A if B is better on all metrics
            benefit_better = metrics_b.get("net_benefit", 0) > metrics_a.get("net_benefit", 0)
            hours_better = metrics_b.get("setup_hours", 0) < metrics_a.get("setup_hours", 0)
            risk_better = metrics_b.get("risk_score", 0) < metrics_a.get("risk_score", 0)
            
            # If B is strictly better on all fronts, A is dominated
            if benefit_better and hours_better and risk_better:
                is_dominated = True
                break
        
        if is_dominated:
            dominated.append(scenario_a)
        else:
            frontier.append(scenario_a)
    
    # Build summary of frontier options
    summary = {}
    if frontier:
        # Best financial option
        best_financial = max(frontier, key=lambda x: x.get("metrics", {}).get("net_benefit", 0))
        summary["best_financial"] = best_financial.get("scenario")
        
        # Fastest option
        fastest = min(frontier, key=lambda x: x.get("metrics", {}).get("setup_hours", float('inf')))
        summary["fastest"] = fastest.get("scenario")
        
        # Lowest risk option
        safest = min(frontier, key=lambda x: x.get("metrics", {}).get("risk_score", 1))
        summary["safest"] = safest.get("scenario")
    
    return {
        "frontier_solutions": frontier,
        "dominated_solutions": dominated,
        "summary": summary,
        "frontier_count": len(frontier),
        "dominated_count": len(dominated)
    }


def optimize_decision(
    source_scene_id: str,
    alternative_targets: list[str],
    dataset: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Find optimal decisions across multiple alternative targets.
    
    FULL WORKFLOW:
    1. Analyze cost/benefit for each target
    2. Find Pareto frontier (non-dominated solutions)
    3. Return ranked options with rationale
    
    Returns:
    {
        "optimal_solutions": [
            {
                "rank": 1,
                "scenario": "SWAP sc_42 ↔ sc_09",
                "rationale": "Best overall value",
                "metrics": {...},
                "recommendation": "Proceed with this option"
            },
            ...
        ],
        "decision_support": {
            "if_priority_is_financial": "Use Option 1",
            "if_priority_is_speed": "Use Option 2",
            "if_priority_is_safety": "Use Option 3"
        }
    }
    """
    
    if dataset is None:
        dataset = load_dataset("data")
    
    # Step 1: Analyze all scenarios
    scenarios = []
    for target_id in alternative_targets:
        decision = {
            "decision_type": "SWAP",
            "source_scene_id": source_scene_id,
            "target_scene_id": target_id
        }
        
        scenario = analyze_scenario_costs(decision, dataset)
        if scenario:
            scenarios.append(scenario)
    
    # Step 2: Find Pareto frontier
    frontier_result = find_pareto_frontier(scenarios)
    frontier_solutions = frontier_result.get("frontier_solutions", [])
    
    # Step 3: Rank and provide decision support
    optimal_solutions = []
    
    # Rank by net benefit first, then by other metrics
    sorted_frontier = sorted(
        frontier_solutions,
        key=lambda x: x.get("metrics", {}).get("net_benefit", 0),
        reverse=True
    )
    
    for rank, solution in enumerate(sorted_frontier, 1):
        metrics = solution.get("metrics", {})
        
        # Determine rationale based on position
        if rank == 1:
            rationale = f"Best overall value (₹{metrics.get('net_benefit', 0):,} benefit, {metrics.get('risk_score', 0):.1%} risk)"
            recommendation = "Recommended - optimal balance of cost & risk"
        elif metrics.get("risk_score", 1) == min(s.get("metrics", {}).get("risk_score", 1) for s in sorted_frontier):
            rationale = f"Lowest risk option ({metrics.get('risk_score', 0):.1%} risk score)"
            recommendation = "If risk mitigation is priority"
        elif metrics.get("setup_hours", 0) == min(s.get("metrics", {}).get("setup_hours", float('inf')) for s in sorted_frontier):
            rationale = f"Fastest to implement ({metrics.get('setup_hours', 0):.1f} hours)"
            recommendation = "If speed is critical"
        else:
            rationale = f"Alternative option (₹{metrics.get('net_benefit', 0):,} benefit)"
            recommendation = "Consider if other constraints apply"
        
        optimal_solutions.append({
            "rank": rank,
            "scenario": solution.get("scenario"),
            "source": solution.get("source_scene"),
            "target": solution.get("target_scene"),
            "rationale": rationale,
            "metrics": metrics,
            "financial": solution.get("financial"),
            "recommendation": recommendation
        })
    
    # Decision support matrix
    decision_support = {}
    if sorted_frontier:
        best_financial = max(sorted_frontier, key=lambda x: x.get("metrics", {}).get("net_benefit", 0))
        fastest = min(sorted_frontier, key=lambda x: x.get("metrics", {}).get("setup_hours", float('inf')))
        safest = min(sorted_frontier, key=lambda x: x.get("metrics", {}).get("risk_score", 1))
        
        decision_support = {
            "if_financial_priority": f"Use {best_financial.get('scenario')} (₹{best_financial.get('metrics', {}).get('net_benefit', 0):,})",
            "if_speed_priority": f"Use {fastest.get('scenario')} ({fastest.get('metrics', {}).get('setup_hours', 0):.1f}h)",
            "if_safety_priority": f"Use {safest.get('scenario')} ({safest.get('metrics', {}).get('risk_score', 0):.1%} risk)"
        }
    
    return {
        "status": "success",
        "source_scene": source_scene_id,
        "scenarios_analyzed": len(scenarios),
        "frontier_count": len(frontier_solutions),
        "optimal_solutions": optimal_solutions,
        "decision_support": decision_support,
        "summary": frontier_result.get("summary", {})
    }
