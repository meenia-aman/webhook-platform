from enum import Enum
import uuid
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

from sqlalchemy import TIMESTAMP, UUID, ForeignKey, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base


class SessionStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(
            SessionStatus,
            name="ck_auth_session_status",
            native_enum=False,
            create_constraint=True,
            validating_string=True,
        ),
        nullable=False,
        default=SessionStatus.PENDING,
        server_default=SessionStatus.PENDING.value,
    )

    device_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ip_address: Mapped[IPv4Address | IPv6Address | None] = mapped_column(
        INET,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    last_used_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )

    revoked_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
    )

    revoke_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
