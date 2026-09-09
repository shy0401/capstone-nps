import pytest
from sqlalchemy import select
from nps.auth import authorize_project, consume_refresh, create_refresh, hasher, issue_access, user_from_token
from nps.errors import DomainError
from nps.models import Project, ProjectMember


def test_argon_and_access(db, users):
    user = users["demo-user"]
    assert user.password_hash.startswith("$argon2id$")
    assert hasher.verify(user.password_hash, "synthetic-test-passphrase")
    assert user_from_token(db, issue_access(user)).id == user.id


@pytest.mark.parametrize("role", ["user", "reviewer", "orgadmin", "systemadmin"])
def test_cross_org_idor(db, users, role):
    project = db.scalar(select(Project).where(Project.org_id == users["other-user"].org_id))
    with pytest.raises(DomainError, match="AUTH_FORBIDDEN"):
        authorize_project(db, users[f"demo-{role}"], project.id)


def test_system_admin_still_needs_membership(db, users):
    user = users["demo-systemadmin"]
    member = db.scalar(select(ProjectMember).where(ProjectMember.user_id == user.id))
    project_id = member.project_id
    db.delete(member)
    db.commit()
    with pytest.raises(DomainError, match="AUTH_FORBIDDEN"):
        authorize_project(db, user, project_id)


def test_refresh_rotation(db, users):
    token = create_refresh(db, users["demo-user"])
    db.commit()
    assert consume_refresh(db, token).id == users["demo-user"].id
    db.commit()
    with pytest.raises(DomainError, match="AUTH_REFRESH_INVALID"):
        consume_refresh(db, token)
