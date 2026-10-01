install:
	python3 -m pip install --upgrade pip
	python3 -m pip install flake8 mypy pytest
	python3 -m pip install mazegenerator-2.1.0-py3-none-any.whl

run:
	python3 pac-man.py config/default.json

debug:
	python3 -m pdb pac-man.py config/default.json

demo-ghost:
	PYTHONPATH=src python3 tools/ghost_demo.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

lint:
	flake8 src tests tools pac-man.py
	mypy src tests tools pac-man.py --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 src tests tools pac-man.py
	mypy src tests tools pac-man.py --strict

test:
	PYTHONPATH=src pytest

check: lint test
