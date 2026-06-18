from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select

from src.auth.models import OrganizationMember, User
from src.channels.models import Channel, ChannelMember
from src.channels.schemas import ChannelListResponse, ChannelPublic, CreateChannelRequest


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
    return ChannelListResponse(
        channels=[ChannelPublic.model_validate(c) for c in channels]
    )


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
