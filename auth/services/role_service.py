from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from models.roles import Role
from models.user import User
from schemas.roles import RoleCreateRequest, RoleUpdateRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


class RoleService:
    @staticmethod
    async def create_role(role_data: RoleCreateRequest, db: AsyncSession):
        result = await db.execute(select(Role).filter(Role.name == role_data.name))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role already exists",
            )

        new_role = Role(name=role_data.name, description=role_data.description)

        db.add(new_role)
        try:
            await db.commit()
            await db.refresh(new_role)
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating role",
            )

        return new_role

    @staticmethod
    async def get_roles(db: AsyncSession):
        result = await db.execute(select(Role))
        roles = result.scalars().all()
        return roles

    @staticmethod
    async def get_role(role_id: UUID, db: AsyncSession):
        result = await db.execute(select(Role).filter(Role.id == role_id))
        role = result.scalars().first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    @staticmethod
    async def update_role(
        role_id: UUID,
        role_data: RoleUpdateRequest,
        db: AsyncSession,
    ):
        result = await db.execute(select(Role).filter(Role.id == role_id))
        role = result.scalars().first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if role_data.name:
            role.name = role_data.name
        if role_data.description:
            role.description = role_data.description
        try:
            await db.commit()
            await db.refresh(role)
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating role",
            )
        return role

    @staticmethod
    async def delete_role(role_id: UUID, db: AsyncSession):
        result = await db.execute(select(Role).filter(Role.id == role_id))
        role = result.scalars().first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        await db.delete(role)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting role",
            )
        return {"message": "Role deleted successfully"}

    @staticmethod
    async def assign_role_to_user(user_id: UUID, role_id: UUID, db: AsyncSession):
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        result = await db.execute(select(Role).filter(Role.id == role_id))
        role = result.scalars().first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if role in user.roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role already assigned to user",
            )
        user.roles.append(role)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error assigning role to user",
            )
        return {"message": "Role assigned to user successfully"}

    @staticmethod
    async def revoke_role_from_user(user_id: UUID, role_id: UUID, db: AsyncSession):
        stmt = select(User).options(selectinload(User.roles)).filter(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        result = await db.execute(select(Role).filter(Role.id == role_id))
        role = result.scalars().first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role not assigned to user",
            )
        user.roles.remove(role)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error revoking role from user",
            )
        return {"message": "Role revoked from user successfully"}

    @staticmethod
    async def check_user_permission(
        user_id: UUID,
        required_roles: List[str],
        db: AsyncSession,
    ):
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_role_names = [role.name for role in user.roles]
        has_permission = any(role in user_role_names for role in required_roles)
        return {"has_permission": has_permission}
