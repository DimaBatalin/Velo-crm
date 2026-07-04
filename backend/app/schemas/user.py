from pydantic import BaseModel, ConfigDict


# ── Login ────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


# ── Token ────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User responses ───────────────────────────────────────────
class UserBase(BaseModel):
    email: str
    full_name: str
    is_active: bool


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
