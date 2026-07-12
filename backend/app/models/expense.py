import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Enum, Numeric, Date, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExpenseTypeEnum(str, enum.Enum):
    toll = "toll"
    parking = "parking"
    insurance = "insurance"
    registration_fee = "registration_fee"
    fine = "fine"
    maintenance_related = "maintenance_related"
    cleaning = "cleaning"
    other = "other"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), nullable=True)
    
    expense_type: Mapped[ExpenseTypeEnum] = mapped_column(
        Enum(ExpenseTypeEnum),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

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
    vehicle = relationship("Vehicle", backref="expenses")
    trip = relationship("Trip", backref="expenses")
    creator = relationship("User", backref="expenses")

    __table_args__ = (
        CheckConstraint("cost > 0", name="check_expense_cost_positive"),
    )
