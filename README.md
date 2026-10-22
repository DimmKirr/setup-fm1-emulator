# setup-fm1-emulator

GitHub Action that sets up the [fm1-emu](https://github.com/joakimeriksson/fm1-emu) synthesizer emulator for E2E firmware UI testing in CI. No hardware needed.

[![CI](https://img.shields.io/github/actions/workflow/status/DimmKirr/setup-fm1-emulator/release.yml?branch=main&label=CI)](https://github.com/DimmKirr/setup-fm1-emulator/actions)
[![License](https://img.shields.io/github/license/DimmKirr/setup-fm1-emulator)](LICENSE)

<p align="center">
  <img src="https://github.com/DimmKirr/setup-fm1-emulator/releases/download/release-screenshots/felucca-play-note.gif" alt="Playing notes on the FM-1 emulator" width="680">
</p>

Test your FM-1 firmware UI in CI: rotate encoders, press buttons, play notes, capture screenshots, and record GIFs. All through Playwright against a WASM emulator, no hardware required.

## Usage

```yaml
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: '3.12'

      - uses: dimmkirr/setup-fm1-emulator@v1

      - run: fm1-emu --help
```

Pin a specific emulator version:

```yaml
- uses: dimmkirr/setup-fm1-emulator@v1
  with:
    version: v0.2.0
```

### Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `version` | fm1-emu release tag (e.g. `v0.2.0`) | baked into action release |
| `github-token` | GitHub token for downloading release assets | `${{ github.token }}` |
| `install-playwright` | Install Playwright, Chromium, and ffmpeg | `true` |

By default the emulator version baked into the action release is used. Override with `version` to pin a specific upstream release.

### Outputs

| Output | Description |
|--------|-------------|
| `version` | Installed fm1-emu version |
| `bin-path` | Absolute path to the fm1-emu binary |
| `web-path` | Path to the WASM emulator directory |
| `cache-hit` | Whether restored from cache |
| `chromium-path` | Path to Playwright Chromium (empty if `install-playwright` is `false`) |

## fm1_playwright package

The repo includes `fm1_playwright`, a reusable Playwright test harness for driving the FM-1 emulator. Install it directly from GitHub:

```bash
pip install git+https://github.com/DimmKirr/setup-fm1-emulator.git
```

Or pin a version:

```bash
pip install git+https://github.com/DimmKirr/setup-fm1-emulator.git@v1
```

Then subclass `FirmwareUITest` in your tests:

```python
from fm1_playwright import FirmwareUITest

class MyFirmwareTest(FirmwareUITest):
    def test_boot(self):
        self._get_page()
        self._screenshot('home')
```

### View modes

Set `FM1_VIEW` to control what gets captured in screenshots and GIFs:

| Value | Captures | Size |
|-------|----------|------|
| `DEVICE` (default) | Full device canvas (panel + buttons + keys) | Variable |
| `SCREEN` | LCD screen only (`#lcdcopy`) | 240x240 |

```bash
FM1_VIEW=SCREEN python3 -m unittest my_tests -v
```

## E2E Testing

See [`examples/`](https://github.com/DimmKirr/setup-fm1-emulator/tree/main/examples) for E2E test examples (both DEVICE and SCREEN modes) and [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for a full working workflow with screenshot uploads and GIF recording.

<details>
<summary>Matrix workflow example</summary>

```yaml
jobs:
  e2e:
    runs-on: ubuntu-24.04
    strategy:
      matrix:
        include:
          - firmware: felucca
            url: https://thefirmwarehub.com/fw/felucca-1.6.1.fwsc
          - firmware: sloop
            url: https://thefirmwarehub.com/fw/sloop-2.6.fwsc
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: '3.12'
      - uses: dimmkirr/setup-fm1-emulator@v1
        id: emu
      - env:
          FM1_WEB_DIR: ${{ steps.emu.outputs.web-path }}
          FIRMWARE_NAME: ${{ matrix.firmware }}
          FIRMWARE_URL: ${{ matrix.url }}
        run: python3 -m unittest examples.e2e_firmware_ui_test -v
```

</details>

## Emulator Control

Programmatic control of the emulator via Playwright:

- `rotate_encoder(name, direction, steps)`: rotate any encoder (select, k1, k2, presets, algorithm, master, knob1-4)
- `press_button(name)`: press a button (home, scl, env, lfo, edit, fx, etc.)
- `play_note(note, hold_ms)`: play a note on the music keyboard (C4..F5)
- `hold_button(name)`: context manager for holding a button while performing other actions
- `record_gif(name)`: record canvas frames into an animated GIF
- Canvas-only screenshots (device view, not full page)

```python
# Change preset
self.rotate_encoder('k2', direction=1, steps=1)

# Play a C# minor chord
self.play_note('C#4', hold_ms=500)
self.play_note('E4', hold_ms=500)
self.play_note('G#4', hold_ms=500)

# Hold EDIT while rotating K1
with self.hold_button('edit'):
    self.rotate_encoder('k1', direction=1, steps=3)

# Record a GIF of preset scrolling
with self.record_gif('preset-scroll') as snap:
    for _ in range(4):
        snap()
        self.rotate_encoder('k2', direction=1, steps=1, delay_ms=600)
```

<details>
<summary>More screenshots</summary>

| Firmware | Home screen |
|----------|-------------|
| felucca | ![felucca home](https://github.com/DimmKirr/setup-fm1-emulator/releases/download/release-screenshots/felucca-home.png) |
| sloop | ![sloop home](https://github.com/DimmKirr/setup-fm1-emulator/releases/download/release-screenshots/sloop-home.png) |
| melodee | ![melodee home](https://github.com/DimmKirr/setup-fm1-emulator/releases/download/release-screenshots/melodee-home.png) |

</details>

## Local usage (Taskfile)

The included `Taskfile.yml` is a local equivalent of the GitHub Action. Import it into your project:

```yaml
# Taskfile.yml (your project)
version: '3'

includes:
  fm1-emulator:
    taskfile: https://raw.githubusercontent.com/DimmKirr/setup-fm1-emulator/v1/Taskfile.yml

tasks:
  test:
    deps: [fm1-emulator:download]
    env:
      FM1_WEB_DIR: '{{.HOME}}/.fm1-emulator/web'
    cmds:
      - python3 -m unittest my_tests.e2e_test -v
```

Commands:

| Command | Description |
|---------|-------------|
| `task fm1-emulator:download` | Download fm1-emu binary, WASM emulator, and Playwright |
| `task fm1-emulator:download:fm1-emu` | Native binary only |
| `task fm1-emulator:download:wasm` | WASM emulator only |
| `task fm1-emulator:download:playwright` | Playwright + Chromium + ffmpeg only |
| `task fm1-emulator:remove` | Remove `~/.fm1-emulator`, results, and Playwright |

Installs to `~/.fm1-emulator/` (same location as the GitHub Action). Downloads the pre-built WASM from the vendor-sync mirror first, falls back to building from source if the mirror release doesn't exist.

## Credits

This action wraps [fm1-emu](https://github.com/joakimeriksson/fm1-emu), the FM1 synthesizer emulator created by [Joakim Eriksson](https://github.com/joakimeriksson). The WASM browser emulator is built from the upstream source and redistributed as a release asset.

## License

[MIT](LICENSE)
