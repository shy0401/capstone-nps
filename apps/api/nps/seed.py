"""Idempotent synthetic dev seed; never embeds passwords."""

import json
from sqlalchemy import select
from nps.auth import hasher
from nps.config import settings
from nps.db import SessionLocal
from nps.models import OrganizationUnit, Project, ProjectMember, Template, User


def seed(db, password):
    if not password:
        return
    if db.scalar(select(User).limit(1)):
        return
    template = Template(
        name="내부 개발용 템플릿",
        version="1.0",
        official_flag=False,
        config=json.loads(settings().template_policy.read_text(encoding="utf-8")),
    )
    db.add(template)
    orgs = [OrganizationUnit(name=f"합성 연구조직 {i}", code=f"synthetic-{i}") for i in (1, 2)]
    db.add_all(orgs)
    db.flush()
    for index, org in enumerate(orgs):
        users = []
        roles = ["User", "Reviewer", "OrgAdmin", "SystemAdmin"] if index == 0 else ["User"]
        for role in roles:
            user = User(
                username=f"demo-{role.lower()}" if index == 0 else "other-user",
                password_hash=hasher.hash(password),
                role=role,
                org_id=org.id,
            )
            db.add(user)
            users.append(user)
        db.flush()
        project = Project(
            name=f"합성 데이터 검증 프로젝트 {index + 1}",
            org_id=org.id,
            owner_id=users[0].id,
            template_id=template.id,
        )
        db.add(project)
        db.flush()
        for user in users:
            db.add(ProjectMember(project_id=project.id, user_id=user.id, role=user.role))
    db.commit()


if __name__ == "__main__":
    if settings().environment == "dev":
        with SessionLocal() as session:
            seed(session, settings().seed_password)
