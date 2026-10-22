# Examples

E2E test examples for the FM-1 emulator using Playwright.

Run any example with:

```bash
FM1_WEB_DIR=$HOME/.fm1-emulator/web \
FIRMWARE_NAME=felucca \
RESULTS_DIR=results \
python3 -m unittest examples.e2e_firmware_ui_test -v
```

## 1. Switch Preset (rotate encoder)

Rotate the K2 encoder to change the active preset:

```python
# Rotate K2 one click clockwise to switch to the next preset
self.rotate_encoder('k2', direction=1, steps=1, delay_ms=800)
self._screenshot('preset-next')
```

Before (home screen on boot):

![felucca home](https://github.com/DimmKirr/setup-fm1-emulator/releases/download/release-screenshots/felucca-home.png)

After (preset changed from ANALOG ACID to FM6 PAD):

![felucca preset next](https://github.com/DimmKirr/setup-fm1-emulator/releases/download/release-screenshots/felucca-preset-next.png)

Available encoders:

| Encoder | Input method | Name |
|---------|-------------|------|
| SELECT | keyboard (ArrowLeft/Right) | `select` |
| K1 | keyboard (ArrowUp/Down) | `k1` |
| K2 | keyboard (. / ,) | `k2` |
| MASTER | mouse wheel on canvas | `master` |
| PRESETS | mouse wheel on canvas | `presets` |
| ALGORITHM | mouse wheel on canvas | `algorithm` |
| KNOB1-4 | mouse wheel on canvas | `knob1`..`knob4` |

## 2. Play Notes

Play notes on the music keyboard (C4 through F5):

```python
# Play a C# minor triad
self.play_note('C#4', hold_ms=500, delay_ms=200)
self.play_note('E4', hold_ms=500, delay_ms=200)
self.play_note('G#4', hold_ms=500, delay_ms=200)
```

![felucca play note](https://github.com/DimmKirr/setup-fm1-emulator/releases/download/release-screenshots/felucca-play-note.gif)

Available notes (mapped to computer keyboard):

| Note | Key | Note | Key |
|------|-----|------|-----|
| C4 | `a` | C5 | `k` |
| C#4 | `w` | C#5 | `o` |
| D4 | `s` | D5 | `l` |
| D#4 | `e` | D#5 | `p` |
| E4 | `d` | E5 | `;` |
| F4 | `f` | F5 | `'` |
| F#4 | `t` | | |
| G4 | `g` | | |
| G#4 | `y` | | |
| A4 | `h` | | |
| A#4 | `u` | | |
| B4 | `j` | | |

## 3. Buttons and Combos

Press buttons and combine with encoder rotation:

```python
# Press the HOME button
self.press_button('home', delay_ms=500)

# Hold EDIT while rotating K1
with self.hold_button('edit'):
    self.rotate_encoder('k1', direction=1, steps=3)
```

Available buttons: `fx`, `scl`, `env`, `lfo`, `edit`, `glo`, `home`, `save`, `arp`, `seq`, `oct-`, `oct+`, `play`, `rec`

## 4. GIF Recording

Record an animated GIF of any interaction:

```python
with self.record_gif('preset-scroll', fps=2) as snap:
    for _ in range(4):
        snap()  # capture frame before each action
        self.rotate_encoder('k2', direction=1, steps=1, delay_ms=600)
```

![felucca preset scroll](https://github.com/DimmKirr/setup-fm1-emulator/releases/download/release-screenshots/felucca-preset-scroll.gif)

Requires `ffmpeg` (installed automatically by the action when `install-playwright: true`).

## Full Test File

See [`e2e_firmware_ui_test.py`](e2e_firmware_ui_test.py) for the complete test suite.
