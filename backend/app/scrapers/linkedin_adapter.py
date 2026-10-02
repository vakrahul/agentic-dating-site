from __future__ import annotations

import re
from typing import Any

KNOWN_ACTORS: dict[str, dict[str, Any]] = {
    "linkedintel-core/linkedin-profile-scraper-no-cookies": {
        "input_key": "profileUrls",
        "input_kind": "urls",
    },
    "maximedupre/linkedin-profile-scraper-no-cookie": {
        "input_key": "profileUrls",
        "input_kind": "objects",
    },
    "bovi/linkedin-profile-scraper": {"input_key": "profileUrls", "input_kind": "urls"},
    "gopalakrishnan/linkedin-profile": {"input_key": "profiles", "input_kind": "urls"},
    "supreme_coder/linkedin-profile-scraper": {"input_key": "urls", "input_kind": "urls"},
}


def extract_slug(url: str) -> str:
    match = re.search(r"linkedin\.com/in/([^/?#]+)", url.lower())
    return match.group(1) if match else url.rstrip("/").split("/")[-1]


def build_input(url: str, actor_id: str) -> dict[str, Any]:
    spec = KNOWN_ACTORS.get(actor_id, {"input_key": "urls", "input_kind": "urls"})
    key = spec["input_key"]
    if spec["input_kind"] == "objects":
        return {key: [{"url": url}]}
    return {key: [url]}


def adapt(raw: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
    items = raw.get("items") or []
    row: dict[str, Any] = {}
    for item in items:
        if isinstance(item, dict) and (item.get("error") or item.get("scrapeStatus") == "error"):
            continue
        if isinstance(item, dict):
            row = item
            break
    if not row:
        return {"name": None, "headline": None, "about": None, "experience": [],
                "education": [], "skills": [], "location": None, "raw": raw}

    name = _first(row, "name", "fullName", "full_name", "profileName")
    headline = _first(row, "headline", "title", "occupation", "currentPosition")
    about = _first(row, "about", "summary", "description")
    location = _first(row, "location", "geoLocation", "geo_location", "region")
    current_company = _first(row, "current_company", "company", "currentCompanyName")
    experience = _experience(row)
    education = _education(row)
    skills = _skills(row)

    return {
        "name": name,
        "headline": headline,
        "about": about,
        "location": location,
        "current_company": current_company,
        "experience": experience,
        "education": education,
        "skills": skills,
        "follower_count": row.get("follower_count"),
        "recent_posts": row.get("recent_posts") or [],
        "actor_id": actor_id,
        "raw": row,
    }


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value:
            return value
    return None


def _experience(row: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("experience", "experiences", "positions", "workExperience"):
        value = row.get(key)
        if isinstance(value, list):
            out = []
            for item in value:
                if not isinstance(item, dict):
                    continue
                # In some scrapers, item has 'company', in others 'name' represents the company
                title = _first(item, "title", "role", "position", "job_title", "occupation")
                company = _first(item, "company", "companyName", "organization")
                if not company and not title:
                    company = _first(item, "name")
                elif not company and item.get("name") != title:
                    company = _first(item, "name")
                out.append(
                    {
                        "title": title,
                        "company": company,
                        "description": _first(item, "description", "summary"),
                        "duration": _first(item, "duration", "dateRange", "period"),
                        "start": _first(item, "start", "startDate"),
                        "end": _first(item, "end", "endDate"),
                    }
                )
            return out
    return []


def _education(row: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("education", "educations", "schools"):
        value = row.get(key)
        if isinstance(value, list):
            out = []
            for item in value:
                if not isinstance(item, dict):
                    continue
                out.append(
                    {
                        "school": _first(item, "school", "schoolName", "institution", "name"),
                        "degree": _first(item, "degree", "degreeName", "fieldOfStudy", "field"),
                        "duration": _first(item, "duration", "dateRange", "period"),
                    }
                )
            return out
    return []


def _skills(row: dict[str, Any]) -> list[str]:
    for key in ("skills", "skillList", "topSkills"):
        value = row.get(key)
        if isinstance(value, list):
            out: list[str] = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip())
                elif isinstance(item, dict):
                    name = _first(item, "name", "skill", "title")
                    if name:
                        out.append(str(name).strip())
            return out
    return []
