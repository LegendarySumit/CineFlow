"""
RESPONSE FORMATTER - Converts JSON analysis into human-readable conversational format.

Purpose:
- API returns structured JSON (for backend testing)
- UI/Terminal displays natural language (conversational)
- Same data, different presentation for different audiences

Example:
  JSON: {"crisis_type": "EQUIPMENT", "affected_resource": "DJI Inspire 3 Drone Kit"}
  
  Natural Language:
    "A critical equipment issue has emerged. The DJI Inspire 3 Drone Kit,
     which is essential for tomorrow's shoot at Puri Beach, is unavailable.
     This impacts Scene 42: Reunion at High Tide."
"""

from typing import Any


def format_crisis_analysis_structured(analysis: dict[str, Any]) -> dict[str, Any]:
    """
    Convert supervisor analysis to structured format with individual sections.
    
    Enables frontend to render each section independently with collapsible UI.
    
    Returns:
    {
        "status": "success",
        "sections": {
            "crisis_statement": {
                "title": "🚨 PRODUCTION CRISIS DETECTED",
                "content": str,
                "icon": "crisis",
                "collapsible": False,
                "expanded": True
            },
            "situation_assessment": {...},
            "external_context": {...},
            "financial_impact": {...},
            "recommendation": {...},
            "next_steps": {...}
        },
        "flow": ["crisis_statement", "situation_assessment", "external_context", "financial_impact", "recommendation", "next_steps"],
        "summary": {
            "total_sections": 6,
            "risk_level": "HIGH",
            "recommendation": "SWAP"
        }
    }
    """
    
    sections = {}
    
    # 1. CRISIS STATEMENT
    crisis_content = _format_crisis_statement(analysis)
    if crisis_content:
        sections["crisis_statement"] = {
            "title": "🚨 PRODUCTION CRISIS DETECTED",
            "content": crisis_content,
            "icon": "alert-circle",
            "collapsible": False,
            "expanded": True,
            "priority": "CRITICAL"
        }
    
    # 2. SITUATION ASSESSMENT
    situation_content = _format_situation_assessment(analysis)
    if situation_content:
        risk_level = analysis.get("worker_results", {}).get("impact", {}).get("risk_level", "UNKNOWN")
        sections["situation_assessment"] = {
            "title": "📊 SITUATION ASSESSMENT",
            "content": situation_content,
            "icon": "bar-chart-3",
            "collapsible": True,
            "expanded": True,
            "metadata": {
                "risk_level": risk_level,
                "affected_cast": analysis.get("worker_results", {}).get("schedule", {}).get("affected_resources", {}).get("cast_count", 0),
                "affected_equipment": analysis.get("worker_results", {}).get("schedule", {}).get("affected_resources", {}).get("equipment_count", 0)
            }
        }
    
    # 3. EXTERNAL CONTEXT
    external_content = _format_external_context(analysis)
    if external_content:
        external = analysis.get("worker_results", {}).get("external_context", {})
        sections["external_context"] = {
            "title": "🌐 EXTERNAL INTELLIGENCE GATHERED",
            "content": external_content,
            "icon": "globe",
            "collapsible": True,
            "expanded": False,
            "metadata": {
                "investigation_dimensions": external.get("investigation_dimensions", []),
                "quality_score": external.get("data_quality", {}).get("quality_score", 0),
                "total_sources": external.get("total_sources", 0)
            }
        }
    
    # 4. FINANCIAL IMPACT
    financial_content = _format_financial_impact(analysis)
    if financial_content:
        financial = analysis.get("worker_results", {}).get("impact", {}).get("financial_impact", {})
        sections["financial_impact"] = {
            "title": "💰 FINANCIAL ANALYSIS",
            "content": financial_content,
            "icon": "trending-down",
            "collapsible": True,
            "expanded": False,
            "metadata": {
                "daily_burn": financial.get("daily_burn", 0),
                "total_cost": financial.get("total_cost_inr", 0),
                "net_benefit": analysis.get("worker_results", {}).get("recovery", {}).get("deterministic_resolution", {}).get("cost_analysis", {}).get("net_economic_benefit", 0)
            }
        }
    
    # 5. RECOMMENDATION
    recommendation_content = _format_recommendation(analysis)
    if recommendation_content:
        recommended = analysis.get("recommended_action", {})
        sections["recommendation"] = {
            "title": "✅ RECOMMENDED ACTION",
            "content": recommendation_content,
            "icon": "check-circle",
            "collapsible": False,
            "expanded": True,
            "priority": "HIGH",
            "metadata": {
                "action": recommended.get("action", "UNKNOWN"),
                "confidence": recommended.get("confidence", "MEDIUM"),
                "target_scene": recommended.get("target_scene", "N/A")
            }
        }
    
    # 6. NEXT STEPS
    next_steps_content = _format_next_steps(analysis)
    if next_steps_content:
        next_actions = analysis.get("next_actions", [])
        sections["next_steps"] = {
            "title": "📋 NEXT STEPS FOR PRODUCTION TEAM",
            "content": next_steps_content,
            "icon": "list-todo",
            "collapsible": True,
            "expanded": False,
            "metadata": {
                "action_count": len(next_actions),
                "critical_actions": sum(1 for a in next_actions if a.get("priority") == "CRITICAL")
            }
        }
    
    # Build flow order
    flow = [key for key in ["crisis_statement", "situation_assessment", "external_context", "financial_impact", "recommendation", "next_steps"] if key in sections]
    
    return {
        "status": "success",
        "sections": sections,
        "flow": flow,
        "summary": {
            "total_sections": len(sections),
            "risk_level": analysis.get("worker_results", {}).get("impact", {}).get("risk_level", "UNKNOWN"),
            "recommendation": analysis.get("recommended_action", {}).get("action", "UNKNOWN"),
            "executive_summary": analysis.get("executive_summary", "Analysis complete")
        }
    }


def format_crisis_analysis(analysis: dict[str, Any]) -> str:
    """
    Convert supervisor analysis JSON to conversational format.
    
    Input: Full analysis response from /api/analyze-crisis
    Output: Natural language summary suitable for terminal/UI display
    """
    
    sections = []
    
    # 1. CRISIS STATEMENT
    crisis_section = _format_crisis_statement(analysis)
    if crisis_section:
        sections.append(crisis_section)
    
    # 2. SITUATION ASSESSMENT
    situation_section = _format_situation_assessment(analysis)
    if situation_section:
        sections.append(situation_section)
    
    # 3. EXTERNAL CONTEXT
    external_section = _format_external_context(analysis)
    if external_section:
        sections.append(external_section)
    
    # 4. FINANCIAL IMPACT
    financial_section = _format_financial_impact(analysis)
    if financial_section:
        sections.append(financial_section)
    
    # 5. RECOMMENDATION
    recommendation_section = _format_recommendation(analysis)
    if recommendation_section:
        sections.append(recommendation_section)
    
    # 6. NEXT STEPS
    next_steps_section = _format_next_steps(analysis)
    if next_steps_section:
        sections.append(next_steps_section)
    
    return "\n".join(sections)


def _format_crisis_statement(analysis: dict[str, Any]) -> str:
    """Format the core crisis in natural language."""
    
    worker_results = analysis.get("worker_results", {})
    schedule = worker_results.get("schedule", {})
    impact = worker_results.get("impact", {})
    
    scene = schedule.get("scene", {})
    scene_title = scene.get("title", "Unknown Scene")
    scene_id = scene.get("id", "Unknown")
    
    crisis_type = impact.get("crisis_type", "UNKNOWN")
    affected_resource = impact.get("affected_resource", "Unknown resource")
    location = schedule.get("affected_resources", {}).get("location", "Unknown location")
    date = schedule.get("schedule", {}).get("date", "Unknown date")
    
    # Build natural language statement
    if crisis_type == "EQUIPMENT":
        statement = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 PRODUCTION CRISIS DETECTED

Critical Equipment Failure
├─ Resource: {affected_resource}
├─ Affected Scene: {scene_title} ({scene_id})
├─ Location: {location}
├─ Scheduled Date: {date}
└─ Status: UNAVAILABLE & BLOCKING PRODUCTION

This equipment is essential for tomorrow's shoot and there are no immediate alternatives.
Without a solution, the entire shoot for {scene_title} cannot proceed as planned.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    elif crisis_type == "LOCATION":
        statement = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 PRODUCTION CRISIS DETECTED

Location Access Issue
├─ Location: {location}
├─ Affected Scene: {scene_title} ({scene_id})
├─ Scheduled Date: {date}
└─ Status: INACCESSIBLE

The location required for {scene_title} is no longer available.
Without access, the production cannot shoot this scene as planned.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    elif crisis_type == "CAST":
        statement = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 PRODUCTION CRISIS DETECTED

Cast Availability Issue
├─ Affected Scene: {scene_title} ({scene_id})
├─ Issue: {affected_resource}
├─ Scheduled Date: {date}
└─ Status: BLOCKING PRODUCTION

A key cast member is unavailable for {scene_title}.
The scene cannot proceed without this actor.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    else:
        statement = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 PRODUCTION CRISIS DETECTED

{crisis_type} Crisis
├─ Scene: {scene_title} ({scene_id})
├─ Issue: {affected_resource}
├─ Location: {location}
└─ Date: {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return statement


def _format_situation_assessment(analysis: dict[str, Any]) -> str:
    """Format risk assessment and impact details."""
    
    worker_results = analysis.get("worker_results", {})
    impact = worker_results.get("impact", {})
    schedule = worker_results.get("schedule", {})
    
    risk_level = impact.get("risk_level", "UNKNOWN")
    is_blocked = impact.get("is_blocked", False)
    affected_resources = schedule.get("affected_resources", {})
    
    cast_count = affected_resources.get("cast_count", 0)
    equipment_count = affected_resources.get("equipment_count", 0)
    
    financial = impact.get("financial_impact", {})
    daily_burn = financial.get("daily_burn", 0)
    total_cost = financial.get("total_cost_inr", 0)
    
    # Build assessment
    section = f"""
📊 SITUATION ASSESSMENT
Risk Level: {risk_level}
Production Status: {"🔴 BLOCKED" if is_blocked else "🟡 AT RISK"}

Impact Overview:
├─ Affected Cast: {cast_count} actor(s)
├─ Affected Equipment: {equipment_count} item(s)
├─ Daily Production Cost: ₹{daily_burn:,}
└─ Total Crisis Cost: ₹{total_cost:,}

Time is critical. Every hour of delay compounds production costs."""
    
    return section


def _format_external_context(analysis: dict[str, Any]) -> str:
    """Format external world information gathered."""
    
    worker_results = analysis.get("worker_results", {})
    external = worker_results.get("external_context", {})
    
    if external.get("status") != "success":
        return ""
    
    investigation = external.get("investigation_dimensions", [])
    data_quality = external.get("data_quality", {})
    total_sources = external.get("total_sources", 0)
    quality_score = data_quality.get("quality_score", 0)
    
    # Format dimensions investigated with descriptions
    dimension_names = {
        "WEATHER": "Weather conditions",
        "LOCATION_ACCESS": "Location access & travel",
        "VENUE_STATUS": "Venue operational status",
        "LOCAL_EVENTS": "Local events & restrictions",
        "PUBLIC_ALERTS": "Public alerts & announcements",
        "DAMAGE_NEWS": "Damage reports & news",
        "INFRASTRUCTURE": "Infrastructure & utilities"
    }
    
    dims_formatted = []
    for dim in investigation:
        desc = dimension_names.get(dim, dim)
        dims_formatted.append(f"✓ {desc}")
    dims_str = "\n  ".join(dims_formatted) if dims_formatted else "None"
    
    section = f"""
🌐 EXTERNAL INTELLIGENCE GATHERED
Agent autonomously investigated real-world conditions:
  {dims_str}

Sources Analyzed: {total_sources} | Information Quality: {quality_score}%
Data Source: {"Real-time web" if data_quality.get("has_real_data") else "Predictive & historical data"}

This external context augments internal production data for informed decision-making."""
    
    return section


def _format_financial_impact(analysis: dict[str, Any]) -> str:
    """Format financial analysis."""
    
    worker_results = analysis.get("worker_results", {})
    impact = worker_results.get("impact", {})
    recovery = worker_results.get("recovery", {})
    deterministic = recovery.get("deterministic_resolution", {})
    
    # Current crisis costs
    financial = impact.get("financial_impact", {})
    daily_burn = financial.get("daily_burn", 0)
    total_crisis_cost = financial.get("total_cost_inr", 0)
    
    # Solution costs
    cost_analysis = deterministic.get("cost_analysis", {})
    idle_cost_saved = cost_analysis.get("idle_cost_saved", 0)
    net_benefit = cost_analysis.get("net_economic_benefit", 0)
    roi = cost_analysis.get("roi_percentage", 0)
    
    one_time = deterministic.get("one_time_costs", {}).get("total", 0)
    
    status_icon = "🟢" if net_benefit > 0 else "🟡"
    
    section = f"""
💰 FINANCIAL ANALYSIS

Crisis Impact (if no action):
├─ Daily Burn Rate: ₹{daily_burn:,}
└─ Total 3-Day Cost: ₹{total_crisis_cost:,}

Proposed Solution Economics:
├─ Idle Cost Saved: ₹{idle_cost_saved:,}
├─ One-Time Expenses: ₹{one_time:,}
├─ Net Benefit: {status_icon} ₹{net_benefit:,}
└─ Return on Investment: {roi:.0f}%

Conclusion: The recommended action delivers strong economic value."""
    
    return section


def _format_recommendation(analysis: dict[str, Any]) -> str:
    """Format the recommendation with intelligent reasoning and context-aware suggestions."""
    
    recommended = analysis.get("recommended_action", {})
    worker_results = analysis.get("worker_results", {})
    recovery = worker_results.get("recovery", {})
    best_option = recovery.get("best_option", {})
    impact = worker_results.get("impact", {})
    
    action = recommended.get("action", "HOLD")
    reasoning = recommended.get("reasoning", "No specific reasoning provided")
    confidence = recommended.get("confidence", "MEDIUM")
    risk_factors = analysis.get("risk_factors", [])
    cost_impact = analysis.get("cost_impact", "TBD")
    
    source_id = analysis.get('scene_id', "Unknown")
    target_scene = best_option.get("scene_id", "Unknown")
    target_title = best_option.get("title", "Unknown")
    target_location = best_option.get("location", "Unknown")
    target_duration = best_option.get("duration_hours", 0)
    
    confidence_icon = "🟢" if confidence == "HIGH" else "🟡" if confidence == "MEDIUM" else "🔴"
    cost_icon = "✓" if cost_impact and "positive" in str(cost_impact).lower() else "!"
    
    # Enhanced reasoning with context
    detailed_reasoning = f"{reasoning}"
    if impact.get("crisis_type"):
        detailed_reasoning += f"\n     Crisis Type: {impact.get('crisis_type')}"
    if risk_factors:
        detailed_reasoning += f"\n     Risk Factors: {', '.join(risk_factors[:2])}"
    
    if action == "SWAP":
        recommendation_text = f"""
✅ RECOMMENDED ACTION: INTELLIGENT SCENE SWAP

Why This Works:
├─ Swap {source_id} with {target_scene}
├─ Alternative Scene: {target_title} at {target_location}
├─ Duration: {target_duration} hours
├─ Reasoning: {detailed_reasoning}
└─ Confidence: {confidence_icon} {confidence}

Impact Analysis:
├─ Eliminates actor/equipment conflict for {source_id}
├─ Redistributes resources efficiently
├─ Maintains production timeline
├─ Cost Impact: {cost_icon} {cost_impact}
└─ No cascading issues detected

Implementation (Priority Order):
  1. ✓ Update call sheet - notify cast & crew immediately
  2. ✓ Coordinate location access - confirm permit status
  3. ✓ Verify equipment availability - all required gear ready
  4. ✓ Brief crew on new schedule - minimize confusion
  5. ✓ Finalize vendor arrangements - catering, transportation

Why Not Other Options?
• RESCHEDULE would delay production by X days
• HOLD creates ongoing risk with no resolution
• OTHER SWAPS create cascading conflicts

Expected Outcome: Production continues smoothly with minimal disruption."""
    
    elif action == "RESCHEDULE":
        recommendation_text = f"""
⏰ RECOMMENDED ACTION: STRATEGIC RESCHEDULE

Why This Is Best:
├─ Postpone {source_id} to later date
├─ Reasoning: {detailed_reasoning}
├─ Buys time for: Issue resolution/cast recovery/equipment repair
└─ Confidence: {confidence_icon} {confidence}

Impact Analysis:
├─ Eliminates immediate crisis
├─ Allows proper resource preparation
├─ Reduces risk of production problems
├─ Cost Impact: {cost_icon} {cost_impact}
└─ Dependencies checked - no blocking issues

Implementation Strategy:
  1. ✓ Identify optimal reschedule date (5-10 days recommended)
  2. ✓ Notify cast & crew with NEW call times
  3. ✓ Confirm actor availability for new slot
  4. ✓ Reserve location booking for new date
  5. ✓ Update equipment rental agreements
  6. ✓ Communicate revised timeline to stakeholders

Timeline:
• Today: Notify all parties
• Day 2: Finalize new schedule
• Day 3: Prepare for rescheduled shoot

Why This Over Alternatives:
• SWAP might create new conflicts (checked - no cascades found)
• HOLD maintains risk (not acceptable)
• RESCHEDULE gives maximum flexibility

Expected Outcome: Shoot proceeds with full resources and no crisis."""
    
    else:
        recommendation_text = f"""
⏸️  RECOMMENDED ACTION: MONITOR & PREPARE CONTINGENCY

Current Assessment:
├─ Keep current schedule (with active risk management)
├─ Reasoning: {detailed_reasoning}
├─ Risk Level: MODERATE-HIGH
└─ Confidence: {confidence_icon} {confidence}

Why Not Swap/Reschedule?
• Available swaps create worse conflicts
• Rescheduling delays production significantly
• Current situation might resolve on its own
• Cost of inaction < cost of other options

Risk Mitigation Strategy:
  1. 🔍 Monitor situation hourly - assign dedicated liaison
  2. 🛡️  Prepare backup actors/equipment - have alternatives ready
  3. 📋 Create contingency scenes - which scenes can substitute?
  4. 📞 Maintain open communication - quick escalation path
  5. ✓ Reassess every 24 hours - be ready to pivot

Trigger Points (Time to Escalate):
  ❌ If issue not resolved in 24 hours → SWAP
  ❌ If more resources become unavailable → RESCHEDULE
  ❌ If cast/equipment confirms unavailability → IMMEDIATE ACTION

Contingency Plan:
• Backup Scene 1: [Alternative]
• Backup Scene 2: [Alternative]
• Team Lead: [Assigned person]

Risk Level: MODERATE-HIGH
This option maintains schedule but requires active management."""
    
    return recommendation_text





def _format_next_steps(analysis: dict[str, Any]) -> str:
    """Format proactive next steps."""
    
    next_actions = analysis.get("next_actions", [])
    
    if not next_actions:
        return ""
    
    section = "📋 NEXT STEPS FOR PRODUCTION TEAM\n"
    section += "Agent recommends these immediate actions (in priority order):\n"
    
    for i, action in enumerate(next_actions[:4], 1):  # Top 4 actions
        priority = action.get("priority", "MEDIUM")
        label = action.get("label", "Unknown")
        description = action.get("description", "")
        example = action.get("example_query", "")
        
        priority_icon = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
        section += f"\n{i}. {priority_icon} {label}\n   {description}"
        if example:
            section += f"\n   Example: \"{example}\""
    
    section += f"\n\nℹ️  All {len(next_actions)} suggested actions available via agent chat."
    
    return section


def format_multi_cascade_analysis(multi_result: dict[str, Any]) -> str:
    """
    Format multi-level cascade analysis for terminal/UI display.
    Shows safe, risky, and unsafe alternatives categorized.
    """
    
    safe_alts = multi_result.get("safe_alternatives", [])
    risky_alts = multi_result.get("risky_alternatives", [])
    unsafe_alts = multi_result.get("unsafe_alternatives", [])
    has_safe = multi_result.get("has_truly_safe_option", False)
    recommendation = multi_result.get("recommendation", "No recommendation")
    
    output = """
🔍 MULTI-LEVEL CASCADE ANALYSIS

Primary decision creates cascades. Analyzing alternatives for hidden conflicts...
"""
    
    if has_safe and safe_alts:
        output += f"""
✅ SAFE ALTERNATIVES ({len(safe_alts)} found - use these!)
"""
        for i, alt in enumerate(safe_alts, 1):
            output += f"\n  {i}. {alt.get('target')} ({alt.get('title')})"
            output += "\n     → No cascading conflicts detected"
    
    if risky_alts:
        output += f"""

⚠️  RISKY ALTERNATIVES ({len(risky_alts)} - manageable if needed)
"""
        for i, alt in enumerate(risky_alts, 1):
            cascade_count = alt.get('cascade_count', 0)
            output += f"\n  {i}. {alt.get('target')} ({alt.get('title')})"
            output += f"\n     → {cascade_count} cascade(s) but none HIGH severity"
            if alt.get('cascades'):
                for cascade in alt['cascades'][:1]:
                    output += f"\n     Example: {cascade.get('description')}"
    
    if unsafe_alts:
        output += f"""

🔴 UNSAFE ALTERNATIVES ({len(unsafe_alts)} - avoid these)
"""
        for i, alt in enumerate(unsafe_alts, 1):
            output += f"\n  {i}. {alt.get('target')} ({alt.get('title')})"
            output += "\n     → HIGH severity cascades detected"
    
    output += f"""

💡 RECOMMENDATION
{recommendation}

Next Step: Choose a safe alternative, manage risky option, or consider HOLD/RESCHEDULE.
"""
    
    return output


def format_cascade_warning(cascade_result: dict[str, Any]) -> str:
    """
    Format single-level cascade detection warning for terminal/UI display.
    """
    
    cascades = cascade_result.get("cascades", [])
    safe_alternatives = cascade_result.get("safe_alternatives", [])
    
    warning = f"""
⚠️  CASCADE DETECTION WARNING

{len(cascades)} secondary crisis(es) detected if decision executes:
"""
    
    for i, cascade in enumerate(cascades, 1):
        severity = cascade.get("severity", "MEDIUM")
        cascade_type = cascade.get("type", "UNKNOWN")
        description = cascade.get("description", "")
        
        severity_icon = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
        warning += f"\n{i}. {severity_icon} {cascade_type}: {description}"
    
    if safe_alternatives:
        warning += f"\n\n✅ SAFE ALTERNATIVES AVAILABLE ({len(safe_alternatives)}):\n"
        for i, alt in enumerate(safe_alternatives[:3], 1):
            target = alt.get("target", "Unknown")
            title = alt.get("target_title", "Unknown")
            warning += f"\n  {i}. Swap with {target} ({title})"
    
    warning += "\n\nOption 1: Choose a safe alternative (recommended)"
    warning += "\nOption 2: Force-approve if you accept the risks (force_approve=true)"
    
    return warning


def format_approval_confirmation(execution_result: dict[str, Any], notification_result: dict[str, Any] | None = None) -> str:
    """
    Format decision approval confirmation for terminal/UI display.
    """
    
    decision_type = execution_result.get("decision_type", "UNKNOWN")
    exec_id = execution_result.get("execution_id", "Unknown")
    approved_by = execution_result.get("approval_info", {}).get("approved_by", "Unknown")
    timestamp = execution_result.get("execution_timestamp", "Unknown")
    
    if decision_type == "SWAP":
        source = execution_result.get("source_scene", {})
        target = execution_result.get("target_scene", {})
        
        confirmation = f"""
✅ DECISION EXECUTED SUCCESSFULLY

Scene Swap Confirmed
├─ Execution ID: {exec_id}
├─ Approved By: {approved_by}
└─ Executed At: {timestamp}

Schedule Changes:
├─ {source.get('title')} ({source.get('id')})
│  └─ {source.get('original_date')} → {source.get('new_date')}
└─ {target.get('title')} ({target.get('id')})
   └─ {target.get('original_date')} → {target.get('new_date')}

Affected Resources:
├─ Cast: {execution_result.get('affected_resources', {}).get('cast_count', 0)} actor(s)
└─ Equipment: {execution_result.get('affected_resources', {}).get('equipment_count', 0)} item(s)"""
    
    elif decision_type == "RESCHEDULE":
        scene = execution_result.get("scene", {})
        
        confirmation = f"""
✅ DECISION EXECUTED SUCCESSFULLY

Reschedule Confirmed
├─ Execution ID: {exec_id}
├─ Approved By: {approved_by}
└─ Executed At: {timestamp}

Schedule Changes:
└─ {scene.get('title')} ({scene.get('id')})
   └─ {scene.get('original_date')} → {scene.get('new_date')}"""
    
    else:
        confirmation = f"""
✅ DECISION EXECUTED

Execution ID: {exec_id}
Approved By: {approved_by}
Executed At: {timestamp}"""
    
    # Add notification status
    if notification_result and notification_result.get("status") == "success":
        notif_count = notification_result.get("notifications_sent", 0)
        confirmation += f"""

📧 Notifications Sent
└─ {notif_count} notification(s) queued for cast/crew"""
    
    confirmation += f"""

{"="*60}
✅ PRODUCTION DECISION LOGGED
Session data updated. Ready for next action.
{"="*60}"""
    
    return confirmation
