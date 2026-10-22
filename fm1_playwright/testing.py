# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Dmitry Kireev
"""Base test case for driving FM-1 firmware in the WASM emulator via Playwright."""

import contextlib
import http.server
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from fm1_playwright.mappings import (
    BOOT_PATTERN,
    _BUTTON_KEYS,
    _ENC_KEYS,
    _KNOB_POSITIONS,
    _NOTE_KEYS,
)

FM1_WEB_DIR = Path(os.environ.get('FM1_WEB_DIR', os.environ.get('FM1_EMU_SOURCE', '')))
FIRMWARE_NAME = os.environ.get('FIRMWARE_NAME', '')
FIRMWARE_URL = os.environ.get('FIRMWARE_URL', '')
RESULTS_DIR = Path(os.environ.get('RESULTS_DIR', 'results'))
CHROMIUM_PATH = os.environ.get('CHROMIUM_PATH')
VIEW_MODE = os.environ.get('FM1_VIEW', 'DEVICE').upper()  # DEVICE | SCREEN


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


class FirmwareUITest(unittest.TestCase):
    """Base class for E2E firmware tests running in the fm1-emu WASM emulator.

    Subclass this and write test methods using rotate_encoder(), press_button(),
    play_note(), hold_button(), record_gif(), and _screenshot().
    """

    _server = None
    _thread = None
    _pw = None
    _browser = None
    _page = None
    emu_url = None
    _screenshot_dir = None

    @classmethod
    def setUpClass(cls):
        web_dir = FM1_WEB_DIR
        if not (web_dir / 'fm1_web.wasm').is_file():
            raise unittest.SkipTest(
                f'fm1_web.wasm not found in {web_dir} (set FM1_WEB_DIR)')
        if not FIRMWARE_NAME:
            raise unittest.SkipTest('FIRMWARE_NAME not set')

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
            f'http://127.0.0.1:{port}/?fw={FIRMWARE_NAME}&mhz=100&debug=1')

        cls._pw = sync_playwright().start()
        launch_kwargs = dict(
            headless=True,
            args=['--autoplay-policy=no-user-gesture-required'],
        )
        if CHROMIUM_PATH and os.path.isfile(CHROMIUM_PATH):
            launch_kwargs['executable_path'] = CHROMIUM_PATH
        cls._browser = cls._pw.chromium.launch(**launch_kwargs)

        cls._screenshot_dir = RESULTS_DIR / FIRMWARE_NAME / 'screenshots'
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
                print(f'\n=== Boot failed for {FIRMWARE_NAME}. '
                      f'#status: {status}', flush=True)
                for msg in page._console_logs[-20:]:
                    print(f'  {msg}', flush=True)
                raise
            page.wait_for_timeout(2000)
            self.__class__._page = page
        return self.__class__._page

    def _get_screenshot_target(self):
        page = self._get_page()
        if VIEW_MODE == 'SCREEN':
            lcd = page.query_selector('#lcdcopy')
            if lcd:
                page.evaluate('''() => {
                    const c = document.getElementById("lcdcopy");
                    if (c) c.style.display = "block";
                }''')
                return lcd
        canvas = page.query_selector('canvas#panel')
        return canvas or page.query_selector('canvas') or page

    def _screenshot(self, name):
        path = self._screenshot_dir / f'{FIRMWARE_NAME}-{name}.png'
        target = self._get_screenshot_target()
        target.screenshot(path=str(path))
        return path

    def _capture_frame(self, frames_dir, index):
        target = self._get_screenshot_target()
        path = os.path.join(frames_dir, f'frame-{index:04d}.png')
        target.screenshot(path=path)
        return path

    @contextlib.contextmanager
    def record_gif(self, name, fps=4):
        """Record canvas frames during a block, then stitch into a GIF.

        Usage:
            with self.record_gif('preset-scroll') as snap:
                for _ in range(5):
                    snap()
                    self.rotate_encoder('k2', direction=1, steps=1, delay_ms=400)
        """
        frames_dir = tempfile.mkdtemp(prefix='fm1-gif-')
        frames = []

        def snap():
            path = self._capture_frame(frames_dir, len(frames))
            frames.append(path)

        yield snap
        snap()

        gif_path = self._screenshot_dir / f'{FIRMWARE_NAME}-{name}.gif'
        if len(frames) >= 2 and shutil.which('ffmpeg'):
            subprocess.run([
                'ffmpeg', '-y',
                '-framerate', str(fps),
                '-i', os.path.join(frames_dir, 'frame-%04d.png'),
                '-vf', 'split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
                str(gif_path),
            ], capture_output=True)
        shutil.rmtree(frames_dir, ignore_errors=True)
        if gif_path.exists():
            print(f'  GIF: {gif_path} ({len(frames)} frames)', flush=True)

    def rotate_encoder(self, name, direction=1, steps=1, delay_ms=300):
        """Rotate a named encoder.

        Args:
            name: encoder name ('select', 'k1', 'k2', 'presets', 'algorithm',
                  'master', 'knob1'..'knob4')
            direction: +1 for clockwise/right, -1 for counter-clockwise/left
            steps: number of clicks
            delay_ms: wait after rotation
        """
        page = self._get_page()
        name = name.lower()

        if name in _ENC_KEYS:
            cw_key, ccw_key = _ENC_KEYS[name]
            key = cw_key if direction > 0 else ccw_key
            for _ in range(steps):
                page.keyboard.press(key)
                page.wait_for_timeout(50)
        elif name in _KNOB_POSITIONS:
            fx, fy = _KNOB_POSITIONS[name]
            delta_y = -40 * direction
            for _ in range(steps):
                page.evaluate(f'''() => {{
                    const c = document.querySelector("canvas");
                    const r = c.getBoundingClientRect();
                    c.dispatchEvent(new WheelEvent("wheel", {{
                        clientX: r.left + r.width * {fx},
                        clientY: r.top + r.height * {fy},
                        deltaY: {delta_y},
                        bubbles: true, cancelable: true
                    }}));
                }}''')
                page.wait_for_timeout(50)
        else:
            raise ValueError(f'Unknown encoder: {name}')

        page.wait_for_timeout(delay_ms)

    def press_button(self, name, delay_ms=300):
        """Press a named button.

        Args:
            name: button name ('fx', 'scl', 'env', 'lfo', 'edit', 'glo',
                  'home', 'save', 'arp', 'seq', 'oct-', 'oct+', 'play', 'rec')
            delay_ms: wait after press
        """
        page = self._get_page()
        key = _BUTTON_KEYS.get(name.lower())
        if key is None:
            raise ValueError(f'Unknown button: {name}')
        page.keyboard.down(key)
        page.wait_for_timeout(80)
        page.keyboard.up(key)
        page.wait_for_timeout(delay_ms)

    def play_note(self, note, hold_ms=300, delay_ms=100):
        """Play a note on the music keyboard.

        Args:
            note: note name like 'C4', 'C#4', 'D4', etc. (C4..F5)
            hold_ms: how long to hold the note
            delay_ms: wait after releasing
        """
        page = self._get_page()
        key = _NOTE_KEYS.get(note.lower())
        if key is None:
            raise ValueError(
                f'Unknown note: {note}. '
                f'Available: {", ".join(n.upper() for n in _NOTE_KEYS)}')
        page.keyboard.down(key)
        page.wait_for_timeout(hold_ms)
        page.keyboard.up(key)
        page.wait_for_timeout(delay_ms)

    @contextlib.contextmanager
    def hold_button(self, name):
        """Hold a button while performing other actions.

        Usage:
            with self.hold_button('edit'):
                self.rotate_encoder('k1', direction=1, steps=3)
        """
        page = self._get_page()
        key = _BUTTON_KEYS.get(name.lower())
        if key is None:
            raise ValueError(f'Unknown button: {name}')
        page.keyboard.down(key)
        page.wait_for_timeout(80)
        try:
            yield
        finally:
            page.keyboard.up(key)
            page.wait_for_timeout(300)
