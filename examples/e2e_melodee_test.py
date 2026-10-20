#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Kerem Kilic (Ellic Studio)
"""E2E tests for Melodee firmware in fm1-emu WASM emulator.

Melodee UI (Felucca fork): long-press HOME (button 7) opens settings,
K2 (encoder 3) scrolls menu items, button X selects, button Z goes back.
PRESET (encoder 6) scrolls inside the About screen.
"""
import unittest

from examples.base import FirmwareTestBase


class MelodeeTest(FirmwareTestBase):
    FIRMWARE = 'melodee'

    def test_01_boot_and_screenshot(self):
        page = self._get_page()
        self._screenshot('home')
        status = page.text_content('#status')
        self.assertIn('instructions/s', status)
        self.assertIn('melodee', status.lower())

    def test_02_start_button_hidden_after_boot(self):
        page = self._get_page()
        self.assertTrue(
            page.evaluate('() => document.getElementById("start")?.hidden'),
            'Start button should be hidden after boot')

    def test_03_lcd_canvas_renders_after_boot(self):
        page = self._get_page()
        self._screenshot('lcd-after-boot')
        canvas = page.query_selector('canvas')
        self.assertIsNotNone(canvas, 'LCD canvas should exist after boot')

    def test_04_navigate_to_about(self):
        page = self._get_page()

        # Long-press HOME (button 7) to open settings
        self._long_push(page, '7', hold_ms=900)
        self._screenshot('settings-menu')

        # K2 (physical enc 3): 19 clicks to reach About
        self._send_enc(page, 3, 19, delay_ms=500)
        self._screenshot('settings-about-selected')

        # Press X to enter About screen
        self._push(page, 'x', delay_ms=800)
        self._screenshot('about')

        # PRESET (physical enc 6): scroll the About document
        self._send_enc(page, 6, 3, delay_ms=400)
        self._screenshot('about-scrolled')

        # Back out
        self._push(page, 'z', delay_ms=300)
        self._long_push(page, '7', hold_ms=900)

    def test_05_write_log(self):
        self._write_log()


if __name__ == '__main__':
    unittest.main()
