from nps.auth import issue_access


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
