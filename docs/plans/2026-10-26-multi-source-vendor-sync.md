# Multi-Source Vendor Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Support syncing fm1-emu from both upstream (joakimeriksson/fm1-emu) and fork (DimmKirr/fm1-emu) via a matrix in vendor-sync, and let action/Taskfile consumers choose which source to use.

**Architecture:** Add a matrix to `vendor-sync.yml` so each source repo gets its own WASM prerelease tag (`wasm-{label}-{version}`). Add a `source-repo` input to `action.yml` and `FM1_SOURCE_REPO` var to `Taskfile.yml` that controls both binary download URL and WASM tag prefix. Backward-compatible: defaults to upstream, falls back to old `wasm-{version}` tag format.

**Tech Stack:** GitHub Actions, composite actions, go-task/Taskfile, bash, gh CLI

---

### Task 1: Update vendor-sync.yml with matrix strategy

**Files:**
- Modify: `.github/workflows/vendor-sync.yml`

**Step 1: Add matrix strategy to the sync job**

Replace the single `sync` job definition (line 20-21) with a matrix:

```yaml
jobs:
  sync:
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false
      matrix:
        include:
          - repo: joakimeriksson/fm1-emu
            label: upstream
            bump-pr: true
          - repo: DimmKirr/fm1-emu
            label: dimmkirr
            bump-pr: false
```

**Step 2: Update "Check for new fm1-emu release" step (lines 32-47)**

Replace the hardcoded repo with matrix variable:

```yaml
      - name: Check for new fm1-emu release
        id: upstream
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          LATEST=$(gh release view --repo ${{ matrix.repo }} --json tagName -q .tagName 2>/dev/null || echo "")
          if [ -z "$LATEST" ]; then
            echo "No releases found on ${{ matrix.repo }}"
            echo "new=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          CURRENT="${{ steps.current.outputs.version }}"
          echo "Source: ${{ matrix.repo }} (${{ matrix.label }})"
          echo "Current baked: $CURRENT"
          echo "Latest:  $LATEST"
          echo "latest=$LATEST" >> "$GITHUB_OUTPUT"
          if [ "$LATEST" != "$CURRENT" ] || [ "${{ matrix.bump-pr }}" != "true" ]; then
            echo "new=true" >> "$GITHUB_OUTPUT"
          else
            echo "new=false" >> "$GITHUB_OUTPUT"
          fi
```

Note: for fork (bump-pr: false), always treat as "new" so WASM gets built even if version matches upstream's baked version.

**Step 3: Update WASM tag format in "Check if WASM mirror release exists" step (lines 50-62)**

Replace the tag format:

```yaml
      - name: Check if WASM mirror release exists
        id: wasm-exists
        if: steps.upstream.outputs.new == 'true' || inputs.force
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          TAG="wasm-${{ matrix.label }}-${{ steps.upstream.outputs.latest }}"
          if gh release view "$TAG" --json tagName -q .tagName >/dev/null 2>&1; then
            echo "exists=true" >> "$GITHUB_OUTPUT"
          else
            echo "exists=false" >> "$GITHUB_OUTPUT"
          fi
```

**Step 4: Update "Clone fm1-emu source" step (lines 66-72)**

Use matrix repo:

```yaml
      - name: Clone fm1-emu source
        if: >-
          (steps.upstream.outputs.new == 'true' || inputs.force)
          && steps.wasm-exists.outputs.exists != 'true'
        run: |
          git clone --depth 1 --branch "${{ steps.upstream.outputs.latest }}" \
            https://github.com/${{ matrix.repo }}.git /tmp/fm1-emu-src
```

**Step 5: Update "Publish WASM release" step (lines 108-135)**

Use new tag format with label:

```yaml
      - name: Publish WASM release
        if: >-
          (steps.upstream.outputs.new == 'true' || inputs.force)
          && steps.wasm-exists.outputs.exists != 'true'
        env:
          GH_TOKEN: ${{ github.token }}
          VERSION: ${{ steps.upstream.outputs.latest }}
          LABEL: ${{ matrix.label }}
          SOURCE_REPO: ${{ matrix.repo }}
        run: |
          set -euo pipefail
          RELEASE_TAG="wasm-${LABEL}-${VERSION}"

          gh release create "$RELEASE_TAG" \
            /tmp/fm1-web-dist.tar.gz /tmp/fm1-web-dist.tar.gz.sha256 \
            --repo "${{ github.repository }}" \
            --prerelease \
            --title "WASM ${VERSION} from ${SOURCE_REPO}" \
            --notes "$(cat <<EOF
          **Pre-built WASM emulator for fm1-emu ${VERSION}**

          Built from [${SOURCE_REPO} \`${VERSION}\`](https://github.com/${SOURCE_REPO}/releases/tag/${VERSION}).
          Used by the [setup-fm1-emulator](https://github.com/${{ github.repository }}) GitHub Action.

          **Source:** \`${SOURCE_REPO}\` (label: \`${LABEL}\`)
          **Archive SHA256:** \`$(cut -d' ' -f1 /tmp/fm1-web-dist.tar.gz.sha256)\`

          Contains: \`index.html\`, \`fm1_web.wasm\`, \`fm1_web.js\`, and supporting web assets.
          EOF
          )"
          echo "Published release $RELEASE_TAG"
```

**Step 6: Guard "Create version bump PR" step with matrix condition (lines 161-194)**

Add the matrix condition:

```yaml
      - name: Create version bump PR
        if: steps.upstream.outputs.new == 'true' && matrix.bump-pr == true
        env:
          GH_TOKEN: ${{ github.token }}
          NEW_VERSION: ${{ steps.upstream.outputs.latest }}
          OLD_VERSION: ${{ steps.current.outputs.version }}
        run: |
          # ... rest unchanged ...
```

**Step 7: Verify the workflow YAML is valid**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/vendor-sync.yml'))"`
Expected: no error

**Step 8: Commit**

```bash
git add .github/workflows/vendor-sync.yml
git commit -m "feat(vendor-sync): add matrix for upstream and fork sources

WASM prerelease tags now use wasm-{label}-{version} format
(e.g. wasm-upstream-v0.2.0, wasm-dimmkirr-v0.2.0)."
```

---

### Task 2: Add source-repo input to action.yml

**Files:**
- Modify: `action.yml`

**Step 1: Add the source-repo input (after line 18)**

```yaml
  source-repo:
    description: 'GitHub repo to download fm1-emu from (owner/name)'
    required: false
    default: 'joakimeriksson/fm1-emu'
```

**Step 2: Add label derivation to "Resolve version and platform" step (after line 63)**

Add label derivation at the end of the resolve step:

```bash
        # Derive source label for WASM tag lookup
        SOURCE_REPO="${{ inputs.source-repo }}"
        case "$SOURCE_REPO" in
          joakimeriksson/fm1-emu) LABEL="upstream" ;;
          DimmKirr/fm1-emu)      LABEL="dimmkirr" ;;
          *)                     LABEL=$(echo "$SOURCE_REPO" | cut -d'/' -f1 | tr '[:upper:]' '[:lower:]') ;;
        esac
        echo "label=$LABEL"       >> "$GITHUB_OUTPUT"
        echo "source-repo=$SOURCE_REPO" >> "$GITHUB_OUTPUT"
```

**Step 3: Update binary download URL (line 86)**

Replace the hardcoded URL:

```bash
        URL="https://github.com/${{ inputs.source-repo }}/releases/download/${VERSION}/${ASSET}"
```

**Step 4: Update WASM download step (lines 114-141)**

Replace the WASM tag and clone URL to use source-repo and label, with fallback to old format:

```yaml
    - name: Download or build WASM emulator
      if: steps.cache.outputs.cache-hit != 'true'
      shell: bash
      env:
        GH_TOKEN: ${{ inputs.github-token }}
        VERSION: ${{ steps.resolve.outputs.version }}
        LABEL: ${{ steps.resolve.outputs.label }}
        SOURCE_REPO: ${{ steps.resolve.outputs.source-repo }}
      run: |
        set -euo pipefail
        INSTALL_DIR="$HOME/.fm1-emulator"
        WEB_DIR="$INSTALL_DIR/web"
        mkdir -p "$WEB_DIR"

        if [ -f "$WEB_DIR/fm1_web.wasm" ]; then
          echo "WASM already present at $WEB_DIR/fm1_web.wasm, skipping"
          exit 0
        fi

        ACTION_REPO="${{ github.action_repository }}"
        ACTION_REPO="${ACTION_REPO:-${{ github.repository }}}"

        # Try new format first: wasm-{label}-{version}
        WASM_TAG="wasm-${LABEL}-${VERSION}"
        echo "Trying vendor-sync prerelease: $WASM_TAG"
        DOWNLOADED=false
        gh release download "$WASM_TAG" \
          --repo "$ACTION_REPO" \
          --pattern "fm1-web-dist.tar.gz" \
          --dir /tmp \
          2>/dev/null && DOWNLOADED=true || true

        # Fallback to old format: wasm-{version}
        if [ "$DOWNLOADED" != true ]; then
          WASM_TAG_OLD="wasm-${VERSION}"
          echo "Trying legacy tag: $WASM_TAG_OLD"
          gh release download "$WASM_TAG_OLD" \
            --repo "$ACTION_REPO" \
            --pattern "fm1-web-dist.tar.gz" \
            --dir /tmp \
            2>/dev/null && DOWNLOADED=true || true
        fi

        if [ "$DOWNLOADED" = true ]; then
          tar -xzf /tmp/fm1-web-dist.tar.gz -C "$WEB_DIR"
          rm -f /tmp/fm1-web-dist.tar.gz
          echo "WASM dist downloaded from vendor-sync prerelease ($WASM_TAG)"
        else
          echo "::warning::Pre-built WASM not found, building from source..."
          SOURCE_DIR="$(mktemp -d)"
          git clone --depth 1 --branch "$VERSION" \
            "https://github.com/${SOURCE_REPO}.git" "$SOURCE_DIR"
          rustup target add wasm32-unknown-unknown
          cd "$SOURCE_DIR" && bash web/build.sh
          cp -r "$SOURCE_DIR/web/dist/"* "$WEB_DIR/"
          rm -rf "$SOURCE_DIR"
          echo "WASM built from source (${SOURCE_REPO})"
        fi

        ls "$WEB_DIR/fm1_web.wasm"
```

**Step 5: Update cache key to include source-repo**

Replace line 71:

```yaml
        key: fm1-emulator-v2-${{ inputs.source-repo }}-${{ steps.resolve.outputs.version }}-${{ steps.resolve.outputs.platform }}
```

**Step 6: Verify YAML validity**

Run: `python3 -c "import yaml; yaml.safe_load(open('action.yml'))"`
Expected: no error

**Step 7: Commit**

```bash
git add action.yml
git commit -m "feat(action): add source-repo input for fork support

Defaults to joakimeriksson/fm1-emu. Controls binary download URL,
WASM tag lookup (wasm-{label}-{version}), and source-build fallback.
Falls back to legacy wasm-{version} tag format for backward compat."
```

---

### Task 3: Add FM1_SOURCE_REPO to Taskfile.yml

**Files:**
- Modify: `Taskfile.yml`

**Step 1: Add FM1_SOURCE_REPO var and LABEL derivation (line 5)**

```yaml
vars:
  FM1_VERSION: v0.2.0
  FM1_SOURCE_REPO: '{{default "joakimeriksson/fm1-emu" .FM1_SOURCE_REPO}}'
  FM1_SOURCE_LABEL:
    sh: |
      case "{{.FM1_SOURCE_REPO}}" in
        joakimeriksson/fm1-emu) echo "upstream" ;;
        DimmKirr/fm1-emu)      echo "dimmkirr" ;;
        *)                     echo "{{.FM1_SOURCE_REPO}}" | cut -d'/' -f1 | tr '[:upper:]' '[:lower:]' ;;
      esac
  MIRROR_REPO: dimmkirr/setup-fm1-emulator
  INSTALL_DIR: '{{.HOME}}/.fm1-emulator'
```

**Step 2: Update binary download URL in download:fm1-emu task (line 37-38)**

Replace the curl URL:

```yaml
      - curl -fSL --retry 3 -o /tmp/fm1-emu.tar.gz
          "https://github.com/{{.FM1_SOURCE_REPO}}/releases/download/{{.FM1_VERSION}}/fm1-emu-{{.SEMVER}}-{{.PLATFORM_MAP}}.tar.gz"
```

**Step 3: Update WASM download in download:wasm task (lines 52-78)**

Replace the WASM tag and clone URL with label-based lookup and fallback:

```yaml
      - |
        set -euo pipefail
        WASM_TAG="wasm-{{.FM1_SOURCE_LABEL}}-{{.FM1_VERSION}}"
        WASM_TAG_OLD="wasm-{{.FM1_VERSION}}"

        echo "Trying vendor-sync prerelease: $WASM_TAG..."
        DOWNLOADED=false
        gh release download "$WASM_TAG" \
          --repo "{{.MIRROR_REPO}}" \
          --pattern "fm1-web-dist.tar.gz" \
          --dir /tmp \
          2>/dev/null && DOWNLOADED=true || true

        # Fallback to legacy tag format
        if [ "$DOWNLOADED" != true ]; then
          echo "Trying legacy tag: $WASM_TAG_OLD..."
          gh release download "$WASM_TAG_OLD" \
            --repo "{{.MIRROR_REPO}}" \
            --pattern "fm1-web-dist.tar.gz" \
            --dir /tmp \
            2>/dev/null && DOWNLOADED=true || true
        fi

        if [ "$DOWNLOADED" = true ]; then
          tar -xzf /tmp/fm1-web-dist.tar.gz -C "{{.INSTALL_DIR}}/web"
          rm -f /tmp/fm1-web-dist.tar.gz
          echo "[wasm] Downloaded from vendor-sync prerelease"
        else
          echo "WARNING: Pre-built WASM not found, building from source..."
          SOURCE_DIR="$(mktemp -d)"
          git clone --depth 1 --branch "{{.FM1_VERSION}}" \
            "https://github.com/{{.FM1_SOURCE_REPO}}.git" "$SOURCE_DIR"
          rustup target add wasm32-unknown-unknown
          cd "$SOURCE_DIR" && bash web/build.sh
          cp -r "$SOURCE_DIR/web/dist/"* "{{.INSTALL_DIR}}/web/"
          rm -rf "$SOURCE_DIR"
          echo "[wasm] Built from source ({{.FM1_SOURCE_REPO}})"
        fi
```

**Step 4: Verify Taskfile is valid**

Run: `task --list`
Expected: lists all tasks without errors

**Step 5: Commit**

```bash
git add Taskfile.yml
git commit -m "feat(taskfile): add FM1_SOURCE_REPO for fork support

Override with: task download FM1_SOURCE_REPO=DimmKirr/fm1-emu
Derives WASM tag label automatically. Falls back to legacy tag format."
```

---

### Task 4: Verify end-to-end

**Step 1: Dry-run Taskfile with fork source**

Run: `task --dry download FM1_SOURCE_REPO=DimmKirr/fm1-emu`
Expected: shows commands with `DimmKirr/fm1-emu` in URLs and `wasm-dimmkirr-v0.2.0` tag

**Step 2: Verify action.yml parses correctly**

Run: `python3 -c "import yaml; d=yaml.safe_load(open('action.yml')); print(d['inputs']['source-repo'])"`
Expected: prints the input definition with default `joakimeriksson/fm1-emu`

**Step 3: Verify vendor-sync.yml matrix**

Run: `python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/vendor-sync.yml')); print(d['jobs']['sync']['strategy']['matrix'])"`
Expected: prints matrix with both repos

**Step 4: Commit (if any fixups needed)**

```bash
git add -A
git commit -m "fix: address verification issues from multi-source vendor sync"
```
