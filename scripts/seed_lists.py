import argparse
import asyncio
import os
from typing import Any, Dict, List, Optional

import httpx


API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


async def ensure_user(client: httpx.AsyncClient, email: str, password: str, full_name: Optional[str] = None) -> str:
    # Try signup; if already exists fall back to login
    r = await client.post(
        f"{API_URL}/auth/signup",
        json={"email": email, "password": password, "full_name": full_name or "Seed User"},
        timeout=30.0,
    )
    if r.status_code not in (201, 400):
        raise RuntimeError(f"Signup failed: {r.status_code} {r.text}")

    r = await client.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=30.0,
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    return token


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_list(client: httpx.AsyncClient, token: str, name: str, description: Optional[str] = None, sort_order: Optional[int] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"name": name}
    if description is not None:
        payload["description"] = description
    if sort_order is not None:
        payload["sort_order"] = sort_order

    r = await client.post(f"{API_URL}/lists", json=payload, headers=_auth_headers(token))
    r.raise_for_status()
    return r.json()


async def create_child_list(client: httpx.AsyncClient, token: str, parent_id: str, name: str, description: Optional[str] = None, sort_order: Optional[int] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"name": name}
    if description is not None:
        payload["description"] = description
    if sort_order is not None:
        payload["sort_order"] = sort_order

    r = await client.post(f"{API_URL}/lists/{parent_id}/children", json=payload, headers=_auth_headers(token))
    r.raise_for_status()
    return r.json()


async def seed_lists(
    email: str,
    password: str,
    top_level: int,
    children_per_top: int,
    grandchildren_per_child: int,
) -> None:
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Health check early
        hr = await client.get(f"{API_URL}/health")
        hr.raise_for_status()

        token = await ensure_user(client, email, password)

        created_top: List[Dict[str, Any]] = []
        for i in range(top_level):
            lst = await create_list(client, token, name=f"List {i+1:02d}", description=None, sort_order=i)
            created_top.append(lst)

        # Create children
        for i, parent in enumerate(created_top):
            for c in range(children_per_top):
                child = await create_child_list(
                    client,
                    token,
                    parent_id=parent["id"],
                    name=f"{parent['name']} - Sub {c+1}",
                    description=None,
                    sort_order=c,
                )
                # Create grandchildren under the first N children to add depth
                for g in range(grandchildren_per_child):
                    await create_child_list(
                        client,
                        token,
                        parent_id=child["id"],
                        name=f"{child['name']} - Sub {g+1}",
                        description=None,
                        sort_order=g,
                    )

        # Summary
        r = await client.get(f"{API_URL}/lists", headers=_auth_headers(token), params={"include_total": True, "limit": 1, "offset": 0})
        r.raise_for_status()
        total = r.headers.get("X-Total-Count") or "?"
        print(f"Seed complete. Total lists reported: {total}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed lots of empty lists with nesting via API")
    parser.add_argument("--email", default="demo_lists@example.com")
    parser.add_argument("--password", default="demo123")
    parser.add_argument("--top-level", type=int, default=25, dest="top_level")
    parser.add_argument("--children-per-top", type=int, default=4, dest="children_per_top")
    parser.add_argument("--grandchildren-per-child", type=int, default=2, dest="grandchildren_per_child")
    args = parser.parse_args()

    asyncio.run(
        seed_lists(
            email=args.email,
            password=args.password,
            top_level=args.top_level,
            children_per_top=args.children_per_top,
            grandchildren_per_child=args.grandchildren_per_child,
        )
    )


if __name__ == "__main__":
    main()

