from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_org_role
from src.auth.models import OrgRole, OrganizationMember, User
from src.channels import service
from src.channels.schemas import ChannelListResponse, ChannelPublic, CreateChannelRequest
from src.core.database import get_session

router = APIRouter(prefix="/channels", tags=["channels"])


@router.post("", response_model=ChannelPublic, status_code=status.HTTP_201_CREATED)
async def create_channel(
    data: CreateChannelRequest,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> ChannelPublic:
    return await service.create_channel(data, current_user, membership, session)


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> ChannelListResponse:
    return await service.list_channels(current_user, membership, session)


@router.get("/{channel_id}", response_model=ChannelPublic)
async def get_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> ChannelPublic:
    return await service.get_channel(channel_id, current_user, membership, session)


@router.post("/{channel_id}/join", response_model=ChannelPublic)
async def join_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> ChannelPublic:
    return await service.join_channel(channel_id, current_user, membership, session)


@router.delete("/{channel_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    await service.leave_channel(channel_id, current_user, session)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: UUID,
    membership: OrganizationMember = Depends(require_org_role(OrgRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await service.delete_channel(channel_id, membership, session)
