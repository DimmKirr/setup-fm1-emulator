#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Kerem Kilic (Ellic Studio)
"""E2E tests for Felucca firmware in fm1-emu WASM emulator.

Felucca UI: long-press button 7 opens settings menu, encoder 3 navigates
menu items, button X selects, button Z goes back.
"""
import unittest

from examples.base import FirmwareTestBase


class FeluccaTest(FirmwareTestBase):
    FIRMWARE = 'felucca'

    def test_01_boot_and_screenshot(self):
        page = self._get_page()
        self._screenshot('home')
        status = page.text_content('#status')
        self.assertIn('instructions/s', status)

    def test_02_navigate_to_about(self):
        page = self._get_page()

        # Long-press 7 to open settings menu
        self._long_push(page, '7', hold_ms=900)
        self._screenshot('settings-menu')

        # Encoder 3: scroll down to About
        self._send_enc(page, 3, 19, delay_ms=500)
        self._screenshot('settings-about-selected')

        # Press X to enter About screen
        self._push(page, 'x', delay_ms=800)
        self._screenshot('about')

        # Scroll down in About
        self._send_enc(page, 6, 3, delay_ms=400)
        self._screenshot('about-scrolled')

        # Back out
        self._push(page, 'z', delay_ms=300)
        self._long_push(page, '7', hold_ms=900)

    def test_03_write_log(self):
        self._write_log()


if __name__ == '__main__':
    unittest.main()
