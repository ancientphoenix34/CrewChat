from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class Channel(SQLModel, table=True):
    __tablename__ = "channels"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(foreign_key="organizations.id", index=True)
    name: str = Field(index=True)
    description: str | None = Field(default=None)
    is_private: bool = Field(default=False)
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    members: list["ChannelMember"] = Relationship(back_populates="channel")


class ChannelMember(SQLModel, table=True):
    __tablename__ = "channel_members"

    channel_id: UUID = Field(foreign_key="channels.id", primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    channel: Channel | None = Relationship(back_populates="members")


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    channel_id: UUID = Field(foreign_key="channels.id", index=True)
    sender_id: UUID = Field(foreign_key="users.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

