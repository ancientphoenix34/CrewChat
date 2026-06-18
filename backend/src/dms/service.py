import base64
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.models import OrganizationMember, User
from src.dms.models import Conversation, DirectMessage
from src.dms.schemas import ConversationPublic, DMListResponse, DirectMessagePublic, SendDMRequest


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
