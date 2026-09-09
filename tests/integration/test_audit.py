from uuid import uuid4
from sqlalchemy import select
from nps.auth import issue_access
from nps.models import AuditEvent


def test_audit_correlates_without_document_or_credential_values(client, db, users):
    correlation = str(uuid4())
    headers = {"Authorization": "Bearer " + issue_access(users["demo-user"]), "X-Correlation-ID": correlation}
    result = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "synthetic confidential title", "description": "SENSITIVE_SYNTHETIC_TEXT"},
    )
    assert result.status_code == 201
    event = db.scalar(select(AuditEvent).where(AuditEvent.action == "PROJECT_CREATE"))
    assert event.correlation_id == correlation
    assert "SENSITIVE" not in str(event.detail) and "confidential" not in str(event.detail)
