from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # По умолчанию токен типа Bearer
    refresh_token: str = (
        None  # Это поле опционально, зависит от того, используется ли refresh токен
    )
    user_id: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str
