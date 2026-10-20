# setup-fm1-emulator

GitHub Action for [fm1-emu](https://github.com/joakimeriksson/fm1-emu), the FM1 synthesizer emulator. Downloads the pre-built binary and checks out the source (for web/WASM assets, patching, etc.).

## CI Usage

```yaml
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: dimmkirr/setup-fm1-emulator@v1
      - run: fm1-emu --help
```

Pin to a specific version:

```yaml
- uses: dimmkirr/setup-fm1-emulator@v1
  with:
    version: v0.2.0
```

### Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `version` | fm1-emu release tag | `v0.2.0` |
| `github-token` | GitHub token for downloads | `${{ github.token }}` |

### Outputs

| Output | Description |
|--------|-------------|
| `version` | Installed fm1-emu version |
| `bin-path` | Absolute path to the fm1-emu binary |
| `source-path` | Path to the fm1-emu source checkout |
| `web-path` | Path to the web/ directory (WASM emulator) |
| `cache-hit` | Whether restored from cache |

## How It Works

1. Detects the runner platform (linux-x86_64, linux-arm64, macos-arm64)
2. Downloads the pre-built binary from fm1-emu GitHub Releases
3. Checks out the source at the same tag (for web assets, tools, etc.)
4. Caches everything under `~/.fm1-emulator` via `actions/cache`
5. Adds the binary to `PATH` and exports output paths

## License

MIT
