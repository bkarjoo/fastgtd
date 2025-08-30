import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app


def _auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def run() -> int:
    client = TestClient(app)

    # 0) Health
    r = client.get("/health")
    assert r.status_code == 200, r.text

    # 1) Signup and login
    email = f"test_{uuid.uuid4().hex[:12]}@example.com"
    password = "Test1234!"
    r = client.post("/auth/signup", json={"email": email, "password": password, "full_name": "Tester"})
    assert r.status_code == 201, r.text
    user = r.json()
    assert user["email"].lower() == email.lower()

    # duplicate should 400
    r = client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 400, r.text

    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers=_auth_headers(token))
    assert r.status_code == 200, r.text
    assert r.json()["email"].lower() == email.lower()

    # 2) Lists CRUD
    r = client.post("/lists", headers=_auth_headers(token), json={"name": "Inbox", "description": "Default", "sort_order": 1})
    assert r.status_code == 201, r.text
    lst = r.json()
    list_id = lst["id"]

    r = client.get("/lists", headers=_auth_headers(token))
    assert r.status_code == 200, r.text
    assert any(x["id"] == list_id for x in r.json())

    r = client.get(f"/lists/{list_id}", headers=_auth_headers(token))
    assert r.status_code == 200, r.text

    r = client.patch(f"/lists/{list_id}", headers=_auth_headers(token), json={"name": "Inbox+", "sort_order": 2})
    assert r.status_code == 200 and r.json()["name"] == "Inbox+", r.text

    # 3) Tasks CRUD + filters + parent rules
    task_payload = {"list_id": list_id, "title": "Task A", "priority": "high", "status": "todo"}
    r = client.post("/tasks", headers=_auth_headers(token), json=task_payload)
    assert r.status_code == 201, r.text
    task_a = r.json()

    r = client.post(
        "/tasks",
        headers=_auth_headers(token),
        json={"list_id": list_id, "title": "Task B", "status": "in_progress", "priority": "medium"},
    )
    assert r.status_code == 201, r.text
    task_b = r.json()

    # subtask under A
    r = client.post(
        "/tasks",
        headers=_auth_headers(token),
        json={"list_id": list_id, "title": "Subtask A1", "parent_id": task_a["id"]},
    )
    assert r.status_code == 201, r.text
    sub_a1 = r.json()

    # update A to done
    r = client.patch(f"/tasks/{task_a['id']}", headers=_auth_headers(token), json={"status": "done"})
    assert r.status_code == 200 and r.json()["status"] == "done", r.text

    # try to move A to another list while it has children -> 400
    r = client.post("/lists", headers=_auth_headers(token), json={"name": "Work"})
    assert r.status_code == 201, r.text
    other_list_id = r.json()["id"]
    r = client.patch(
        f"/tasks/{task_a['id']}", headers=_auth_headers(token), json={"list_id": other_list_id}
    )
    assert r.status_code == 400, r.text

    # list filters
    r = client.get(
        "/tasks",
        headers=_auth_headers(token),
        params={"status_": "done", "include_total": True},
    )
    assert r.status_code == 200, r.text
    assert r.headers.get("X-Total-Count") is not None
    assert any(t["id"] == task_a["id"] for t in r.json())

    # 4) Tags CRUD + association
    r = client.post("/tags", headers=_auth_headers(token), json={"name": "p1", "description": "prio"})
    assert r.status_code == 201, r.text
    tag = r.json()
    tag_id = tag["id"]

    # attach to Task B
    r = client.post(f"/tasks/{task_b['id']}/tags/{tag_id}", headers=_auth_headers(token))
    assert r.status_code == 204, r.text
    r = client.get(f"/tasks/{task_b['id']}/tags", headers=_auth_headers(token))
    assert r.status_code == 200 and any(t["id"] == tag_id for t in r.json()), r.text

    # detach
    r = client.delete(f"/tasks/{task_b['id']}/tags/{tag_id}", headers=_auth_headers(token))
    assert r.status_code == 204, r.text

    # 5) Notes on task and list
    r = client.post("/notes", headers=_auth_headers(token), json={"task_id": task_b["id"], "body": "note for task"})
    assert r.status_code == 201, r.text
    note_task = r.json()
    r = client.post("/notes", headers=_auth_headers(token), json={"list_id": list_id, "body": "note for list"})
    assert r.status_code == 201, r.text
    note_list = r.json()

    r = client.get("/notes", headers=_auth_headers(token), params={"task_id": task_b["id"]})
    assert r.status_code == 200 and any(n["id"] == note_task["id"] for n in r.json()), r.text
    r = client.get("/notes", headers=_auth_headers(token), params={"list_id": list_id})
    assert r.status_code == 200 and any(n["id"] == note_list["id"] for n in r.json()), r.text

    r = client.patch(f"/notes/{note_task['id']}", headers=_auth_headers(token), json={"body": "updated"})
    assert r.status_code == 200 and r.json()["body"] == "updated", r.text

    # 6) Artifacts
    r = client.post(
        "/artifacts",
        headers=_auth_headers(token),
        json={"task_id": task_b["id"], "kind": "link", "uri": "https://example.com", "title": "ex"},
    )
    assert r.status_code == 201, r.text
    art = r.json()
    r = client.get("/artifacts", headers=_auth_headers(token), params={"task_id": task_b["id"]})
    assert r.status_code == 200 and any(a["id"] == art["id"] for a in r.json()), r.text
    r = client.patch(f"/artifacts/{art['id']}", headers=_auth_headers(token), json={"title": "ex2"})
    assert r.status_code == 200 and r.json()["title"] == "ex2", r.text

    # 7) Cascades: delete parent task -> subtask gone
    r = client.delete(f"/tasks/{task_a['id']}", headers=_auth_headers(token))
    assert r.status_code == 204, r.text
    r = client.get(f"/tasks/{sub_a1['id']}", headers=_auth_headers(token))
    assert r.status_code == 404, r.text

    # Clean up remaining created resources
    client.delete(f"/artifacts/{art['id']}", headers=_auth_headers(token))
    client.delete(f"/notes/{note_task['id']}", headers=_auth_headers(token))
    client.delete(f"/notes/{note_list['id']}", headers=_auth_headers(token))
    client.delete(f"/tasks/{task_b['id']}", headers=_auth_headers(token))
    client.delete(f"/lists/{other_list_id}", headers=_auth_headers(token))
    client.delete(f"/lists/{list_id}", headers=_auth_headers(token))

    print("✅ Smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run())

