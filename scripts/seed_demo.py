import asyncio
import uuid

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import get_sessionmaker
from app.models.user import User
from app.models.task_list import TaskList
from app.models.task import Task


async def main():
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as db:
        # upsert user by email
        email = "demo@example.com"
        res = await db.execute(select(User).where(User.email == email))
        user = res.scalar_one_or_none()
        if not user:
            user = User(email=email, password_hash=hash_password("demo123"), full_name="Demo User")
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"Created user {user.email} {user.id}")
        else:
            print(f"Using existing user {user.email} {user.id}")

        # create list if missing
        res = await db.execute(
            select(TaskList).where(TaskList.owner_id == user.id, TaskList.name == "Inbox")
        )
        lst = res.scalar_one_or_none()
        if not lst:
            lst = TaskList(owner_id=user.id, name="Inbox")
            db.add(lst)
            await db.commit()
            await db.refresh(lst)
            print(f"Created list {lst.name} {lst.id}")
        else:
            print(f"Using existing list {lst.name} {lst.id}")

        # add a couple tasks
        t1 = Task(list_id=lst.id, title="Try the API", description="Hit /auth/login then /tasks")
        t2 = Task(list_id=lst.id, title="Create a subtask")
        db.add_all([t1, t2])
        await db.commit()
        await db.refresh(t1)
        await db.refresh(t2)
        # make t2 a subtask of t1
        t2.parent_id = t1.id
        await db.commit()
        print(f"Seeded tasks: {t1.id}, {t2.id} (child of {t1.id})")


if __name__ == "__main__":
    asyncio.run(main())

