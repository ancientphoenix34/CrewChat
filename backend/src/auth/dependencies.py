from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.models import OrgRole, OrganizationMember, User
from src.auth.utils import decode_access_token
from src.core.database import get_session

# OAuth2PasswordBearer tells FastAPI: "look for a Bearer token in the Authorization header."
# It also makes the /docs UI show a padlock + login form automatically.
# Node parallel: the logic inside a middleware that does:
#   const token = req.headers.authorization?.split(' ')[1]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),       # ← extracts Bearer token from header
    session: AsyncSession = Depends(get_session),  # ← gets a DB session for this request
) -> User:
    # This single exception is reused for ALL auth failures — don't leak whether
    # it was a bad token, expired token, or user-not-found. Same error every time.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # OAuth2 standard header
    )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch the user from DB — confirms they still exist and are still active.
    # Node parallel: User.findUnique({ where: { id: userId } })
    user = await session.get(User, UUID(user_id))

    if user is None or not user.is_active:
        raise credentials_exception

    return user


# A stricter version — requires the user to be verified.
# Used on sensitive endpoints (inviting teammates, promoting admins).
# Node parallel: a second middleware you'd chain: requireVerified(requireAuth(handler))
async def get_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return current_user


# Checks the user's role in a specific org.
# Returns a factory function — the outer function takes the required role,
# the inner async function is the actual Depends() callable.
def require_org_role(minimum_role: OrgRole):
    async def _check(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> OrganizationMember:
        # Node parallel: checking req.user.role >= requiredRole
        statement = select(OrganizationMember).where(
            OrganizationMember.user_id == current_user.id
        )
        result = await session.exec(statement)  # type: ignore[attr-defined]
        membership = result.first()

        role_hierarchy = [OrgRole.MEMBER, OrgRole.MANAGER, OrgRole.ADMIN, OrgRole.OWNER]

        if (
            membership is None
            or role_hierarchy.index(membership.role) < role_hierarchy.index(minimum_role)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return membership
    return _check
