import asyncio
import datetime

import typer
from core.security import get_password_hash
from db.db import get_session
from models.roles import Role
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

app = typer.Typer()


async def create_superuser(
    login: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    session: AsyncSession,
):
    # Проверяем существование пользователя по логину, имени и фамилии
    existing_user = await session.execute(select(User).filter(User.login == login))
    if existing_user.scalars().first():
        typer.echo(f"User with login '{login}' already exists.")
        return

    # Hash the password
    hashed_password = get_password_hash(password)

    # Create a new superuser
    now = datetime.datetime.now().replace(tzinfo=None)
    new_superuser = User(
        login=login,
        email=email,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        created_at=now,
        last_login=now,
        is_admin=True,  # Устанавливаем флаг суперпользователя
        is_staff=True,  # Даем права доступа в админку
        is_active=True,  # Делаем пользователя активным
    )

    # Check if the 'admin' role exists, create if it doesn't
    result = await session.execute(select(Role).filter(Role.name == "admin"))
    admin_role = result.scalars().first()

    if not admin_role:
        admin_role = Role(
            name="admin",
            description="Superuser role with all permissions",
        )
        session.add(admin_role)
        await session.commit()
        await session.refresh(admin_role)

    # Assign the 'admin' role to the user
    new_superuser.roles.append(admin_role)

    # Save the user to the database
    session.add(new_superuser)
    await session.commit()
    typer.echo(f"Superuser '{login}' created successfully.")


@app.command()
def createsuperuser(
    login: str = typer.Option(..., prompt=True, help="The login for the superuser"),
    email: str = typer.Option(..., prompt=True, help="The email for the superuser"),
    password: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="The password for the superuser",
    ),
    first_name: str = typer.Option(
        ...,
        prompt=True,
        help="The first name of the superuser",
    ),
    last_name: str = typer.Option(
        ...,
        prompt=True,
        help="The last name of the superuser",
    ),
):
    """Create a new superuser with admin privileges."""

    async def run():
        async for session in get_session():
            await create_superuser(
                login, email, password, first_name, last_name, session
            )

    asyncio.run(run())


if __name__ == "__main__":
    app()
