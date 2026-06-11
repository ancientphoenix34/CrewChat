from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.models import OrgRole, Organization, OrganizationMember, User
from src.auth.schemas import AuthResponse, OrganizationPublic, RegisterOrgRequest, UserPublic
from src.auth.utils import create_access_token, hash_password


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
