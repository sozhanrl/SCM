from flask import request
from app.extensions import db
from app.models.activity import ActivityLog

def log_activity(action: str, user_id: int = None, details: str = None, ip_address: str = None):
    try:
        if not ip_address and request:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
    except Exception:
        ip_address = None

    try:
        entry = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.session.add(entry)
        db.session.commit()
        return entry
    except Exception:
        db.session.rollback()
        return None
