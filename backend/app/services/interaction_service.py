from __future__ import annotations

import uuid
from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Interaction
from datetime import datetime, time, date as date_type


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p"):
        try:
            return datetime.strptime(value.strip(), fmt).time()
        except ValueError:
            continue
    return None


def _parse_date(value: str | None) -> date_type | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


async def create_interaction(db: AsyncSession, data: InteractionCreate) -> Interaction:
    interaction = Interaction(
        hcp_name=data.hcp_name,
        interaction_type=data.interaction_type,
        date=_parse_date(data.date),
        time=_parse_time(data.time),
        attendees=data.attendees,
        topics_discussed=data.topics_discussed,
        materials_shared=data.materials_shared,
        samples_distributed=data.samples_distributed,
        sentiment=data.sentiment,
        outcomes=data.outcomes,
        follow_up_actions=data.follow_up_actions,
        ai_suggested_followups=data.ai_suggested_followups,
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return interaction


async def get_interaction(db: AsyncSession, interaction_id: uuid.UUID) -> Interaction | None:
    result = await db.execute(
        select(Interaction).where(Interaction.id == interaction_id)
    )
    return result.scalar_one_or_none()


async def update_interaction(
    db: AsyncSession, interaction_id: uuid.UUID, data: InteractionUpdate
) -> Interaction | None:
    interaction = await get_interaction(db, interaction_id)
    if not interaction:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "time" in update_data:
        update_data["time"] = _parse_time(update_data["time"])
    if "date" in update_data:
        update_data["date"] = _parse_date(update_data["date"])

    for field, value in update_data.items():
        setattr(interaction, field, value)

    await db.commit()
    await db.refresh(interaction)
    return interaction
