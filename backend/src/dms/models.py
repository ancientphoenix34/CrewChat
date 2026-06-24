from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    org_id: UUID = Field(foreign_key="organizations.id", index=True)
    participant_a: UUID = Field(foreign_key="users.id")
    participant_b: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DirectMessage(SQLModel, table=True):
    __tablename__ = "direct_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id", index=True)
    sender_id: UUID = Field(foreign_key="users.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)



class DMLastRead(SQLModel, table=True):
     __tablename__ = "dm_last_reads"
 
     user_id: UUID = Field(foreign_key="users.id", primary_key=True)
     conversation_id: UUID = Field(foreign_key="conversations.id", primary_key=True)
     last_read_at: datetime = Field(default_factory=datetime.utcnow)


class DMMessageHide(SQLModel, table=True):
     __tablename__ = "dm_message_hides"
 
     user_id: UUID = Field(foreign_key="users.id", primary_key=True)
     message_id: UUID = Field(foreign_key="direct_messages.id", primary_key=True)