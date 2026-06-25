from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_org_role
from src.auth.models import OrgRole, OrganizationMember, User
from src.channels.ws import manager
from src.core.database import get_session
from src.dms import service
from src.dms.schemas import ConversationPublic, DMListResponse, DirectMessagePublic, SendDMRequest, ConversationPublic, ConversationListResponse, EditDMRequest

router = APIRouter(prefix="/dms", tags=["dms"])


@router.post("/{user_id}", response_model=ConversationPublic, status_code=status.HTTP_200_OK)
async def open_conversation(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> ConversationPublic:
    return await service.get_or_create_conversation(user_id, current_user, membership, session)


@router.post("/{conversation_id}/messages", response_model=DirectMessagePublic, status_code=status.HTTP_201_CREATED)
async def send_dm(
    conversation_id: UUID,
    data: SendDMRequest,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> DirectMessagePublic:
    return await service.send_dm(conversation_id, data, current_user, membership, session)


@router.get("/{conversation_id}/messages", response_model=DMListResponse)
async def list_dms(
    conversation_id: UUID,
    before: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
    session: AsyncSession = Depends(get_session),
) -> DMListResponse:
    return await service.list_dms(conversation_id, current_user, membership, session, before, limit)


@router.websocket("/{conversation_id}/ws")
async def dm_websocket(
    conversation_id: UUID,
    token: str,
    ws: WebSocket,
) -> None:
    import json
    from src.auth.utils import decode_access_token

    payload = decode_access_token(token)
    if not payload:
        await ws.close(code=1008)
        return

    await manager.connect(str(conversation_id), ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                event = json.loads(data)
                if event.get("type") == "typing":
                    await manager.broadcast_others(str(conversation_id), ws, event)
            except (ValueError, KeyError):
                pass
    except WebSocketDisconnect:
        manager.disconnect(str(conversation_id), ws)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
     current_user: User = Depends(get_current_user),
     membership: OrganizationMember = Depends(require_org_role(OrgRole.MEMBER)),
     session: AsyncSession = Depends(get_session),
 ) -> ConversationListResponse:
     return await service.list_conversations(current_user, membership, session)


@router.patch("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_dm_read(
     conversation_id: UUID,
     current_user: User = Depends(get_current_user),
     session: AsyncSession = Depends(get_session),
 ) -> None:
     await service.mark_dm_read(conversation_id, current_user, session)

@router.delete("/{conversation_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dm_message(
     conversation_id: UUID,
     message_id: UUID,
     current_user: User = Depends(get_current_user),
     session: AsyncSession = Depends(get_session),
 ) -> None:
     await service.delete_dm_message(conversation_id, message_id, current_user, session)
 
 
@router.post("/{conversation_id}/messages/{message_id}/hide", status_code=status.HTTP_204_NO_CONTENT)
async def hide_dm_message(
     conversation_id: UUID,
     message_id: UUID,
     current_user: User = Depends(get_current_user),
     session: AsyncSession = Depends(get_session),
 ) -> None:
     await service.hide_dm_message(message_id, current_user, session)


@router.patch("/{conversation_id}/messages/{message_id}", response_model=DirectMessagePublic)
async def edit_dm_message(
     conversation_id: UUID,
     message_id: UUID,
     data: EditDMRequest,
     current_user: User = Depends(get_current_user),
     session: AsyncSession = Depends(get_session),
 ) -> DirectMessagePublic:
     return await service.edit_dm_message(conversation_id, message_id, data, current_user, session)

