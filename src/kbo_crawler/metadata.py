from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


BASE_URL = "https://www.koreabaseball.com"
CURRENT_SEASON = datetime.now().year


@dataclass(frozen=True)
class Option:
    code: str
    name: str


@dataclass(frozen=True)
class RecordPage:
    key: str
    record_group: str
    category: str
    page_kind: str
    path: str
    season_start: int
    season_end: int
    supports_team: bool = False
    supports_position: bool = False
    supports_situation: bool = False

    @property
    def url(self) -> str:
        return f"{BASE_URL}{self.path}"


SERIES_OPTIONS = [
    Option("0", "KBO 정규시즌"),
    Option("1", "KBO 시범경기"),
    Option("4", "KBO 와일드카드"),
    Option("3", "KBO 준플레이오프"),
    Option("5", "KBO 플레이오프"),
    Option("7", "KBO 한국시리즈"),
]

TEAM_OPTIONS = [
    Option("SS", "삼성"),
    Option("LG", "LG"),
    Option("KT", "KT"),
    Option("HT", "KIA"),
    Option("HH", "한화"),
    Option("OB", "두산"),
    Option("SK", "SSG"),
    Option("LT", "롯데"),
    Option("WO", "키움"),
    Option("NC", "NC"),
]

POSITION_OPTIONS = [
    Option("2", "포수"),
    Option("3,4,5,6", "내야수"),
    Option("7,8,9", "외야수"),
]

HITTER_SITUATION_OPTIONS = [
    Option("MONTH_SC", "월별"),
    Option("WEEK_SC", "요일별"),
    Option("STADIUM_SC", "구장별"),
    Option("HOMEAYAY_SC", "홈/방문별"),
    Option("OPPTEAM_SC", "상대팀별"),
    Option("DAYNIGHT_SC", "주/야간별"),
    Option("HALF_SC", "전/후반기별"),
    Option("41", "투수유형별"),
    Option("43", "주자상황별"),
    Option("44", "볼카운트별"),
    Option("45", "아웃카운트별"),
    Option("46", "이닝별"),
    Option("47", "타순별"),
]

PITCHER_SITUATION_OPTIONS = [
    Option("MONTH_SC", "월별"),
    Option("WEEK_SC", "요일별"),
    Option("STADIUM_SC", "구장별"),
    Option("HOMEAYAY_SC", "홈/방문별"),
    Option("OPPTEAM_SC", "상대팀별"),
    Option("DAYNIGHT_SC", "주/야간별"),
    Option("HALF_SC", "전/후반기별"),
    Option("42", "타자유형별"),
    Option("43", "주자상황별"),
    Option("44", "볼카운트별"),
    Option("45", "아웃카운트별"),
    Option("46", "이닝별"),
    Option("47", "타순별"),
]

RECORD_PAGES = [
    RecordPage("player_hitter_basic1", "player", "hitter", "basic1", "/Record/Player/HitterBasic/Basic1.aspx", 1982, CURRENT_SEASON, True, True, True),
    RecordPage("player_hitter_basic2", "player", "hitter", "basic2", "/Record/Player/HitterBasic/Basic2.aspx", 1982, CURRENT_SEASON, True, True, True),
    RecordPage("player_hitter_detail1", "player", "hitter", "detail1", "/Record/Player/HitterBasic/Detail1.aspx", 1982, CURRENT_SEASON, True, True, True),
    RecordPage("player_pitcher_basic1", "player", "pitcher", "basic1", "/Record/Player/PitcherBasic/Basic1.aspx", 1982, CURRENT_SEASON, True, False, True),
    RecordPage("player_pitcher_basic2", "player", "pitcher", "basic2", "/Record/Player/PitcherBasic/Basic2.aspx", 1982, CURRENT_SEASON, True, False, True),
    RecordPage("player_pitcher_detail1", "player", "pitcher", "detail1", "/Record/Player/PitcherBasic/Detail1.aspx", 1982, CURRENT_SEASON, True, False, True),
    RecordPage("player_pitcher_detail2", "player", "pitcher", "detail2", "/Record/Player/PitcherBasic/Detail2.aspx", 1982, CURRENT_SEASON, True, False, True),
    RecordPage("player_defense_basic", "player", "defense", "basic", "/Record/Player/Defense/Basic.aspx", 2001, CURRENT_SEASON, True, True, False),
    RecordPage("player_runner_basic", "player", "runner", "basic", "/Record/Player/Runner/Basic.aspx", 2001, CURRENT_SEASON, True, True, False),
    RecordPage("team_hitter_basic1", "team", "hitter", "basic1", "/Record/Team/Hitter/Basic1.aspx", 2001, CURRENT_SEASON),
    RecordPage("team_hitter_basic2", "team", "hitter", "basic2", "/Record/Team/Hitter/Basic2.aspx", 2001, CURRENT_SEASON),
    RecordPage("team_pitcher_basic1", "team", "pitcher", "basic1", "/Record/Team/Pitcher/Basic1.aspx", 2001, CURRENT_SEASON),
    RecordPage("team_pitcher_basic2", "team", "pitcher", "basic2", "/Record/Team/Pitcher/Basic2.aspx", 2001, CURRENT_SEASON),
    RecordPage("team_defense_basic", "team", "defense", "basic", "/Record/Team/Defense/Basic.aspx", 2001, CURRENT_SEASON),
    RecordPage("team_runner_basic", "team", "runner", "basic", "/Record/Team/Runner/Basic.aspx", 2001, CURRENT_SEASON),
]

PAGES_BY_KEY = {page.key: page for page in RECORD_PAGES}


def page_situation_options(page: RecordPage) -> list[Option]:
    if page.category == "hitter":
        return HITTER_SITUATION_OPTIONS
    if page.category == "pitcher":
        return PITCHER_SITUATION_OPTIONS
    return []

