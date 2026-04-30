from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from typing import Optional
from src.domain.enums import Department, UserType


class UserIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[Department] = None
    user_type: Optional[UserType] = None
    email: Optional[EmailStr] = None


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    department: Department
    user_type: UserType


class UserOut(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    department: Department
    user_type: UserType


class FailedUser(BaseModel):
    email: EmailStr
    reason: str


class CreateUserResults(BaseModel):
    success: list[UserOut]
    failed: list[FailedUser]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
