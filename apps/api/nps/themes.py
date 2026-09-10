"""Durable design retrieval. Style memory is not model weight training."""

import json
import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from sqlalchemy import or_, select
from nps.errors import DomainError
from nps.models import Template

BASE = {
    "version": "2.0",
    "official_flag": False,
    "font": "Noto Sans CJK KR",
    "title_pt": 32,
    "body_pt": 24,
    "min_font_pt": 18,
    "line_spacing": 1.22,
    "safe_margin_inches": 0.5,
    "width_inches": 13.333333,
    "height_inches": 7.5,
    "background": "F7F9FC",
    "foreground": "142D43",
    "accent": "217C82",
    "image_policy": "contain",
    "official_spec": "TBD-NPS-OUT-001",
    "design_engine": "editorial-2",
}


def visible_templates(db, org_id):
    return db.scalars(select(Template).where(or_(Template.org_id.is_(None), Template.org_id == org_id))).all()


def scoped_template(db, template_id, org_id):
    template = db.get(Template, str(template_id))
    if not template or template.org_id not in {None, org_id}:
        raise DomainError("TEMPLATE_NOT_FOUND", 404)
    return template


def seed_themes(db):
    path = Path("templates/catalog.json")
    if not path.exists():
        return
    for spec in json.loads(path.read_text(encoding="utf-8")):
        ident = str(uuid5(NAMESPACE_URL, "nps-theme:" + spec["slug"]))
        row = db.get(Template, ident)
        if row is None:
            row = Template(id=ident, name=spec["name"], version="2.0", org_id=None, config={})
            db.add(row)
        row.config = {**BASE, **spec, "source": "bundled"}
    db.flush()


def choose_theme(db, project, plan):
    if project.template_id:
        candidate = scoped_template(db, project.template_id, project.org_id)
        if candidate.config.get("design_engine") == "editorial-2":
            return candidate
    content = plan["title"] + " " + " ".join(s["title"] for s in plan["slides"])
    tokens = set(re.findall(r"[가-힣A-Za-z]{2,}", content.lower()))
    candidates = [
        t for t in visible_templates(db, project.org_id) if t.config.get("design_engine") == "editorial-2"
    ]
    if not candidates:
        raise DomainError("TEMPLATE_NOT_FOUND", 404)

    def score(t):
        tags = set(t.config.get("tags", []))
        overlap = sum(1 for tag in tags if tag in content.lower() or tag in tokens)
        # Newly learned designs are preferred when relevance ties, within the same organization.
        learned = t.config.get("source") == "uploaded-reference"
        default = t.config.get("slug") == "editorial-navy"
        return (overlap, learned, default, str(t.created_at), t.id)

    return max(candidates, key=score)


def attach_theme(db, project, plan):
    selected = choose_theme(db, project, plan)
    plan["provenance"] = {
        **plan["provenance"],
        "design_engine": "editorial-2",
        "theme_id": selected.id,
        "theme_name": selected.name,
        "theme_policy": selected.config,
        "theme_selection": "project-selected"
        if project.template_id == selected.id
        else "organization-style-retrieval",
        "learning_method": "style-feature-memory; no model weight training",
    }


def plan_theme(db, plan):
    ident = plan.data.get("provenance", {}).get("theme_id")
    if ident:
        from nps.models import Project

        return scoped_template(db, ident, db.get(Project, plan.project_id).org_id)
    return None
