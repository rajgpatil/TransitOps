import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Enum, Numeric, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TripStatusEnum(str, enum.Enum):
    draft = "draft"
    dispatched = "dispatched"
    completed = "completed"
    cancelled = "cancelled"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    
    cargo_weight: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    planned_distance: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    actual_distance: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    fuel_consumed: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    final_odometer: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    
    status: Mapped[TripStatusEnum] = mapped_column(
        Enum(TripStatusEnum),
        default=TripStatusEnum.draft,
        nullable=False
    )
    
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

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

    # Relationships
    vehicle = relationship("Vehicle", backref="trips")
    driver = relationship("Driver", backref="trips")
