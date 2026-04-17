#!/usr/bin/env python3
"""Unified launcher for the TEC4GOOD Python tools.

Usage:
    python3 main.py              # interactive menu
    python3 main.py adhd         # launch ADHD activity planner
    python3 main.py nutrition    # launch nutrition advisor
    python3 main.py terms        # print the disclaimer and exit
    python3 main.py --help       # this help

This script does not contain business logic of its own; it is a thin
wrapper that dispatches to the two existing scripts. See
TERMS_AND_CONDITIONS.md for the medical disclaimer.
"""
from __future__ import annotations

import argparse
import importlib.util
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _run_adhd() -> None:
    runpy.run_path(str(ROOT / "adhd_activity_planner.py"), run_name="__main__")


def _run_nutrition() -> None:
    # The filename contains a space and parentheses, so we load by path
    # via importlib rather than a plain import statement.
    path = ROOT / "nutrition_advisor (1).py"
    if not path.is_file():
        print(f"Error: {path.name} not found in {ROOT}", file=sys.stderr)
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("nutrition_advisor", path)
    if spec is None or spec.loader is None:
        print("Error: cannot load nutrition advisor module.", file=sys.stderr)
        sys.exit(1)
    module = importlib.util.module_from_spec(spec)
    sys.modules["nutrition_advisor"] = module
    spec.loader.exec_module(module)
    module.main()


def _print_terms() -> None:
    path = ROOT / "TERMS_AND_CONDITIONS.md"
    if not path.is_file():
        print("Error: TERMS_AND_CONDITIONS.md not found.", file=sys.stderr)
        sys.exit(1)
    print(path.read_text(encoding="utf-8"))


def _interactive_menu() -> str:
    print("=" * 60)
    print("  TEC4GOOD — Educational wellness toolkit")
    print("=" * 60)
    print("  [1] ADHD activity & step planner")
    print("  [2] Nutrition advisor")
    print("  [3] Print terms & conditions")
    print("  [q] Quit")
    print("-" * 60)
    while True:
        try:
            choice = input("  Choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"
        if choice in {"1", "adhd"}:
            return "adhd"
        if choice in {"2", "nutrition", "nut"}:
            return "nutrition"
        if choice in {"3", "terms"}:
            return "terms"
        if choice in {"q", "quit", "exit"}:
            return "quit"
        print("  Invalid choice. Type 1, 2, 3 or q.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tec4good",
        description="Unified launcher for the TEC4GOOD Python tools.",
    )
    parser.add_argument(
        "tool",
        nargs="?",
        choices=["adhd", "nutrition", "terms"],
        help="Which tool to launch. If omitted, an interactive menu is shown.",
    )
    args = parser.parse_args(argv)

    tool = args.tool or _interactive_menu()

    try:
        if tool == "adhd":
            _run_adhd()
        elif tool == "nutrition":
            _run_nutrition()
        elif tool == "terms":
            _print_terms()
        elif tool == "quit":
            print("Goodbye.")
    except KeyboardInterrupt:
        print("\n\n  Session cancelled. Goodbye!")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
