import os
import secrets

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = secrets.token_urlsafe(40)
os.environ["ADAPTER_SECRET"] = secrets.token_urlsafe(40)
os.environ["ENVIRONMENT"] = "dev"
os.environ["SCAN_MODE"] = "mock"
os.environ["DEV_INSECURE_COOKIE"] = "true"

import pytest  # noqa: E402
from nps.db import Base, engine, SessionLocal  # noqa: E402
from nps.seed import seed  # noqa: E402


@pytest.fixture
def db(tmp_path, monkeypatch):
    from nps.config import settings

    monkeypatch.setattr(settings(), "storage_root", tmp_path / "storage")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed(session, "synthetic-test-" + "passphrase")
        yield session


@pytest.fixture
def client(db):
    from fastapi.testclient import TestClient
    from nps.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def users(db):
    from sqlalchemy import select
    from nps.models import User

    return {u.username: u for u in db.scalars(select(User))}
