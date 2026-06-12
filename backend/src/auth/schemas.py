from uuid import UUID

from pydantic import EmailStr, field_validator
from sqlmodel import SQLModel

from src.auth.models import OrgRole
from datetime import datetime


# ── Input schemas (what the API receives) ────────────────────────────────────

class RegisterOrgRequest(SQLModel):
    # EmailStr validates it's a real email format — like z.string().email() in Zod
    email: EmailStr
    password: str
    display_name: str
    org_name: str

    # field_validator runs before the data is accepted — like Zod's .transform()
    # Normalizing email here means the DB always gets lowercase — no case-sensitivity bugs.
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# ── Output schemas (what the API returns) ────────────────────────────────────

# UserPublic is what we send back to the client — never includes hashed_password.
# Node parallel: a DTO (Data Transfer Object) — a separate type for API output.
class UserPublic(SQLModel):
    id: UUID
    email: str
    display_name: str
    is_active: bool
    is_email_verified: bool


class OrganizationPublic(SQLModel):
    id: UUID
    name: str


class MemberPublic(SQLModel):
    user: UserPublic
    organization: OrganizationPublic
    role: OrgRole


# The response after register-org or login — contains the JWT + user info
class AuthResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"   # OAuth2 convention — always "bearer"
    user: UserPublic
    organization: OrganizationPublic


class LoginRequest(SQLModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()
    

class InviteRequest(SQLModel):
    email: EmailStr
    role: OrgRole = OrgRole.MEMBER

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class AcceptInviteRequest(SQLModel):
    token: str
    display_name: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class InvitePublic(SQLModel):
    id: UUID
    email: str
    role: OrgRole
    expires_at: datetime
    is_used: bool

