import base64
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select
from sqlalchemy import func

from src.auth.models import OrganizationMember, User
from src.dms.models import Conversation, DirectMessage, DMLastRead, DMMessageHide
from src.dms.schemas import (ConversationListResponse, ConversationPublic, ConversationWithUser,
     DMListResponse, DirectMessagePublic, SendDMRequest, EditDMRequest
 )


async def get_or_create_conversation(
    other_user_id: UUID,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
) -> ConversationPublic:
    a, b = sorted([str(current_user.id), str(other_user_id)])

    result = await session.execute(
        select(Conversation).where(
            Conversation.org_id == membership.org_id,
            Conversation.participant_a == UUID(a),
            Conversation.participant_b == UUID(b),
        )
    )
    conv = result.scalar_one_or_none()

    if not conv:
        conv = Conversation(
            org_id=membership.org_id,
            participant_a=UUID(a),
            participant_b=UUID(b),
        )
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

    return ConversationPublic.model_validate(conv)


async def list_conversations(
     current_user: User,
     membership: OrganizationMember,
     session: AsyncSession,
 ) -> ConversationListResponse:
     result = await session.execute(
         select(Conversation).where(
             Conversation.org_id == membership.org_id,
             or_(
                 Conversation.participant_a == current_user.id,
                 Conversation.participant_b == current_user.id,
             )
         ).order_by(Conversation.created_at.desc())
     )
     conversations = result.scalars().all()
 
     items = []
     for conv in conversations:
         other_id = conv.participant_b if conv.participant_a == current_user.id else conv.participant_a
         other_user = await session.get(User, other_id)
         other_name = other_user.display_name if other_user else str(other_id)[:8]
 
         lr = await session.get(DMLastRead, (current_user.id, conv.id))
         last_read_at = lr.last_read_at if lr else datetime(1970, 1, 1)
 
         count_result = await session.execute(
             select(func.count(DirectMessage.id)).where(
                 DirectMessage.conversation_id == conv.id,
                 DirectMessage.created_at > last_read_at,
             )
         )
         unread = count_result.scalar_one()
 
         items.append(ConversationWithUser(
             id=conv.id,
             other_user_id=other_id,
             other_user_name=other_name,
             unread_count=unread,
         ))
 
     return ConversationListResponse(conversations=items)
 
 
async def mark_dm_read(
     conversation_id: UUID,
     current_user: User,
     session: AsyncSession,
 ) -> None:
     lr = await session.get(DMLastRead, (current_user.id, conversation_id))
     if lr:
         lr.last_read_at = datetime.utcnow()
     else:
         session.add(DMLastRead(user_id=current_user.id, conversation_id=conversation_id))
     await session.commit()



async def send_dm(
    conversation_id: UUID,
    data: SendDMRequest,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
) -> DirectMessagePublic:
    conv = await session.get(Conversation, conversation_id)
    if not conv or conv.org_id != membership.org_id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user.id not in (conv.participant_a, conv.participant_b):
        raise HTTPException(status_code=403, detail="Access denied")

    msg = DirectMessage(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=data.content,
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)

    from src.channels.ws import manager
    payload = DirectMessagePublic.model_validate(msg).model_dump(mode="json")
    await manager.broadcast(str(conversation_id), payload)

    return DirectMessagePublic.model_validate(msg)


async def list_dms(
    conversation_id: UUID,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
    before: str | None = None,
    limit: int = 50,
) -> DMListResponse:
    conv = await session.get(Conversation, conversation_id)
    if not conv or conv.org_id != membership.org_id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user.id not in (conv.participant_a, conv.participant_b):
        raise HTTPException(status_code=403, detail="Access denied")

    query = (
        select(DirectMessage)
        .where(DirectMessage.conversation_id == conversation_id)
        .where(
             ~DirectMessage.id.in_(
                 select(DMMessageHide.message_id).where(DMMessageHide.user_id == current_user.id)
             )
         )
        .order_by(DirectMessage.created_at.desc())
        .limit(limit + 1)
    )

    if before:
        cursor_dt = datetime.fromisoformat(
            base64.b64decode(before.encode()).decode()
        )
        query = query.where(DirectMessage.created_at < cursor_dt)

    result = await session.execute(query)
    messages = result.scalars().all()

    next_cursor = None
    if len(messages) > limit:
        messages = messages[:limit]
        oldest = messages[-1]
        next_cursor = base64.b64encode(oldest.created_at.isoformat().encode()).decode()

    return DMListResponse(
        messages=[DirectMessagePublic.model_validate(m) for m in reversed(messages)],
        next_cursor=next_cursor,
    )

async def delete_dm_message(
     conversation_id: UUID,
     message_id: UUID,
     current_user: User,
     session: AsyncSession,
 ) -> None:
     msg = await session.get(DirectMessage, message_id)
     if not msg or msg.sender_id != current_user.id or msg.conversation_id != conversation_id:
         raise HTTPException(status_code=403, detail="Cannot delete this message")
     await session.delete(msg)
     await session.commit()
     from src.channels.ws import manager
     await manager.broadcast(str(conversation_id), {
         "type": "message_deleted",
         "message_id": str(message_id),
     })
 
 
async def hide_dm_message(
     message_id: UUID,
     current_user: User,
     session: AsyncSession,
 ) -> None:
     existing = await session.get(DMMessageHide, (current_user.id, message_id))
     if not existing:
         session.add(DMMessageHide(user_id=current_user.id, message_id=message_id))
         await session.commit()


async def edit_dm_message(
     conversation_id: UUID,
     message_id: UUID,
     data: EditDMRequest,
     current_user: User,
     session: AsyncSession,
 ) -> DirectMessagePublic:
     msg = await session.get(DirectMessage, message_id)
     if not msg or msg.sender_id != current_user.id or msg.conversation_id != conversation_id:
         raise HTTPException(status_code=403, detail="Cannot edit this message")
     msg.content = data.content
     session.add(msg)
     await session.commit()
     from src.channels.ws import manager
     await manager.broadcast(str(conversation_id), {
         "type": "message_edited",
         "message_id": str(message_id),
         "content": data.content,
     })
     return DirectMessagePublic.model_validate(msg)


