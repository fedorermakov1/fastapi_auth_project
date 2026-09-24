from sqlalchemy import String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models import Base

from datetime import datetime
from sqlalchemy import DateTime


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )

    full_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    hashed_password: Mapped[str]

    disabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(100),
        default="user",
        nullable=False,
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user"
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user"
    )

