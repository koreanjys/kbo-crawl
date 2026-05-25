from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Referer": "https://www.koreabaseball.com/",
}


@dataclass(frozen=True)
class SelectField:
    name: str
    field_id: str
    selected: str


class WebFormsClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.current_url: str | None = None

    def get(self, url: str) -> str:
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        self.current_url = response.url
        return response.text

    def postback(self, html: str, event_target: str, updates: dict[str, str] | None = None) -> str:
        if not self.current_url:
            raise RuntimeError("postback called before get")

        data = self._form_data(html)
        data["__EVENTTARGET"] = event_target
        data["__EVENTARGUMENT"] = ""
        for key, value in (updates or {}).items():
            data[key] = value

        response = self.session.post(self.current_url, data=data, timeout=20)
        response.raise_for_status()
        self.current_url = response.url
        return response.text

    def select_by_id(self, html: str, field_id: str, value: str) -> str:
        field = self.find_select(html, field_id)
        return self.postback(html, field.name, {field.name: value})

    def find_select(self, html: str, field_id: str) -> SelectField:
        soup = BeautifulSoup(html, "lxml")
        select = soup.find("select", {"id": field_id})
        if select is None:
            raise ValueError(f"select not found: {field_id}")
        selected = select.find("option", selected=True)
        if selected is None:
            selected = select.find("option")
        return SelectField(
            name=select.get("name", ""),
            field_id=field_id,
            selected=selected.get("value", "") if selected else "",
        )

    def _form_data(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "lxml")
        form = soup.find("form")
        if form is None:
            raise ValueError("ASP.NET form not found")

        data: dict[str, str] = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            if not name:
                continue
            input_type = (input_tag.get("type") or "text").lower()
            if input_type in {"submit", "button", "image", "file"}:
                continue
            if input_type in {"checkbox", "radio"} and not input_tag.has_attr("checked"):
                continue
            data[name] = input_tag.get("value", "")

        for select in form.find_all("select"):
            name = select.get("name")
            if not name:
                continue
            selected = select.find("option", selected=True) or select.find("option")
            data[name] = selected.get("value", "") if selected else ""

        data.setdefault("__EVENTTARGET", "")
        data.setdefault("__EVENTARGUMENT", "")
        return data


def extract_postback_target(href: str | None) -> str | None:
    if not href:
        return None
    match = re.search(r"__doPostBack\('([^']+)'", href)
    return match.group(1) if match else None


def absolute_url(base_url: str, href: str | None) -> str | None:
    if not href:
        return None
    return urljoin(base_url, href)
