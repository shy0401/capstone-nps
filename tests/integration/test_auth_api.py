from nps.auth import issue_access


def test_project_settings_and_owner_scope(client, users):
    h = {"Authorization": "Bearer " + issue_access(users["demo-user"])}
    project = client.get("/api/v1/projects", headers=h).json()[0]
    template = client.get("/api/v1/templates", headers=h).json()[0]
    data = {
        "name": "Synthetic edited",
        "description": "Synthetic only",
        "security_class": "synthetic-test",
        "template_id": template["id"],
    }
    url = f"/api/v1/projects/{project['id']}"
    reviewer = {"Authorization": "Bearer " + issue_access(users["demo-reviewer"])}
    assert client.patch(url, headers=reviewer, json=data).status_code == 403
    result = client.patch(url, headers=h, json=data)
    assert result.status_code == 200
    assert all(result.json()[k] == v for k, v in data.items())


def test_admin_users_scope_and_active_audit(client, users):
    h = {"Authorization": "Bearer " + issue_access(users["demo-orgadmin"])}
    normal = {"Authorization": "Bearer " + issue_access(users["demo-user"])}
    assert client.get("/api/v1/admin/users", headers=normal).status_code == 403
    rows = client.get("/api/v1/admin/users", headers=h).json()
    assert all(u["org_id"] == users["demo-orgadmin"].org_id for u in rows)
    assert all("password_hash" not in u for u in rows)
    target = users["demo-user"]
    assert (
        client.patch(
            f"/api/v1/admin/users/{target.id}", headers=h, json={"role": "Reviewer", "active": False}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/me", headers=normal).status_code == 401
    events = client.get("/api/v1/admin/audit", headers=h).json()
    event = next(e for e in events if e["action"] == "USER_ROLE_CHANGE")
    assert event["detail"]["old_active"] is True and event["detail"]["new_active"] is False


def test_login_refresh_logout(client):
    assert client.get("/api/v1/me").status_code == 401
    result = client.post(
        "/api/v1/auth/login", json={"username": "demo-user", "password": "synthetic-test-passphrase"}
    )
    assert result.status_code == 200
    cookie = result.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie
    token = client.post("/api/v1/auth/refresh").json()["access_token"]
    assert client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}).status_code == 204
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_scope_and_cors(client, users):
    auth = {"Authorization": "Bearer " + issue_access(users["demo-user"])}
    project = client.get("/api/v1/projects", headers=auth).json()[0]
    other = {"Authorization": "Bearer " + issue_access(users["other-user"])}
    assert client.get(f"/api/v1/projects/{project['id']}", headers=other).status_code == 403
    assert client.get("/api/v1/admin/audit", headers=auth).status_code == 403
    assert (
        client.options(
            "/api/v1/projects",
            headers={"Origin": "https://evil.invalid", "Access-Control-Request-Method": "GET"},
        ).status_code
        == 400
    )


def test_owner_can_choose_same_org_reviewer(client, users):
    auth = {"Authorization": "Bearer " + issue_access(users["demo-user"])}
    project = client.post("/api/v1/projects", headers=auth, json={"name": "Synthetic review project"}).json()
    url = f"/api/v1/projects/{project['id']}/reviewer-candidates"
    candidates = client.get(url, headers=auth).json()
    assert candidates == [{"id": users["demo-reviewer"].id, "username": "demo-reviewer"}]
    other = {"Authorization": "Bearer " + issue_access(users["other-user"])}
    assert client.get(url, headers=other).status_code == 403
    reviewer = {"Authorization": "Bearer " + issue_access(users["demo-reviewer"])}
    assert client.get(f"/api/v1/projects/{project['id']}", headers=reviewer).status_code == 403
    added = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=auth,
        json={"user_id": candidates[0]["id"], "role": "Reviewer"},
    )
    assert added.status_code == 201
    assert client.get(f"/api/v1/projects/{project['id']}", headers=reviewer).status_code == 200
