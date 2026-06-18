from datetime import datetime
from uuid import UUID

from pydantic import field_validator
from sqlmodel import SQLModel


# ── Input ────────────────────────────────────────────────────────────────────

class CreateChannelRequest(SQLModel):
    name: str
    description: str | None = None
    is_private: bool = False

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 1:
            raise ValueError("Channel name cannot be empty")
        return v


# ── Output ───────────────────────────────────────────────────────────────────

class ChannelPublic(SQLModel):
    id: UUID
    org_id: UUID
    name: str
    description: str | None
    is_private: bool
    created_by: UUID
    created_at: datetime


class ChannelListResponse(SQLModel):
    channels: list[ChannelPublic]
