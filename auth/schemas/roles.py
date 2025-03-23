from uuid import UUID

from pydantic import BaseModel, Field


class RoleCreateRequest(BaseModel):
    name: str = Field(..., max_length=50)
    description: str = Field(None, max_length=255)


class RoleUpdateRequest(BaseModel):
    name: str = Field(None, max_length=50)
    description: str = Field(None, max_length=255)


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str = None

    class Config:
        orm_mode = True
