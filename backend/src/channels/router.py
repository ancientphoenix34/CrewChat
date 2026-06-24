from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_org_role
from src.auth.models import OrgRole, OrganizationMember, User
from src.channels import service
from src.channels.schemas import ChannelListResponse, ChannelPublic, CreateChannelRequest, MessageListResponse, MessagePublic, SendMessageRequest
from src.core.database import get_session
from src.channels.ws import manager

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


@router.post("/{channel_id}/messages", response_model=MessagePublic, status_code=status.HTTP_201_CREATED)
async def send_message(
    channel_id: UUID,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> MessagePublic:
    return await service.send_message(channel_id, data, current_user, membership, session)


@router.get("/{channel_id}/messages", response_model=MessageListResponse)
async def list_messages(
    channel_id: UUID,
    before: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> MessageListResponse:
    return await service.list_messages(channel_id, current_user, membership, session, before, limit)


@router.websocket("/{channel_id}/ws")
async def channel_websocket(
    channel_id: UUID,
    token: str,
    ws: WebSocket,
) -> None:
    import json
    from src.auth.utils import decode_access_token

    payload = decode_access_token(token)
    if not payload:
        await ws.close(code=1008)
        return

    await manager.connect(str(channel_id), ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                event = json.loads(data)
                if event.get("type") == "typing":
                    await manager.broadcast_others(str(channel_id), ws, event)
            except (ValueError, KeyError):
                pass
    except WebSocketDisconnect:
        manager.disconnect(str(channel_id), ws)


@router.delete("/{channel_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
     channel_id: UUID,
     message_id: UUID,
     current_user: User = Depends(get_current_user),
     session: AsyncSession = Depends(get_session),
 ) -> None:
     await service.delete_message(message_id, current_user, session)
 
 
@router.post("/{channel_id}/messages/{message_id}/hide", status_code=status.HTTP_204_NO_CONTENT)
async def hide_message(
     channel_id: UUID,
     message_id: UUID,
     current_user: User = Depends(get_current_user),
     session: AsyncSession = Depends(get_session),
 ) -> None:
     await service.hide_message(message_id, current_user, session)


