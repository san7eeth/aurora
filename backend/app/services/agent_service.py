"""Persistence helpers for agent plans and execution history."""

from sqlalchemy import desc, select

from ..database.engine import async_session
from ..database.models import AgentRun


class AgentService:
    async def create(self, task: str, plan: list[dict]) -> AgentRun:
        async with async_session() as session:
            run = AgentRun(task=task, plan=plan, status="awaiting_confirmation")
            session.add(run)
            await session.commit()
            await session.refresh(run)
            return run

    async def get(self, run_id: str) -> AgentRun | None:
        async with async_session() as session:
            result = await session.execute(select(AgentRun).where(AgentRun.id == run_id))
            return result.scalar_one_or_none()

    async def list(self, limit: int = 30) -> list[AgentRun]:
        async with async_session() as session:
            result = await session.execute(
                select(AgentRun).order_by(desc(AgentRun.created_at)).limit(limit)
            )
            return list(result.scalars().all())

    async def update(self, run_id: str, status: str, result_data: dict | None = None) -> None:
        async with async_session() as session:
            run = await session.get(AgentRun, run_id)
            if run:
                run.status = status
                run.result = result_data
                await session.commit()
