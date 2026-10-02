from __future__ import annotations

import pytest

from app.dating.scenes import pick_scene
from app.schemas import PairInput
from app.scrapers.linkedin_adapter import adapt, build_input, extract_slug

FIXTURE_ROW = {
    "name": "Jane Doe",
    "headline": "Senior Engineer at Acme",
    "summary": "I build reliable systems.",
    "geoLocation": "Berlin, Germany",
    "experience": [
        {"title": "Senior Engineer", "companyName": "Acme", "description": "k8s", "dateRange": "2020-2024"}
    ],
    "education": [{"schoolName": "TU Munich", "degreeName": "BSc"}],
    "skills": [{"name": "Python"}, {"name": "K8s"}],
}


class TestAdapter:
    def test_build_input_known_actor(self) -> None:
        inp = build_input("https://www.linkedin.com/in/janedoe", "linkedintel-core/linkedin-profile-scraper-no-cookies")
        assert inp == {"profileUrls": ["https://www.linkedin.com/in/janedoe"]}

    def test_build_input_object_style_actor(self) -> None:
        inp = build_input("https://www.linkedin.com/in/x", "maximedupre/linkedin-profile-scraper-no-cookie")
        assert inp == {"profileUrls": [{"url": "https://www.linkedin.com/in/x"}]}

    def test_build_input_unknown_actor_defaults_to_urls(self) -> None:
        inp = build_input("https://www.linkedin.com/in/x", "some/unknown-actor")
        assert inp == {"urls": ["https://www.linkedin.com/in/x"]}

    def test_adapt_normalizes_fields(self) -> None:
        out = adapt({"items": [FIXTURE_ROW]}, actor_id="test/actor")
        assert out["name"] == "Jane Doe"
        assert out["headline"] == "Senior Engineer at Acme"
        assert out["about"] == "I build reliable systems."
        assert out["location"] == "Berlin, Germany"
        assert out["experience"][0]["title"] == "Senior Engineer"
        assert out["experience"][0]["company"] == "Acme"
        assert out["education"][0]["school"] == "TU Munich"
        assert out["skills"] == ["Python", "K8s"]

    def test_adapt_skips_error_rows(self) -> None:
        out = adapt({"items": [{"error": "not found"}, FIXTURE_ROW]}, actor_id="t")
        assert out["name"] == "Jane Doe"

    def test_adapt_empty_items(self) -> None:
        out = adapt({"items": []}, actor_id="t")
        assert out["name"] is None and out["skills"] == []

    def test_extract_slug(self) -> None:
        assert extract_slug("https://www.linkedin.com/in/Jane-Doe/?x=1") == "jane-doe"


class TestUrlValidation:
    def test_valid_pair(self) -> None:
        item = PairInput(
            linkedin_url="https://www.linkedin.com/in/janedoe",
            instagram_url="https://www.instagram.com/janedoe",
        )
        assert item.linkedin_url.endswith("/in/janedoe") or item.linkedin_url.endswith("janedoe")

    def test_rejects_bad_linkedin(self) -> None:
        with pytest.raises(Exception):
            PairInput(linkedin_url="https://example.com/x", instagram_url="https://www.instagram.com/a")

    def test_rejects_bad_instagram(self) -> None:
        with pytest.raises(Exception):
            PairInput(linkedin_url="https://www.linkedin.com/in/a", instagram_url="not-a-url")

    def test_adds_scheme_and_strips_trailing_slash(self) -> None:
        item = PairInput(
            linkedin_url="www.linkedin.com/in/janedoe/",
            instagram_url="www.instagram.com/janedoe/",
        )
        assert item.linkedin_url.startswith("https://")
        assert not item.linkedin_url.endswith("/")


class TestScenes:
    def test_shared_interest_picks_matching_scene(self) -> None:
        scene = pick_scene(["running", "coffee"], ["coffee", "art"])
        assert "coffee shop" in scene

    def test_no_shared_interest_falls_back(self) -> None:
        assert pick_scene(["chess"], ["surfing"]) == "a coffee shop"

    def test_unknown_shared_interest_falls_back_to_topic(self) -> None:
        scene = pick_scene(["knitting"], ["knitting"])
        assert "knitting" in scene
