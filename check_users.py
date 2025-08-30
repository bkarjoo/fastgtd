#!/usr/bin/env python3
import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User

async def check_users():
    async with async_session_maker() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        print("Existing users:")
        for user in users:
            print(f"  - {user.email} (id: {user.id})")
        return users

if __name__ == "__main__":
    asyncio.run(check_users())