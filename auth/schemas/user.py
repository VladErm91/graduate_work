from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    login: str
    password: str
    email: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""


class UserOut(BaseModel):
    id: UUID
    login: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class UserProfile(UserOut):
    roles: List[str] = []
    activity_log: List[dict] = []


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
