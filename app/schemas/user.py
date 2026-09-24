from pydantic import EmailStr, BaseModel

from datetime import datetime

from app.schemas.base import BaseSchema
from app.core.roles import RoleEnum


class UserBase(BaseSchema):
    username: str
    email: EmailStr


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None

class UserRoleUpdate(BaseModel):
    role: RoleEnum

class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    created_at: datetime
    disabled: bool
    role: str
