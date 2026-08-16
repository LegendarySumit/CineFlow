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
    """Format the recommendation in natural language."""
    
    recommended = analysis.get("recommended_action", {})
    worker_results = analysis.get("worker_results", {})
    recovery = worker_results.get("recovery", {})
    best_option = recovery.get("best_option", {})
    
    action = recommended.get("action", "HOLD")
    reasoning = recommended.get("reasoning", "No specific reasoning provided")
    confidence = recommended.get("confidence", "MEDIUM")
    
    source_id = analysis.get('scene_id', "Unknown")
    target_scene = best_option.get("scene_id", "Unknown")
    target_title = best_option.get("title", "Unknown")
    target_location = best_option.get("location", "Unknown")
    target_duration = best_option.get("duration_hours", 0)
    
    confidence_icon = "🟢" if confidence == "HIGH" else "🟡" if confidence == "MEDIUM" else "🔴"
    
    if action == "SWAP":
        recommendation_text = f"""
✅ RECOMMENDED ACTION: SCENE SWAP

Swap {source_id} ↔ {target_scene}
├─ Alternative Scene: {target_title}
├─ Location: {target_location}
├─ Duration: {target_duration} hours
├─ Reason: {reasoning}
└─ Confidence: {confidence_icon} {confidence}

Action Steps:
  1. Update call sheet (notify cast)
  2. Coordinate location access
  3. Confirm equipment availability
  4. Brief crew on new schedule

Benefit: Eliminates crisis while maintaining production momentum.
No additional delays. Minimal crew disruption."""
    
    elif action == "RESCHEDULE":
        recommendation_text = f"""
⏰ RECOMMENDED ACTION: RESCHEDULE

Postpone {source_id} to a later date
├─ Reason: {reasoning}
├─ Allows: Time to resolve underlying issue
└─ Confidence: {confidence_icon} {confidence}

Action Steps:
  1. Notify cast & crew of new dates
  2. Check actor availability for new slot
  3. Confirm location booking
  4. Update equipment schedules

Benefit: Buys time for equipment repair or cast recovery.
Lower risk than rushing with problematic resources."""
    
    else:
        recommendation_text = f"""
⏸️  RECOMMENDED ACTION: HOLD & MONITOR

Keep current schedule (with caution)
├─ Reason: {reasoning}
└─ Confidence: {confidence_icon} {confidence}

Action Steps:
  1. Monitor situation closely
  2. Prepare contingency plans
  3. Reassess every 24 hours
  4. Have backup scenes ready

Risk Level: MODERATE-HIGH
This option maintains schedule but requires active risk management."""
    
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
