from __future__ import annotations

from app.analysis.verify import is_substring, normalize_text, verify_analysis

LINKEDIN = {
    "name": "Jane Doe",
    "headline": "Senior Engineer at Acme",
    "about": "I build reliable systems and mentor junior engineers.",
    "location": "Berlin",
    "experience": [
        {"title": "Senior Engineer", "company": "Acme", "description": "Led migration to k8s", "duration": "2020 - 2024"}
    ],
    "education": [{"school": "TU Munich", "degree": "BSc Computer Science"}],
    "skills": ["Python", "Kubernetes"],
}

INSTAGRAM = {
    "username": "janedoe",
    "full_name": "Jane",
    "biography": "Trail runner | espresso | film photography",
    "latest_posts": [
        {"caption": "Sunday long run done #running #trail", "hashtags": ["running", "trail"]},
        {"caption": "New roll of film developed", "hashtags": []},
    ],
}


class TestNormalize:
    def test_collapses_whitespace_and_case(self) -> None:
        assert normalize_text("Hello   World\n") == "hello world"

    def test_nfkc_unicode(self) -> None:
        assert normalize_text("ﬁne") == "fine"


class TestIsSubstring:
    def test_verbatim_pass(self) -> None:
        assert is_substring("I build reliable systems", LINKEDIN["about"])

    def test_case_insensitive_normalization(self) -> None:
        assert is_substring("i BUILD reliable SYSTEMS", LINKEDIN["about"])

    def test_whitespace_variants_pass(self) -> None:
        assert is_substring("I  build   reliable systems", LINKEDIN["about"])

    def test_missing_quote_fails(self) -> None:
        assert not is_substring("I design rockets to Mars", LINKEDIN["about"])

    def test_empty_quote_fails(self) -> None:
        assert not is_substring("", LINKEDIN["about"])

    def test_quote_from_other_source_fails(self) -> None:
        assert not is_substring("Sunday long run done", LINKEDIN["about"])


def _payload(claims, gaps=None):
    return {
        "claims": claims,
        "say_do_gap": gaps or [],
        "data_gaps": [],
    }


class TestVerifyAnalysis:
    def test_valid_claim_kept(self) -> None:
        payload, dropped = verify_analysis(
            _payload(
                [{"claim": "engineer", "source": "linkedin",
                  "quote": "Senior Engineer at Acme", "kind": "stated", "confidence": 0.9}]
            ),
            LINKEDIN,
            INSTAGRAM,
        )
        assert len(payload["claims"]) == 1
        assert dropped == []

    def test_fabricated_quote_dropped_and_recorded(self) -> None:
        payload, dropped = verify_analysis(
            _payload(
                [
                    {"claim": "astronaut", "source": "linkedin",
                     "quote": "Flew to the ISS in 2019", "kind": "stated", "confidence": 0.9},
                    {"claim": "engineer", "source": "linkedin",
                     "quote": "Senior Engineer at Acme", "kind": "stated", "confidence": 0.9},
                ]
            ),
            LINKEDIN,
            INSTAGRAM,
        )
        assert len(payload["claims"]) == 1
        assert len(dropped) == 1
        assert payload["claims"][0]["claim"] == "engineer"
        assert "failed verbatim verification" in payload["data_gaps"][0]

    def test_instagram_quote_checked_against_instagram(self) -> None:
        payload, dropped = verify_analysis(
            _payload(
                [{"claim": "runs trails", "source": "instagram",
                  "quote": "Trail runner", "kind": "stated", "confidence": 0.8}]
            ),
            LINKEDIN,
            INSTAGRAM,
        )
        assert len(payload["claims"]) == 1 and not dropped

    def test_say_do_gap_evidence_verified(self) -> None:
        payload, dropped = verify_analysis(
            _payload(
                claims=[],
                gaps=[
                    {
                        "stated": "builds systems",
                        "lived": "runs trails",
                        "type": "agree",
                        "evidence": [
                            {"source": "linkedin", "quote": "I build reliable systems"},
                            {"source": "instagram", "quote": "never said this"},
                        ],
                    }
                ],
            ),
            LINKEDIN,
            INSTAGRAM,
        )
        assert len(payload["say_do_gap"]) == 1
        assert len(payload["say_do_gap"][0]["evidence"]) == 1
        assert len(dropped) == 1

    def test_gap_with_no_evidence_dropped(self) -> None:
        payload, dropped = verify_analysis(
            _payload(
                claims=[],
                gaps=[
                    {
                        "stated": "a",
                        "lived": "b",
                        "type": "diverge",
                        "evidence": [{"source": "linkedin", "quote": "totally made up"}],
                    }
                ],
            ),
            LINKEDIN,
            INSTAGRAM,
        )
        assert payload["say_do_gap"] == []
        assert any(d["kind"] == "say_do_gap" for d in dropped)
