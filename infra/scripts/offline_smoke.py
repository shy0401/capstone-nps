"""Execute in a fresh venv, dependencies installed with --no-index --require-hashes."""

import json
import socket
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/api"))


def deny_network(*args, **kwargs):
    raise RuntimeError("OFFLINE_NETWORK_CALL_DENIED")


socket.create_connection = deny_network
socket.getaddrinfo = deny_network
from nps.contracts import ContentBlock, Evidence, PlannedSlide, SlidePlanContract  # noqa: E402
from nps.ppt import render_ppt, qa_ppt  # noqa: E402
from nps.video import render_video, qa_video  # noqa: E402

ref = Evidence(document_version_id=uuid4(), chunk_id=uuid4(), section="offline-synthetic")
plan = SlidePlanContract(
    title="오프라인 합성 검증",
    document_versions=[ref.document_version_id],
    mock=True,
    provenance={"mode": "offline-mock"},
    slides=[
        PlannedSlide(
            order=1,
            title="오프라인 합성 검증",
            source_refs=[ref],
            content_blocks=[ContentBlock(text="이 자료는 공개 합성 데이터입니다.", source_refs=[ref])],
        )
    ],
).model_dump(mode="json")
policy = json.loads((ROOT / "templates/default.json").read_text(encoding="utf-8"))
out = ROOT / "test-results/offline-samples"
out.mkdir(parents=True, exist_ok=True)
render_ppt(plan, out / "offline.pptx", policy)
ppt = qa_ppt(out / "offline.pptx", plan, policy)
storyboard = render_video(plan, out / "offline.mp4", policy)
video = qa_video(out / "offline.mp4", storyboard)
result = {
    "host_dependency_subgate": "PASS" if ppt["status"] == video["status"] == "PASS" else "FAIL",
    "pip_no_index": True,
    "python_socket_dns": "DENIED",
    "ppt_qa": ppt["status"],
    "video_qa": video["status"],
    "full_offline_gate": "BLOCKED",
    "reason": "Clean Docker host/image import/ClamAV signatures/rollback not yet verified",
    "limitations": "Host ffmpeg and installed Korean font are reused; socket guard applies to Python only, not host network namespace",
}
(ROOT / "test-results/offline-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["host_dependency_subgate"] == "PASS" else 1)
