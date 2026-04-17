"""Unit tests for nutrition_advisor.

Covers the pure-calculation functions. Interactive input functions are
not exercised here (those would need monkeypatching of stdin).
"""
from __future__ import annotations

import pytest

from tests.conftest import nutrition as n


# ── BMI ────────────────────────────────────────────────────────────
class TestBMI:
    def test_normal_weight(self) -> None:
        # 70 kg, 175 cm → 22.86
        assert n.calculate_bmi(70, 175) == pytest.approx(22.86, abs=0.05)

    def test_underweight_category(self) -> None:
        assert n.bmi_category(17.0) == "Underweight"

    def test_normal_category(self) -> None:
        assert n.bmi_category(22.0) == "Normal weight"

    def test_overweight_category(self) -> None:
        assert n.bmi_category(27.0) == "Overweight"

    def test_obese_category(self) -> None:
        assert n.bmi_category(32.0) == "Obese"

    def test_category_boundaries(self) -> None:
        # Exact 18.5 is "Normal" per Mifflin convention (strict <)
        assert n.bmi_category(18.5) == "Normal weight"
        assert n.bmi_category(25.0) == "Overweight"
        assert n.bmi_category(30.0) == "Obese"


# ── BMR (Mifflin-St Jeor) ──────────────────────────────────────────
class TestBMR:
    def test_male_known_value(self) -> None:
        # 80 kg, 180 cm, 30 y, male
        # 10*80 + 6.25*180 - 5*30 + 5 = 800 + 1125 - 150 + 5 = 1780
        assert n.calculate_bmr(80, 180, 30, "male") == pytest.approx(1780.0)

    def test_female_known_value(self) -> None:
        # 65 kg, 165 cm, 28 y, female
        # 10*65 + 6.25*165 - 5*28 - 161 = 650 + 1031.25 - 140 - 161 = 1380.25
        assert n.calculate_bmr(65, 165, 28, "female") == pytest.approx(1380.25)

    def test_bmr_is_clamped(self) -> None:
        # Absurd inputs should not yield values below 800 kcal.
        # (Defensive clamp added in safety hardening.)
        low = n.calculate_bmr(25, 120, 100, "female")
        assert low >= 800.0

    def test_bmr_non_negative(self) -> None:
        assert n.calculate_bmr(10, 50, 120, "female") > 0


# ── TDEE ───────────────────────────────────────────────────────────
class TestTDEE:
    @pytest.mark.parametrize(
        "activity, factor",
        [(1, 1.2), (2, 1.375), (3, 1.55), (4, 1.725), (5, 1.9)],
    )
    def test_factors(self, activity: int, factor: float) -> None:
        bmr = 1500.0
        assert n.calculate_tdee(bmr, activity) == pytest.approx(bmr * factor)

    def test_invalid_activity_raises(self) -> None:
        with pytest.raises(KeyError):
            n.calculate_tdee(1500.0, 99)


# ── Calorie adjustment ────────────────────────────────────────────
class TestAdjustCalories:
    def test_normal_bmi_no_adjust(self) -> None:
        adj, notes = n.adjust_calories(2000.0, 22.0, 2)
        assert adj == pytest.approx(2000.0)
        assert notes == []

    def test_overweight_applies_deficit(self) -> None:
        adj, notes = n.adjust_calories(2000.0, 27.0, 2)
        assert adj == pytest.approx(2000.0 * 0.85)
        assert len(notes) == 1
        assert "deficit" in notes[0].lower()

    def test_obese_applies_deficit(self) -> None:
        adj, _ = n.adjust_calories(2000.0, 32.0, 2)
        assert adj == pytest.approx(2000.0 * 0.85)

    def test_underweight_applies_surplus(self) -> None:
        adj, notes = n.adjust_calories(2000.0, 17.0, 2)
        assert adj == pytest.approx(2000.0 * 1.15)
        assert "surplus" in notes[0].lower()

    def test_high_activity_adds_buffer(self) -> None:
        adj, notes = n.adjust_calories(2000.0, 22.0, 4)
        assert adj == pytest.approx(2150.0)
        assert any("150" in note for note in notes)

    def test_overweight_plus_very_active(self) -> None:
        # 2000 * 0.85 + 150 = 1850
        adj, _ = n.adjust_calories(2000.0, 27.0, 5)
        assert adj == pytest.approx(1850.0)


# ── Macros ─────────────────────────────────────────────────────────
class TestMacros:
    def test_baseline_ratios_sum_to_one(self) -> None:
        macros = n.calculate_macros(2000.0, 2)
        total = sum(m["pct"] for m in macros.values())
        assert total == pytest.approx(100.0)

    def test_high_activity_boosts_protein(self) -> None:
        low = n.calculate_macros(2000.0, 2)
        high = n.calculate_macros(2000.0, 4)
        assert high["protein"]["pct"] > low["protein"]["pct"]
        assert high["carbs"]["pct"] < low["carbs"]["pct"]

    def test_grams_match_kcal(self) -> None:
        macros = n.calculate_macros(2000.0, 2)
        assert macros["protein"]["grams"] == pytest.approx(macros["protein"]["kcal"] / 4)
        assert macros["carbs"]["grams"] == pytest.approx(macros["carbs"]["kcal"] / 4)
        assert macros["fat"]["grams"] == pytest.approx(macros["fat"]["kcal"] / 9)


# ── Meal plan ──────────────────────────────────────────────────────
class TestMealPlan:
    def test_meal_count(self) -> None:
        macros = n.calculate_macros(2000.0, 2)
        plan = n.build_meal_plan(2000.0, macros)
        assert len(plan) == 5

    def test_meal_fractions_sum_to_total(self) -> None:
        macros = n.calculate_macros(2000.0, 2)
        plan = n.build_meal_plan(2000.0, macros)
        total_kcal = sum(m["kcal"] for m in plan)
        assert total_kcal == pytest.approx(2000.0)

    def test_meal_has_required_fields(self) -> None:
        macros = n.calculate_macros(2000.0, 2)
        plan = n.build_meal_plan(2000.0, macros)
        required = {"name", "time", "kcal", "protein_g", "carbs_g", "fat_g", "suggestions"}
        assert required.issubset(plan[0].keys())
