import datetime

from core.security import get_password_hash, verify_password
from models.user import User
from repositories.user_repository import create_user
from schemas.user import UserProfile


async def register_user(db, user_data):
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        login=user_data.login,
        password=hashed_password,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        created_at=datetime.datetime.now(),
    )
    return await create_user(db, new_user)


async def update_user_profile(db, current_user, update_data):
    if update_data.first_name is not None:
        current_user.first_name = update_data.first_name
    if update_data.last_name is not None:
        current_user.last_name = update_data.last_name

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


async def change_user_password(db, current_user, old_password, new_password):
    if not verify_password(old_password, current_user.password):
        raise Exception("Incorrect old password")

    current_user.password = get_password_hash(new_password)
    db.add(current_user)
    await db.commit()
    return current_user


async def build_user_profile(
    current_user: User,
    roles: list[str],
    activity: list[dict],
) -> UserProfile:
    return UserProfile(
        id=current_user.id,
        login=current_user.login,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        created_at=current_user.created_at,
        roles=roles,
        activity_log=activity,
    )
