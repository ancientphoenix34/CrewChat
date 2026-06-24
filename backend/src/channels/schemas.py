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
    unread_count: int = 0


class ChannelListResponse(SQLModel):
    channels: list[ChannelPublic]




class SendMessageRequest(SQLModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message content cannot be empty")
        return v


class MessagePublic(SQLModel):
    id: UUID
    channel_id: UUID
    sender_id: UUID
    content: str
    created_at: datetime


class MessageListResponse(SQLModel):
    messages: list[MessagePublic]
    next_cursor: str | None  # for pagination

