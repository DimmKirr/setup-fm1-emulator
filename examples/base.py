#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright"]
# ///
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Kerem Kilic (Ellic Studio)
"""Shared E2E test infrastructure for fm1-emu firmware testing."""
import http.server
import os
import socket
import threading
import unittest
from pathlib import Path

EMU_SOURCE = Path(os.environ.get('FM1_EMU_SOURCE', ''))
FIRMWARE_NAME = os.environ.get('FIRMWARE_NAME', '')
FIRMWARE_URL = os.environ.get('FIRMWARE_URL', '')
RESULTS_DIR = Path(os.environ.get('RESULTS_DIR', 'results'))
CHROMIUM_PATH = os.environ.get('CHROMIUM_PATH')
BOOT_PATTERN = 'instructions/s'


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def _make_handler(directory):
    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(directory), **kw)
        def end_headers(self):
            self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
            self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
            super().end_headers()
        def log_message(self, fmt, *args):
            pass
    return _Handler


class FirmwareTestBase(unittest.TestCase):
    """Base class: boots firmware in fm1-emu WASM, provides helpers."""

    FIRMWARE: str = ''

    _server = None
    _thread = None
    _pw = None
    _browser = None
    _page = None
    emu_url = None
    _screenshot_dir = None

    @classmethod
    def setUpClass(cls):
        fw = cls.FIRMWARE or FIRMWARE_NAME
        if not fw:
            raise unittest.SkipTest('FIRMWARE_NAME not set')

        web_dir = EMU_SOURCE / 'web'
        if not web_dir.is_dir():
            raise unittest.SkipTest(
                f'FM1_EMU_SOURCE/web not found ({web_dir})')

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            try:
                from patchright.sync_api import sync_playwright
            except ImportError:
                raise unittest.SkipTest('playwright not installed')

        port = _find_free_port()
        cls._server = http.server.HTTPServer(
            ('127.0.0.1', port), _make_handler(web_dir))
        cls._thread = threading.Thread(
            target=cls._server.serve_forever, daemon=True)
        cls._thread.start()
        cls.emu_url = (
            f'http://127.0.0.1:{port}/?fw={fw}&mhz=100&debug=1')

        cls._pw = sync_playwright().start()
        launch_kwargs = dict(
            headless=True,
            args=['--autoplay-policy=no-user-gesture-required'],
        )
        if CHROMIUM_PATH and os.path.isfile(CHROMIUM_PATH):
            launch_kwargs['executable_path'] = CHROMIUM_PATH
        cls._browser = cls._pw.chromium.launch(**launch_kwargs)

        cls._screenshot_dir = RESULTS_DIR / fw / 'screenshots'
        cls._screenshot_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if cls._page:
            try:
                cls._page.close()
            except Exception:
                pass
        if cls._browser:
            cls._browser.close()
        if cls._pw:
            cls._pw.stop()
        if cls._server:
            cls._server.shutdown()

    @classmethod
    def _fw_name(cls):
        return cls.FIRMWARE or FIRMWARE_NAME

    def _get_page(self):
        if self.__class__._page is None:
            page = self._browser.new_page()
            page._console_logs = []
            page.on('console', lambda msg: page._console_logs.append(
                f'[{msg.type}] {msg.text}'))
            page.on('pageerror', lambda err: page._console_logs.append(
                f'[pageerror] {err}'))
            page.goto(self.emu_url)
            page.wait_for_load_state('networkidle', timeout=30_000)

            if FIRMWARE_URL:
                page.evaluate('''(url) => {
                    const sel = document.getElementById("fw");
                    if (sel) {
                        const opt = document.createElement("option");
                        opt.value = url;
                        opt.textContent = "custom";
                        opt.selected = true;
                        sel.appendChild(opt);
                    }
                }''', FIRMWARE_URL)

            page.click('#start')
            try:
                page.wait_for_function(
                    f'() => document.getElementById("status")'
                    f'?.textContent?.includes("{BOOT_PATTERN}")',
                    timeout=90_000)
            except Exception:
                status = page.text_content('#status') or '(empty)'
                print(f'\n=== Boot failed for {self._fw_name()}. '
                      f'#status: {status}', flush=True)
                for msg in page._console_logs[-20:]:
                    print(f'  {msg}', flush=True)
                raise
            page.wait_for_timeout(2000)
            self.__class__._page = page
        return self.__class__._page

    def _screenshot(self, name):
        fw = self._fw_name()
        page = self._get_page()
        path = self._screenshot_dir / f'{fw}-{name}.png'
        page.screenshot(path=str(path))
        return path

    @staticmethod
    def _push(page, key, delay_ms=300):
        page.keyboard.down(key)
        page.wait_for_timeout(80)
        page.keyboard.up(key)
        page.wait_for_timeout(delay_ms)

    @staticmethod
    def _long_push(page, key, hold_ms=900, delay_ms=500):
        page.keyboard.down(key)
        page.wait_for_timeout(hold_ms)
        page.keyboard.up(key)
        page.wait_for_timeout(delay_ms)

    @staticmethod
    def _send_enc(page, enc, clicks, delay_ms=300):
        page.evaluate('''([enc, clicks]) => {
            document.documentElement.dataset.fm1cmd =
                JSON.stringify({op:"send", m:{type:"enc", enc, clicks}});
            window.dispatchEvent(new Event("fm1-cmd"));
        }''', [enc, clicks])
        page.wait_for_timeout(delay_ms)

    def _write_log(self):
        page = self._get_page()
        fw = self._fw_name()
        log_dir = RESULTS_DIR / fw
        log_dir.mkdir(parents=True, exist_ok=True)

        info = page.evaluate('''() => {
            const r = {};
            r.status = document.getElementById('status')?.textContent || '';
            r.title = document.title || '';
            r.fm1log = document.getElementById('fm1log')?.textContent || '';
            return r;
        }''')
        lines = [
            f'firmware: {fw}',
            f'title:    {info["title"]}',
            f'status:   {info["status"]}',
            '',
            f'--- #fm1log ---',
            info.get('fm1log', '(empty)'),
            '',
            f'--- JS console ({len(page._console_logs)} messages) ---',
        ]
        lines.extend(page._console_logs or ['(no console output)'])
        (log_dir / 'emulator.log').write_text('\n'.join(lines) + '\n')
