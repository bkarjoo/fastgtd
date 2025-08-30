#!/usr/bin/env python3
"""
Minimal smoke test for TagList restrictions with inheritance.

Usage:
  python scripts/smoke_taglists.py --base http://localhost:8000 --email you@example.com --password pass

It will:
  - signup/login
  - create TagLists Biology & Physics
  - create Tags Cell (Biology) and Quantum (Physics)
  - create a parent Note List and a child Note List
  - attach Biology to the parent (effective on child via inheritance)
  - verify available-tags includes Cell
  - create a Note in child and attach Cell (OK)
  - try attaching Quantum (should fail)
Prints concise OK/FAIL messages and exits nonzero on failure.
"""
import argparse
import sys
import uuid
import requests


def req(method, url, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers.setdefault("Content-Type", "application/json")
    resp = requests.request(method, url, headers=headers, **kwargs)
    return resp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", required=True)
    args = ap.parse_args()

    base = args.base.rstrip("/")

    # signup (ignore if exists)
    r = req("POST", f"{base}/auth/signup", json={"email": args.email, "password": args.password})
    if r.status_code not in (201, 400):
        print("FAIL: signup", r.status_code, r.text)
        sys.exit(1)

    # login
    r = req("POST", f"{base}/auth/login", json={"email": args.email, "password": args.password})
    if r.status_code != 200:
        print("FAIL: login", r.status_code, r.text)
        sys.exit(1)
    token = r.json()["access_token"]
    print("OK: login")

    # TagLists
    bio = req("POST", f"{base}/taglists", token, json={"name": "Biology"})
    if bio.status_code not in (201, 409, 422):
        # 409 or 422 if already exists due to unique name
        pass
    # fetch Biology id (list and pick by name)
    tl = req("GET", f"{base}/taglists", token)
    bio_id = None
    phy_id = None
    for t in tl.json():
        if t["name"] == "Biology":
            bio_id = t["id"]
        if t["name"] == "Physics":
            phy_id = t["id"]
    if not bio_id:
        bio = req("POST", f"{base}/taglists", token, json={"name": "Biology"})
        if bio.status_code != 201:
            print("FAIL: create Biology TagList", bio.status_code, bio.text)
            sys.exit(1)
        bio_id = bio.json()["id"]
    if not phy_id:
        phy = req("POST", f"{base}/taglists", token, json={"name": "Physics"})
        if phy.status_code != 201:
            print("FAIL: create Physics TagList", phy.status_code, phy.text)
            sys.exit(1)
        phy_id = phy.json()["id"]
    print("OK: taglists Biology & Physics ready")

    # Tags
    cell = req("POST", f"{base}/tags", token, json={"name": "Cell", "tag_list_id": bio_id})
    if cell.status_code not in (201, 409, 422):
        pass
    quantum = req("POST", f"{base}/tags", token, json={"name": "Quantum", "tag_list_id": phy_id})
    if quantum.status_code not in (201, 409, 422):
        pass
    # get tag ids by listing
    tags = req("GET", f"{base}/tags", token).json()
    cell_id = next((t["id"] for t in tags if t["name"] == "Cell"), None)
    quantum_id = next((t["id"] for t in tags if t["name"] == "Quantum"), None)
    if not cell_id or not quantum_id:
        print("FAIL: ensure tags existed")
        sys.exit(1)
    print("OK: tags Cell & Quantum ready")

    # Create parent and child Note Lists
    parent = req("POST", f"{base}/note-lists", token, json={"name": "All Notes"})
    if parent.status_code not in (201, 409, 422):
        pass
    # fetch id of All Notes
    nls = req("GET", f"{base}/note-lists", token).json()
    parent_id = next((n["id"] for n in nls if n["name"] == "All Notes"), None)
    if not parent_id:
        parent = req("POST", f"{base}/note-lists", token, json={"name": "All Notes"})
        if parent.status_code != 201:
            print("FAIL: create parent note list", parent.status_code, parent.text)
            sys.exit(1)
        parent_id = parent.json()["id"]

    child = req("POST", f"{base}/note-lists/{parent_id}/children", token, json={"name": "Biology Notes"})
    if child.status_code not in (201, 409, 422):
        pass
    # get child id
    children = req("GET", f"{base}/note-lists/{parent_id}/children", token).json()
    child_id = next((c["id"] for c in children if c["name"] == "Biology Notes"), None)
    if not child_id:
        print("FAIL: ensure child note list exists")
        sys.exit(1)
    print("OK: note lists ready")

    # Attach Biology TagList to parent
    a = req("POST", f"{base}/note-lists/{parent_id}/taglists/{bio_id}", token)
    if a.status_code not in (204, 200):
        print("FAIL: attach Biology to parent", a.status_code, a.text)
        sys.exit(1)

    # Check available tags for child includes Cell
    avail = req("GET", f"{base}/note-lists/{child_id}/available-tags", token)
    if avail.status_code != 200:
        print("FAIL: available-tags", avail.status_code, avail.text)
        sys.exit(1)
    names = {t["name"] for t in avail.json()}
    if "Cell" not in names:
        print("FAIL: available-tags missing 'Cell'", names)
        sys.exit(1)
    print("OK: inheritance works (Cell available)")

    # Create a note in child
    note = req("POST", f"{base}/notes", token, json={"note_list_id": child_id, "title": "Test", "body": "..."})
    if note.status_code != 201:
        print("FAIL: create note", note.status_code, note.text)
        sys.exit(1)
    note_id = note.json()["id"]

    # Attach Cell (allowed)
    at = req("POST", f"{base}/notes/{note_id}/tags/{cell_id}", token)
    if at.status_code not in (200, 201, 204):
        print("FAIL: attach allowed tag", at.status_code, at.text)
        sys.exit(1)
    print("OK: attach allowed tag")

    # Try attach Quantum (not allowed)
    bad = req("POST", f"{base}/notes/{note_id}/tags/{quantum_id}", token)
    if bad.status_code == 400:
        print("OK: forbidden tag blocked")
    else:
        print("FAIL: forbidden tag expected 400, got", bad.status_code, bad.text)
        sys.exit(1)

    print("SUCCESS: Smoke test passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FAIL:", e)
        sys.exit(1)

