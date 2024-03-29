from __future__ import annotations

import logging
from contextlib import asynccontextmanager as actxmgr
from datetime import date as _date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, AsyncIterator, cast

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import BaseModel, Field, computed_field
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator

from ai.backend.common.logging import BraceStyleAdapter

from .auth import auth_required
from .types import CORSOptions, WebMiddleware
from .utils import pydantic_params_api_handler

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect

    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


Base: Any = declarative_base()


class MetricMap(BaseModel):
    pct: Decimal | None = Field(default=None)
    current: Decimal | None = Field(default=None)
    capacity: Decimal | None = Field(default=None)


class MetricColumn(TypeDecorator):
    impl = pgsql.JSONB
    cache_ok = True

    def process_result_value(self, value: dict[str, Any] | None, dialect: Dialect) -> MetricMap:
        if value is None:
            return MetricMap()
        return MetricMap(**value)


class SessionMetric(Base):
    __tablename__ = "session_computesessionmetric"
    __table_args__ = (sa.PrimaryKeyConstraint("time"),)

    time = sa.Column("time", sa.DateTime(timezone=True), index=True, nullable=False)
    session_id = sa.Column("session_id", pgsql.UUID(), nullable=False)
    status = sa.Column("status", sa.String(length=32), nullable=False)
    cpu_util = sa.Column("cpu_util", MetricColumn())
    cpu_used = sa.Column("cpu_used", MetricColumn())
    mem = sa.Column("mem", MetricColumn())
    accel_util = sa.Column("accel_util", MetricColumn())
    accel_mem = sa.Column("accel_mem", MetricColumn())
    io_read = sa.Column("io_read", MetricColumn())
    io_write = sa.Column("io_write", MetricColumn())
    net_rx = sa.Column("net_rx", MetricColumn())
    net_tx = sa.Column("net_tx", MetricColumn())
    accel_type = sa.Column("accel_type", sa.String(length=32))


class DailyUtilizationRequestModel(BaseModel):
    start: _date = Field()
    end: _date = Field()


class UtilizationMetricValue(BaseModel):
    max: Decimal | None = Field(default=None)
    min: Decimal | None = Field(default=None)
    total: Decimal = Field(default=Decimal(0))
    cnt: Decimal = Field(default=Decimal(0))

    @computed_field  # type: ignore[misc]
    @property
    def avg(self) -> Decimal | None:
        if self.cnt == 0:
            return None
        return self.total / self.cnt

    def update(self, val: Decimal | None) -> None:
        if val is None:
            return
        if self.max is None or val > self.max:
            self.max = val
        if self.min is None or val < self.min:
            self.min = val
        self.total += val
        self.cnt += 1


class UtilizationMetricMap(BaseModel):
    pct: UtilizationMetricValue = Field(default_factory=UtilizationMetricValue)
    current: UtilizationMetricValue = Field(default_factory=UtilizationMetricValue)
    capacity: UtilizationMetricValue = Field(default_factory=UtilizationMetricValue)

    def update(self, val: MetricMap) -> None:
        self.pct.update(val.pct)
        self.current.update(val.current)
        self.capacity.update(val.capacity)


class DailyUtilization(BaseModel):
    date: _date = Field()
    cpu_util: UtilizationMetricMap = Field(
        default_factory=UtilizationMetricMap, description="CPU utilization."
    )
    mem: UtilizationMetricMap = Field(
        default_factory=UtilizationMetricMap, description="Main memory utilization."
    )
    accel_util: UtilizationMetricMap = Field(
        default_factory=UtilizationMetricMap, description="Accelerator utilization."
    )
    accel_mem: UtilizationMetricMap = Field(
        default_factory=UtilizationMetricMap, description="Accelerator memory utilization."
    )

    def update_from_row(self, metric: SessionMetric) -> None:
        self.cpu_util.update(metric.cpu_util)
        self.mem.update(metric.mem)
        self.accel_util.update(metric.accel_util)
        self.accel_mem.update(metric.accel_mem)


@actxmgr
async def begin_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        async with AsyncSession(conn) as session:
            async with session.begin():
                yield session


@auth_required
@pydantic_params_api_handler(DailyUtilizationRequestModel)
async def get_daily_util(
    request: web.Request, params: DailyUtilizationRequestModel
) -> list[DailyUtilization]:
    root_ctx: RootContext = request.app["_root.context"]
    if root_ctx.stat_db is None:
        # TODO: Add middleware to do null check
        return []
    start, end = params.start, params.end
    async with begin_session(root_ctx.stat_db) as db_session:
        stmt = (
            sa.select(SessionMetric)
            .where((SessionMetric.time >= start) & (SessionMetric.time <= end))
            .order_by(SessionMetric.time)
        )
        result = (await db_session.scalars(stmt)).all()
        metric_rows = cast(list[SessionMetric], result)

        daily: dict[_date, DailyUtilization] = {}
        for r in metric_rows:
            _date = r.time.date()
            if _date not in daily:
                daily[_date] = DailyUtilization(date=_date)
            daily[_date].update_from_row(r)

        return list(daily.values())


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(default_cors_options: CORSOptions) -> tuple[web.Application, list[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "stats"
    app["api_versions"] = (
        4,
        5,
    )
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route("GET", "/utilization", get_daily_util))
    # cors.add(add_route("GET", "/allocation", get_daily_alloc))
    return app, []
