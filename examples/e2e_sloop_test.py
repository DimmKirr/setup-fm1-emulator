#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Kerem Kilic (Ellic Studio)
"""E2E tests for Sloop XOX firmware in fm1-emu WASM emulator.

Sloop UI: button 8 opens menu, encoder 1 navigates, button X selects,
button Z goes back.
"""
import unittest

from examples.base import FirmwareTestBase


class SloopTest(FirmwareTestBase):
    FIRMWARE = 'sloop'

    def test_01_boot_and_screenshot(self):
        page = self._get_page()
        self._screenshot('home')
        status = page.text_content('#status')
        self.assertIn('instructions/s', status)

    def test_02_navigate_to_about(self):
        page = self._get_page()

        # Button 8 opens menu on Sloop
        self._long_push(page, '8', hold_ms=900)
        self._screenshot('menu')

        # Encoder 1: scroll to About
        self._send_enc(page, 1, 12, delay_ms=500)
        self._screenshot('about-selected')

        # Select
        self._push(page, 'x', delay_ms=800)
        self._screenshot('about')

        # Back out
        self._push(page, 'z', delay_ms=300)

    def test_03_write_log(self):
        self._write_log()


if __name__ == '__main__':
    unittest.main()
