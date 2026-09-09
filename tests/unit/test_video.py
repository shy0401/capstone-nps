import importlib.util
import json
from pathlib import Path
from nps.video import qa_video, render_video


def test_valid_cpu_mp4(tmp_path, monkeypatch):
    from nps.config import settings

    monkeypatch.setattr(settings(), "storage_root", tmp_path / "storage")
    spec = importlib.util.spec_from_file_location("ppt_test", "tests/unit/test_ppt.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "sample.mp4"
    storyboard = render_video(
        module.sample_plan(), path, json.loads(Path("templates/default.json").read_text(encoding="utf-8"))
    )
    qa = qa_video(path, storyboard)
    assert qa["status"] == "PASS", qa
    assert (qa["width"], qa["height"], qa["codec"]) == (1920, 1080, "h264")
    assert qa["all_frames_decoded"]
