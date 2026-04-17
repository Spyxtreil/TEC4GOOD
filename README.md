# TEC4GOOD

Educational wellness toolkit built as a student project. Three loosely-coupled
modules that share the same ethos: **useful, transparent, and explicitly
non-clinical**.

| Module | What it does | Language |
|--------|--------------|----------|
| `adhd_activity_planner.py` | Interactive CLI that generates a weekly exercise plan and daily step target for people with ADHD, with intensity interleaving and an impulse-control ranking. | Python 3.10+ |
| `nutrition_advisor (1).py` | Interactive CLI that estimates BMR, TDEE, macronutrients and a 5-meal schedule from user inputs (Mifflin-St Jeor). | Python 3.10+ |
| `pulso_simple.ino` / `sensooooor2.ino` | Arduino sketches for a MAX30102 pulse/SpO₂ prototype. The "full" sketch adds a serial-driven calibration routine, portability across Uno/Nano/ESP8266/ESP32, and a watchdog-style boot retry. | Arduino C++ |

> ⚠️ **Not a medical device.** These are educational tools. Read
> [`TERMS_AND_CONDITIONS.md`](TERMS_AND_CONDITIONS.md) before using anything in this repo.

---

## Table of contents

- [Quick start](#quick-start)
- [Repo layout](#repo-layout)
- [The Python tools](#the-python-tools)
- [The Arduino sketches](#the-arduino-sketches)
  - [Wiring](#wiring)
  - [Calibration flow](#calibration-flow)
- [Development](#development)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## Quick start

### Python tools

```bash
# Requires Python 3.10+. No runtime dependencies.
python3 adhd_activity_planner.py
python3 "nutrition_advisor (1).py"
# or, unified entry point:
python3 main.py
```

### Arduino sketch

1. Open the `.ino` file in the Arduino IDE.
2. Install **"SparkFun MAX3010x Pulse and Proximity Sensor Library"** from the Library Manager.
3. Wire the sensor (see [wiring](#wiring)).
4. Flash. Open the Serial Monitor at `115200` baud.
5. Type `?` in the Serial Monitor to see commands. Type `c` to start a 60-second calibration.

---

## Repo layout

```
.
├── adhd_activity_planner.py      # ADHD CLI planner
├── nutrition_advisor (1).py      # Nutrition CLI
├── main.py                       # Unified launcher for both
├── pulso_simple.ino              # Minimal MAX30102 pulse sketch
├── sensooooor2.ino               # Full sketch with calibration, SpO2, watchdog
├── tests/                        # Pytest suite
├── .github/workflows/ci.yml      # Lint + tests on every push
├── pyproject.toml                # ruff + mypy + pytest config
├── requirements.txt              # (empty — stdlib only)
├── requirements-dev.txt          # pytest, ruff, mypy
├── .pre-commit-config.yaml       # pre-commit hooks
├── TERMS_AND_CONDITIONS.md       # Full medical/legal disclaimer
├── SECURITY.md                   # Vulnerability reporting policy
└── LICENSE                       # MIT + safety addendum
```

---

## The Python tools

Both scripts are pure-stdlib Python ≥ 3.10 (they use `dict[str, T]` / `list[T]`
syntax natively). They run fully locally — no network, no file writes, no
telemetry. All inputs are range-validated and EOF (Ctrl-D) and Ctrl-C exit
cleanly.

On first run each script prints a disclaimer and requires explicit acceptance
before continuing. Nutrition flows additionally screen for conditions (diabetes,
kidney disease, heart disease, eating disorders, pregnancy/breastfeeding) and
decline to generate a plan when any of them applies, directing the user to a
professional instead.

### Renaming the nutrition file

The filename `nutrition_advisor (1).py` contains a space and parentheses. Python
can still execute it via `python3 "nutrition_advisor (1).py"` but for cleaner
imports and tests it is loaded by path in `tests/conftest.py`. Renaming it to
`nutrition_advisor.py` is on the to-do list — not done yet because it would
break any existing shell history and expected inputs.

---

## The Arduino sketches

### Wiring

| MAX30102 | Arduino Uno / Nano | ESP8266 (NodeMCU) | ESP32 |
|----------|--------------------|-------------------|-------|
| VIN      | **3.3V**           | 3.3V              | 3.3V  |
| GND      | GND                | GND               | GND   |
| SDA      | **A4**             | **D2** (GPIO4)    | 21    |
| SCL      | **A5**             | **D1** (GPIO5)    | 22    |
| INT/RD/IRD | *(not used)*     | —                 | —     |

> Do **not** connect VIN to 5 V. Many modules tolerate it thanks to an onboard
> regulator, but for the prototype we keep things at 3.3 V.

### Calibration flow

`sensooooor2.ino` supports serial commands once the sketch is running and the
Serial Monitor is open at 115 200 baud:

| Command | Effect |
|---------|--------|
| `c`     | Start calibration (60 s total). Follow on-screen prompts. |
| `r`     | Reset calibration back to factory defaults. |
| `?`     | Print help. |

The calibration routine runs in three steps:

1. **Finger present (30 s)** — average IR reading with a still finger.
2. **Finger absent (15 s)** — average IR reading without a finger.
3. **Optional SpO₂ offset (≤ 30 s)** — if you have a reference pulse oximeter,
   type its reading in the Serial Monitor and the sketch will compute an
   offset for the local SpO₂ formula.

The resulting `finger_threshold` is set to the midpoint between the two IR
averages (bounded to ≥ 20 000 for safety), and `spo2_a` is shifted by the
offset. See `sensooooor2.ino` for the full logic.

> Calibration currently lives in RAM and is lost on reboot. EEPROM persistence
> is on the roadmap.

---

## Development

### Setup

```bash
git clone <this-repo>
cd TEC4GOOD
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install       # optional but recommended
```

### Run tests

```bash
pytest                   # runs everything in tests/
pytest --cov             # with coverage (requires pytest-cov)
```

### Lint and type-check

```bash
ruff check .
ruff format --check .
mypy adhd_activity_planner.py main.py
```

### CI

GitHub Actions runs `ruff` + `pytest` on every push and pull request. See
[`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Contributing

- Open an issue first for anything non-trivial.
- Pull requests must pass `ruff` and `pytest`.
- Every user-facing change must be compatible with the disclaimer in
  `TERMS_AND_CONDITIONS.md`. Do **not** add features that present the
  output as medical advice.
- Security issues: see [`SECURITY.md`](SECURITY.md). Do not open a public
  issue for vulnerabilities.

### Roadmap

- [ ] Rename `nutrition_advisor (1).py` → `nutrition_advisor.py`.
- [ ] EEPROM persistence for the Arduino calibration state.
- [ ] CSV export of serial samples for offline analysis.
- [ ] Optional OLED (SSD1306) output for the sensor.
- [ ] Band-pass filtering of the IR signal before `checkForBeat`.
- [ ] Unify the two Python tools so the planner can ingest resting HR
      measured by the Arduino.

---

## Security

See [`SECURITY.md`](SECURITY.md) for the vulnerability reporting policy and
scope.

## License

[MIT](LICENSE), with an explicit non-medical-device notice.
