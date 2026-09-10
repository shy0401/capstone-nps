from datetime import datetime
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from nps.db import Base, Record


class OrganizationUnit(Record, Base):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(80), unique=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"))


class User(Record, Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30), default="User")
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class RefreshSession(Record, Base):
    __tablename__ = "refresh_sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Project(Record, Base):
    __tablename__ = "projects"
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    security_class: Mapped[str] = mapped_column(String(30), default="synthetic")
    template_id: Mapped[str | None] = mapped_column(ForeignKey("templates.id"))


class ProjectMember(Record, Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(30), default="User")


class Document(Record, Base):
    __tablename__ = "documents"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(255))
    current_version_id: Mapped[str | None] = mapped_column(String(36))
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class DocumentVersion(Record, Base):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version"),)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    version: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size: Mapped[int] = mapped_column(Integer)
    mime: Mapped[str] = mapped_column(String(120))
    extension: Mapped[str] = mapped_column(String(10))
    storage_key: Mapped[str] = mapped_column(Text)
    scan_status: Mapped[str] = mapped_column(String(20), default="CLEAN")
    scan_mode: Mapped[str] = mapped_column(String(20))


class ParseResult(Record, Base):
    __tablename__ = "parse_results"
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id"), unique=True)
    data: Mapped[dict] = mapped_column(JSON)
    storage_key: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="SUCCEEDED")


class Chunk(Record, Base):
    __tablename__ = "chunks"
    version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id"), index=True)
    parse_result_id: Mapped[str] = mapped_column(ForeignKey("parse_results.id"))
    data: Mapped[dict] = mapped_column(JSON)


class SlidePlan(Record, Base):
    __tablename__ = "slide_plans"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="VALIDATED")
    data: Mapped[dict] = mapped_column(JSON)
    approved_version: Mapped[int | None] = mapped_column(Integer)


class Slide(Record, Base):
    __tablename__ = "slides"
    __table_args__ = (UniqueConstraint("plan_id", "slide_id", "version"),)
    plan_id: Mapped[str] = mapped_column(ForeignKey("slide_plans.id"))
    slide_id: Mapped[str] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(JSON)


class VisualAsset(Record, Base):
    __tablename__ = "visual_assets"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    plan_id: Mapped[str] = mapped_column(ForeignKey("slide_plans.id"))
    slide_id: Mapped[str] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer, default=1)
    storage_key: Mapped[str] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSON)


class GenerationJob(Record, Base):
    __tablename__ = "generation_jobs"
    __table_args__ = (UniqueConstraint("project_id", "requested_by", "idempotency_key"),)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(30))
    state: Mapped[str] = mapped_column(String(30), default="QUEUED", index=True)
    step: Mapped[str] = mapped_column(String(40), default="")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    seq: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    fingerprint: Mapped[str] = mapped_column(String(64))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    estimated_vram_mb: Mapped[int] = mapped_column(Integer, default=0)
    required_capability: Mapped[str] = mapped_column(String(30), default="cpu")
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    resume_from_step: Mapped[str | None] = mapped_column(String(40))
    worker_id: Mapped[str | None] = mapped_column(String(100))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobStep(Record, Base):
    __tablename__ = "job_steps"
    __table_args__ = (UniqueConstraint("job_id", "step_type"),)
    job_id: Mapped[str] = mapped_column(ForeignKey("generation_jobs.id"))
    step_type: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(20), default="QUEUED")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(80))


class Artifact(Record, Base):
    __tablename__ = "artifacts"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    plan_id: Mapped[str] = mapped_column(ForeignKey("slide_plans.id"))
    type: Mapped[str] = mapped_column(String(10))
    current_version_id: Mapped[str | None] = mapped_column(String(36))


class ArtifactVersion(Record, Base):
    __tablename__ = "artifact_versions"
    __table_args__ = (UniqueConstraint("artifact_id", "version"),)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.id"))
    version: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    job_id: Mapped[str] = mapped_column(ForeignKey("generation_jobs.id"))
    qa_status: Mapped[str] = mapped_column(String(20))
    qa_report: Mapped[dict] = mapped_column(JSON)
    approval_status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    provenance: Mapped[dict] = mapped_column(JSON)


class Review(Record, Base):
    __tablename__ = "reviews"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[str] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(30))
    comment: Mapped[str] = mapped_column(Text, default="")


class Approval(Record, Base):
    __tablename__ = "approvals"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[str] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer)
    approver_id: Mapped[str] = mapped_column(ForeignKey("users.id"))


class Template(Record, Base):
    __tablename__ = "templates"
    org_id: Mapped[str | None] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(30))
    config: Mapped[dict] = mapped_column(JSON)
    storage_key: Mapped[str | None] = mapped_column(Text)
    official_flag: Mapped[bool] = mapped_column(Boolean, default=False)


class PromptPack(Record, Base):
    __tablename__ = "prompt_packs"
    version: Mapped[str] = mapped_column(String(30))
    sha256: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)


class ModelManifest(Record, Base):
    __tablename__ = "model_manifests"
    version: Mapped[str] = mapped_column(String(80))
    sha256: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)


class WorkflowManifest(Record, Base):
    __tablename__ = "workflow_manifests"
    version: Mapped[str] = mapped_column(String(80))
    sha256: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)


class ReleaseManifest(Record, Base):
    __tablename__ = "release_manifests"
    version: Mapped[str] = mapped_column(String(80))
    data: Mapped[dict] = mapped_column(JSON)


class AuditEvent(Record, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str] = mapped_column(String(36))
    org_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str] = mapped_column(String(36), default="system")
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[str] = mapped_column(String(100))
    result: Mapped[str] = mapped_column(String(30), default="SUCCESS")
    correlation_id: Mapped[str] = mapped_column(String(36))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
