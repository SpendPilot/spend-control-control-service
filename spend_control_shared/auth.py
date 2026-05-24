from typing import Literal

from pydantic import BaseModel, EmailStr

RoleName = Literal["employee", "manager", "finance_admin"]


class JWTClaims(BaseModel):
    sub: str
    email: EmailStr
    role: RoleName
    user_id: int
    department_id: int | None = None
    exp: int

