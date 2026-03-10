import uuid
from datetime import date, time, datetime

from sqlalchemy import String, Text, Date, Time, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hcp_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Meeting"
    )
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    time: Mapped[time | None] = mapped_column(Time, nullable=True)
    attendees: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    topics_discussed: Mapped[str | None] = mapped_column(Text, nullable=True)
    materials_shared: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    samples_distributed: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    sentiment: Mapped[str] = mapped_column(
        String(10), nullable=False, default="Neutral"
    )
    outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_suggested_followups: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
