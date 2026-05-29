from datetime import datetime, date

from sqlalchemy import Integer, ForeignKey, String, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str] = mapped_column(String, nullable=False)
    hired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
