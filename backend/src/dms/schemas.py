from datetime import datetime
from uuid import UUID

from pydantic import field_validator
from sqlmodel import SQLModel


class SendDMRequest(SQLModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


class ConversationPublic(SQLModel):
    id: UUID
    org_id: UUID
    participant_a: UUID
    participant_b: UUID
    created_at: datetime


class DirectMessagePublic(SQLModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    content: str
    created_at: datetime


class DMListResponse(SQLModel):
    messages: list[DirectMessagePublic]
    next_cursor: str | None
