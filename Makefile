.PHONY: test build release-patch release-minor release-major release clean

test:
	uv run python -m pytest

build:
	uv build

clean:
	rm -rf dist/ build/ *.egg-info

release-patch:
	uv run python scripts/release.py patch

release-minor:
	uv run python scripts/release.py minor

release-major:
	uv run python scripts/release.py major

release:
	@echo "Usage: make release-patch | release-minor | release-major"
	@echo "  Or:  uv run python scripts/release.py 0.2.0"
