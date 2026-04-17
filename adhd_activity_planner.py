#!/usr/bin/env python3
"""
ADHD Activity & Step Planner
Calculates daily steps and recommends structured physical activities
to help individuals with ADHD manage impulse control.

DISCLAIMER: This tool is for educational purposes only. It is NOT
medical advice and does not replace consultation with a qualified
healthcare professional. See TERMS_AND_CONDITIONS.md in the
repository root before using.
"""

import math
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────
#  DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class Activity:
    name: str
    emoji: str
    duration_min: int        # recommended minutes per session
    sessions_per_week: int
    steps_per_min: float     # approximate steps generated
    impulse_control_score: int  # 1–10
    focus_benefit: str
    tips: list[str]
    intensity: str           # Low / Medium / High


# ─────────────────────────────────────────────
#  ACTIVITY DATABASE
# ─────────────────────────────────────────────

ACTIVITY_POOL: list[Activity] = [
    Activity(
        name="Brisk Walking / Hiking",
        emoji="🚶",
        duration_min=30,
        sessions_per_week=5,
        steps_per_min=100,
        impulse_control_score=7,
        focus_benefit="Rhythmic movement boosts dopamine & serotonin. Great for clearing mental chatter.",
        tips=[
            "Use a podcast or audiobook to keep your mind engaged.",
            "Change your route regularly to stay stimulated.",
            "Morning walks set a calm tone for the whole day.",
        ],
        intensity="Low",
    ),
    Activity(
        name="Swimming",
        emoji="🏊",
        duration_min=45,
        sessions_per_week=3,
        steps_per_min=0,   # non-step activity — handled separately
        impulse_control_score=9,
        focus_benefit="Full sensory immersion forces present-moment focus. Bilateral movement synchronises brain hemispheres.",
        tips=[
            "Counting laps gives an easy mindfulness anchor.",
            "Try interval sets: sprint 2 laps, rest 30 s — this matches ADHD energy bursts.",
            "Water resistance provides deep proprioceptive feedback.",
        ],
        intensity="Medium",
    ),
    Activity(
        name="Gym / Strength Training",
        emoji="🏋️",
        duration_min=50,
        sessions_per_week=3,
        steps_per_min=30,
        impulse_control_score=8,
        focus_benefit="Progressive overload requires tracking numbers — gives ADHD brains a concrete goal.",
        tips=[
            "Use a workout log app to satisfy the ADHD need for novelty & progress.",
            "Superset exercises to minimise idle time between sets.",
            "Focus on compound lifts: squats, deadlifts, bench — fewer decisions, bigger payoff.",
        ],
        intensity="High",
    ),
    Activity(
        name="Martial Arts / Boxing",
        emoji="🥋",
        duration_min=60,
        sessions_per_week=3,
        steps_per_min=60,
        impulse_control_score=10,
        focus_benefit="Requires split-second decision-making under pressure — directly trains impulse inhibition circuits.",
        tips=[
            "The structured belts/ranks system is deeply motivating for ADHD.",
            "Sparring channels aggression and impulsivity constructively.",
            "Breathing techniques from martial arts carry over to daily stress.",
        ],
        intensity="High",
    ),
    Activity(
        name="Cycling (Outdoor or Spin)",
        emoji="🚴",
        duration_min=45,
        sessions_per_week=4,
        steps_per_min=0,
        impulse_control_score=7,
        focus_benefit="Sustained aerobic load releases BDNF — the brain's fertiliser for focus and self-regulation.",
        tips=[
            "Outdoor cycling adds sensory variety to prevent boredom.",
            "Track distance/speed metrics to gamify the experience.",
            "Evening rides help burn off residual hyperactivity before bed.",
        ],
        intensity="Medium",
    ),
    Activity(
        name="Team Sports (Basketball, Football, etc.)",
        emoji="⚽",
        duration_min=60,
        sessions_per_week=2,
        steps_per_min=110,
        impulse_control_score=9,
        focus_benefit="Social accountability + fast-paced unpredictability keeps ADHD brains fully engaged.",
        tips=[
            "Join a recreational league for regular commitment.",
            "Role-based play (defender, striker) provides structure within chaos.",
            "Post-game socialising is a natural dopamine reward.",
        ],
        intensity="High",
    ),
    Activity(
        name="Yoga / Mindful Movement",
        emoji="🧘",
        duration_min=40,
        sessions_per_week=3,
        steps_per_min=15,
        impulse_control_score=8,
        focus_benefit="Deliberate breath-movement synchronisation builds the 'pause before acting' neural pathway.",
        tips=[
            "Vinyasa flow yoga is better for ADHD than slow Hatha — more movement.",
            "Use a guided class to prevent mind-wandering.",
            "Even 10 minutes of yoga before work reduces impulsivity measurably.",
        ],
        intensity="Low",
    ),
    Activity(
        name="Dance / Zumba",
        emoji="💃",
        duration_min=45,
        sessions_per_week=3,
        steps_per_min=80,
        impulse_control_score=8,
        focus_benefit="Learning choreography uses working memory and timing — key ADHD deficit areas.",
        tips=[
            "Classes are better than solo — social pressure aids follow-through.",
            "Upbeat music naturally elevates mood and motivation.",
            "New routines regularly challenge and stimulate the ADHD brain.",
        ],
        intensity="Medium",
    ),
    Activity(
        name="Rock Climbing / Bouldering",
        emoji="🧗",
        duration_min=60,
        sessions_per_week=2,
        steps_per_min=20,
        impulse_control_score=10,
        focus_benefit="Problem-solving under physical strain is hyperfocus-inducing for ADHD. Zero space for distraction.",
        tips=[
            "Each 'problem' (route) is a discrete task — perfect for ADHD task-chunking.",
            "The social, supportive gym culture helps accountability.",
            "Progress tracking (V-grades) feeds the ADHD reward system.",
        ],
        intensity="High",
    ),
    Activity(
        name="Jump Rope / HIIT",
        emoji="⏱️",
        duration_min=25,
        sessions_per_week=4,
        steps_per_min=140,
        impulse_control_score=7,
        focus_benefit="Short, intense bursts match ADHD natural energy cycle. Quick dopamine hit without long commitment.",
        tips=[
            "Tabata format (20 s on / 10 s off) is tailor-made for ADHD attention spans.",
            "Can be done anywhere — removes the 'effort to get there' barrier.",
            "Track rounds/reps to satisfy the ADHD number-tracking urge.",
        ],
        intensity="High",
    ),
]


# ─────────────────────────────────────────────
#  STEP CALCULATION ENGINE
# ─────────────────────────────────────────────

def calculate_daily_steps(
    age: int,
    weight_kg: float,
    height_cm: float,
    fitness_level: str,       # sedentary / moderate / active
    has_adhd_hyperactive: bool,
) -> dict:
    """
    Calculate a personalised daily step target.
    Base: WHO recommendation 8,000–10,000 steps/day.
    Adjustments for age, weight, fitness, and ADHD subtype.
    """
    # Base target by fitness level
    base = {"sedentary": 8_000, "moderate": 10_000, "active": 12_000}[fitness_level]

    # Age adjustment (older adults: slightly lower; children/teens: higher)
    if age < 18:
        age_factor = 1.20
    elif age < 30:
        age_factor = 1.10
    elif age < 50:
        age_factor = 1.00
    elif age < 65:
        age_factor = 0.92
    else:
        age_factor = 0.85

    # BMI-based adjustment
    bmi = weight_kg / ((height_cm / 100) ** 2)
    if bmi < 18.5:
        bmi_factor = 0.95
    elif bmi < 25:
        bmi_factor = 1.00
    elif bmi < 30:
        bmi_factor = 1.05   # overweight: benefit from more walking
    else:
        bmi_factor = 1.10   # obese: walking is first-line exercise

    # ADHD hyperactive subtype benefits from extra movement
    adhd_bonus = 1_500 if has_adhd_hyperactive else 500

    daily_steps = int(base * age_factor * bmi_factor) + adhd_bonus

    return {
        "daily_steps": daily_steps,
        "bmi": round(bmi, 1),
        "bmi_category": _bmi_category(bmi),
        "base": base,
        "age_factor": round(age_factor, 2),
        "bmi_factor": round(bmi_factor, 2),
        "adhd_bonus": adhd_bonus,
    }


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def steps_to_distance_km(steps: int, height_cm: float) -> float:
    """Convert steps to distance using stride-length formula."""
    stride_m = height_cm * 0.413 / 100
    return round(steps * stride_m / 1000, 2)


def steps_to_calories(steps: int, weight_kg: float) -> int:
    """Approximate calories burned from steps."""
    # Defense in depth: guard against zero / negative weight even though
    # the input layer clamps to [20, 250].
    if weight_kg <= 0:
        return 0
    # ~0.04 kcal per step per kg body weight / 70 kg reference
    return int(steps * 0.04 * (weight_kg / 70))


# ─────────────────────────────────────────────
#  ACTIVITY RECOMMENDATION ENGINE
# ─────────────────────────────────────────────

def recommend_activities(
    fitness_level: str,
    adhd_subtype: str,          # hyperactive / inattentive / combined
    available_days: int,
    preferences: list[str],     # e.g. ["outdoor", "solo", "team"]
    time_per_session_max: int,  # max minutes per session
) -> list[Activity]:
    """
    Select and rank activities based on user profile.
    Prioritises high impulse-control-score activities for ADHD.
    """
    pool = ACTIVITY_POOL.copy()

    # Filter by max session time
    pool = [a for a in pool if a.duration_min <= time_per_session_max]

    # For hyperactive subtype, prefer high-intensity
    if adhd_subtype == "hyperactive":
        pool.sort(key=lambda a: (a.impulse_control_score, a.intensity == "High"), reverse=True)
    elif adhd_subtype == "inattentive":
        # Prefer activities with clear structure/goals
        preferred = ["Martial Arts / Boxing", "Rock Climbing / Bouldering", "Gym / Strength Training"]
        pool.sort(key=lambda a: (a.name in preferred, a.impulse_control_score), reverse=True)
    else:  # combined
        pool.sort(key=lambda a: a.impulse_control_score, reverse=True)

    # Pick top activities fitting the available days
    chosen: list[Activity] = []
    total_sessions = 0
    for activity in pool:
        if total_sessions + activity.sessions_per_week <= available_days:
            chosen.append(activity)
            total_sessions += activity.sessions_per_week
        if total_sessions >= available_days:
            break

    return chosen


# ─────────────────────────────────────────────
#  WEEKLY SCHEDULE BUILDER
# ─────────────────────────────────────────────

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def build_weekly_schedule(activities: list[Activity], available_days: int) -> dict[str, Optional[Activity]]:
    """Spread recommended activities across the week, inserting rest days.

    Uses interleaving to avoid two consecutive High-intensity days
    whenever the pool allows it (i.e. count(High) <= count(non-High) + 1).
    If the pool is dominated by High activities, falls back gracefully.
    """
    schedule: dict[str, Optional[Activity]] = {d: None for d in DAYS}
    active_days = DAYS[:max(0, min(available_days, len(DAYS)))]

    sessions: list[Activity] = []
    for act in activities:
        sessions.extend([act] * act.sessions_per_week)
    random.shuffle(sessions)

    # Split by intensity, interleave High with non-High as much as possible.
    highs = [s for s in sessions if s.intensity == "High"]
    others = [s for s in sessions if s.intensity != "High"]

    placed: list[Activity] = []
    # Leading toggle: if we have more highs, start with a high.
    take_high = len(highs) >= len(others)
    while (highs or others) and len(placed) < len(active_days):
        if take_high and highs:
            placed.append(highs.pop(0))
        elif not take_high and others:
            placed.append(others.pop(0))
        elif highs:
            placed.append(highs.pop(0))
        elif others:
            placed.append(others.pop(0))
        take_high = not take_high

    for day, session in zip(active_days, placed):
        schedule[day] = session

    return schedule


# ─────────────────────────────────────────────
#  PRETTY PRINTER
# ─────────────────────────────────────────────

# Only emit ANSI color codes when stdout is a real terminal; otherwise
# (e.g. when redirected to a file or piped) strip them to avoid garbage.
_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

def _c(code: str) -> str:
    return code if _USE_COLOR else ""

CYAN    = _c("\033[96m")
GREEN   = _c("\033[92m")
YELLOW  = _c("\033[93m")
MAGENTA = _c("\033[95m")
BLUE    = _c("\033[94m")
RED     = _c("\033[91m")
BOLD    = _c("\033[1m")
DIM     = _c("\033[2m")
RESET   = _c("\033[0m")

INTENSITY_COLOR = {"Low": GREEN, "Medium": YELLOW, "High": RED}

def banner():
    print(f"""
{CYAN}{BOLD}
 ╔══════════════════════════════════════════════════════════╗
 ║       🧠  ADHD  ACTIVITY  &  STEP  PLANNER  🏃          ║
 ║   Science-backed movement plans for impulse control      ║
 ╚══════════════════════════════════════════════════════════╝
{RESET}""")


def section(title: str):
    print(f"\n{BOLD}{BLUE}{'─'*60}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'─'*60}{RESET}")


def print_step_summary(result: dict, height_cm: float, weight_kg: float):
    steps = result["daily_steps"]
    dist  = steps_to_distance_km(steps, height_cm)
    cals  = steps_to_calories(steps, weight_kg)

    section("📊 YOUR DAILY STEP TARGET")
    print(f"""
  {BOLD}Target Steps   :{RESET} {GREEN}{BOLD}{steps:,}{RESET}  steps / day
  {BOLD}≈ Distance     :{RESET} {dist} km
  {BOLD}≈ Calories     :{RESET} {cals} kcal
  {BOLD}BMI            :{RESET} {result['bmi']}  ({result['bmi_category']})
  {BOLD}ADHD Bonus     :{RESET} +{result['adhd_bonus']:,} steps added for impulse regulation

  {DIM}Tip: split your steps — morning walk + evening activity is
  better for ADHD regulation than one long session.{RESET}
""")


def print_activities(activities: list[Activity]):
    section("🏆 RECOMMENDED ACTIVITIES FOR YOU")
    for rank, a in enumerate(activities, 1):
        intensity_str = f"{INTENSITY_COLOR[a.intensity]}{a.intensity}{RESET}"
        bar = "█" * a.impulse_control_score + "░" * (10 - a.impulse_control_score)
        print(f"""
  {BOLD}{rank}. {a.emoji}  {a.name}{RESET}
     Intensity    : {intensity_str}
     Duration     : {YELLOW}{a.duration_min} min/session{RESET}  ×  {a.sessions_per_week}×/week
     Impulse Score: {MAGENTA}{bar}{RESET}  {a.impulse_control_score}/10
     Brain Benefit: {DIM}{a.focus_benefit}{RESET}
     💡 Tips:""")
        for tip in a.tips:
            print(f"        • {tip}")


def print_schedule(schedule: dict[str, Optional[Activity]]):
    section("🗓️  YOUR WEEKLY SCHEDULE")
    for day, activity in schedule.items():
        if activity:
            ic  = INTENSITY_COLOR[activity.intensity]
            tag = f"{ic}[{activity.intensity}]{RESET}"
            print(f"  {BOLD}{day:<12}{RESET}  {activity.emoji}  {activity.name:<32} {tag}  {YELLOW}{activity.duration_min} min{RESET}")
        else:
            print(f"  {BOLD}{day:<12}{RESET}  {DIM}🛌  Rest / Light stretching{RESET}")


def print_adhd_science_note():
    section("🔬 WHY EXERCISE HELPS ADHD IMPULSE CONTROL")
    print(f"""
  {DIM}Exercise increases dopamine and norepinephrine — the same
  neurotransmitters targeted by ADHD medications (e.g. Ritalin,
  Adderall). A 30-min aerobic session can improve executive
  function and impulse inhibition for up to 2–4 hours afterwards.

  Key mechanisms:
    • ↑ Prefrontal cortex activation  → better 'braking' of impulses
    • ↑ BDNF (brain-derived neurotrophic factor) → neural plasticity
    • ↑ Dopamine receptor sensitivity  → sustained motivation
    • ↓ Cortisol & baseline hyperarousal → emotional regulation

  Research note: High-intensity interval training (HIIT) and
  martial arts show the strongest effect sizes for impulse
  control in ADHD populations.  (Pontifex et al., 2013;
  Hoza et al., 2015; John Ratey, "Spark", 2008){RESET}
""")


# ─────────────────────────────────────────────
#  INPUT HELPERS
# ─────────────────────────────────────────────

def _safe_input(prompt: str) -> str:
    """input() wrapper that turns EOF / Ctrl-D into a clean exit."""
    try:
        return input(prompt)
    except EOFError:
        print(f"\n\n  {DIM}Input stream closed. Goodbye!{RESET}")
        sys.exit(0)


def ask_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        try:
            val = int(_safe_input(f"  {CYAN}{prompt}{RESET} "))
            if lo <= val <= hi:
                return val
            print(f"  {RED}Please enter a value between {lo} and {hi}.{RESET}")
        except ValueError:
            print(f"  {RED}Invalid input — enter a whole number.{RESET}")


def ask_float(prompt: str, lo: float, hi: float) -> float:
    while True:
        try:
            val = float(_safe_input(f"  {CYAN}{prompt}{RESET} "))
            if lo <= val <= hi:
                return val
            print(f"  {RED}Please enter a value between {lo} and {hi}.{RESET}")
        except ValueError:
            print(f"  {RED}Invalid input — enter a number.{RESET}")


def ask_choice(prompt: str, options: list[str]) -> str:
    """Ask the user to pick one of *options*.

    Accepts either the 1-based index or an unambiguous case-insensitive
    prefix of the option name. Empty input is rejected (previous
    implementation silently returned the first option for empty input
    because `"" == ""[:0]` is True).
    """
    opts_str = " / ".join(f"{YELLOW}[{i+1}]{RESET} {o}" for i, o in enumerate(options))
    while True:
        print(f"  {CYAN}{prompt}{RESET}")
        print(f"      {opts_str}")
        raw = _safe_input("  → ").strip()

        if not raw:
            print(f"  {RED}Please enter a choice.{RESET}")
            continue

        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]

        raw_low = raw.lower()
        matches = [o for o in options if o.lower().startswith(raw_low)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            joined = ", ".join(matches)
            print(f"  {RED}Ambiguous — matches: {joined}. Be more specific.{RESET}")
            continue
        print(f"  {RED}Invalid choice. Enter a number or the option name.{RESET}")


def ask_yes_no(prompt: str) -> bool:
    while True:
        raw = _safe_input(f"  {CYAN}{prompt} (y/n){RESET} ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print(f"  {RED}Enter y or n.{RESET}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def show_disclaimer_and_require_acceptance() -> None:
    """Print the medical disclaimer and require explicit user acceptance."""
    section("⚠️  IMPORTANT — READ BEFORE CONTINUING")
    print(f"""
  {BOLD}This tool is for EDUCATIONAL and INFORMATIONAL purposes only.{RESET}

  It is {BOLD}NOT{RESET} a medical device and does {BOLD}NOT{RESET} replace advice from
  a physician, psychiatrist, dietitian or certified professional.

  Do not use this tool as a substitute for diagnosis or treatment.
  Consult a healthcare provider before starting any exercise plan,
  especially if you have cardiovascular, respiratory, musculoskeletal
  or psychiatric conditions.

  Full terms: see {BOLD}TERMS_AND_CONDITIONS.md{RESET} in the repository root.
""")
    if not ask_yes_no("Do you understand and accept these terms?"):
        print(f"\n  {YELLOW}You must accept the terms to use this tool. Exiting.{RESET}\n")
        sys.exit(0)


def main():
    banner()
    show_disclaimer_and_require_acceptance()

    print(f"  {BOLD}Welcome! Answer a few questions and I'll build your personalised{RESET}")
    print(f"  {BOLD}ADHD activity plan with daily step targets.{RESET}\n")

    # ── Personal details ──────────────────────────────────────────
    section("👤 PERSONAL DETAILS")
    age        = ask_int("Your age (years):", 8, 90)
    weight_kg  = ask_float("Your weight (kg):", 20, 250)
    height_cm  = ask_float("Your height (cm):", 100, 230)

    # ── ADHD profile ──────────────────────────────────────────────
    section("🧠 ADHD PROFILE")
    adhd_subtype = ask_choice(
        "Your ADHD subtype:",
        ["hyperactive", "inattentive", "combined"],
    )
    has_hyperactive = adhd_subtype in ("hyperactive", "combined")

    # ── Fitness & availability ────────────────────────────────────
    section("💪 FITNESS & AVAILABILITY")
    fitness_level = ask_choice(
        "Current fitness level:",
        ["sedentary", "moderate", "active"],
    )
    available_days = ask_int("Days per week available for exercise (1–7):", 1, 7)
    max_minutes    = ask_int("Maximum minutes per session (15–120):", 15, 120)

    # ── Compute results ───────────────────────────────────────────
    step_result  = calculate_daily_steps(age, weight_kg, height_cm, fitness_level, has_hyperactive)
    activities   = recommend_activities(
        fitness_level=fitness_level,
        adhd_subtype=adhd_subtype,
        available_days=available_days,
        preferences=[],
        time_per_session_max=max_minutes,
    )
    schedule = build_weekly_schedule(activities, available_days)

    # ── Display results ───────────────────────────────────────────
    print_step_summary(step_result, height_cm, weight_kg)
    print_activities(activities)
    print_schedule(schedule)
    print_adhd_science_note()

    # ── Daily step breakdown ──────────────────────────────────────
    section("🔢 DAILY STEP BREAKDOWN SUGGESTION")
    daily = step_result["daily_steps"]
    morning   = int(daily * 0.35)
    midday    = int(daily * 0.25)
    afternoon = int(daily * 0.25)
    evening   = daily - morning - midday - afternoon
    print(f"""
  Split your {GREEN}{BOLD}{daily:,}{RESET} steps across the day:

    🌅  Morning  (walk / commute)   {YELLOW}{morning:,}{RESET} steps  (~{morning//100} min)
    ☀️   Midday   (lunch walk)       {YELLOW}{midday:,}{RESET} steps  (~{midday//100} min)
    🌤️   Afternoon (activity block)  {YELLOW}{afternoon:,}{RESET} steps  (~{afternoon//100} min)
    🌙  Evening  (wind-down walk)   {YELLOW}{evening:,}{RESET} steps  (~{evening//100} min)
""")

    print(f"\n{GREEN}{BOLD}  ✅  Plan generated! Consistency beats perfection — start today.{RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Session cancelled. Goodbye!{RESET}\n")
        sys.exit(0)
