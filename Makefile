export UV_CACHE_DIR=./.cache/uv

install:
	uv sync

run:
	uv run python3 pac-man.py config/default.json

debug:
	uv run python3 -m pdb pac-man.py config/default.json

demo-ghost:
	uv run python3 tools/ghost_demo.py

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache .venv build dist

lint:
	uv run flake8 src tests tools pac-man.py
	uv run mypy src tests tools pac-man.py --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 src tests tools pac-man.py
	uv run mypy src tests tools pac-man.py --strict

test:
	uv run pytest

check: lint test

package-mac:
	@test "$$(uname -s)" = Darwin || { echo "package-mac must run on macOS (PyInstaller can't cross-build)."; exit 1; }
	uv run pyinstaller pacman.spec --noconfirm --distpath dist/mac --workpath build/mac
	ditto -c -k --keepParent dist/mac/PacMan.app dist/PacMan-mac.zip
	@echo "Package ready: dist/PacMan-mac.zip"

package-linux:
	@test "$$(uname -s)" = Linux || { echo "package-linux must run on Linux (PyInstaller can't cross-build)."; exit 1; }
	uv run pyinstaller pacman.spec --noconfirm --distpath dist/linux --workpath build/linux
	tar -czf dist/PacMan-linux.tar.gz -C dist/linux PacMan
	@echo "Package ready: dist/PacMan-linux.tar.gz"


MAC_APP = dist/mac/PacMan.app/Contents/MacOS/PacMan
LINUX_APP = dist/linux/PacMan/PacMan

mac-run:
	@test -x $(MAC_APP) || { echo "No macOS package yet: run 'make package-mac' first."; exit 1; }
	$(MAC_APP) config/default.json

linux-run:
	@test -x $(LINUX_APP) || { echo "No Linux package yet: run 'make package-linux' first."; exit 1; }
	$(LINUX_APP) config/default.json

.PHONY: install run debug demo-ghost clean lint lint-strict test check \
	package-mac package-linux mac-run linux-run
