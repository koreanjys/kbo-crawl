from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import delete
from sqlmodel import Session

from kbo_crawler.metadata import (
    Option,
    PAGES_BY_KEY,
    POSITION_OPTIONS,
    RECORD_PAGES,
    SERIES_OPTIONS,
    TEAM_OPTIONS,
    RecordPage,
)
from kbo_crawler.models import CollectionRun, RecordRow
from kbo_crawler.parser import KboTableParser
from kbo_crawler.webforms import WebFormsClient


SELECT_IDS = {
    "season": "cphContents_cphContents_cphContents_ddlSeason_ddlSeason",
    "series": "cphContents_cphContents_cphContents_ddlSeries_ddlSeries",
    "team": "cphContents_cphContents_cphContents_ddlTeam_ddlTeam",
    "position": "cphContents_cphContents_cphContents_ddlPos_ddlPos",
}


@dataclass(frozen=True)
class CrawlTarget:
    page: RecordPage
    season: int
    series: Option
    team: Option | None = None
    position: Option | None = None

    @property
    def condition_key(self) -> str:
        parts = [
            self.page.key,
            str(self.season),
            self.series.code,
            self.team.code if self.team else "",
            self.position.code if self.position else "",
        ]
        return "|".join(parts)


@dataclass(frozen=True)
class CrawlResult:
    target: CrawlTarget
    rows: int


class KboCrawler:
    def __init__(self) -> None:
        self.parser = KboTableParser()

    def crawl_target(self, target: CrawlTarget, session: Session) -> CrawlResult:
        run = CollectionRun(status="running", page_key=target.page.key, condition_key=target.condition_key)
        session.add(run)
        session.commit()
        session.refresh(run)

        try:
            rows = self._crawl_target_rows(target)
            self._replace_rows(target, rows, session)
            run.status = "success"
            run.rows_scraped = len(rows)
            run.finished_at = datetime.now(timezone.utc)
            session.add(run)
            session.commit()
            return CrawlResult(target=target, rows=len(rows))
        except Exception as exc:
            session.rollback()
            run.status = "failed"
            run.error_message = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            session.add(run)
            session.commit()
            raise

    def _crawl_target_rows(self, target: CrawlTarget) -> list[RecordRow]:
        client = WebFormsClient()
        html = client.get(target.page.url)
        html = self._apply_filters(client, html, target)

        records: list[RecordRow] = []
        source_page = 1
        seen_pages: set[int] = set()

        while True:
            table = self.parser.parse(html)
            for parsed in table.rows:
                records.append(
                    RecordRow(
                        page_key=target.page.key,
                        record_group=target.page.record_group,
                        category=target.page.category,
                        page_kind=target.page.page_kind,
                        season=target.season,
                        series_code=target.series.code,
                        series_name=target.series.name,
                        team_code=target.team.code if target.team else None,
                        team_name=target.team.name if target.team else None,
                        position_code=target.position.code if target.position else None,
                        position_name=target.position.name if target.position else None,
                        condition_key=target.condition_key,
                        source_url=target.page.url,
                        source_page=source_page,
                        row_index=parsed.row_index,
                        rank=parsed.rank,
                        entity_name=parsed.entity_name,
                        entity_id=parsed.entity_id,
                        entity_team=parsed.entity_team,
                        columns_json=table.columns,
                        values_json=parsed.values,
                    )
                )

            seen_pages.add(source_page)
            next_page = self.parser.next_page(html)
            if next_page is None:
                break
            source_page = next_page.page_number or source_page + 1
            if source_page in seen_pages:
                break
            html = client.postback(html, next_page.event_target)

        return records

    def _apply_filters(self, client: WebFormsClient, html: str, target: CrawlTarget) -> str:
        html = client.select_by_id(html, SELECT_IDS["season"], str(target.season))
        html = client.select_by_id(html, SELECT_IDS["series"], target.series.code)
        if target.page.supports_team and target.team is not None:
            html = client.select_by_id(html, SELECT_IDS["team"], target.team.code)
        if target.page.supports_position and target.position is not None:
            html = client.select_by_id(html, SELECT_IDS["position"], target.position.code)
        return html

    def _replace_rows(self, target: CrawlTarget, rows: list[RecordRow], session: Session) -> None:
        session.exec(delete(RecordRow).where(RecordRow.condition_key == target.condition_key))
        for row in rows:
            session.add(row)
        session.commit()


def build_targets(
    page_keys: Iterable[str] | None = None,
    seasons: Iterable[int] | None = None,
    include_team_filters: bool = False,
    include_position_filters: bool = False,
) -> list[CrawlTarget]:
    pages = [PAGES_BY_KEY[key] for key in page_keys] if page_keys else RECORD_PAGES
    targets: list[CrawlTarget] = []
    for page in pages:
        target_seasons = list(seasons) if seasons else [page.season_end]
        target_seasons = [season for season in target_seasons if page.season_start <= season <= page.season_end]
        for season in target_seasons:
            for series in SERIES_OPTIONS:
                base_targets = [CrawlTarget(page=page, season=season, series=series)]
                if include_team_filters and page.supports_team:
                    base_targets.extend(CrawlTarget(page=page, season=season, series=series, team=team) for team in TEAM_OPTIONS)
                if include_position_filters and page.supports_position:
                    expanded: list[CrawlTarget] = []
                    for base_target in base_targets:
                        expanded.append(base_target)
                        expanded.extend(
                            CrawlTarget(
                                page=page,
                                season=season,
                                series=series,
                                team=base_target.team,
                                position=position,
                            )
                            for position in POSITION_OPTIONS
                        )
                    base_targets = expanded
                targets.extend(base_targets)
    return targets

