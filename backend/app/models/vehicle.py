import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Enum, Numeric, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VehicleStatusEnum(str, enum.Enum):
    available = "available"
    on_trip = "on_trip"
    in_shop = "in_shop"
    retired = "retired"


class VehicleTypeEnum(str, enum.Enum):
    truck = "truck"
    van = "van"
    bus = "bus"
    sedan = "sedan"
    pickup = "pickup"
    other = "other"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    registration_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[VehicleTypeEnum] = mapped_column(
        Enum(VehicleTypeEnum),
        nullable=False
    )
    max_load_capacity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    odometer: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    acquisition_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[VehicleStatusEnum] = mapped_column(
        Enum(VehicleStatusEnum),
        default=VehicleStatusEnum.available,
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
        CheckConstraint("max_load_capacity > 0", name="check_vehicle_max_load_capacity_positive"),
        CheckConstraint("odometer >= 0", name="check_vehicle_odometer_non_negative"),
        CheckConstraint("acquisition_cost >= 0", name="check_vehicle_acquisition_cost_non_negative"),
    )
