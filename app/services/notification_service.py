"""
NOTIFICATION SERVICE - Autonomous notifications to cast/crew.

Responsible for:
- Sending schedule change notifications
- Email templates for different crisis types
- Notification tracking
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def notify_schedule_change(
    execution_result: dict[str, Any],
    recipients: list[dict[str, str]]
) -> dict[str, Any]:
    """
    Notify cast/crew of schedule changes after decision execution.
    
    recipients format: [{"type": "ACTOR", "id": "actor_1", "email": "..."}]
    """
    
    notifications_sent = []
    
    for recipient in recipients:
        recipient_type = recipient.get("type") or "UNKNOWN"  # ACTOR, CREW, DEPARTMENT
        recipient_id = recipient.get("id") or "unknown"
        recipient_email = recipient.get("email") or "unknown@example.com"
        
        # Build notification content based on decision type
        decision_type = execution_result.get("decision_type")
        
        if decision_type == "SWAP":
            notification = _build_swap_notification(execution_result, recipient_type)
        elif decision_type == "RESCHEDULE":
            notification = _build_reschedule_notification(execution_result, recipient_type)
        else:
            notification = {"subject": "Schedule Update", "body": "Your schedule has been updated."}
        
        # In production, this would actually send email
        # For now, we log it and track it
        notification["recipient_id"] = recipient_id
        notification["recipient_email"] = recipient_email
        notification["sent_at"] = datetime.now(timezone.utc).isoformat()
        notification["status"] = "QUEUED"  # Would be "SENT" after actual email
        
        logger.info(f"NOTIFICATION: {recipient_type} → {recipient_email}: {notification['subject']}")
        notifications_sent.append(notification)
    
    return {
        "status": "success",
        "notifications_sent": len(notifications_sent),
        "notifications": notifications_sent,
        "execution_id": execution_result.get("execution_id")
    }


def _build_swap_notification(execution_result: dict[str, Any], recipient_type: str) -> dict[str, str]:
    """Build notification for scene swap."""
    
    source = execution_result.get("source_scene", {})
    target = execution_result.get("target_scene", {})
    
    subject = f"Schedule Update: {source.get('title')} moved"
    
    if recipient_type == "ACTOR":
        body = f"""
Your schedule has been updated due to production adjustments.

CHANGED:
  Scene: {source.get('title')}
  Original Date: {source.get('original_date')}
  New Date: {source.get('new_date')}

REASON: Equipment and resource optimization

Please confirm your availability at the new date.
If you have conflicts, please notify production immediately.
        """
    else:
        body = f"""
Production Schedule Change - Scene Swap

SWAP DETAILS:
  {source.get('title')} → {source.get('new_date')}
  {target.get('title')} → {target.get('new_date')}

Affected Resources:
  Cast: {execution_result.get('affected_resources', {}).get('cast_count', 0)}
  Equipment: {execution_result.get('affected_resources', {}).get('equipment_count', 0)}

Please ensure all resources are coordinated accordingly.
        """
    
    return {
        "subject": subject,
        "body": body,
        "type": "SWAP_NOTIFICATION"
    }


def _build_reschedule_notification(execution_result: dict[str, Any], recipient_type: str) -> dict[str, str]:
    """Build notification for reschedule."""
    
    scene = execution_result.get("scene", {})
    
    subject = f"Schedule Change: {scene.get('title')} rescheduled"
    
    if recipient_type == "ACTOR":
        body = f"""
Your shooting schedule has been rescheduled.

SCENE: {scene.get('title')}
ORIGINAL DATE: {scene.get('original_date')}
NEW DATE: {scene.get('new_date')}

Please update your availability and confirm with production.
        """
    else:
        body = f"""
Scene Reschedule Notice

SCENE: {scene.get('title')}
FROM: {scene.get('original_date')}
TO: {scene.get('new_date')}

All departments must coordinate resource allocation for new date.
        """
    
    return {
        "subject": subject,
        "body": body,
        "type": "RESCHEDULE_NOTIFICATION"
    }


def get_notification_history(execution_id: str) -> list[dict[str, Any]]:
    """Retrieve notification history for an execution."""
    
    # In production, would query database
    return [
        {
            "execution_id": execution_id,
            "status": "SENT",
            "note": "Notification history would be stored in database"
        }
    ]
