from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


# Python Enum — like TypeScript's enum or a string union type.
# Stored as a string in the DB, not an integer.
class OrgRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"


# ── Organization ─────────────────────────────────────────────────────────────
# Prisma parallel:
#   model Organization {
#     id        String   @id @default(uuid())
#     name      String
#     createdAt DateTime @default(now())
#   }
class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Back-reference: org.members gives you a list of OrganizationMember rows.
    # Like Prisma's `members OrganizationMember[]`
    members: list["OrganizationMember"] = Relationship(back_populates="organization")


# ── User ─────────────────────────────────────────────────────────────────────
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # unique=True → DB-level uniqueness constraint (not just app-level check).
    # Normalized at the schema layer (lowercased) before reaching here.
    email: str = Field(unique=True, index=True)

    hashed_password: str          # bcrypt hash — never the raw password
    display_name: str

    # is_active=False is "soft delete" — preserves message history with attribution.
    # We never hard-delete users. Node parallel: a `deletedAt` timestamp pattern.
    is_active: bool = Field(default=True)
    is_email_verified: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Back-reference to org memberships (a user can belong to multiple orgs later)
    org_memberships: list["OrganizationMember"] = Relationship(back_populates="user")


# ── OrganizationMember ────────────────────────────────────────────────────────
# This is the join table with an extra `role` column.
# Prisma parallel:
#   model OrganizationMember {
#     userId String
#     orgId  String
#     role   OrgRole
#     user   User         @relation(fields: [userId], references: [id])
#     org    Organization @relation(fields: [orgId],  references: [id])
#     @@id([userId, orgId])
#   }
class OrganizationMember(SQLModel, table=True):
    __tablename__ = "organization_members"

    # Composite primary key — a user can only have one role per org.
    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    org_id: UUID = Field(foreign_key="organizations.id", primary_key=True)

    role: OrgRole = Field(default=OrgRole.MEMBER)
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships let you do member.user and member.organization
    user: User | None = Relationship(back_populates="org_memberships")
    organization: Organization | None = Relationship(back_populates="members")
