"""Authentication and user management models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from spb_shared.database import Base


class Profile(Base):
    """User profile with message permissions."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="profile")
    message_permissions: Mapped[list["ProfileMessagePermission"]] = relationship(
        "ProfileMessagePermission", back_populates="profile", cascade="all, delete-orphan"
    )


class ProfileMessagePermission(Base):
    """Junction table for profile and allowed message types."""

    __tablename__ = "profile_message_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    msg_id: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="message_permissions")


class User(Base):
    """User authentication table."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    profile: Mapped[Optional["Profile"]] = relationship("Profile", back_populates="users")
