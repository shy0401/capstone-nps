import hashlib
import ipaddress
import json
import socket
from pathlib import Path
from urllib.parse import urlparse
import httpx
from pydantic import ValidationError
from nps.chunking import validate_evidence
from nps.config import settings
from nps.contracts import (
    ContentBlock,
    Contract,
    Evidence,
    PlannedSlide,
    SemanticChunk,
    SlidePlanContract,
    VisualPlan,
)
from nps.errors import DomainError


class StageOutput(Contract):
    task: str
    items: list[str]
    mock: bool


def prompt_pack():
    raw = Path("prompts/slide-v1.json").read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def local_url(url, hosts):
    parsed = urlparse(url)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or parsed.hostname not in hosts.split(",")
    ):
        raise DomainError("AI_EXTERNAL_URL_DENIED", 503)
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 80)
        if any(
            not (ipaddress.ip_address(a[4][0]).is_private or ipaddress.ip_address(a[4][0]).is_loopback)
            for a in addresses
        ):
            raise DomainError("AI_EXTERNAL_URL_DENIED", 503)
    except socket.gaierror:
        raise DomainError("AI_BACKEND_UNAVAILABLE", 503) from None
    return url.rstrip("/")


def evidence(chunk):
    return Evidence(
        document_version_id=chunk.version_id,
        chunk_id=chunk.chunk_id,
        page=chunk.source_location.page,
        section=chunk.section_id,
        node_ids=chunk.table_refs + chunk.image_refs,
    )


class MockLLMAdapter:
    mode = "mock"

    def generate(self, task, payload):
        chunks = [SemanticChunk.model_validate(c) for c in payload["chunks"]]
        if task != "slide_plan":
            return StageOutput(task=task, items=[c.text[:120] for c in chunks[:20]], mock=True).model_dump(
                mode="json"
            )
        pack, digest = prompt_pack()
        nodes = {n["node_id"]: n for s in payload["normalized"]["sections"] for n in s["nodes"]}
        slides = []
        for chunk in chunks:
            ref = evidence(chunk)
            blocks = []
            if chunk.table_refs:
                node = nodes[str(chunk.table_refs[0])]
                cells = node["cells"]
                # Preserve every cell. Oversized tables are paginated, never silently truncated.
                if any(len(r) > 8 for r in cells) or any(len(c) > 120 for r in cells for c in r):
                    raise DomainError("PLAN_TABLE_REVIEW_REQUIRED", 422)
                for offset in range(1, len(cells), 7):
                    blocks.append(
                        ContentBlock(
                            type="table", cells=[cells[0]] + cells[offset : offset + 7], source_refs=[ref]
                        )
                    )
                if len(cells) == 1:
                    blocks.append(ContentBlock(type="table", cells=cells, source_refs=[ref]))
            elif chunk.image_refs:
                blocks = [ContentBlock(type="image", text="원문 이미지", source_refs=[ref])]
            else:
                blocks = [
                    ContentBlock(text=chunk.text[i : i + 400], source_refs=[ref])
                    for i in range(0, len(chunk.text), 400)
                ]
            for block in blocks:
                slides.append(
                    PlannedSlide(
                        order=len(slides) + 1,
                        title=f"문서 검토 · {chunk.section_id}",
                        layout_type=block.type if block.type in {"table", "image"} else "title_content",
                        content_blocks=[block],
                        source_refs=[ref],
                        visual_plan=VisualPlan(
                            mode="preserve" if block.type in {"table", "image"} else "none"
                        ),
                    )
                )
        model_hash = hashlib.sha256(Path("services/llm-adapter/model-manifest.json").read_bytes()).hexdigest()
        return SlidePlanContract(
            document_versions=list({c.version_id for c in chunks}),
            title="문서 검토 계획",
            slides=slides,
            mock=True,
            provenance={
                "prompt_pack_version": pack["version"],
                "prompt_hash": digest,
                "model_manifest_id": "mock-extractive-1.0",
                "model_hash": model_hash,
                "schema_version": "1.0",
            },
        ).model_dump(mode="json")


class LocalLLMAdapter:
    def __init__(self, mode):
        self.mode = mode

    def generate(self, task, payload):
        base = local_url(settings().llm_backend_url, settings().llm_backend_hosts)
        pack, digest = prompt_pack()
        contract = SlidePlanContract if task == "slide_plan" else StageOutput
        schema = contract.model_json_schema()
        messages = [
            {"role": "system", "content": pack["system"] + " Task: " + task},
            {"role": "user", "content": json.dumps({"untrusted_document": payload}, ensure_ascii=False)},
        ]
        for attempt in range(settings().llm_retries + 1):
            try:
                with httpx.Client(
                    timeout=settings().llm_timeout, trust_env=False, follow_redirects=False
                ) as client:
                    if self.mode == "ollama":
                        response = client.post(
                            base + "/api/chat",
                            json={
                                "model": settings().llm_model,
                                "messages": messages,
                                "format": schema,
                                "stream": False,
                            },
                        )
                        response.raise_for_status()
                        data = json.loads(response.json()["message"]["content"])
                    else:
                        response = client.post(
                            base + "/v1/chat/completions",
                            json={
                                "model": settings().llm_model,
                                "messages": messages,
                                "response_format": {
                                    "type": "json_schema",
                                    "json_schema": {"name": task, "strict": True, "schema": schema},
                                },
                            },
                        )
                        response.raise_for_status()
                        data = json.loads(response.json()["choices"][0]["message"]["content"])
                result = contract.model_validate(data).model_dump(mode="json")
                result["mock"] = False
                if task == "slide_plan":
                    result["provenance"] = {
                        "prompt_pack_version": pack["version"],
                        "prompt_hash": digest,
                        "model_manifest_id": settings().llm_model,
                        "model_hash": "TBD-NPS-GPU-001",
                        "provider": self.mode,
                        "schema_version": "1.0",
                    }
                    validate_evidence(
                        SlidePlanContract.model_validate(result),
                        [SemanticChunk.model_validate(c) for c in payload["chunks"]],
                    )
                return result
            except (httpx.HTTPError, ValueError, KeyError, ValidationError, DomainError):
                if attempt == settings().llm_retries:
                    raise DomainError("LLM_INVALID_OUTPUT", 422) from None
        raise DomainError("LLM_INVALID_OUTPUT", 422)


def backend():
    if settings().llm_mode == "mock":
        return MockLLMAdapter()
    if settings().llm_mode in {"ollama", "openai_compatible_local"}:
        return LocalLLMAdapter(settings().llm_mode)
    raise DomainError("LLM_MODE_UNSUPPORTED", 503)


class LLMClient:
    """Worker boundary: only adapter service URLs are called from business code."""

    def generate(self, task, payload):
        try:
            response = httpx.post(
                settings().llm_adapter_url + "/generate",
                headers={"X-Adapter-Key": settings().adapter_secret},
                json={"task": task, "payload": payload},
                timeout=settings().llm_timeout * 3,
                trust_env=False,
            )
            if response.status_code >= 400:
                raise DomainError("LLM_ADAPTER_FAILED", 502)
            return response.json()
        except httpx.HTTPError:
            raise DomainError("LLM_ADAPTER_UNAVAILABLE", 503) from None
