"""CPU extractive presentation editing; source text is data, never instructions.

The local LLM adapter can rewrite semantically. This fallback ranks and condenses
source sentences without claiming generative understanding or weight training.
"""

import re
from collections import Counter
from pathlib import Path
from nps.contracts import ContentBlock, PlannedSlide, SlidePlanContract, VisualPlan

KEYWORDS = (
    "목표",
    "핵심",
    "결과",
    "성과",
    "문제",
    "개선",
    "추진",
    "계획",
    "증가",
    "감소",
    "비교",
    "효과",
    "필요",
)


def sentences(text):
    result = []
    for value in re.split(r"\n+|(?<=[.!?。])\s+", text):
        value = re.sub(r"^[\s○●□■▪•·\-*]+", "", value).strip()
        value = re.sub(r"\s+", " ", value)
        if len(value) >= 5 and not re.fullmatch(r"[\d\s.\-/]+", value) and value not in result:
            result.append(value)
    return result


def compact(text, limit=94):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    # A visible ellipsis signals omitted wording; numbers are never paraphrased.
    prefix = text[: limit - 1]
    boundary = max(prefix.rfind(" "), prefix.rfind(","), prefix.rfind(";"))
    return prefix[: boundary if boundary > limit * 0.55 else len(prefix)].rstrip() + "…"


def draft(payload, chunks, ref_for, provenance):
    all_text = " ".join(c.text for c in chunks)
    frequency = Counter(re.findall(r"[가-힣A-Za-z]{2,}", all_text.lower()))

    def rank(text):
        words = set(re.findall(r"[가-힣A-Za-z]{2,}", text.lower()))
        return (
            sum(min(frequency[w], 8) for w in words) / max(1, len(words))
            + sum(k in text for k in KEYWORDS) * 2
            + bool(re.search(r"\d[%건명억만년월]", text)) * 2
        )

    nodes = {n["node_id"]: n for section in payload["normalized"]["sections"] for n in section["nodes"]}
    headings = {s["section_id"]: s.get("heading", "") for s in payload["normalized"]["sections"]}
    # Prefer distinctive, informative sections; do not map every raw chunk to a slide.
    ranked = sorted(
        enumerate(chunks),
        key=lambda pair: rank(pair[1].text) + (2 if pair[1].table_refs or pair[1].image_refs else 0),
        reverse=True,
    )
    selected, seen = [], set()
    for index, chunk in ranked:
        key = re.sub(r"\W", "", chunk.text)[:100]
        if key in seen:
            continue
        seen.add(key)
        selected.append((index, chunk))
        if len(selected) >= 10:
            break
    selected.sort(key=lambda pair: pair[0])
    slides = []
    for index, chunk in selected:
        ref = ref_for(chunk)
        text_sentences = sentences(chunk.text)
        chosen = sorted(sorted(enumerate(text_sentences), key=lambda v: rank(v[1]), reverse=True)[:3])
        bullets = [compact(v) for _, v in chosen]
        heading = headings.get(chunk.section_id, "")
        if not heading or heading == chunk.section_id or len(heading) > 64 or heading.startswith("HWP "):
            heading = bullets[0] if bullets else "원문 자료"
        title = compact(heading, 44)
        if len(bullets) > 1:
            bullets = [b for b in bullets if b != title] or bullets
        layout, visual = "key_points", VisualPlan()
        if chunk.table_refs and str(chunk.table_refs[0]) in nodes:
            node = nodes[str(chunk.table_refs[0])]
            cells = node["cells"]
            # Large tables are explicitly excerpted for presentation, with source evidence retained.
            excerpt = [[compact(str(c), 45) for c in row[:5]] for row in cells[:7]]
            numeric = (
                len(excerpt) > 1
                and 2 <= len(excerpt[0]) <= 3
                and all(re.fullmatch(r"-?\d+(\.\d+)?", c) for row in excerpt[1:] for c in row[1:])
            )
            if not numeric:
                excerpt = [[compact(str(c), 26) for c in row[:4]] for row in cells[:4]]
            layout = "chart" if numeric else "table"
            block = ContentBlock(
                type=layout,
                cells=excerpt,
                source_refs=[ref],
                text="원문 표 발췌"
                if len(cells) > len(excerpt) or len(cells[0]) > len(excerpt[0])
                else "원문 표",
            )
        elif chunk.image_refs:
            layout, visual = "image", VisualPlan(mode="preserve")
            block = ContentBlock(type="image", text=title, source_refs=[ref])
        else:
            if not bullets:
                continue
            if len(bullets) >= 2 and any(word in chunk.text for word in ("단계", "절차", "순서", "프로세스")):
                layout = "process"
            elif len(bullets) >= 2 and any(
                word in chunk.text for word in ("비교", "차이", "장점", "단점", "반면")
            ):
                layout = "comparison"
            block = ContentBlock(text="\n".join(bullets), source_refs=[ref])
        slides.append(
            PlannedSlide(
                order=len(slides) + 1,
                title=title,
                layout_type=layout,
                content_blocks=[block],
                source_refs=[ref],
                visual_plan=visual,
            )
        )
    if not slides:
        from nps.errors import DomainError

        raise DomainError("DOC_NO_PRESENTABLE_CONTENT", 422)
    title = compact(slides[0].title or Path(payload.get("document_title", "")).stem, 58)
    cover = PlannedSlide(
        order=1,
        title=title,
        layout_type="cover",
        content_blocks=[
            ContentBlock(
                text=compact(slides[0].content_blocks[0].text.split("\n")[0], 90),
                source_refs=slides[0].source_refs,
            )
        ],
        source_refs=slides[0].source_refs,
    )
    slides.insert(0, cover)
    for i, s in enumerate(slides):
        s.order = i + 1
    return SlidePlanContract(
        document_versions=list(dict.fromkeys(c.version_id for c in chunks)),
        title=title,
        slides=slides,
        mock=True,
        provenance={
            **provenance,
            "design_engine": "editorial-2",
            "content_strategy": "cpu-ranked-extractive-summary",
            "model_fine_tuned": False,
            "source_chunk_count": len(chunks),
            "selected_chunk_count": len(selected),
            "omitted_chunk_count": len(chunks) - len(selected),
            "editorial_notice": "발표용 핵심문장 발췌. 전체 원문은 근거에서 확인. 실제 LLM 요약 아님.",
        },
    ).model_dump(mode="json")
