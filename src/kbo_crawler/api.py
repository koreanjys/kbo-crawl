from __future__ import annotations

from collections import OrderedDict

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, select

from kbo_crawler.config import settings
from kbo_crawler.database import create_db_and_tables, get_session
from kbo_crawler.metadata import (
    POSITION_OPTIONS,
    RECORD_PAGES,
    SERIES_OPTIONS,
    TEAM_OPTIONS,
)
from kbo_crawler.models import RecordRow


app = FastAPI(title="KBO Crawler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def session_dep():
    with get_session() as session:
        yield session


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metadata")
def metadata() -> dict:
    return {
        "pages": [
            {
                "key": page.key,
                "recordGroup": page.record_group,
                "category": page.category,
                "pageKind": page.page_kind,
                "seasonStart": page.season_start,
                "seasonEnd": page.season_end,
                "supportsTeam": page.supports_team,
                "supportsPosition": page.supports_position,
                "supportsSituation": page.supports_situation,
            }
            for page in RECORD_PAGES
        ],
        "series": [option.__dict__ for option in SERIES_OPTIONS],
        "teams": [option.__dict__ for option in TEAM_OPTIONS],
        "positions": [option.__dict__ for option in POSITION_OPTIONS],
    }


@app.get("/records")
def records(
    page_key: str | None = Query(default=None),
    record_group: str | None = Query(default=None),
    category: str | None = Query(default=None),
    series_code: str | None = Query(default=None),
    season: int | None = Query(default=None),
    q: str | None = Query(default=None),
    merged: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(session_dep),
) -> dict:
    statement = select(RecordRow)
    count_statement = select(func.count(RecordRow.id))

    filters = _record_filters(
        page_key=page_key,
        record_group=record_group,
        category=category,
        series_code=series_code,
        season=season,
        query=q,
    )

    for condition in filters:
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    if merged:
        if not record_group or not category:
            raise HTTPException(status_code=400, detail="merged records require record_group and category")
        statement = statement.where(
            RecordRow.team_code.is_(None),
            RecordRow.position_code.is_(None),
            RecordRow.situation_code.is_(None),
        )
        rows = session.exec(statement).all()
        merged_rows = _merge_record_rows(rows)
        total = len(merged_rows)
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "rows": merged_rows[offset : offset + limit],
        }

    statement = statement.order_by(RecordRow.page_key, RecordRow.source_page, RecordRow.row_index).offset(offset).limit(limit)
    total = session.exec(count_statement).one()
    rows = session.exec(statement).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "rows": [
            {
                "id": row.id,
                "pageKey": row.page_key,
                "recordGroup": row.record_group,
                "category": row.category,
                "pageKind": row.page_kind,
                "season": row.season,
                "seriesName": row.series_name,
                "teamName": row.team_name,
                "positionName": row.position_name,
                "sourcePage": row.source_page,
                "rowIndex": row.row_index,
                "rank": row.rank,
                "entityName": row.entity_name,
                "entityId": row.entity_id,
                "entityTeam": row.entity_team,
                "columns": row.columns_json,
                "values": row.values_json,
                "collectedAt": row.collected_at.isoformat(),
            }
            for row in rows
        ],
    }


def _merge_record_rows(rows: list[RecordRow]) -> list[dict]:
    page_order = {page.key: index for index, page in enumerate(RECORD_PAGES)}
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            page_order.get(row.page_key, len(page_order)),
            row.source_page,
            row.row_index,
            row.id or 0,
        ),
    )
    merged_rows: OrderedDict[str, dict] = OrderedDict()
    for row in sorted_rows:
        key = _merge_key(row)
        if key not in merged_rows:
            merged_rows[key] = {
                "id": f"merged:{key}",
                "recordGroup": row.record_group,
                "category": row.category,
                "season": row.season,
                "seriesName": row.series_name,
                "teamName": row.team_name,
                "positionName": row.position_name,
                "rank": row.rank,
                "entityName": row.entity_name,
                "entityId": row.entity_id,
                "entityTeam": row.entity_team,
                "pageKeys": [],
                "pageKinds": [],
                "columns": [],
                "values": {},
                "collectedAt": row.collected_at.isoformat(),
            }

        merged = merged_rows[key]
        if row.page_key not in merged["pageKeys"]:
            merged["pageKeys"].append(row.page_key)
        if row.page_kind not in merged["pageKinds"]:
            merged["pageKinds"].append(row.page_kind)
        if row.collected_at.isoformat() > merged["collectedAt"]:
            merged["collectedAt"] = row.collected_at.isoformat()

        for column in row.columns_json:
            if column not in merged["columns"]:
                merged["columns"].append(column)
            value = row.values_json.get(column)
            if column not in merged["values"] or merged["values"][column] in {None, ""}:
                merged["values"][column] = value

    return list(merged_rows.values())


def _record_filters(
    *,
    page_key: str | None = None,
    record_group: str | None = None,
    category: str | None = None,
    series_code: str | None = None,
    season: int | None = None,
    query: str | None = None,
) -> list[ColumnElement[bool]]:
    filters = []
    if page_key:
        filters.append(RecordRow.page_key == page_key)
    if record_group:
        filters.append(RecordRow.record_group == record_group)
    if category:
        filters.append(RecordRow.category == category)
    if series_code:
        filters.append(RecordRow.series_code == series_code)
    if season:
        filters.append(RecordRow.season == season)
    search = query.strip() if query else ""
    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                RecordRow.entity_name.like(search_pattern),
                RecordRow.entity_team.like(search_pattern),
                RecordRow.team_name.like(search_pattern),
            )
        )
    return filters


def _merge_key(row: RecordRow) -> str:
    entity_key = row.entity_id or f"{row.entity_name or ''}:{row.entity_team or ''}"
    return "|".join(
        [
            row.record_group,
            row.category,
            str(row.season or ""),
            row.series_code or "",
            entity_key,
        ]
    )


def main() -> None:
    uvicorn.run("kbo_crawler.api:app", host=settings.api_host, port=settings.api_port, reload=True)
