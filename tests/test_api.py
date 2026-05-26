from __future__ import annotations

from sqlmodel import select

from kbo_crawler.api import _merge_record_rows, _record_filters
from kbo_crawler.models import RecordRow


def test_merge_record_rows_combines_page_columns_for_same_entity() -> None:
    rows = [
        _record_row(
            page_key="player_hitter_basic1",
            page_kind="basic1",
            columns=["순위", "선수명", "AVG"],
            values={"순위": "1", "선수명": "박성한", "AVG": "0.369"},
        ),
        _record_row(
            page_key="player_hitter_basic2",
            page_kind="basic2",
            columns=["순위", "선수명", "OPS"],
            values={"순위": "1", "선수명": "박성한", "OPS": "0.900"},
        ),
    ]

    merged = _merge_record_rows(rows)

    assert len(merged) == 1
    assert merged[0]["columns"] == ["순위", "선수명", "AVG", "OPS"]
    assert merged[0]["values"]["AVG"] == "0.369"
    assert merged[0]["values"]["OPS"] == "0.900"
    assert merged[0]["pageKinds"] == ["basic1", "basic2"]


def test_merge_record_rows_keeps_different_entities_separate() -> None:
    rows = [
        _record_row(entity_id="1", entity_name="박성한", row_index=1),
        _record_row(entity_id="2", entity_name="최원준", row_index=2),
    ]

    merged = _merge_record_rows(rows)

    assert [row["entityName"] for row in merged] == ["박성한", "최원준"]


def test_record_filters_apply_search_to_entity_and_team_fields() -> None:
    filters = _record_filters(query="박성한")
    statement = select(RecordRow)
    for condition in filters:
        statement = statement.where(condition)

    sql = str(statement)

    assert "record_rows.entity_name LIKE" in sql
    assert "record_rows.entity_team LIKE" in sql
    assert "record_rows.team_name LIKE" in sql


def _record_row(
    *,
    page_key: str = "player_hitter_basic1",
    page_kind: str = "basic1",
    columns: list[str] | None = None,
    values: dict[str, str] | None = None,
    entity_id: str = "123",
    entity_name: str = "박성한",
    row_index: int = 1,
) -> RecordRow:
    return RecordRow(
        page_key=page_key,
        record_group="player",
        category="hitter",
        page_kind=page_kind,
        season=2026,
        series_code="0",
        series_name="KBO 정규시즌",
        condition_key="sample",
        source_url="https://example.com",
        source_page=1,
        row_index=row_index,
        rank=str(row_index),
        entity_name=entity_name,
        entity_id=entity_id,
        entity_team="SSG",
        columns_json=columns or ["순위", "선수명", "AVG"],
        values_json=values or {"순위": str(row_index), "선수명": entity_name, "AVG": "0.369"},
    )
