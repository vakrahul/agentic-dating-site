from __future__ import annotations

import math

import pytest

from app.scoring.composite import (
    final_score,
    geometric_mean,
    referee_mean,
    rescale_embeddings,
    score_breakdown,
)
from app.scoring.normalize import normal_cdf, z_normalize, z_scores
from app.scoring.ranks import (
    FALSE_FRIEND,
    SURPRISE,
    badge_for,
    link_badge_turn,
    match_ranks,
    rank_desc,
)


class TestZNormalize:
    def test_zero_variance_maps_to_fifty(self) -> None:
        assert z_normalize([70.0, 70.0, 70.0]) == [50.0, 50.0, 50.0]

    def test_single_value_maps_to_fifty(self) -> None:
        assert z_normalize([80.0]) == [50.0]

    def test_preserves_order_and_spans(self) -> None:
        values = [60.0, 70.0, 80.0]
        out = z_normalize(values)
        assert out[0] < out[1] < out[2]
        assert all(0.0 <= v <= 100.0 for v in out)

    def test_symmetric_values_center_on_fifty(self) -> None:
        out = z_normalize([50.0, 100.0])
        mean = sum(out) / len(out)
        assert mean == pytest.approx(50.0, abs=0.5)
        assert out[1] - mean == pytest.approx(mean - out[0], abs=0.5)
        assert out[0] < 50.0 < out[1]

    def test_z_scores_mean_zero(self) -> None:
        zs = z_scores([10.0, 20.0, 30.0])
        assert sum(zs) / len(zs) == pytest.approx(0.0, abs=1e-9)

    def test_normal_cdf_known_values(self) -> None:
        assert normal_cdf(0.0) == pytest.approx(0.5)
        assert normal_cdf(1.96) == pytest.approx(0.975, abs=0.001)

    def test_empty_input(self) -> None:
        assert z_normalize([]) == []

    def test_generous_scorer_normalized_unchanged_ordering(self) -> None:
        generous = z_normalize([90.0, 95.0, 99.0])
        harsh = z_normalize([10.0, 20.0, 30.0])
        assert generous[0] < generous[2]
        assert harsh[0] < harsh[2]


class TestGeometricMean:
    def test_basic(self) -> None:
        assert geometric_mean(4.0, 9.0) == pytest.approx(6.0)

    def test_zero(self) -> None:
        assert geometric_mean(0.0, 50.0) == 0.0

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            geometric_mean(-1.0, 5.0)


class TestRefereeMean:
    def test_mean_of_five(self) -> None:
        dims = {
            "chemistry": 80.0,
            "values_fit": 60.0,
            "lifestyle_fit": 70.0,
            "ambition_fit": 90.0,
            "interests_fit": 50.0,
        }
        assert referee_mean(dims) == pytest.approx(70.0)

    def test_empty(self) -> None:
        assert referee_mean({}) == 0.0


class TestEmbeddingRescale:
    def test_min_max_spans_full_range(self) -> None:
        out = rescale_embeddings([0.2, 0.4, 0.6])
        assert out[0] == pytest.approx(0.0)
        assert out[2] == pytest.approx(100.0)
        assert out[1] == pytest.approx(50.0)

    def test_degenerate_falls_back_to_clip(self) -> None:
        out = rescale_embeddings([0.5, 0.5])
        assert out == [50.0, 50.0]

    def test_empty(self) -> None:
        assert rescale_embeddings([]) == []


class TestFinalScore:
    def test_weighted_composite(self) -> None:
        value = final_score(mutual=80.0, referee=70.0, embedding=60.0)
        assert value == pytest.approx(0.45 * 80 + 0.40 * 70 + 0.15 * 60)

    def test_bounds(self) -> None:
        assert final_score(100.0, 100.0, 100.0) == pytest.approx(100.0)
        assert final_score(0.0, 0.0, 0.0) == pytest.approx(0.0)


class TestBreakdown:
    def test_maps_referee_dims(self) -> None:
        dims = {
            "chemistry": 1.0,
            "values_fit": 2.0,
            "lifestyle_fit": 3.0,
            "ambition_fit": 4.0,
            "interests_fit": 5.0,
        }
        out = score_breakdown(dims)
        assert out == {
            "values": 2.0,
            "interests": 5.0,
            "lifestyle": 3.0,
            "ambition": 4.0,
            "chemistry": 1.0,
        }


class TestRanks:
    def test_rank_desc_ordering_and_ties(self) -> None:
        ranks = rank_desc([("a", 90.0), ("b", 95.0), ("c", 95.0)])
        assert ranks["b"] == 1
        assert ranks["c"] == 2
        assert ranks["a"] == 3

    def test_match_ranks_delta_direction(self) -> None:
        partners = [
            {"person_id": 1, "embedding": 10.0, "final": 95.0},
            {"person_id": 2, "embedding": 95.0, "final": 40.0},
        ]
        rows = {r["person_id"]: r for r in match_ranks(partners)}
        assert rows[1]["similarity_rank"] == 2
        assert rows[1]["final_rank"] == 1
        assert rows[1]["delta"] == 1
        assert rows[2]["similarity_rank"] == 1
        assert rows[2]["final_rank"] == 2
        assert rows[2]["delta"] == -1

    def test_sorted_by_final_rank(self) -> None:
        partners = [
            {"person_id": 1, "embedding": 50.0, "final": 30.0},
            {"person_id": 2, "embedding": 60.0, "final": 80.0},
        ]
        out = match_ranks(partners)
        assert out[0]["person_id"] == 2
        assert out[1]["person_id"] == 1


class TestBadges:
    def test_surprise_match(self) -> None:
        assert badge_for(similarity_rank=4, final_rank=3, partner_count=6) == SURPRISE

    def test_surprise_requires_bottom_half(self) -> None:
        assert badge_for(similarity_rank=3, final_rank=2, partner_count=6) is None

    def test_false_friend(self) -> None:
        assert badge_for(similarity_rank=2, final_rank=6, partner_count=8) == FALSE_FRIEND

    def test_false_friend_requires_outside_top_five(self) -> None:
        assert badge_for(similarity_rank=2, final_rank=5, partner_count=8) is None

    def test_no_badge_for_mid_ranks(self) -> None:
        assert badge_for(similarity_rank=5, final_rank=5, partner_count=9) is None


class TestBadgeTurnLink:
    def test_surprise_prefers_spark(self) -> None:
        tags = [
            {"turn_index": 3, "tag": "friction", "reason": "clash"},
            {"turn_index": 7, "tag": "spark", "reason": "click"},
        ]
        link = link_badge_turn(tags, SURPRISE)
        assert link is not None and link["turn_index"] == 7

    def test_false_friend_prefers_friction(self) -> None:
        tags = [
            {"turn_index": 2, "tag": "spark", "reason": "click"},
            {"turn_index": 9, "tag": "friction", "reason": "clash"},
        ]
        link = link_badge_turn(tags, FALSE_FRIEND)
        assert link is not None and link["turn_index"] == 9

    def test_falls_back_to_earliest_tag(self) -> None:
        tags = [{"turn_index": 5, "tag": "friction", "reason": "x"}]
        link = link_badge_turn(tags, SURPRISE)
        assert link is not None and link["turn_index"] == 5

    def test_no_tags_returns_none(self) -> None:
        assert link_badge_turn([], SURPRISE) is None

    def test_no_badge_returns_none(self) -> None:
        tags = [{"turn_index": 1, "tag": "spark", "reason": "x"}]
        assert link_badge_turn(tags, None) is None
