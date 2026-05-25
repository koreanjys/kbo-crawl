from __future__ import annotations

import argparse

from kbo_crawler.crawler import KboCrawler, build_targets
from kbo_crawler.database import create_db_and_tables, get_session
from kbo_crawler.metadata import RECORD_PAGES


def main() -> None:
    parser = argparse.ArgumentParser(prog="kbo-crawl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create database tables")

    crawl_parser = subparsers.add_parser("crawl", help="Crawl KBO record room data")
    crawl_parser.add_argument("--season", type=int, action="append", help="Season to crawl. Can be repeated.")
    crawl_parser.add_argument("--all-seasons", action="store_true", help="Crawl every supported season for selected pages.")
    crawl_parser.add_argument("--page-key", action="append", choices=[page.key for page in RECORD_PAGES], help="Record page key to crawl. Can be repeated.")
    crawl_parser.add_argument("--include-team-filters", action="store_true", help="Also crawl team-filtered player pages.")
    crawl_parser.add_argument("--include-position-filters", action="store_true", help="Also crawl position-filtered player pages.")
    crawl_parser.add_argument("--limit-targets", type=int, help="Limit number of generated targets for smoke tests.")

    args = parser.parse_args()

    if args.command == "init-db":
        create_db_and_tables()
        print("Database tables are ready.")
        return

    if args.command == "crawl":
        create_db_and_tables()
        selected_pages = [page for page in RECORD_PAGES if not args.page_key or page.key in args.page_key]
        seasons = None
        if args.all_seasons:
            min_season = min(page.season_start for page in selected_pages)
            max_season = max(page.season_end for page in selected_pages)
            seasons = range(min_season, max_season + 1)
        elif args.season:
            seasons = args.season

        targets = build_targets(
            page_keys=args.page_key,
            seasons=seasons,
            include_team_filters=args.include_team_filters,
            include_position_filters=args.include_position_filters,
        )
        if args.limit_targets:
            targets = targets[: args.limit_targets]

        crawler = KboCrawler()
        with get_session() as session:
            total_rows = 0
            for index, target in enumerate(targets, start=1):
                print(f"[{index}/{len(targets)}] {target.condition_key}")
                result = crawler.crawl_target(target, session)
                total_rows += result.rows
                print(f"  rows={result.rows}")
        print(f"Crawl completed. targets={len(targets)} rows={total_rows}")

