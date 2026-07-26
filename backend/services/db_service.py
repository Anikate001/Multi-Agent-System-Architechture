"""Database service using SQLAlchemy async ORM for task persistence, report
storage, and agent-action audit logging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Boolean,
    JSON,
    select,
    update,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from schemas.agents import AgentAction

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# ORM base & table definitions
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


class TaskRow(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True)
    query = Column(Text, nullable=False)
    depth = Column(String(16), nullable=False, default="standard")
    status = Column(String(32), nullable=False, default="planning")
    current_agent = Column(String(32), nullable=True)
    progress_pct = Column(Float, nullable=False, default=0.0)
    token_usage = Column(JSON, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ReportRow(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False, index=True, unique=True)
    report_json = Column(JSON, nullable=False)
    quality_score = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class AgentActionRow(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False, index=True)
    agent = Column(String(32), nullable=False)
    action = Column(Text, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    tokens_used = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Float, nullable=False, default=0.0)
    success = Column(Boolean, nullable=False, default=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class DatabaseService:
    """Async database service for task, report, and action persistence."""

    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def init_db(self) -> None:
        """Create all tables (idempotent)."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_initialised")

    async def dispose(self) -> None:
        """Dispose of the connection pool."""
        await self._engine.dispose()
        logger.info("database_disposed")

    # ------------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------------

    async def save_task(
        self,
        task_id: str,
        query: str,
        status: str = "planning",
        depth: str = "standard",
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                session.add(
                    TaskRow(
                        id=task_id,
                        query=query,
                        status=status,
                        depth=depth,
                    )
                )
        logger.info("task_saved", task_id=task_id, status=status)

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: float = 0.0,
        current_agent: Optional[str] = None,
        token_usage: Optional[dict[str, int]] = None,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                values: dict[str, Any] = {
                    "status": status,
                    "progress_pct": progress,
                    "updated_at": datetime.now(timezone.utc),
                }
                if current_agent is not None:
                    values["current_agent"] = current_agent
                if token_usage is not None:
                    values["token_usage"] = token_usage
                await session.execute(
                    update(TaskRow).where(TaskRow.id == task_id).values(**values)
                )
        logger.info(
            "task_status_updated",
            task_id=task_id,
            status=status,
            progress=progress,
        )

    async def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(TaskRow).where(TaskRow.id == task_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return {
                "task_id": row.id,
                "query": row.query,
                "depth": row.depth,
                "status": row.status,
                "current_agent": row.current_agent,
                "progress_pct": row.progress_pct,
                "token_usage": row.token_usage or {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    async def save_report(
        self,
        task_id: str,
        report_json: dict[str, Any],
        quality_score: Optional[float] = None,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                session.add(
                    ReportRow(
                        task_id=task_id,
                        report_json=report_json,
                        quality_score=quality_score,
                    )
                )
        logger.info("report_saved", task_id=task_id)

    async def get_report(self, task_id: str) -> Optional[dict[str, Any]]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ReportRow).where(ReportRow.task_id == task_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return row.report_json

    # ------------------------------------------------------------------
    # Agent actions
    # ------------------------------------------------------------------

    async def log_agent_action(
        self,
        task_id: str,
        action: AgentAction,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                session.add(
                    AgentActionRow(
                        task_id=task_id,
                        agent=action.agent.value,
                        action=action.action,
                        input_data=action.input_data if isinstance(action.input_data, (dict, list, type(None))) else str(action.input_data),
                        output_data=action.output_data if isinstance(action.output_data, (dict, list, type(None))) else str(action.output_data),
                        tokens_used=action.tokens_used,
                        latency_ms=action.latency_ms,
                        success=action.success,
                        timestamp=action.timestamp,
                    )
                )
        logger.debug("agent_action_logged", task_id=task_id, agent=action.agent.value)

    async def get_task_actions(self, task_id: str) -> list[AgentAction]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentActionRow)
                .where(AgentActionRow.task_id == task_id)
                .order_by(AgentActionRow.timestamp)
            )
            rows = result.scalars().all()
            return [
                AgentAction(
                    agent=row.agent,
                    action=row.action,
                    input_data=row.input_data,
                    output_data=row.output_data,
                    tokens_used=row.tokens_used,
                    latency_ms=row.latency_ms,
                    success=row.success,
                    timestamp=row.timestamp,
                )
                for row in rows
            ]

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Return ``True`` if the database is reachable."""
        try:
            async with self._session_factory() as session:
                await session.execute(select(1))
            return True
        except Exception:
            logger.warning("db_health_check_failed")
            return False
