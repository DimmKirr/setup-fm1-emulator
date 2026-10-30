#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Dmitry Kireev
"""E2E: boot firmware in fm1-emu WASM, screenshot home, change preset."""
import unittest

from unittest import mock

from fm1_playwright import FirmwareUITest
from fm1_playwright.testing import BOOT_PATTERN


class ExampleFirmwareTest(FirmwareUITest):
    """Example tests: boot, screenshot, preset scroll, play notes."""

    def test_01_boot_and_screenshot(self):
        self._get_page()
        self._screenshot('home')
        status = self._get_page().text_content('#status')
        self.assertIn(BOOT_PATTERN, status)

    def test_02_change_preset_and_screenshot(self):
        self.rotate_encoder('k2', direction=1, steps=1, delay_ms=800)
        self._screenshot('preset-next')

    def test_03_preset_scroll_gif(self):
        self.press_button('home', delay_ms=500)
        with self.record_gif('preset-scroll', fps=2) as snap:
            for _ in range(4):
                snap()
                self.rotate_encoder('k2', direction=1, steps=1, delay_ms=600)

    def test_04_play_note_gif(self):
        self.press_button('home', delay_ms=500)
        with self.record_gif('play-note', fps=4) as snap:
            snap()
            self.play_note('C#4', hold_ms=500, delay_ms=200)
            snap()
            self.play_note('E4', hold_ms=500, delay_ms=200)
            snap()
            self.play_note('G#4', hold_ms=500, delay_ms=200)
            snap()

    def test_05_switch_track_and_screenshot(self):
        self.press_button('home', delay_ms=500)
        self.rotate_encoder('select', direction=1, steps=3, delay_ms=800)
        self.press_button('home', delay_ms=500)
        self._screenshot('track4-home')

    def test_06_melody_gif(self):
        """Play 32 notes as an ascending/descending melody, record as GIF."""
        melody = [
            'C4', 'E4', 'G4', 'C5',
            'C4', 'E4', 'G4', 'C5',
            'D4', 'F4', 'A4', 'D5',
            'D4', 'F4', 'A4', 'D5',
            'E4', 'G4', 'B4', 'E5',
            'E4', 'G4', 'B4', 'E5',
            'C4', 'E4', 'G4', 'C5',
            'C4', 'D4', 'E4', 'C4',
        ]
        self.press_button('home', delay_ms=300)
        with self.record_gif('melody-32', fps=6) as snap:
            for note in melody:
                snap()
                self.play_note(note, hold_ms=200, delay_ms=150)


@mock.patch('fm1_playwright.testing.VIEW_MODE', 'SCREEN')
class ScreenModeTest(FirmwareUITest):
    """Same tests rendered in SCREEN mode (LCD-only, 240x240)."""

    def test_01_boot_screenshot_screen(self):
        self._get_page()
        self._screenshot('home-screen')
        status = self._get_page().text_content('#status')
        self.assertIn(BOOT_PATTERN, status)

    def test_02_preset_scroll_gif_screen(self):
        self.press_button('home', delay_ms=500)
        with self.record_gif('preset-scroll-screen', fps=2) as snap:
            for _ in range(4):
                snap()
                self.rotate_encoder('k2', direction=1, steps=1, delay_ms=600)

    def test_03_play_note_gif_screen(self):
        self.press_button('home', delay_ms=500)
        with self.record_gif('play-note-screen', fps=4) as snap:
            snap()
            self.play_note('C#4', hold_ms=500, delay_ms=200)
            snap()
            self.play_note('E4', hold_ms=500, delay_ms=200)
            snap()


if __name__ == '__main__':
    unittest.main()
