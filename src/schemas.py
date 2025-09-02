from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(UserBase):
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    extra_info: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    extra_info: Optional[str] = None

    class Config:
        from_attributes = True


class ContactRead(ContactBase):
    id: int

    class Config:
        from_attributes = True
