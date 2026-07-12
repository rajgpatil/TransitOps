import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Enum, Numeric, Date, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DriverStatusEnum(str, enum.Enum):
    available = "available"
    on_trip = "on_trip"
    off_duty = "off_duty"
    suspended = "suspended"


class LicenseCategoryEnum(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    CE = "CE"
    DE = "DE"


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    license_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False
    )
    license_category: Mapped[LicenseCategoryEnum] = mapped_column(
        Enum(LicenseCategoryEnum),
        nullable=False
    )
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    safety_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("100.00"),
        nullable=False
    )
    status: Mapped[DriverStatusEnum] = mapped_column(
        Enum(DriverStatusEnum),
        default=DriverStatusEnum.available,
        nullable=False
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("safety_score >= 0 AND safety_score <= 100", name="check_driver_safety_score_bounds"),
    )
