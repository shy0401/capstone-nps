import hashlib
import secrets
from contextvars import ContextVar
from datetime import timedelta, timezone
from typing import Protocol
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from nps.config import settings
from nps.db import get_db, utcnow, uid
from nps.errors import DomainError
from nps.models import AuditEvent, OrganizationUnit, Project, ProjectMember, RefreshSession, User

hasher = PasswordHasher()
audit_correlation = ContextVar("audit_correlation", default=None)
bearer = HTTPBearer(auto_error=False)


class AuthProvider(Protocol):
    def authenticate(self, db: Session, username: str, password: str) -> User: ...


class LocalAuthProvider:
    def authenticate(self, db, username, password):
        user = db.scalar(select(User).where(User.username == username, User.active.is_(True)))
        if user:
            try:
                if hasher.verify(user.password_hash, password):
                    return user
            except (VerifyMismatchError, InvalidHashError):
                pass
        raise DomainError("AUTH_INVALID_CREDENTIALS", 401)


AUTH_PROVIDERS: dict[str, AuthProvider] = {"local": LocalAuthProvider()}


def provider():
    if settings().auth_provider not in AUTH_PROVIDERS:
        raise DomainError("AUTH_PROVIDER_NOT_CONFIGURED", 503)
    return AUTH_PROVIDERS[settings().auth_provider]


def issue_access(user):
    if len(settings().jwt_secret) < 32:
        raise DomainError("AUTH_SECRET_NOT_CONFIGURED", 503)
    return jwt.encode(
        {
            "sub": user.id,
            "jti": uid(),
            "type": "access",
            "iat": utcnow(),
            "exp": utcnow() + timedelta(minutes=settings().access_minutes),
        },
        settings().jwt_secret,
        algorithm="HS256",
    )


def user_from_token(db, token):
    try:
        payload = jwt.decode(
            token,
            settings().jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
        if payload["type"] != "access":
            raise ValueError("wrong token type")
        user = db.get(User, payload["sub"])
        if not user or not user.active:
            raise ValueError("inactive")
        return user
    except (jwt.PyJWTError, ValueError):
        raise DomainError("AUTH_REQUIRED", 401) from None


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
):
    if not credentials:
        raise DomainError("AUTH_REQUIRED", 401)
    return user_from_token(db, credentials.credentials)


def create_refresh(db, user):
    token = secrets.token_urlsafe(48)
    db.add(
        RefreshSession(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=utcnow() + timedelta(days=settings().refresh_days),
        )
    )
    return token


def consume_refresh(db, token):
    hashed = hashlib.sha256((token or "").encode()).hexdigest()
    record = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == hashed).with_for_update())
    if not record or record.revoked or record.expires_at.replace(tzinfo=timezone.utc) <= utcnow():
        raise DomainError("AUTH_REFRESH_INVALID", 401)
    record.revoked = True
    user = db.get(User, record.user_id)
    if not user or not user.active:
        raise DomainError("AUTH_REQUIRED", 401)
    return user


def org_scope(db, user):
    if user.role == "SystemAdmin":
        return {o.id for o in db.scalars(select(OrganizationUnit))}
    allowed = {user.org_id}
    if user.role == "OrgAdmin":
        rows = list(db.scalars(select(OrganizationUnit)))
        while True:
            expanded = allowed | {o.id for o in rows if o.parent_id in allowed}
            if expanded == allowed:
                break
            allowed = expanded
    return allowed


def authorize_project(db, user, project_id, roles=None, owner=False):
    project = db.get(Project, str(project_id))
    if not project:
        raise DomainError("RESOURCE_NOT_FOUND", 404)
    member = db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id)
    )
    # System administration does not automatically confer document access.
    if project.org_id not in org_scope(db, user) or member is None:
        raise DomainError("AUTH_FORBIDDEN", 403)
    if roles and user.role not in roles:
        raise DomainError("AUTH_FORBIDDEN", 403)
    if owner and project.owner_id != user.id and user.role not in {"OrgAdmin", "SystemAdmin"}:
        raise DomainError("AUTH_FORBIDDEN", 403)
    return project


def require_admin(user, system=False):
    if user.role not in ({"SystemAdmin"} if system else {"OrgAdmin", "SystemAdmin"}):
        raise DomainError("AUTH_FORBIDDEN", 403)


def audit(db, user, action, target, project_id="system", correlation_id=None, result="SUCCESS", detail=None):
    # Only bounded metadata enters the audit stream. Never document text or review comments.
    safe = {
        k: v for k, v in (detail or {}).items() if k in {"old_role", "new_role", "version", "step", "mode"}
    }
    db.add(
        AuditEvent(
            actor_id=user.id if user else "anonymous",
            org_id=user.org_id if user else "system",
            project_id=project_id,
            action=action,
            target=str(target),
            result=result,
            correlation_id=correlation_id or audit_correlation.get() or uid(),
            detail=safe,
        )
    )
