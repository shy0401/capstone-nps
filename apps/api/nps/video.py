import json
import shutil
import subprocess
from pathlib import Path
from nps.config import settings
from nps.errors import DomainError
from nps.models import Artifact, ArtifactVersion
from nps.ppt import persist_artifact, template_for
from nps.rendering import preview_slide, run_process
from nps.storage import storage


def render_video(plan, output, policy, cancelled=lambda: None, previous_scenes=None, selected=None):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise DomainError("FFMPEG_UNAVAILABLE", 503)
    profile = json.loads(Path("templates/video-profile.json").read_text(encoding="utf-8"))
    fps, seconds = settings().video_fps, settings().video_scene_seconds
    scenes = []
    previous = {s["source_slide_id"]: s for s in (previous_scenes or [])}
    for slide in plan["slides"]:
        cancelled()
        old = previous.get(slide["slide_id"])
        if (
            old
            and slide["slide_id"] != selected
            and old["slide_version"] == slide["version"]
            and storage.path(old["storage_key"]).exists()
        ):
            scenes.append(old)
            continue
        image_key, image_path = storage.allocate("visuals", ".png")
        preview_slide(slide, image_path, policy)
        clip_key, clip = storage.allocate("visuals", ".mp4")
        frames = max(1, round(seconds * fps))
        vf = f"zoompan=z='min(zoom+0.0003,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={profile['width']}x{profile['height']}:fps={fps},format=yuv420p"
        run_process(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(image_path),
                "-vf",
                vf,
                "-frames:v",
                str(frames),
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "23",
                "-threads",
                "2",
                "-movflags",
                "+faststart",
                str(clip),
            ],
            cancelled,
        )
        scenes.append(
            {
                "source_slide_id": slide["slide_id"],
                "source_refs": slide["source_refs"],
                "slide_version": slide["version"],
                "scene_version": (old["scene_version"] + 1) if old else 1,
                "storage_key": clip_key,
                "preview_key": image_key,
                "duration": frames / fps,
                "mock": True,
            }
        )
    list_path = output.with_suffix(".concat.txt")
    # All filenames below are server UUIDs under the storage adapter.
    list_path.write_text(
        "\n".join(
            "file '" + storage.path(s["storage_key"]).resolve().as_posix().replace("'", "'\\''") + "'"
            for s in scenes
        ),
        encoding="utf-8",
    )
    try:
        run_process(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output),
            ],
            cancelled,
        )
    finally:
        list_path.unlink(missing_ok=True)
    return {
        "scenes": scenes,
        "profile": {**profile, "fps": fps, "scene_seconds": seconds},
        "renderer": "cpu-mock-pan-zoom",
        "mock": True,
    }


def qa_video(path, storyboard):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise DomainError("FFPROBE_UNAVAILABLE", 503)
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True,
        timeout=30,
        check=False,
    )
    issues = []
    if result.returncode or path.stat().st_size == 0:
        return {"status": "FAIL", "issues": ["VID-STRUCT"]}
    data = json.loads(result.stdout)
    videos = [s for s in data["streams"] if s["codec_type"] == "video"]
    profile = storyboard["profile"]
    if len(videos) != 1:
        issues.append("VID-STREAMS")
    else:
        stream = videos[0]
        if (stream["codec_name"], stream["width"], stream["height"], stream.get("pix_fmt")) != (
            "h264",
            profile["width"],
            profile["height"],
            "yuv420p",
        ):
            issues.append("VID-FORMAT")
        numerator, denominator = map(int, stream["avg_frame_rate"].split("/"))
        if not denominator or abs(numerator / denominator - profile["fps"]) > 0.01:
            issues.append("VID-FPS")
    duration = float(data["format"].get("duration", 0))
    if abs(duration - sum(s["duration"] for s in storyboard["scenes"])) > 0.15:
        issues.append("VID-DURATION")
    if any(not s["source_refs"] or not s["source_slide_id"] for s in storyboard["scenes"]):
        issues.append("VID-EVID")
    # Decode every frame: ffprobe metadata alone does not prove lack of corruption.
    decode = subprocess.run(
        [shutil.which("ffmpeg"), "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        timeout=120,
    )
    if decode.returncode:
        issues.append("VID-DECODE")
    return {
        "status": "FAIL" if issues else "PASS",
        "issues": issues,
        "duration": duration,
        "width": videos[0]["width"] if videos else None,
        "height": videos[0]["height"] if videos else None,
        "codec": videos[0]["codec_name"] if videos else None,
        "ffprobe": data,
        "all_frames_decoded": decode.returncode == 0,
    }


def render_step(db, job, plan, cancelled):
    previous = None
    if job.payload.get("artifact_id"):
        artifact = db.get(Artifact, job.payload["artifact_id"])
        previous = (
            db.get(ArtifactVersion, artifact.current_version_id)
            .provenance.get("storyboard", {})
            .get("scenes")
        )
    key, path = storage.allocate("artifacts", ".mp4")
    storyboard = render_video(
        plan.data, path, template_for(db, plan).config, cancelled, previous, job.payload.get("slide_id")
    )
    return {"storage_key": key, "storyboard": storyboard}


def qa_step(db, job, plan):
    from nps.pipeline import result_for

    result = result_for(db, job, "VIDEO")
    qa = qa_video(storage.path(result["storage_key"]), result["storyboard"])
    return persist_artifact(
        db,
        job,
        plan,
        "MP4",
        result["storage_key"],
        qa,
        {"storyboard": result["storyboard"], "video_mock": True},
    )
