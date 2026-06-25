from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select
import base64

from src.auth.models import OrganizationMember, User
from src.channels.models import Channel, ChannelLastRead, ChannelMember, Message, MessageHide
from src.channels.schemas import ChannelListResponse, ChannelPublic, CreateChannelRequest, MessageListResponse, MessagePublic, SendMessageRequest, EditMessageRequest
from src.channels.ws import manager


async def create_channel(
    data: CreateChannelRequest,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
) -> ChannelPublic:
    # Check no channel with same name exists in this org
    existing = await session.execute(
        select(Channel).where(
            Channel.org_id == membership.org_id,
            Channel.name == data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Channel name already exists in this org")

    channel = Channel(
        org_id=membership.org_id,
        name=data.name,
        description=data.description,
        is_private=data.is_private,
        created_by=current_user.id,
    )
    session.add(channel)
    await session.flush()  # get channel.id before commit

    # Auto-add creator as a member
    session.add(ChannelMember(channel_id=channel.id, user_id=current_user.id))

    await session.commit()
    await session.refresh(channel)
    return ChannelPublic.model_validate(channel)


async def list_channels(
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
) -> ChannelListResponse:
    result = await session.execute(
        select(Channel).where(
            Channel.org_id == membership.org_id,
            or_(
                Channel.is_private == False,
                Channel.id.in_(
                    select(ChannelMember.channel_id).where(
                        ChannelMember.user_id == current_user.id
                    )
                ),
            ),
        )
    )
    channels = result.scalars().all()
    items = []
    for ch in channels:
         lr = await session.get(ChannelLastRead, (current_user.id, ch.id))
         last_read_at = lr.last_read_at if lr else datetime(1970, 1, 1)
 
         count_result = await session.execute(
             select(func.count(Message.id)).where(
                 Message.channel_id == ch.id,
                 Message.created_at > last_read_at,
             )
         )
         unread = count_result.scalar_one()
         items.append(ChannelPublic.model_validate(ch).model_copy(update={'unread_count': unread}))
 
    return ChannelListResponse(channels=items)
 
 
async def mark_channel_read(
     channel_id: UUID,
     current_user: User,
     session: AsyncSession,
 ) -> None:
     lr = await session.get(ChannelLastRead, (current_user.id, channel_id))
     if lr:
         lr.last_read_at = datetime.utcnow()
     else:
         session.add(ChannelLastRead(user_id=current_user.id, channel_id=channel_id))
     await session.commit()


async def get_channel(
    channel_id: UUID,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
) -> ChannelPublic:
    channel = await session.get(Channel, channel_id)

    if not channel or channel.org_id != membership.org_id:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel.is_private:
        member = await session.get(ChannelMember, (channel_id, current_user.id))
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")

    return ChannelPublic.model_validate(channel)


async def join_channel(
    channel_id: UUID,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
) -> ChannelPublic:
    channel = await session.get(Channel, channel_id)

    if not channel or channel.org_id != membership.org_id:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel.is_private:
        raise HTTPException(status_code=403, detail="Cannot self-join a private channel")

    existing = await session.get(ChannelMember, (channel_id, current_user.id))
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    session.add(ChannelMember(channel_id=channel_id, user_id=current_user.id))
    await session.commit()
    return ChannelPublic.model_validate(channel)


async def leave_channel(
    channel_id: UUID,
    current_user: User,
    session: AsyncSession,
) -> None:
    member = await session.get(ChannelMember, (channel_id, current_user.id))

    if not member:
        raise HTTPException(status_code=404, detail="You are not a member of this channel")

    await session.delete(member)
    await session.commit()


async def delete_channel(
    channel_id: UUID,
    membership: OrganizationMember,
    session: AsyncSession,
) -> None:
    channel = await session.get(Channel, channel_id)

    if not channel or channel.org_id != membership.org_id:
        raise HTTPException(status_code=404, detail="Channel not found")

    await session.delete(channel)
    await session.commit()


async def send_message(
    channel_id: UUID,
    data: SendMessageRequest,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
) -> MessagePublic:
    channel = await session.get(Channel, channel_id)
    if not channel or channel.org_id != membership.org_id:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Private channels: must be a member
    if channel.is_private:
        member = await session.get(ChannelMember, (channel_id, current_user.id))
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")

    message = Message(
        channel_id=channel_id,
        sender_id=current_user.id,
        content=data.content,
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    payload = MessagePublic.model_validate(message).model_dump(mode="json")
    await manager.broadcast(str(channel_id), payload)
    return MessagePublic.model_validate(message)


async def list_messages(
    channel_id: UUID,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
    before: str | None = None,  # cursor
    limit: int = 50,
) -> MessageListResponse:
    channel = await session.get(Channel, channel_id)
    if not channel or channel.org_id != membership.org_id:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel.is_private:
        member = await session.get(ChannelMember, (channel_id, current_user.id))
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")

    query = (
        select(Message)
        .where(Message.channel_id == channel_id)
        .where(
             ~Message.id.in_(
                 select(MessageHide.message_id).where(MessageHide.user_id == current_user.id)
             )
         )
        .order_by(Message.created_at.desc())
        .limit(limit + 1)   # fetch one extra to know if there's a next page
    )

    if before:
        # decode cursor → datetime, filter messages older than that
        cursor_dt = datetime.fromisoformat(
            base64.b64decode(before.encode()).decode()
        )
        query = query.where(Message.created_at < cursor_dt)

    result = await session.execute(query)
    messages = result.scalars().all()

    next_cursor = None
    if len(messages) > limit:
        messages = messages[:limit]
        oldest = messages[-1]
        next_cursor = base64.b64encode(oldest.created_at.isoformat().encode()).decode()

    return MessageListResponse(
        messages=[MessagePublic.model_validate(m) for m in reversed(messages)],
        next_cursor=next_cursor,
    )


async def delete_message(
     message_id: UUID,
     current_user: User,
     session: AsyncSession,
 ) -> None:
     msg = await session.get(Message, message_id)
     if not msg or msg.sender_id != current_user.id:
         raise HTTPException(status_code=403, detail="Cannot delete this message")
     channel_id = str(msg.channel_id)
     await session.delete(msg)
     await session.commit()
     await manager.broadcast(channel_id, {
         "type": "message_deleted",
         "message_id": str(message_id),
     })


async def edit_message(
     message_id: UUID,
     data: EditMessageRequest,
     current_user: User,
     session: AsyncSession,
 ) -> MessagePublic:
     msg = await session.get(Message, message_id)
     if not msg or msg.sender_id != current_user.id:
         raise HTTPException(status_code=403, detail="Cannot edit this message")
     msg.content = data.content
     session.add(msg)
     await session.commit()
     await manager.broadcast(str(msg.channel_id), {
         "type": "message_edited",
         "message_id": str(message_id),
         "content": data.content,
     })
     return MessagePublic.model_validate(msg)

 
 
async def hide_message(
     message_id: UUID,
     current_user: User,
     session: AsyncSession,
 ) -> None:
     existing = await session.get(MessageHide, (current_user.id, message_id))
     if not existing:
         session.add(MessageHide(user_id=current_user.id, message_id=message_id))
         await session.commit()

