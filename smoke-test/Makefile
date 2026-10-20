.PHONY: check
check:
	@command -v fm1-emu >/dev/null 2>&1 || { echo "fm1-emu not on PATH"; exit 1; }
	@fm1-emu --help >/dev/null 2>&1 || fm1-emu --version >/dev/null 2>&1 || { echo "fm1-emu not runnable"; exit 1; }
	@test -d "$(FM1_EMU_SOURCE)/web" || { echo "FM1_EMU_SOURCE/web not found"; exit 1; }
	@echo "smoke test: all checks passed"
