from __future__ import annotations

import uvicorn
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
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
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(session_dep),
) -> dict:
    statement = select(RecordRow)
    count_statement = select(func.count(RecordRow.id))

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

    for condition in filters:
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

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


def main() -> None:
    uvicorn.run("kbo_crawler.api:app", host=settings.api_host, port=settings.api_port, reload=True)
