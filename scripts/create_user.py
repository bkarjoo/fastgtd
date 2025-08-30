import argparse
import asyncio
from sqlalchemy import select

from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import hash_password


async def create_user(email: str, password: str, full_name: str | None = None, active: bool = True) -> User:
    async with async_session_maker() as db:
        # Normalize email to lowercase
        email_l = email.lower()
        res = await db.execute(select(User).where(User.email == email_l))
        existing = res.scalar_one_or_none()
        if existing:
            print(f"User already exists: {existing.email} (id={existing.id})")
            return existing

        user = User(
            email=email_l,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=active,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"Created user: {user.email} (id={user.id})")
        return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a user in the FastGTD backend")
    parser.add_argument("--email", required=True, help="User email (used to login)")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--full-name", dest="full_name", default=None, help="Optional full name")
    parser.add_argument("--inactive", action="store_true", help="Create as inactive user")
    args = parser.parse_args()

    asyncio.run(create_user(args.email, args.password, args.full_name, active=not args.inactive))


if __name__ == "__main__":
    main()

