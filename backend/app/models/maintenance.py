import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Enum, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MaintenanceStatusEnum(str, enum.Enum):
    active = "active"
    closed = "closed"


class MaintenanceTypeEnum(str, enum.Enum):
    oil_change = "oil_change"
    tire_replacement = "tire_replacement"
    brake_service = "brake_service"
    engine_repair = "engine_repair"
    body_work = "body_work"
    inspection = "inspection"
    electrical = "electrical"
    transmission = "transmission"
    other = "other"


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    
    maintenance_type: Mapped[MaintenanceTypeEnum] = mapped_column(
        Enum(MaintenanceTypeEnum),
        nullable=False
    )
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    status: Mapped[MaintenanceStatusEnum] = mapped_column(
        Enum(MaintenanceStatusEnum),
        default=MaintenanceStatusEnum.active,
        nullable=False
    )
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

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
    vehicle = relationship("Vehicle", backref="maintenance_logs")
