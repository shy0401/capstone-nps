from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Role(StrEnum):
    USER = "User"
    REVIEWER = "Reviewer"
    ORG_ADMIN = "OrgAdmin"
    SYSTEM_ADMIN = "SystemAdmin"


class JobState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_REVIEW = "WAITING_REVIEW"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class SourceLocation(Contract):
    page: int | None = None
    section: str = ""
    paragraph: int | None = None
    table: int | None = None
    sheet: str | None = None


class Node(Contract):
    node_id: UUID = Field(default_factory=uuid4)
    type: Literal["heading", "paragraph", "table", "image"]
    text: str = ""
    source_location: SourceLocation
    cells: list[list[str]] = Field(default_factory=list)
    rows: int = 0
    cols: int = 0
    header: bool = False
    merges: list[dict] = Field(default_factory=list)
    image_key: str | None = None
    image_sha256: str | None = None

    @model_validator(mode="after")
    def dimensions(self):
        self.rows = len(self.cells)
        self.cols = max((len(row) for row in self.cells), default=0)
        return self


class Section(Contract):
    section_id: str
    heading: str
    nodes: list[Node]


class NormalizedDocument(Contract):
    schema_version: Literal["1.0"] = "1.0"
    metadata: dict
    sections: list[Section]
    parser_version: str
    warnings: list[str] = Field(default_factory=list)


class Evidence(Contract):
    document_version_id: UUID
    chunk_id: UUID
    page: int | None = None
    section: str
    node_ids: list[UUID] = Field(default_factory=list)


class SemanticChunk(Contract):
    chunk_id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    version_id: UUID
    section_id: str
    text: str
    token_count: int
    source_location: SourceLocation
    previous_chunk_id: UUID | None = None
    next_chunk_id: UUID | None = None
    table_refs: list[UUID] = Field(default_factory=list)
    image_refs: list[UUID] = Field(default_factory=list)
    security_class: str = "synthetic"


class VisualPlan(Contract):
    mode: Literal["preserve", "generate", "none", "controlnet", "ip_adapter"] = "none"
    workflow: str = "wf-image-v1"
    controlnet: Literal["canny", "depth"] | None = None
    ip_adapter: bool = False
    seed: int = 42
    prompt: str = Field(default="", max_length=1000)


class ContentBlock(Contract):
    type: Literal["text", "table", "chart", "image"] = "text"
    text: str = Field(default="", max_length=600)
    cells: list[list[str]] = Field(default_factory=list, max_length=12)
    source_refs: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def table_shape(self):
        if self.type in {"table", "chart"}:
            if not self.cells or not self.cells[0] or len(self.cells[0]) > 8:
                raise ValueError("invalid table dimensions")
            if any(len(row) != len(self.cells[0]) for row in self.cells):
                raise ValueError("ragged table")
            if any(len(c) > 120 for r in self.cells for c in r):
                raise ValueError("table cell too long")
        return self


class PlannedSlide(Contract):
    slide_id: UUID = Field(default_factory=uuid4)
    version: int = 1
    order: int = Field(ge=1)
    layout_type: Literal[
        "title_content", "table", "chart", "image", "cover", "key_points", "process", "comparison"
    ] = "title_content"
    title: str = Field(min_length=1, max_length=80)
    content_blocks: list[ContentBlock] = Field(min_length=1, max_length=5)
    source_refs: list[Evidence] = Field(min_length=1)
    visual_plan: VisualPlan = Field(default_factory=VisualPlan)


class SlidePlanContract(Contract):
    schema_version: Literal["1.0"] = "1.0"
    plan_id: UUID = Field(default_factory=uuid4)
    document_versions: list[UUID] = Field(min_length=1)
    title: str = Field(min_length=1, max_length=120)
    audience: Literal["internal"] = "internal"
    slides: list[PlannedSlide] = Field(min_length=1, max_length=40)
    mock: bool
    provenance: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_slides(self):
        if len({s.slide_id for s in self.slides}) != len(self.slides):
            raise ValueError("duplicate slide IDs")
        if [s.order for s in self.slides] != list(range(1, len(self.slides) + 1)):
            raise ValueError("invalid order")
        return self
