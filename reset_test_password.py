#!/usr/bin/env python3
import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import hash_password

async def reset_password():
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one_or_none()
        if user:
            user.password_hash = hash_password("test123")
            await db.commit()
            print("Password reset for test@example.com to 'test123'")
        else:
            print("User not found")

if __name__ == "__main__":
    asyncio.run(reset_password())