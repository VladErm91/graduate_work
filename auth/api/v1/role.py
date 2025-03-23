from typing import List
from uuid import UUID

from core.auth import get_current_user
from db.db import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User
from schemas.roles import RoleCreateRequest, RoleResponse, RoleUpdateRequest
from services.role_service import RoleService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def is_admin(current_user: User = Depends(get_current_user)):
    user_roles = [role.name for role in current_user.roles]
    if "admin" in user_roles:
        return True
    raise HTTPException(status_code=403, detail="Not enough permissions")


async def require_roles(required_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)):
        user_role_names = [role.name for role in current_user.roles]
        if any(role in user_role_names for role in required_roles):
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return Depends(role_checker)


# CRUD Endpoints for Roles
@router.post("/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreateRequest,
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    new_role = await RoleService.create_role(role_data, db)
    return new_role


@router.get("/", response_model=List[RoleResponse])
async def get_roles(
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    roles = await RoleService.get_roles(db)
    return roles


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    role = await RoleService.get_role(role_id, db)
    return role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdateRequest,
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    role = await RoleService.update_role(role_id, role_data, db)
    return role


@router.delete("/{role_id}", response_model=dict)
async def delete_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    result = await RoleService.delete_role(role_id, db)
    return result


# Endpoints to Assign and Revoke Roles
@router.post("/users/{user_id}/roles/{role_id}", response_model=dict)
async def assign_role_to_user(
    user_id: UUID,
    role_id: UUID,
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    result = await RoleService.assign_role_to_user(user_id, role_id, db)
    return result


@router.delete("/users/{user_id}/roles/{role_id}", response_model=dict)
async def revoke_role_from_user(
    user_id: UUID,
    role_id: UUID,
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    result = await RoleService.revoke_role_from_user(user_id, role_id, db)
    return result


# Endpoint to Check User Permissions
@router.get("/users/{user_id}/has-permission", response_model=dict)
async def check_user_permission(
    user_id: UUID,
    required_roles: str,
    db: AsyncSession = Depends(get_session),
    _: bool = Depends(is_admin),
):
    roles_to_check = [role.strip() for role in required_roles.split(",")]
    result = await RoleService.check_user_permission(user_id, roles_to_check, db)
    return result
