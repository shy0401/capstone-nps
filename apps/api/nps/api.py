from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Cookie, Depends, Request, Response
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from nps.auth import (
    audit,
    authorize_project,
    consume_refresh,
    create_refresh,
    current_user,
    issue_access,
    org_scope,
    provider,
    require_admin,
)
from nps.config import settings
from nps.contracts import Contract, Role
from nps.db import get_db
from nps.errors import DomainError
from nps.models import AuditEvent, OrganizationUnit, Project, ProjectMember, User

router = APIRouter(prefix="/api/v1")
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(current_user)]


def serialize(record, exclude=()):
    return {
        c.name: getattr(record, c.name)
        for c in record.__table__.columns
        if c.name not in {"password_hash", "storage_key", "token_hash", *exclude}
    }


class Login(Contract):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class ProjectInput(Contract):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    security_class: str = Field(default="synthetic", max_length=30)
    template_id: UUID | None = None


class MemberInput(Contract):
    user_id: UUID
    role: Role = Role.USER


class RoleInput(Contract):
    role: Role
    active: bool = True


class ReviewInput(Contract):
    decision: Literal["approve", "reject", "request-change"]
    comment: str = Field(default="", max_length=2000)
    version: int = Field(ge=1)


def tokens(db, user, response):
    response.set_cookie(
        "refresh",
        create_refresh(db, user),
        httponly=True,
        secure=not settings().dev_insecure_cookie,
        samesite="strict",
        path="/api/v1/auth",
        max_age=settings().refresh_days * 86400,
    )
    db.commit()
    return {
        "access_token": issue_access(user),
        "token_type": "bearer",
        "expires_in": settings().access_minutes * 60,
    }


@router.post("/auth/login")
def login(data: Login, request: Request, response: Response, db: DB):
    try:
        user = provider().authenticate(db, data.username, data.password)
    except DomainError:
        audit(
            db, None, "LOGIN_FAIL", "local-auth", correlation_id=request.state.correlation_id, result="DENIED"
        )
        db.commit()
        raise
    audit(db, user, "LOGIN_SUCCESS", user.id, correlation_id=request.state.correlation_id)
    return tokens(db, user, response)


@router.post("/auth/refresh")
def refresh(response: Response, db: DB, refresh: str | None = Cookie(default=None)):
    return tokens(db, consume_refresh(db, refresh), response)


@router.post("/auth/logout", status_code=204)
def logout(response: Response, db: DB, user: Actor, refresh: str | None = Cookie(default=None)):
    if refresh:
        try:
            consume_refresh(db, refresh)
        except DomainError:
            pass
    response.delete_cookie("refresh", path="/api/v1/auth")
    audit(db, user, "LOGOUT", user.id)
    db.commit()


@router.get("/me")
def me(user: Actor):
    return {
        **serialize(user),
        "modes": {"llm": settings().llm_mode, "comfy": settings().comfy_mode, "scan": settings().scan_mode},
        "environment": settings().environment,
        "review_mode": settings().review_mode,
    }


@router.get("/organizations")
def organizations(db: DB, user: Actor):
    require_admin(user)
    return [
        serialize(o)
        for o in db.scalars(select(OrganizationUnit).where(OrganizationUnit.id.in_(org_scope(db, user))))
    ]


@router.get("/projects")
def projects(db: DB, user: Actor):
    rows = db.scalars(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user.id, Project.org_id.in_(org_scope(db, user)))
    )
    return [serialize(p) for p in rows]


@router.post("/projects", status_code=201)
def create_project(data: ProjectInput, db: DB, user: Actor):
    if data.template_id:
        from nps.themes import scoped_template

        scoped_template(db, data.template_id, user.org_id)
    project = Project(**data.model_dump(mode="json"), org_id=user.org_id, owner_id=user.id)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=user.id, role=user.role))
    audit(db, user, "PROJECT_CREATE", project.id, project.id)
    db.commit()
    return serialize(project)


@router.get("/projects/{project_id}")
def project_detail(project_id: UUID, db: DB, user: Actor):
    return serialize(authorize_project(db, user, str(project_id)))


@router.patch("/projects/{project_id}")
def update_project(project_id: UUID, data: ProjectInput, db: DB, user: Actor):
    project = authorize_project(db, user, str(project_id), owner=True)
    if data.template_id:
        from nps.themes import scoped_template

        scoped_template(db, data.template_id, user.org_id)
    for key, value in data.model_dump(mode="json").items():
        setattr(project, key, value)
    audit(db, user, "PROJECT_UPDATE", project.id, project.id)
    db.commit()
    return serialize(project)


@router.get("/projects/{project_id}/members")
def members(project_id: UUID, db: DB, user: Actor):
    project = authorize_project(db, user, str(project_id))
    return [
        serialize(m) for m in db.scalars(select(ProjectMember).where(ProjectMember.project_id == project.id))
    ]


@router.get("/projects/{project_id}/reviewer-candidates")
def reviewer_candidates(project_id: UUID, db: DB, user: Actor):
    project = authorize_project(db, user, str(project_id), owner=True)
    return [
        {"id": reviewer.id, "username": reviewer.username}
        for reviewer in db.scalars(
            select(User).where(User.org_id == project.org_id, User.role == "Reviewer", User.active.is_(True))
        )
    ]


@router.post("/projects/{project_id}/members", status_code=201)
def add_member(project_id: UUID, data: MemberInput, db: DB, user: Actor):
    project = authorize_project(db, user, str(project_id), owner=True)
    target = db.get(User, str(data.user_id))
    if not target or target.org_id != project.org_id:
        raise DomainError("AUTH_FORBIDDEN", 403)
    existing = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id, ProjectMember.user_id == target.id
        )
    )
    if existing:
        return serialize(existing)
    member = ProjectMember(project_id=project.id, user_id=target.id, role=data.role)
    db.add(member)
    audit(db, user, "PROJECT_MEMBER_ADD", target.id, project.id)
    db.commit()
    return serialize(member)


@router.delete("/projects/{project_id}/members/{user_id}", status_code=204)
def remove_member(project_id: UUID, user_id: UUID, db: DB, user: Actor):
    project = authorize_project(db, user, str(project_id), owner=True)
    if str(user_id) == project.owner_id:
        raise DomainError("PROJECT_OWNER_REQUIRED", 409)
    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id, ProjectMember.user_id == str(user_id)
        )
    )
    if member:
        db.delete(member)
    audit(db, user, "PROJECT_MEMBER_REMOVE", str(user_id), project.id)
    db.commit()


@router.patch("/admin/users/{user_id}")
def change_role(user_id: UUID, data: RoleInput, db: DB, user: Actor):
    require_admin(user)
    target = db.get(User, str(user_id))
    if not target or target.org_id not in org_scope(db, user):
        raise DomainError("AUTH_FORBIDDEN", 403)
    if user.role != "SystemAdmin" and (data.role == "SystemAdmin" or target.role == "SystemAdmin"):
        raise DomainError("AUTH_FORBIDDEN", 403)
    old = target.role
    old_active = target.active
    target.role, target.active = data.role, data.active
    audit(
        db,
        user,
        "USER_ROLE_CHANGE",
        target.id,
        detail={"old_role": old, "new_role": data.role, "old_active": old_active, "new_active": data.active},
    )
    db.commit()
    return serialize(target)


@router.get("/admin/users")
def admin_users(db: DB, user: Actor):
    require_admin(user)
    return [
        serialize(u)
        for u in db.scalars(select(User).where(User.org_id.in_(org_scope(db, user))).order_by(User.username))
    ]


@router.get("/admin/audit")
def audit_events(db: DB, user: Actor):
    require_admin(user)
    rows = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.org_id.in_(org_scope(db, user)))
        .order_by(AuditEvent.created_at.desc())
        .limit(200)
    )
    return [serialize(row) for row in rows]


@router.get("/templates")
def templates(db: DB, user: Actor):
    from nps.themes import visible_templates

    return [serialize(t) for t in visible_templates(db, user.org_id)]
