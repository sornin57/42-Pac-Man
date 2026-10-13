install:
	uv sync

run:
	uv run python3 pac-man.py config/default.json

debug:
	uv run python3 -m pdb pac-man.py config/default.json

demo-ghost:
	uv run python3 tools/ghost_demo.py

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache .venv

lint:
	uv run flake8 src tests tools pac-man.py
	uv run mypy src tests tools pac-man.py --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 src tests tools pac-man.py
	uv run mypy src tests tools pac-man.py --strict

test:
	uv run pytest

check: lint test
