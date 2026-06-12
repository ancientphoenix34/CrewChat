import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


from src.auth.models import OrgRole, Organization, OrganizationMember, User, OrgInvite
from src.auth.schemas import AuthResponse, LoginRequest, OrganizationPublic, RegisterOrgRequest, UserPublic, AcceptInviteRequest,  InvitePublic, InviteRequest
from src.auth.utils import create_access_token, hash_password, verify_password


async def register_org(
    data: RegisterOrgRequest,
    session: AsyncSession,
) -> AuthResponse:

    # 1. Check email isn't already taken — DB constraint would catch it too,
    #    but we give a nicer error message here.
    # Node parallel: prisma.user.findUnique({ where: { email } })
    result = await session.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # 2. Create all three rows inside a single transaction.
    #    If any step fails, ALL changes are rolled back automatically.
    #    Node parallel: prisma.$transaction(async (tx) => { ... })
    #
    #    SQLAlchemy's AsyncSession IS the transaction — every session.add()
    #    is staged until session.commit(). One commit = one atomic transaction.

    org = Organization(name=data.org_name)
    session.add(org)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),  # never store plain password
        display_name=data.display_name,
    )
    session.add(user)

    # flush() sends the INSERT statements to the DB so org.id and user.id
    # are populated — but doesn't commit yet. We need the IDs for the membership row.
    # Node parallel: no direct equivalent; Prisma handles this inside $transaction.
    await session.flush()

    membership = OrganizationMember(
        user_id=user.id,
        org_id=org.id,
        role=OrgRole.OWNER,  # first user in an org is always OWNER
    )
    session.add(membership)

    # commit() makes everything permanent. If this fails, all three INSERTs roll back.
    await session.commit()

    # refresh() reloads the objects from DB so all fields (created_at etc.) are populated.
    # Node parallel: prisma returns the full object after create() — SQLAlchemy needs this extra step.
    await session.refresh(user)
    await session.refresh(org)

    # 3. Issue the JWT and return it.
    token = create_access_token(
        user_id=user.id,
        org_id=org.id,
        role=OrgRole.OWNER.value,
    )

    return AuthResponse(
        access_token=token,
        user=UserPublic.model_validate(user),
        organization=OrganizationPublic.model_validate(org),
    )


async def login(
    data: LoginRequest,
    session: AsyncSession,
) -> AuthResponse:

    # 1. Find user by email
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Generic error — never reveal whether email exists or not (security)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )

    # 2. Get their org membership (first org they belong to)
    membership_result = await session.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no organization",
        )

    # 3. Load the org
    org_result = await session.execute(
        select(Organization).where(Organization.id == membership.org_id)
    )
    org = org_result.scalar_one_or_none()

    # 4. Issue JWT
    token = create_access_token(
        user_id=user.id,
        org_id=org.id,
        role=membership.role.value,
    )

    return AuthResponse(
        access_token=token,
        user=UserPublic.model_validate(user),
        organization=OrganizationPublic.model_validate(org),
    )



async def create_invite(
    data: InviteRequest,
    current_user: User,
    membership: OrganizationMember,
    session: AsyncSession,
) -> InvitePublic:
    # Prevent duplicate pending invites for the same email in the same org
    existing = await session.execute(
        select(OrgInvite).where(
            OrgInvite.org_id == membership.org_id,
            OrgInvite.email == data.email,
            OrgInvite.is_used == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active invite for this email already exists",
        )

    invite = OrgInvite(
        org_id=membership.org_id,
        invited_by=current_user.id,
        email=data.email,
        role=data.role,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    session.add(invite)
    await session.commit()
    await session.refresh(invite)
    return InvitePublic.model_validate(invite)


async def accept_invite(data: AcceptInviteRequest, session: AsyncSession) -> AuthResponse:
    result = await session.execute(
        select(OrgInvite).where(OrgInvite.token == data.token)
    )
    invite = result.scalar_one_or_none()

    # One generic error covers: wrong token, already used, expired
    if not invite or invite.is_used or invite.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation",
        )

    existing_user = await session.execute(
        select(User).where(User.email == invite.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=invite.email,
        hashed_password=hash_password(data.password),
        display_name=data.display_name,
    )
    session.add(user)
    await session.flush()

    new_membership = OrganizationMember(
        user_id=user.id,
        org_id=invite.org_id,
        role=invite.role,
    )
    session.add(new_membership)

    invite.is_used = True
    session.add(invite)

    await session.commit()
    await session.refresh(user)

    org_result = await session.execute(
        select(Organization).where(Organization.id == invite.org_id)
    )
    org = org_result.scalar_one_or_none()

    token = create_access_token(
        user_id=user.id,
        org_id=org.id,
        role=invite.role.value,
    )
    return AuthResponse(
        access_token=token,
        user=UserPublic.model_validate(user),
        organization=OrganizationPublic.model_validate(org),
    )


