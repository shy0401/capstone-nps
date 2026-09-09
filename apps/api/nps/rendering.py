import subprocess
import time
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


def text_fits(text, points, width_inches, height_inches):
    font = ImageFont.truetype(font_file(), round(points * 96 / 72))
    lines = wrap_text(text, font, width_inches * 96)
    return len(lines) * points * 96 / 72 * 1.3 <= height_inches * 96


def preview_slide(slide, path, policy, image_path=None):
    """CPU storyboard preview of actual slide text/table, visibly marked mock."""
    image = Image.new("RGB", (1920, 1080), "#" + policy["background"])
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(font_file(), 58)
    body_font = ImageFont.truetype(font_file(), 38)
    small = ImageFont.truetype(font_file(), 25)
    draw.text((90, 80), slide["title"], font=title_font, fill="#" + policy["foreground"])
    y = 240
    for block in slide["content_blocks"]:
        text = (
            "\n".join("   |   ".join(row) for row in block.get("cells", []))
            if block["type"] in {"table", "chart"}
            else block.get("text", "")
        )
        for line in wrap_text(text, body_font, 1700):
            draw.text((90, y), line, font=body_font, fill="#" + policy["foreground"])
            y += 55
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
