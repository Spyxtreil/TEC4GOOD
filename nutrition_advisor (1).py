"""
=============================================================
  AI-Assisted Nutrition Advisor
  A CLI program to generate personalized daily nutrition plans
=============================================================

DISCLAIMER: This tool is for educational purposes only. The
calculations are estimates based on population-level formulas
(Mifflin-St Jeor, WHO activity factors) and do NOT replace the
advice of a registered dietitian or physician. It does not
account for allergies, medical conditions, pregnancy, eating
disorders or medications. See TERMS_AND_CONDITIONS.md in the
repository root before using.
"""

# ── Standard library ──────────────────────────────────────
import sys
import textwrap

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 – USER INPUT
# ─────────────────────────────────────────────────────────────────────────────

ACTIVITY_FACTORS = {
    1: ("Sedentary",          1.2),
    2: ("Lightly active",     1.375),
    3: ("Moderately active",  1.55),
    4: ("Very active",        1.725),
    5: ("Extremely active",   1.9),
}


def _safe_input(prompt: str) -> str:
    """input() wrapper that converts EOF into a clean exit."""
    try:
        return input(prompt)
    except EOFError:
        print("\n\n  Input stream closed. Goodbye!")
        sys.exit(0)


def get_float(prompt: str, min_val: float = 0, max_val: float = 1_000) -> float:
    """Prompt the user for a float in the inclusive range [min_val, max_val]."""
    while True:
        try:
            value = float(_safe_input(prompt).strip())
            # Inclusive on both ends — previous version silently rejected
            # exact-boundary values like weight=10 even though the prompt
            # advertised 10 as valid.
            if not (min_val <= value <= max_val):
                print(f"  ⚠  Please enter a value between {min_val} and {max_val}.")
            else:
                return value
        except ValueError:
            print("  ⚠  Invalid input – please enter a number.")


def get_int(prompt: str, valid: set) -> int:
    """Prompt the user for an integer that belongs to *valid*."""
    while True:
        try:
            value = int(_safe_input(prompt).strip())
            if value in valid:
                return value
            print(f"  ⚠  Please choose one of: {sorted(valid)}")
        except ValueError:
            print("  ⚠  Invalid input – please enter a whole number.")


def get_yes_no(prompt: str) -> bool:
    """Ask a yes/no question."""
    while True:
        raw = _safe_input(prompt).strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  ⚠  Please answer 'y' or 'n'.")


def get_sex() -> str:
    """Ask the user for their biological sex (used in BMR formula)."""
    while True:
        raw = _safe_input("Sex (male / female): ").strip().lower()
        if raw in ("male", "female", "m", "f"):
            return "male" if raw.startswith("m") else "female"
        print("  ⚠  Please type 'male' or 'female'.")


def collect_user_info() -> dict:
    """Gather all required fields from the user and return them as a dict."""
    print("\n" + "=" * 60)
    print("  PERSONAL INFORMATION")
    print("=" * 60)

    # Minimum age 10: below that the Mifflin-St Jeor equation is not
    # validated and can produce misleading results. Pediatric nutrition
    # requires a clinical approach, not a CLI script.
    age    = get_float("Age (years, 10–120): ",    min_val=10, max_val=120)
    sex    = get_sex()
    height = get_float("Height (cm, 120–230): ",   min_val=120, max_val=230)
    weight = get_float("Weight (kg, 25–300): ",    min_val=25,  max_val=300)

    print("\nActivity level:")
    for key, (label, _) in ACTIVITY_FACTORS.items():
        print(f"  {key}. {label}")
    activity = get_int("Choose (1–5): ", valid=set(ACTIVITY_FACTORS))

    print("\nHealth flags (these will block the plan and send you to a professional):")
    has_condition = get_yes_no(
        "  Do you have diabetes, kidney disease, heart disease,\n"
        "  an eating disorder, or are you pregnant/breastfeeding? (y/n): "
    )

    return {
        "age":            int(age),
        "sex":            sex,
        "height":         height,
        "weight":         weight,
        "activity":       activity,
        "has_condition":  has_condition,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 – NUTRITIONAL CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """
    Body Mass Index = weight(kg) / height(m)²
    """
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def bmi_category(bmi: float) -> str:
    """Return a human-readable BMI category."""
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25.0:
        return "Normal weight"
    if bmi < 30.0:
        return "Overweight"
    return "Obese"


def calculate_bmr(weight_kg: float, height_cm: float,
                  age: int, sex: str) -> float:
    """
    Mifflin-St Jeor Equation:
      Male:   BMR = 10·W + 6.25·H − 5·A + 5
      Female: BMR = 10·W + 6.25·H − 5·A − 161
    W = weight in kg, H = height in cm, A = age in years

    Returns a non-negative BMR; values under 800 kcal/day are
    clamped to 800 because anything below that is a modelling
    artifact, not a physiological reality.
    """
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    bmr = base + 5 if sex == "male" else base - 161
    return max(bmr, 800.0)


def calculate_tdee(bmr: float, activity_level: int) -> float:
    """
    Total Daily Energy Expenditure = BMR × activity factor.
    """
    _, factor = ACTIVITY_FACTORS[activity_level]
    return bmr * factor


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 – AI-LIKE ADJUSTMENT LAYER
# ─────────────────────────────────────────────────────────────────────────────

def adjust_calories(tdee: float, bmi: float,
                    activity_level: int) -> tuple[float, list[str]]:
    """
    Apply simple rule-based adjustments and return (adjusted_calories, notes).

    Rules:
      • Overweight / Obese  → reduce by 15 %
      • Underweight         → increase by 15 %
      • Very / Extremely active → extra +150 kcal buffer
    """
    notes: list[str] = []
    adjusted = tdee

    category = bmi_category(bmi)
    if category in ("Overweight", "Obese"):
        adjusted *= 0.85
        notes.append(
            f"Your BMI ({bmi:.1f} – {category}) suggests a moderate "
            "calorie deficit of 15 % has been applied to support healthy "
            "weight loss."
        )
    elif category == "Underweight":
        adjusted *= 1.15
        notes.append(
            f"Your BMI ({bmi:.1f} – {category}) suggests a 15 % calorie "
            "surplus has been applied to support healthy weight gain."
        )

    if activity_level >= 4:
        adjusted += 150
        notes.append(
            "Your high activity level warrants an extra 150 kcal to "
            "support muscle recovery and performance."
        )

    return adjusted, notes


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 – MACRONUTRIENT DISTRIBUTION
# ─────────────────────────────────────────────────────────────────────────────

# Macro split:  Protein 25 % | Carbs 50 % | Fat 25 %
MACRO_RATIOS = {"protein": 0.25, "carbs": 0.50, "fat": 0.25}

# kcal per gram
KCAL_PER_GRAM = {"protein": 4, "carbs": 4, "fat": 9}


def calculate_macros(total_kcal: float,
                     activity_level: int) -> dict[str, dict]:
    """
    Calculate macro grams from total daily calories.
    Very/Extremely active users get a protein boost (+5 pp from carbs).
    """
    ratios = dict(MACRO_RATIOS)
    if activity_level >= 4:
        ratios["protein"] += 0.05
        ratios["carbs"]   -= 0.05

    macros: dict[str, dict] = {}
    for nutrient, ratio in ratios.items():
        kcal  = total_kcal * ratio
        grams = kcal / KCAL_PER_GRAM[nutrient]
        macros[nutrient] = {
            "pct":   ratio * 100,
            "kcal":  kcal,
            "grams": grams,
        }
    return macros


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 – MEAL TIMING PLAN
# ─────────────────────────────────────────────────────────────────────────────

# Each meal: (name, time, calorie fraction, food suggestions)
MEAL_TEMPLATE = [
    ("Breakfast", "08:00", 0.25,
     ["Oatmeal with berries", "Scrambled eggs & whole-grain toast",
      "Greek yogurt with granola", "Avocado toast with poached egg"]),
    ("Morning Snack", "11:00", 0.10,
     ["Apple with almond butter", "Handful of mixed nuts",
      "Cottage cheese with fruit", "Rice cakes with hummus"]),
    ("Lunch", "14:00", 0.30,
     ["Grilled chicken & quinoa salad", "Tuna wrap with veggies",
      "Lentil soup with whole-grain bread", "Brown rice bowl with tofu"]),
    ("Afternoon Snack", "17:00", 0.10,
     ["Protein shake", "Banana with peanut butter",
      "Edamame", "Low-fat cheese & whole-grain crackers"]),
    ("Dinner", "20:00", 0.25,
     ["Salmon with roasted vegetables", "Lean beef stir-fry with noodles",
      "Chickpea curry with basmati rice", "Turkey meatballs with zucchini pasta"]),
]


def build_meal_plan(total_kcal: float,
                    macros: dict[str, dict]) -> list[dict]:
    """
    Distribute calories and macros across the 5-meal schedule.
    Returns a list of meal dicts ready for display.
    """
    plan = []
    for name, time, fraction, suggestions in MEAL_TEMPLATE:
        meal_kcal = total_kcal * fraction
        plan.append({
            "name":        name,
            "time":        time,
            "kcal":        meal_kcal,
            "protein_g":   meal_kcal * (macros["protein"]["pct"] / 100) / 4,
            "carbs_g":     meal_kcal * (macros["carbs"]["pct"]   / 100) / 4,
            "fat_g":       meal_kcal * (macros["fat"]["pct"]     / 100) / 9,
            "suggestions": suggestions,
        })
    return plan


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 – OUTPUT / REPORT
# ─────────────────────────────────────────────────────────────────────────────

LINE = "─" * 60
DLINE = "═" * 60


def _col(label: str, value: str, width: int = 28) -> str:
    """Left-pad a two-column row."""
    return f"  {label:<{width}} {value}"


def print_report(user: dict, bmr: float, tdee: float, adjusted_kcal: float,
                 bmi: float, macros: dict, meal_plan: list,
                 ai_notes: list[str]) -> None:
    """Print the full structured nutrition report to stdout."""

    activity_label, _ = ACTIVITY_FACTORS[user["activity"]]

    # ── Header ──────────────────────────────────────────────
    print("\n" + DLINE)
    print("  🥗  PERSONALIZED DAILY NUTRITION PLAN")
    print(DLINE)

    # ── User summary ────────────────────────────────────────
    print(f"\n{'USER SUMMARY':^60}")
    print(LINE)
    print(_col("Age:",            f"{user['age']} years"))
    print(_col("Sex:",            user["sex"].capitalize()))
    print(_col("Height:",         f"{user['height']:.1f} cm"))
    print(_col("Weight:",         f"{user['weight']:.1f} kg"))
    print(_col("Activity level:", activity_label))
    print(_col("BMI:",            f"{bmi:.1f}  ({bmi_category(bmi)})"))

    # ── Calorie targets ─────────────────────────────────────
    print(f"\n{'CALORIE TARGETS':^60}")
    print(LINE)
    print(_col("Basal Metabolic Rate (BMR):", f"{bmr:,.0f} kcal"))
    print(_col("TDEE (before adjustments):", f"{tdee:,.0f} kcal"))
    print(_col("Adjusted daily calories:",   f"{adjusted_kcal:,.0f} kcal"))

    # ── Macronutrients ──────────────────────────────────────
    print(f"\n{'MACRONUTRIENT TARGETS':^60}")
    print(LINE)
    print(f"  {'Nutrient':<14} {'%':>5}  {'Calories':>10}  {'Grams':>8}")
    print(f"  {'-'*14} {'-'*5}  {'-'*10}  {'-'*8}")
    for nutrient, data in macros.items():
        print(
            f"  {nutrient.capitalize():<14} "
            f"{data['pct']:>4.0f}%  "
            f"{data['kcal']:>9.0f}  "
            f"{data['grams']:>7.1f}g"
        )

    # ── Meal plan ───────────────────────────────────────────
    print(f"\n{'DAILY MEAL SCHEDULE':^60}")
    print(LINE)
    for meal in meal_plan:
        print(
            f"\n  🍽  {meal['name']:<18} ⏰ {meal['time']}"
            f"  |  {meal['kcal']:.0f} kcal"
        )
        print(
            f"     Protein: {meal['protein_g']:.1f}g  "
            f"Carbs: {meal['carbs_g']:.1f}g  "
            f"Fat: {meal['fat_g']:.1f}g"
        )
        print("     💡 Suggestions:")
        for item in meal["suggestions"][:2]:        # show top 2
            print(f"        • {item}")

    # ── AI recommendations ──────────────────────────────────
    if ai_notes:
        print(f"\n{'AI RECOMMENDATIONS':^60}")
        print(LINE)
        for note in ai_notes:
            wrapped = textwrap.fill(note, width=56,
                                    initial_indent="  • ",
                                    subsequent_indent="    ")
            print(wrapped)

    # ── General nutrition advice ────────────────────────────
    advice = (
        "Aim to drink at least 2–3 litres of water daily and include "
        "a variety of colourful vegetables at each main meal for "
        "vitamins and fibre. Prioritise whole foods over processed "
        "options, eat slowly to improve satiety signals, and try to "
        "keep meal times consistent to support your circadian rhythm. "
        "If you engage in resistance training, consider consuming "
        "protein within 30–60 minutes post-workout."
    )
    print(f"\n{'GENERAL NUTRITION ADVICE':^60}")
    print(LINE)
    print(textwrap.fill(advice, width=58,
                        initial_indent="  ",
                        subsequent_indent="  "))

    print("\n" + DLINE)
    print("  Report generated by AI Nutrition Advisor")
    print("  ⚠  This is for informational purposes only.")
    print("  Always consult a registered dietitian or physician.")
    print(DLINE + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 – MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def show_disclaimer_and_require_acceptance() -> None:
    """Print the disclaimer up-front and require explicit acceptance."""
    print(DLINE)
    print("  ⚠  IMPORTANT — MEDICAL DISCLAIMER")
    print(DLINE)
    print(textwrap.fill(
        "This program is for EDUCATIONAL purposes only. It is NOT a "
        "medical tool and does NOT replace advice from a registered "
        "dietitian or physician. The estimates shown are based on "
        "population formulas and may be inaccurate for your individual "
        "situation. Do NOT use this program if you have an eating "
        "disorder or are currently in treatment for one.",
        width=58, initial_indent="  ", subsequent_indent="  "))
    print()
    print("  Full terms: see TERMS_AND_CONDITIONS.md in the repository root.")
    print(DLINE)
    if not get_yes_no("  Do you understand and accept these terms? (y/n): "):
        print("\n  You must accept the terms to use this tool. Exiting.\n")
        sys.exit(0)


def main() -> None:
    print(DLINE)
    print("  Welcome to the AI-Assisted Nutrition Advisor")
    print(DLINE)

    try:
        show_disclaimer_and_require_acceptance()

        # 1. Collect user input
        user = collect_user_info()

        # 1b. Early exit for users with conditions that require
        # professional input — the heuristic plan is unsafe for them.
        if user.get("has_condition"):
            print("\n" + DLINE)
            print("  ⚠  PLAN NOT GENERATED")
            print(DLINE)
            print(textwrap.fill(
                "Based on your answers, this tool is not appropriate "
                "for you. Please consult a registered dietitian or "
                "your physician for a plan tailored to your medical "
                "situation. Generic calorie and macro targets can be "
                "harmful in the presence of diabetes, kidney disease, "
                "heart disease, eating disorders, pregnancy or "
                "breastfeeding.",
                width=58, initial_indent="  ", subsequent_indent="  "))
            print(DLINE + "\n")
            return

        # 2. Core calculations
        bmr  = calculate_bmr(user["weight"], user["height"],
                             user["age"],    user["sex"])
        tdee = calculate_tdee(bmr, user["activity"])
        bmi  = calculate_bmi(user["weight"], user["height"])

        # 3. AI-like adjustments
        adjusted_kcal, ai_notes = adjust_calories(tdee, bmi, user["activity"])

        # 4. Macros
        macros = calculate_macros(adjusted_kcal, user["activity"])

        # 5. Meal plan
        meal_plan = build_meal_plan(adjusted_kcal, macros)

        # 6. Print report
        print_report(user, bmr, tdee, adjusted_kcal,
                     bmi, macros, meal_plan, ai_notes)

    except KeyboardInterrupt:
        print("\n\n  Session cancelled. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
