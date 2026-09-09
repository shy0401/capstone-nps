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
