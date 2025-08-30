from pydantic import BaseModel, EmailStr
import uuid


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None

    class Config:
        from_attributes = True

