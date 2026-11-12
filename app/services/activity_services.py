from sqlalchemy.orm import Session

from app.models.log_activity import ActivityLog


def log_activity(
    db: Session,
    project_id: int,
    user_id: int,
    action: str,
    target_type: str,
    target_id: int | None,
    details: str,
):
    log = ActivityLog(
        project_id=project_id,
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(log)
    db.commit()
