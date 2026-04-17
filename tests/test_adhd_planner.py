"""Unit tests for adhd_activity_planner."""
from __future__ import annotations

import pytest

import adhd_activity_planner as a


# ── Step calculation ──────────────────────────────────────────────
class TestCalculateDailySteps:
    def test_sedentary_adult(self) -> None:
        res = a.calculate_daily_steps(30, 70, 175, "sedentary", False)
        # base 8000 * 1.0 * 1.0 + 500 = 8500
        assert res["daily_steps"] == 8500
        assert res["bmi_category"] == "Normal weight"

    def test_hyperactive_bonus(self) -> None:
        res = a.calculate_daily_steps(30, 70, 175, "moderate", True)
        assert res["adhd_bonus"] == 1_500

    def test_no_hyperactive_bonus_is_smaller(self) -> None:
        a_yes = a.calculate_daily_steps(30, 70, 175, "moderate", True)
        a_no = a.calculate_daily_steps(30, 70, 175, "moderate", False)
        assert a_yes["daily_steps"] > a_no["daily_steps"]

    def test_bmi_obese_category(self) -> None:
        res = a.calculate_daily_steps(40, 110, 170, "sedentary", False)
        assert res["bmi_category"] == "Obese"

    def test_child_factor_higher(self) -> None:
        child = a.calculate_daily_steps(12, 40, 150, "moderate", False)
        adult = a.calculate_daily_steps(40, 70, 175, "moderate", False)
        # child factor 1.20 vs adult 1.00 — per-step base should be higher
        assert child["age_factor"] > adult["age_factor"]

    def test_elderly_factor_lower(self) -> None:
        elderly = a.calculate_daily_steps(70, 70, 170, "moderate", False)
        assert elderly["age_factor"] < 1.0


class TestHelpers:
    def test_bmi_category(self) -> None:
        assert a._bmi_category(17.0) == "Underweight"
        assert a._bmi_category(22.0) == "Normal weight"
        assert a._bmi_category(27.0) == "Overweight"
        assert a._bmi_category(32.0) == "Obese"

    def test_steps_to_distance(self) -> None:
        # 10 000 steps with 175 cm → ~7.23 km
        km = a.steps_to_distance_km(10_000, 175)
        assert 6.5 <= km <= 8.0

    def test_steps_to_calories_reasonable(self) -> None:
        cals = a.steps_to_calories(10_000, 70)
        assert 350 <= cals <= 450

    def test_steps_to_calories_zero_weight(self) -> None:
        # Defense in depth: should not raise / not return nonsense.
        assert a.steps_to_calories(10_000, 0) == 0

    def test_steps_to_calories_negative_weight(self) -> None:
        assert a.steps_to_calories(10_000, -5) == 0


# ── Activity selection ────────────────────────────────────────────
class TestRecommendActivities:
    def test_returns_list(self) -> None:
        chosen = a.recommend_activities(
            fitness_level="moderate",
            adhd_subtype="hyperactive",
            available_days=4,
            preferences=[],
            time_per_session_max=60,
        )
        assert isinstance(chosen, list)
        assert len(chosen) > 0

    def test_filters_by_session_time(self) -> None:
        chosen = a.recommend_activities(
            fitness_level="moderate",
            adhd_subtype="combined",
            available_days=7,
            preferences=[],
            time_per_session_max=30,
        )
        # Every returned activity must fit in 30 min.
        for act in chosen:
            assert act.duration_min <= 30

    def test_respects_available_days(self) -> None:
        chosen = a.recommend_activities(
            fitness_level="moderate",
            adhd_subtype="combined",
            available_days=3,
            preferences=[],
            time_per_session_max=120,
        )
        total = sum(act.sessions_per_week for act in chosen)
        assert total <= 3

    def test_hyperactive_prefers_high_impulse_score(self) -> None:
        chosen = a.recommend_activities(
            fitness_level="active",
            adhd_subtype="hyperactive",
            available_days=2,
            preferences=[],
            time_per_session_max=120,
        )
        # First pick should be near the top of the impulse score distribution.
        assert chosen[0].impulse_control_score >= 8


# ── Weekly schedule ───────────────────────────────────────────────
class TestWeeklySchedule:
    def test_schedule_has_seven_days(self) -> None:
        acts = a.recommend_activities(
            fitness_level="moderate",
            adhd_subtype="combined",
            available_days=4,
            preferences=[],
            time_per_session_max=120,
        )
        sched = a.build_weekly_schedule(acts, 4)
        assert set(sched.keys()) == set(a.DAYS)

    def test_rest_days_respected(self) -> None:
        acts = a.recommend_activities(
            fitness_level="moderate",
            adhd_subtype="combined",
            available_days=3,
            preferences=[],
            time_per_session_max=120,
        )
        sched = a.build_weekly_schedule(acts, 3)
        active_days = [d for d, act in sched.items() if act is not None]
        assert len(active_days) <= 3

    def test_no_back_to_back_high_when_possible(self) -> None:
        # Synthetic input where the constraint IS satisfiable:
        # 2 High + 2 Low activities, 4 days. Any correct greedy
        # placement should never produce two consecutive High days.
        high_a = a.Activity("HA", "", 30, 1, 100, 9, "", ["x"], "High")
        high_b = a.Activity("HB", "", 30, 1, 100, 9, "", ["x"], "High")
        low_a  = a.Activity("LA", "", 30, 1, 100, 7, "", ["x"], "Low")
        low_b  = a.Activity("LB", "", 30, 1, 100, 7, "", ["x"], "Low")

        # Run multiple times because of the internal shuffle.
        for _ in range(50):
            sched = a.build_weekly_schedule([high_a, high_b, low_a, low_b], 4)
            sequence = [sched[d] for d in a.DAYS if sched[d] is not None]
            pairs = sum(
                1 for i in range(len(sequence) - 1)
                if sequence[i].intensity == "High" and sequence[i + 1].intensity == "High"
            )
            assert pairs == 0, f"Unexpected back-to-back: {[s.name for s in sequence]}"

    def test_graceful_when_all_high(self) -> None:
        # If every activity is High, the scheduler must still produce
        # a valid schedule (no crash), even though constraint fails.
        hi = a.Activity("H", "", 30, 1, 100, 9, "", ["x"], "High")
        sched = a.build_weekly_schedule([hi, hi, hi], 3)
        placed = [d for d, s in sched.items() if s is not None]
        assert len(placed) == 3


# ── Data integrity ────────────────────────────────────────────────
class TestActivityPool:
    def test_pool_is_non_empty(self) -> None:
        assert len(a.ACTIVITY_POOL) > 0

    def test_impulse_scores_in_range(self) -> None:
        for act in a.ACTIVITY_POOL:
            assert 1 <= act.impulse_control_score <= 10

    def test_intensities_valid(self) -> None:
        valid = {"Low", "Medium", "High"}
        for act in a.ACTIVITY_POOL:
            assert act.intensity in valid

    def test_all_have_tips(self) -> None:
        for act in a.ACTIVITY_POOL:
            assert len(act.tips) >= 1
