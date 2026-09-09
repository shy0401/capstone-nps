import base64
import hashlib
import io
import json
import time
from pathlib import Path
import httpx
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select
from nps.config import settings
from nps.contracts import VisualPlan
from nps.errors import DomainError
from nps.llm import local_url
from nps.models import ParseResult, VisualAsset
from nps.rendering import font_file
from nps.storage import storage


def workflow_metadata(plan):
    if plan.workflow != "wf-image-v1":
        raise DomainError("WORKFLOW_NOT_ALLOWED", 422)
    path = Path("workflows/comfy/wf-image-v1.json")
    raw = path.read_bytes()
    workflow = json.loads(raw)
    lock = json.loads(Path("workflows/comfy/custom_nodes.lock.json").read_bytes())
    for node in lock["nodes"]:
        if not node.get("commit") or len(node.get("sha256", "")) != 64:
            raise DomainError("WORKFLOW_UNLOCKED", 422)
    return workflow, {
        "workflow_version": workflow["workflow_version"],
        "workflow_sha256": hashlib.sha256(raw).hexdigest(),
        "custom_nodes_lock": lock,
        "model_manifest": json.loads(Path("workflows/comfy/model-manifest.json").read_bytes()),
        "seed": plan.seed,
        "prompt_hash": hashlib.sha256(plan.prompt.encode()).hexdigest(),
        "visual_mode": plan.mode,
        "controlnet": plan.controlnet,
        "ip_adapter": plan.ip_adapter,
    }


class MockComfyAdapter:
    def generate(self, plan):
        _, metadata = workflow_metadata(plan)
        image = Image.new("RGB", (960, 540), "#e3edf0")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_file(), 36)
        draw.text(
            (60, 180),
            "MOCK PLACEHOLDER\n합성 이미지 검증용\n" + plan.mode,
            font=font,
            fill="#1b5261",
            spacing=15,
        )
        output = io.BytesIO()
        image.save(output, "PNG")
        return {
            "image_base64": base64.b64encode(output.getvalue()).decode(),
            "provenance": {**metadata, "mock": True},
        }


class RealComfyAdapter:
    def generate(self, plan):
        workflow, metadata = workflow_metadata(plan)
        if not workflow.get("graph") or workflow.get("mode") != "real":
            raise DomainError("COMFY_WORKFLOW_NOT_CONFIGURED", 503)
        graph = json.loads(json.dumps(workflow["graph"]).replace("${PROMPT}", json.dumps(plan.prompt)[1:-1]))
        # Seed inputs are replaced as values, never injected as executable code.
        for node in graph.values():
            if "seed" in node.get("inputs", {}):
                node["inputs"]["seed"] = plan.seed
        if plan.mode not in workflow["supported_modes"]:
            raise DomainError("COMFY_CAPABILITY_UNSUPPORTED", 422)
        base = local_url(settings().comfy_backend_url, settings().comfy_backend_hosts)
        try:
            with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as client:
                response = client.post(base + "/prompt", json={"prompt": graph})
                response.raise_for_status()
                prompt_id = response.json()["prompt_id"]
                started = time.monotonic()
                while time.monotonic() - started < 120:
                    history = client.get(base + "/history/" + prompt_id)
                    history.raise_for_status()
                    record = history.json().get(prompt_id)
                    if record:
                        if record.get("status", {}).get("status_str") == "error":
                            raise DomainError("COMFY_GENERATION_FAILED", 502)
                        for output in record.get("outputs", {}).values():
                            for image in output.get("images", []):
                                filename = image["filename"]
                                if "/" in filename or "\\" in filename or ".." in filename:
                                    raise DomainError("COMFY_OUTPUT_UNSAFE", 502)
                                asset = client.get(
                                    base + "/view",
                                    params={
                                        "filename": filename,
                                        "subfolder": image.get("subfolder", ""),
                                        "type": "output",
                                    },
                                )
                                asset.raise_for_status()
                                if len(asset.content) > 25 * 1024 * 1024:
                                    raise DomainError("COMFY_OUTPUT_TOO_LARGE", 502)
                                with Image.open(io.BytesIO(asset.content)) as png:
                                    png.verify()
                                return {
                                    "image_base64": base64.b64encode(asset.content).decode(),
                                    "provenance": {**metadata, "mock": False, "prompt_id": prompt_id},
                                }
                    time.sleep(0.5)
                client.post(base + "/interrupt")
                raise DomainError("COMFY_TIMEOUT", 504)
        except (httpx.HTTPError, KeyError, ValueError):
            raise DomainError("COMFY_BACKEND_FAILED", 502) from None


class ComfyClient:
    def generate(self, plan):
        try:
            result = httpx.post(
                settings().comfy_adapter_url + "/generate",
                json=plan.model_dump(mode="json"),
                headers={"X-Adapter-Key": settings().adapter_secret},
                timeout=150,
                trust_env=False,
            )
            if result.status_code >= 400:
                raise DomainError("COMFY_ADAPTER_FAILED", 502)
            return result.json()
        except httpx.HTTPError:
            raise DomainError("COMFY_ADAPTER_UNAVAILABLE", 503) from None


def generate_visuals(db, job, plan, cancelled):
    assets = []
    nodes = {
        n["node_id"]: n
        for parse in db.scalars(
            select(ParseResult).where(ParseResult.document_version_id.in_(plan.data["document_versions"]))
        )
        for section in parse.data["sections"]
        for n in section["nodes"]
    }
    for slide in plan.data["slides"]:
        cancelled()
        existing = db.scalar(
            select(VisualAsset)
            .where(
                VisualAsset.plan_id == plan.id,
                VisualAsset.slide_id == slide["slide_id"],
                VisualAsset.version == slide["version"],
            )
            .order_by(VisualAsset.created_at.desc())
        )
        if existing and job.payload.get("slide_id") != slide["slide_id"]:
            assets.append(existing.id)
            continue
        visual = VisualPlan.model_validate(slide["visual_plan"])
        if visual.mode == "none":
            continue
        if visual.mode == "preserve":
            for block in slide["content_blocks"]:
                if block["type"] != "image":
                    continue
                for ref in block["source_refs"]:
                    for node_id in ref["node_ids"]:
                        node = nodes.get(node_id)
                        if node and node.get("image_key"):
                            asset = VisualAsset(
                                project_id=plan.project_id,
                                plan_id=plan.id,
                                slide_id=slide["slide_id"],
                                version=slide["version"],
                                storage_key=node["image_key"],
                                provenance={
                                    "mode": "preserve",
                                    "mock": False,
                                    "node_id": node_id,
                                    "source_refs": block["source_refs"],
                                },
                            )
                            db.add(asset)
                            db.flush()
                            assets.append(asset.id)
            continue
        result = ComfyClient().generate(visual)
        cancelled()
        content = base64.b64decode(result["image_base64"], validate=True)
        if len(content) > 25 * 1024 * 1024:
            raise DomainError("COMFY_OUTPUT_TOO_LARGE", 502)
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        key, path = storage.allocate("visuals", ".png")
        path.write_bytes(content)
        asset = VisualAsset(
            project_id=plan.project_id,
            plan_id=plan.id,
            slide_id=slide["slide_id"],
            version=slide["version"],
            storage_key=key,
            provenance=result["provenance"],
        )
        db.add(asset)
        db.flush()
        assets.append(asset.id)
    return {"visual_asset_ids": assets, "mode": settings().comfy_mode}
