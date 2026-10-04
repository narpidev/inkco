from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Formula(Base):
    __tablename__ = "formulas"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_formula_user_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    components: Mapped[list["FormulaComponent"]] = relationship(
        back_populates="formula",
        cascade="all, delete-orphan",
        order_by="FormulaComponent.id",
        lazy="selectin",
    )


class FormulaComponent(Base):
    __tablename__ = "formula_components"

    id: Mapped[int] = mapped_column(primary_key=True)
    formula_id: Mapped[int] = mapped_column(
        ForeignKey("formulas.id", ondelete="CASCADE"), index=True
    )
    component_name: Mapped[str] = mapped_column(String(120))
    percentage: Mapped[Decimal] = mapped_column(Numeric(6, 3))

    # Datos de laboratorio (colorimetría), todos opcionales
    lab_l: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), default=None)
    lab_a: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), default=None)
    lab_b: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), default=None)
    delta_e: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), default=None)
    lab_source: Mapped[str | None] = mapped_column(String(50), default=None)  # quick/maquina

    formula: Mapped["Formula"] = relationship(back_populates="components")