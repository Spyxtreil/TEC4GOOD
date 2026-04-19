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

- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Installing Python](#installing-python)
- [Running the Python tools](#running-the-python-tools)
  - [macOS / Linux](#macos--linux)
  - [Windows](#windows)
- [Compiling and flashing the Arduino sketch](#compiling-and-flashing-the-arduino-sketch)
  - [Installing the Arduino IDE](#installing-the-arduino-ide)
  - [Installing the required library](#installing-the-required-library)
  - [Wiring](#wiring)
  - [Board and port selection](#board-and-port-selection)
  - [Compile and upload](#compile-and-upload)
  - [Serial Monitor](#serial-monitor)
  - [Serial commands](#serial-commands)
  - [Calibration flow](#calibration-flow)
- [Repo layout](#repo-layout)
- [The Python tools](#the-python-tools)
- [Development](#development)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## Requirements

**For the Python tools:**
- Python 3.10 or newer (3.12 recommended).
- Any OS: macOS, Windows 10/11, or Linux.
- No third-party runtime dependencies.

**For the Arduino sketch:**
- Arduino IDE 1.8.19 or 2.x (Windows, macOS, Linux).
- Arduino Uno / Nano / ESP8266 / ESP32 (the sketch auto-detects the platform).
- MAX30102 breakout module.
- 4 jumper wires.
- Micro-USB or USB-B cable (depending on your board).

**For development (tests, lint, CI):**
- `pytest`, `ruff`, `mypy` — installed via `requirements-dev.txt`.

---

## Quick start

**macOS / Linux:**
```bash
python3 main.py
```

**Windows (PowerShell or CMD):**
```powershell
py main.py
```

For the Arduino side, see
[Compiling and flashing the Arduino sketch](#compiling-and-flashing-the-arduino-sketch).

---

## Installing Python

Required: **Python 3.10 or newer**. Check with `python3 --version`
(macOS/Linux) or `py --version` (Windows).

### macOS

```bash
# Option 1: Homebrew (recommended)
brew install python@3.12

# Option 2: installer from python.org
# https://www.python.org/downloads/macos/
```

### Windows

1. Download the installer from <https://www.python.org/downloads/windows/>.
2. Run it. **Check "Add python.exe to PATH"** on the first screen.
3. Click *Install Now*.
4. Open a new PowerShell window and verify:
   ```powershell
   py --version
   ```

### Linux (Debian / Ubuntu)

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 --version
```

---

## Running the Python tools

You have three scripts:

- `main.py` — unified launcher with an interactive menu.
- `adhd_activity_planner.py` — ADHD activity & step planner (standalone).
- `nutrition_advisor (1).py` — nutrition advisor (standalone).

### macOS / Linux

```bash
# clone and enter the repo
git clone https://github.com/Spyxtreil/TEC4GOOD.git
cd TEC4GOOD

# option A — unified launcher (recommended)
python3 main.py

# option B — launch a specific tool directly
python3 main.py adhd
python3 main.py nutrition
python3 main.py terms          # print the T&C and exit

# option C — run a script standalone
python3 adhd_activity_planner.py
python3 "nutrition_advisor (1).py"   # quotes are REQUIRED because of the space
```

### Windows

In **PowerShell**:

```powershell
git clone https://github.com/Spyxtreil/TEC4GOOD.git
cd TEC4GOOD

# unified launcher
py main.py

# specific tool
py main.py adhd
py main.py nutrition

# standalone
py adhd_activity_planner.py
py "nutrition_advisor (1).py"     # quotes REQUIRED
```

In **Command Prompt (cmd.exe)** it's the same — replace `py` with
`python` if `py` is not on your PATH.

> The scripts print a disclaimer on first run and require explicit
> acceptance before continuing. Use Ctrl-C (or Ctrl-D on macOS/Linux,
> Ctrl-Z + Enter on Windows) to exit cleanly at any point.

---

## Compiling and flashing the Arduino sketch

There are two sketches in the repo:

| File | What it is |
|------|------------|
| `pulso_simple.ino` | Minimal: reads BPM only. Good for your first test. |
| `sensooooor2.ino`  | Full version: SpO₂, serial commands, calibration, EEPROM persistence, CSV logging, watchdog. |

The steps are identical for both.

### Installing the Arduino IDE

Download and install version **1.8.19** or **2.x** for your OS:

- <https://www.arduino.cc/en/software>

After first launch:

- **Windows:** the IDE usually ships with drivers. If your Uno is a
  clone with a CH340 chip, install the driver from
  <https://sparks.gogo.co.nz/ch340.html>.
- **macOS:** on first connection the system may warn about a "new
  network interface" and ask for permission in *System Settings →
  Privacy & Security*. Allow it.
- **Linux:** add your user to the `dialout` group so the IDE can
  access the serial port:
  ```bash
  sudo usermod -a -G dialout "$USER"
  # log out and back in for the change to take effect
  ```

### Installing the required library

1. Open the Arduino IDE.
2. Go to **Sketch → Include Library → Manage Libraries…** (IDE 1.8)
   or click the books icon in the left sidebar (IDE 2.x).
3. Search for: **SparkFun MAX3010x Pulse and Proximity Sensor Library**.
4. Click **Install**. Accept any dependency prompts.

### Wiring

| MAX30102 | Arduino Uno / Nano | ESP8266 (NodeMCU) | ESP32 |
|----------|--------------------|-------------------|-------|
| VIN      | **3.3V**           | 3.3V              | 3.3V  |
| GND      | GND                | GND               | GND   |
| SDA      | **A4**             | **D2** (GPIO4)    | 21    |
| SCL      | **A5**             | **D1** (GPIO5)    | 22    |
| INT / RD / IRD | *(not used)* | —                 | —     |

> Do **not** connect VIN to 5 V. Many modules tolerate it thanks to an
> onboard regulator, but for this prototype we keep things at 3.3 V.

**Always wire with the Arduino unplugged from USB.** Plug the USB
cable in only after verifying the connections.

### Board and port selection

1. Connect the Arduino to your computer via USB.
2. In the Arduino IDE, open **Tools → Board** and select your board:
   - `Arduino AVR Boards → Arduino Uno`
   - `Arduino AVR Boards → Arduino Nano` (for Nano clones you may also
     need to choose `Processor → ATmega328P (Old Bootloader)`).
   - ESP8266 / ESP32 require installing their respective cores first
     through **Boards Manager**.
3. Open **Tools → Port** and select the serial port:
   - **Windows:** `COM3`, `COM4`, … (whichever appears when you plug
     in the board).
   - **macOS:** `/dev/cu.usbmodem*` or `/dev/cu.usbserial*`.
   - **Linux:** `/dev/ttyUSB0` or `/dev/ttyACM0`.

### Compile and upload

1. In the Arduino IDE, open **File → Open** and select
   `pulso_simple.ino` (or `sensooooor2.ino`).
2. Click **Verify** (the ✓ button) — this compiles only. You should
   see `Done compiling.` with no errors.
3. Click **Upload** (the → button) — this compiles **and** flashes the
   board. You should see `Done uploading.`.

**Command-line alternative (`arduino-cli`):**

```bash
# compile only
arduino-cli compile --fqbn arduino:avr:uno sensooooor2.ino

# compile + upload (replace <port> with your serial port)
arduino-cli upload -p <port> --fqbn arduino:avr:uno sensooooor2.ino
```

### Serial Monitor

1. Open the Serial Monitor: **Tools → Serial Monitor** (or the
   magnifying-glass icon in the top-right of the IDE).
2. Set the baud rate to **115200** (dropdown at the bottom of the
   Serial Monitor).
3. You should see the disclaimer banner followed by
   `Iniciando MAX30102...` and then `Sensor OK.`.
4. Place your finger lightly on the sensor and watch the readings.

> If nothing appears, the most common causes are: wrong baud rate,
> wrong port, sensor wired to 5 V instead of 3.3 V, or SDA/SCL
> swapped.

### Serial commands

`sensooooor2.ino` reads single-letter commands from the Serial
Monitor at any time:

| Command | Effect |
|---------|--------|
| `c` | Start calibration (~60 s total). Follow on-screen prompts. |
| `s` | Save current calibration to EEPROM (persists across reboots). |
| `l` | Load calibration from EEPROM. |
| `r` | Reset calibration to factory defaults. |
| `g` | Toggle CSV logging mode (`timestamp_ms,ir,red,bpm,spo2`). |
| `?` | Print the help menu. |

### Calibration flow

When you type `c`, the sketch runs a three-step routine:

1. **Finger present (30 s)** — hold a still finger on the sensor.
   Averages the IR reading to learn what "finger present" looks like
   for your particular MAX30102 unit.
2. **Finger absent (15 s)** — remove your finger. Averages the IR
   reading to learn the ambient baseline.
3. **Optional SpO₂ offset (≤ 30 s)** — if you have a reference pulse
   oximeter, type its reading (80–100) in the Serial Monitor and
   press Enter; the sketch will compute an offset and apply it to the
   local formula. Send `0` or press nothing to skip.

The resulting `finger_threshold` is set to the midpoint between the
two IR averages (bounded to ≥ 20 000 for safety), and `spo2_a` is
shifted by the offset.

**Persist the calibration:** after calibrating, send `s` to save to
EEPROM. On next power-up the sketch will auto-load it.

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

### Setup (macOS / Linux)

```bash
git clone https://github.com/Spyxtreil/TEC4GOOD.git
cd TEC4GOOD
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install       # optional but recommended
```

### Setup (Windows — PowerShell)

```powershell
git clone https://github.com/Spyxtreil/TEC4GOOD.git
cd TEC4GOOD
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pre-commit install       # optional
```

> If PowerShell refuses to run `Activate.ps1` with "running scripts is
> disabled on this system", run once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
>
> In **cmd.exe** use `.venv\Scripts\activate.bat` instead.

### Run tests

```bash
pytest                   # runs everything in tests/
pytest --cov             # with coverage (requires pytest-cov)
pytest -v                # verbose output
pytest tests/test_adhd_planner.py::TestWeeklySchedule   # single class
```

### Lint and type-check

```bash
ruff check .
ruff format --check .
ruff format .            # auto-fix formatting
mypy adhd_activity_planner.py main.py
```

### CI

GitHub Actions runs `ruff` + `pytest` on Python 3.10, 3.11 and 3.12 on
every push and pull request. The Arduino sketches are also linted with
`arduino-lint`. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

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
- [x] EEPROM persistence for the Arduino calibration state.
- [x] CSV export of serial samples for offline analysis.
- [ ] Optional OLED (SSD1306) output for the sensor.
- [ ] Band-pass filtering of the IR signal before `checkForBeat`.
- [ ] Unify the two Python tools so the planner can ingest resting HR
      measured by the Arduino.
- [ ] React Native companion app for iOS / Android over BLE.

---

## Security

See [`SECURITY.md`](SECURITY.md) for the vulnerability reporting policy and
scope.

## License

[MIT](LICENSE), with an explicit non-medical-device notice.
