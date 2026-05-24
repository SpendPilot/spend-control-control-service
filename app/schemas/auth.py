from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    department_id: int | None = None
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime | None = None


TokenResponse.model_rebuild()

