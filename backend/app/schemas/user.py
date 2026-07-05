from pydantic import BaseModel, ConfigDict, Field

from app.enums.user_role import UserRole


# ── Token ────────────────────────────────────────────────────
# Логин идёт через OAuth2PasswordRequestForm (form-data: username/password),
# отдельная Pydantic-схема для запроса логина не нужна.
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User responses ───────────────────────────────────────────
class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole
    is_active: bool


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: UserRole = Field(
        default=UserRole.MECHANIC,
        description="Роль сотрудника: admin / mechanic / manager",
    )


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
