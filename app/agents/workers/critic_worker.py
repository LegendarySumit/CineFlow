"""
CRITIC WORKER - Validates recovery plans against production constraints.

Role: Quality assurance and plan validation.
Responsibility: Check proposed plans for feasibility and cost.
"""

from typing import Any


def validate_plan(proposed_plan: dict[str, Any]) -> dict[str, Any]:
    """
    Autonomous plan validation task.
    
    Checks proposed recovery against production constraints.
    """
    
    if not proposed_plan:
        return {
            "status": "error",
            "message": "No plan to validate",
            "valid": False
        }
    
    action = proposed_plan.get("action", "")
    
    validation_checks = {
        "plan_exists": bool(action),
        "has_target": "target_day" in proposed_plan,
        "has_reasoning": "reasoning" in proposed_plan or "action" in proposed_plan
    }
    
    all_passed = all(validation_checks.values())
    
    # Determine confidence based on validation results
    if all_passed:
        confidence = "HIGH"
    elif len([v for v in validation_checks.values() if not v]) == 1:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "status": "success",
        "valid": all_passed,
        "confidence": confidence,
        "proposed_action": action,
        "validation_checks": validation_checks,
        "issues": [k for k, v in validation_checks.items() if not v],
        "recommendation": "APPROVE" if all_passed else "REVIEW"
    }
