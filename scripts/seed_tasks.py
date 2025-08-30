import argparse
import asyncio
import os
from typing import Any, Dict, List, Optional

import httpx

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    r = await client.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def get_lists(client: httpx.AsyncClient, token: str, limit: int = 200) -> List[Dict[str, Any]]:
    r = await client.get(f"{API_URL}/lists", headers=headers(token), params={"limit": limit})
    r.raise_for_status()
    return r.json()


async def create_task(client: httpx.AsyncClient, token: str, list_id: str, title: str, sort_order: int) -> Dict[str, Any]:
    payload = {"list_id": list_id, "title": title, "sort_order": sort_order}
    r = await client.post(f"{API_URL}/tasks", headers=headers(token), json=payload)
    r.raise_for_status()
    return r.json()


async def seed(email: str, password: str, per_list: int, lists_count: int) -> None:
    async with httpx.AsyncClient(timeout=60.0) as client:
        token = await login(client, email, password)
        lists = await get_lists(client, token, limit=1000)
        # Choose a subset of lists to seed
        target_lists = lists[:lists_count]
        total_created = 0
        for idx, lst in enumerate(target_lists):
            for i in range(per_list):
                title = f"Task {i+1} for {lst['name']}"
                await create_task(client, token, lst["id"], title, i)
                total_created += 1
        print(f"Seeded {total_created} tasks across {len(target_lists)} lists")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed tasks into existing lists via API")
    parser.add_argument("--email", default="demo_lists@example.com")
    parser.add_argument("--password", default="demo123")
    parser.add_argument("--per-list", type=int, default=4)
    parser.add_argument("--lists", type=int, default=15, dest="lists_count")
    args = parser.parse_args()
    asyncio.run(seed(args.email, args.password, args.per_list, args.lists_count))


if __name__ == "__main__":
    main()

