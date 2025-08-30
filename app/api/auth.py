from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.deps import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token, decode_token


router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower()
    res = await db.execute(select(User).where(User.email == email))
    existing = res.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email_already_registered")

    user = User(email=email, password_hash=hash_password(payload.password), full_name=payload.full_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower()
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    token = create_access_token(subject=str(user.id), extra_claims={"email": user.email})
    return TokenResponse(access_token=token)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("no_sub")
        uid = uuid.UUID(str(user_id))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")

    res = await db.execute(select(User).where(User.id == uid))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")
    return user


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user

