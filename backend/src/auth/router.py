from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_org_role
from src.auth.models import OrgRole, OrganizationMember, User
from src.auth.schemas import (
    AcceptInviteRequest,
    AuthResponse,
    InvitePublic,
    InviteRequest,
    LoginRequest,
    RegisterOrgRequest,
    UserPublic,
)
from src.auth.service import accept_invite, create_invite, login, register_org
from src.core.database import get_session
from src.auth.service import login, register_org
from src.core.database import get_session

# APIRouter is like Express's Router — a mini-app you mount onto the main app.
# Node parallel: const router = express.Router()
# prefix="/auth" means all routes here start with /auth automatically.
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register-org",
    response_model=AuthResponse,       # FastAPI validates + serializes the return value
    status_code=status.HTTP_201_CREATED,  # 201 Created — more correct than 200 for resource creation
)
async def register_org_endpoint(
    data: RegisterOrgRequest,          # FastAPI reads + validates the JSON body automatically
    session: AsyncSession = Depends(get_session),  # DB session injected
) -> AuthResponse:
    # Node parallel:
    # router.post('/register-org', async (req, res) => {
    #   const result = await registerOrgService(req.body, db)
    #   res.status(201).json(result)
    # })
    return await register_org(data, session)

@router.post("/login", response_model=AuthResponse)
async def login_endpoint(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    return await login(data, session)



@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: User = Depends(get_current_user),  # auth enforced by dependency
) -> UserPublic:
    # Node parallel: router.get('/me', authMiddleware, (req, res) => res.json(req.user))
    return UserPublic.model_validate(current_user)


@router.post("/invite", response_model=InvitePublic, status_code=status.HTTP_201_CREATED)
async def invite_member(
    data: InviteRequest,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_org_role(OrgRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> InvitePublic:
    return await create_invite(data, current_user, membership, session)


@router.post("/accept-invite", response_model=AuthResponse)
async def accept_invite_endpoint(
    data: AcceptInviteRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    return await accept_invite(data, session)

