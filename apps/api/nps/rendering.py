import subprocess
import time
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from nps.config import settings
from nps.errors import DomainError


def font_file():
    candidates = [
        settings().font_path,
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgun.ttf",
    ]
    for path in candidates:
        if path and Path(path).is_file():
            return path
    raise DomainError("KOREAN_FONT_UNAVAILABLE", 503)


def wrap_text(text, font, width):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for char in paragraph:
            if current and font.getlength(current + char) > width:
                lines.append(current)
                current = char
            else:
                current += char
        lines.append(current)
    return lines


@lru_cache(maxsize=32)
def metric_font(path, size):
    return ImageFont.truetype(path, size)


def text_fits(text, points, width_inches, height_inches):
    font = metric_font(font_file(), round(points * 96 / 72))
    lines = wrap_text(text, font, width_inches * 96)
    return len(lines) * points * 96 / 72 * 1.3 <= height_inches * 96


def text_layout(text, width, height, preferred, minimum):
    """Preserve all paragraphs; fit at readable size, then flow into columns."""
    for columns in (1, 2, 3, 4):
        column_width = (width - 0.3 * (columns - 1)) / columns
        for size in range(int(preferred), int(minimum) - 1, -1):
            parts, current = [], []
            for paragraph in text.split("\n"):
                candidate = "\n".join(current + [paragraph])
                if current and not text_fits(candidate, size, column_width - 0.12, height - 0.08):
                    parts.append("\n".join(current))
                    current = []
                current.append(paragraph)
            parts.append("\n".join(current))
            if len(parts) <= columns and all(
                text_fits(p, size, column_width - 0.12, height - 0.08) for p in parts
            ):
                return size, column_width, parts
    # No text is discarded. PPT QA will route the oversized draft to review.
    return minimum, width, [text]


def preview_slide(slide, path, policy, image_path=None):
    """CPU storyboard preview of actual slide text/table, visibly marked mock."""
    if policy.get("design_engine") == "editorial-2":
        from nps.presentation_design import preview

        return preview(slide, path, policy, image_path)
    image = Image.new("RGB", (1920, 1080), "#" + policy["background"])
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(font_file(), 58)
    small = ImageFont.truetype(font_file(), 25)
    draw.text((90, 80), slide["title"], font=title_font, fill="#" + policy["foreground"])
    y = 1.65 * 144
    available = 4.7 / len(slide["content_blocks"])
    for block in slide["content_blocks"]:
        text = (
            "\n".join("   |   ".join(row) for row in block.get("cells", []))
            if block["type"] in {"table", "chart"}
            else block.get("text", "")
        )
        size, width, parts = text_layout(text, 12, available - 0.1, policy["body_pt"], policy["min_font_pt"])
        body_font = ImageFont.truetype(font_file(), round(size * 2))
        for index, part in enumerate(parts):
            if not text_fits(part, size, width - 0.12, available - 0.18):
                raise DomainError("VIDEO_CONTENT_OVERFLOW", 422)
            for row, line in enumerate(wrap_text(part, body_font, (width - 0.12) * 144)):
                draw.text(
                    (94 + index * (width + 0.3) * 144, y + row * size * 2 * 1.3),
                    line,
                    font=body_font,
                    fill="#" + policy["foreground"],
                )
        y += available * 144
    if image_path:
        with Image.open(image_path) as visual:
            visual.thumbnail((800, 500))
            image.paste(visual, (1000, 450))
    draw.text((90, 1015), "MOCK / CPU PREVIEW · 내부 개발용 · 근거 연결됨", font=small, fill="#456776")
    image.save(path, "PNG")


def run_process(args, cancelled, timeout=180):
    import tempfile

    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=errors)
        start = time.monotonic()
        try:
            while process.poll() is None:
                cancelled()
                if time.monotonic() - start > timeout:
                    raise DomainError("RENDER_TIMEOUT", 422)
                time.sleep(0.1)
            if process.returncode:
                raise DomainError("RENDER_FAILED", 422)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
