"""Shared test fixtures and module loaders.

`nutrition_advisor (1).py` contains a space and parentheses in its filename,
which is not a valid Python identifier. We load it by path via importlib.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(alias: str, filename: str):
    path = ROOT / filename
    spec = importlib.util.spec_from_file_location(alias, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


# Ensure the repo root is on sys.path for `import adhd_activity_planner`.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Pre-load the awkwardly-named nutrition module under a clean alias.
nutrition = _load("nutrition_advisor", "nutrition_advisor (1).py")
