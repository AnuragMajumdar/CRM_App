import uuid
from datetime import date, datetime

from sqlalchemy import String, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Followup(Base):
    __tablename__ = "followups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hcp_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    followup_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Call"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    linked_interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
