"""
Utility functions for audit logging
Demonstrates transaction tracking in database systems
"""

from models import AuditLog
import json


def log_audit(db, user_id, action, table_name, record_id=None, details=None):
    """
    Create an audit log entry
    
    Args:
        db: Database session
        user_id: ID of user performing action (None for system)
        action: Type of action (CREATE, UPDATE, DELETE, etc.)
        table_name: Table being affected
        record_id: ID of the record being affected
        details: Additional context as dictionary
    """
    try:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            details=json.dumps(details) if details else None
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        # Silent fail - don't break operations due to audit logging
        print(f"Audit log error: {e}")
        pass
