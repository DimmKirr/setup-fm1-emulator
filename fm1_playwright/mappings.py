# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Dmitry Kireev
"""FM-1 hardware mappings: encoders, buttons, knobs, and piano keys."""

BOOT_PATTERN = 'instructions/s'

# Encoder keyboard mappings (from main.js ENC_KEYS)
# ArrowLeft/Right = encoder 0 (SELECT), ArrowUp/Down = encoder 1, ,/. = encoder 2 (K2)
_ENC_KEYS = {
    'select':  ('ArrowRight', 'ArrowLeft'),
    'k1':      ('ArrowUp', 'ArrowDown'),
    'k2':      ('.', ','),
}

# Knob positions on the FM-1 canvas (fraction of canvas width/height)
_KNOB_POSITIONS = {
    'master':    (0.08, 0.22),
    'select':    (0.18, 0.22),
    'presets':   (0.08, 0.42),
    'algorithm': (0.18, 0.42),
    'knob1':     (0.52, 0.12),
    'knob2':     (0.60, 0.12),
    'knob3':     (0.68, 0.12),
    'knob4':     (0.76, 0.12),
}

# Button keyboard mappings (from main.js BUTTONS)
_BUTTON_KEYS = {
    'fx': '1', 'scl': '2', 'env': '3', 'lfo': '4', 'edit': '5',
    'glo': '6', 'home': '7', 'save': '8', 'arp': '9', 'seq': '0',
    'oct-': 'z', 'oct+': 'x', 'play': ' ', 'rec': 'r',
}

# Piano keyboard: computer keys mapped to notes (from main.js PIANO = "awsedftgyhujkolp;'")
_NOTE_KEYS = {
    'c4': 'a', 'c#4': 'w', 'd4': 's', 'd#4': 'e', 'e4': 'd',
    'f4': 'f', 'f#4': 't', 'g4': 'g', 'g#4': 'y', 'a4': 'h',
    'a#4': 'u', 'b4': 'j', 'c5': 'k', 'c#5': 'o', 'd5': 'l',
    'd#5': 'p', 'e5': ';', 'f5': "'",
}
