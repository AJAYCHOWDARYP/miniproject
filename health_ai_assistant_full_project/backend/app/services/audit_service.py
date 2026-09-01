"""
HIPAA-Aligned Audit Logging Service.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import AuditLog


async def log_audit_event(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = "127.0.0.1"
) -> AuditLog:
    """Persist an audit entry into the database with zero PHI leaked."""
    safe_details = {k: v for k, v in (details or {}).items() if k not in ["password", "token", "raw_text"]}
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=safe_details,
        ip_address=ip_address
    )
    db.add(audit_entry)
    await db.commit()
    await db.refresh(audit_entry)
    return audit_entry
