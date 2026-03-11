from __future__ import annotations

import uuid
from datetime import datetime, date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.followup import Followup
from app.schemas.followup import FollowupCreate


def _parse_date(value: str | None) -> date_type | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


async def create_followup(db: AsyncSession, data: FollowupCreate) -> Followup:
    """Save a new followup task to the database."""
    followup = Followup(
        hcp_name=data.hcp_name,
        task=data.task,
        due_date=_parse_date(data.due_date),
        followup_type=data.followup_type,
        status=data.status,
        linked_interaction_id=data.linked_interaction_id,
        notes=data.notes,
    )
    db.add(followup)
    await db.commit()
    await db.refresh(followup)
    return followup


async def get_followups_by_hcp(
    db: AsyncSession, hcp_name: str, limit: int = 20
) -> list[Followup]:
    """Query followups by HCP name (case-insensitive partial match)."""
    result = await db.execute(
        select(Followup)
        .where(Followup.hcp_name.ilike(f"%{hcp_name}%"))
        .order_by(Followup.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_all_followups(
    db: AsyncSession, status: str | None = None, limit: int = 50
) -> list[Followup]:
    """Return all followups, optionally filtered by status."""
    query = select(Followup).order_by(Followup.created_at.desc()).limit(limit)
    if status:
        query = query.where(Followup.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_hcp_interaction_history(
    db: AsyncSession,
    hcp_name: str,
    limit: int = 5,
) -> list:
    """Query the existing interactions table by hcp_name."""
    from app.models.interaction import Interaction

    result = await db.execute(
        select(Interaction)
        .where(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
        .order_by(Interaction.date.desc().nullslast())
        .limit(limit)
    )
    return list(result.scalars().all())
