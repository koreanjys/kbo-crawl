from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CollectionRun(SQLModel, table=True):
    __tablename__ = "collection_runs"

    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(index=True)
    page_key: str | None = Field(default=None, index=True)
    condition_key: str | None = Field(default=None, index=True)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    rows_scraped: int = 0
    error_message: str | None = None


class RecordRow(SQLModel, table=True):
    __tablename__ = "record_rows"
    __table_args__ = (
        UniqueConstraint("condition_key", "source_page", "row_index", name="uq_record_condition_row"),
    )

    id: int | None = Field(default=None, primary_key=True)
    page_key: str = Field(index=True)
    record_group: str = Field(index=True)
    category: str = Field(index=True)
    page_kind: str = Field(index=True)
    season: int | None = Field(default=None, index=True)
    series_code: str | None = Field(default=None, index=True)
    series_name: str | None = None
    team_code: str | None = Field(default=None, index=True)
    team_name: str | None = None
    position_code: str | None = Field(default=None, index=True)
    position_name: str | None = None
    situation_code: str | None = Field(default=None, index=True)
    situation_name: str | None = None
    situation_detail_code: str | None = None
    situation_detail_name: str | None = None
    condition_key: str = Field(index=True)
    source_url: str
    source_page: int = Field(index=True)
    row_index: int = Field(index=True)
    rank: str | None = None
    entity_name: str | None = Field(default=None, index=True)
    entity_id: str | None = Field(default=None, index=True)
    entity_team: str | None = Field(default=None, index=True)
    columns_json: list[str] = Field(sa_column=Column(JSON))
    values_json: dict[str, Any] = Field(sa_column=Column(JSON))
    collected_at: datetime = Field(default_factory=utc_now, index=True)

