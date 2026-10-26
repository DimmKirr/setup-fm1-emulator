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

## E2E Testing with fm1-playwright

For writing E2E tests against the emulator, install the [fm1-playwright](https://github.com/DimmKirr/fm1-playwright) package:

```bash
pip install fm1-playwright
```

Then subclass `FirmwareUITest` in your tests:

```python
from fm1_playwright import FirmwareUITest

class MyFirmwareTest(FirmwareUITest):
    def test_boot(self):
        self._get_page()
        self._screenshot('home')

    def test_change_preset(self):
        self.rotate_encoder('k2', direction=1, steps=1, delay_ms=800)
        self._screenshot('preset-next')
```

See the [fm1-playwright repo](https://github.com/DimmKirr/fm1-playwright) for full API docs, examples, and environment variables.

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
