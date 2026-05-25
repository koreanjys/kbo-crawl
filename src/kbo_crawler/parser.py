from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from kbo_crawler.metadata import BASE_URL
from kbo_crawler.webforms import absolute_url, extract_postback_target


@dataclass(frozen=True)
class ParsedRow:
    row_index: int
    rank: str | None
    entity_name: str | None
    entity_id: str | None
    entity_team: str | None
    values: dict[str, str]


@dataclass(frozen=True)
class ParsedTable:
    columns: list[str]
    rows: list[ParsedRow]


@dataclass(frozen=True)
class NextPage:
    page_number: int | None
    event_target: str


class KboTableParser:
    def parse(self, html: str) -> ParsedTable:
        soup = BeautifulSoup(html, "lxml")
        table = self._find_table(soup)
        if table is None:
            return ParsedTable(columns=[], rows=[])

        columns = [self._clean_text(th) for th in table.select("thead th")]
        rows: list[ParsedRow] = []
        for row_index, tr in enumerate(table.select("tbody tr"), start=1):
            cells = tr.find_all("td")
            if not cells:
                continue
            values = {
                columns[index] if index < len(columns) else f"col_{index + 1}": self._clean_text(cell)
                for index, cell in enumerate(cells)
            }
            entity_name = values.get("선수명") or values.get("팀명")
            entity_team = values.get("팀명") if values.get("선수명") else None
            entity_id = self._extract_player_id(cells)
            rows.append(
                ParsedRow(
                    row_index=row_index,
                    rank=values.get("순위"),
                    entity_name=entity_name,
                    entity_id=entity_id,
                    entity_team=entity_team,
                    values=values,
                )
            )
        return ParsedTable(columns=columns, rows=rows)

    def next_page(self, html: str) -> NextPage | None:
        soup = BeautifulSoup(html, "html.parser")
        current_page = self._current_page(soup)
        if current_page is None:
            return None

        page_targets: dict[int, str] = {}
        for anchor in soup.select(".paging a"):
            text = self._clean_text(anchor)
            if not text.isdigit():
                continue
            target = extract_postback_target(anchor.get("href"))
            if target:
                page_targets[int(text)] = target

        next_number = current_page + 1
        if next_number in page_targets:
            return NextPage(next_number, page_targets[next_number])

        for anchor in soup.select(".paging a"):
            anchor_id = anchor.get("id", "")
            if anchor_id.endswith("btnNext"):
                target = extract_postback_target(anchor.get("href"))
                if target:
                    return NextPage(None, target)
        return None

    def _find_table(self, soup: BeautifulSoup):
        for table in soup.find_all("table"):
            if table.select_one("thead th") and table.select_one("tbody tr"):
                return table
        return None

    def _current_page(self, soup: BeautifulSoup) -> int | None:
        page_input = soup.find("input", id=re.compile("hfPage$"))
        if page_input and str(page_input.get("value", "")).isdigit():
            return int(page_input.get("value", "1"))
        current = soup.select_one(".paging a.on")
        text = self._clean_text(current) if current else ""
        return int(text) if text.isdigit() else None

    def _extract_player_id(self, cells) -> str | None:
        for cell in cells:
            anchor = cell.find("a", href=True)
            if not anchor:
                continue
            url = absolute_url(BASE_URL, anchor.get("href"))
            if not url:
                continue
            match = re.search(r"playerId=(\d+)", url)
            if match:
                return match.group(1)
        return None

    def _clean_text(self, node) -> str:
        if node is None:
            return ""
        return " ".join(node.get_text(" ", strip=True).split())
