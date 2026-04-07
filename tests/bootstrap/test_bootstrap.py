from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_root_package_manifest() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert package["private"] is True
    assert package["packageManager"] == "pnpm@9.15.0"
    assert package["workspaces"] == ["apps/*", "packages/*"]


def test_python_tooling_config() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["requires-python"] == ">=3.12"
    assert pyproject["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]


def test_compose_services_present() -> None:
    compose = (ROOT / "infra/compose/docker-compose.yml").read_text(encoding="utf-8")
    for marker in ("postgres:", "valkey:", "minio:", "tika:"):
        assert marker in compose


def test_bootstrap_env_examples_exist() -> None:
    for rel_path in (
        "infra/env/dev.env.example",
        "infra/env/self-host.env.example",
        "infra/env/compose.env.example",
    ):
        assert (ROOT / rel_path).exists()


def test_makefile_contains_expected_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("bootstrap:", "lint:", "test:", "compose-up:", "compose-down:"):
        assert target in makefile


def test_makefile_supports_windows_virtualenv_layout() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "VENV_PYTHON" in makefile
    assert ".venv/bin" in makefile
    assert ".venv/Scripts" in makefile


def test_python_resolution_supports_common_windows_launchers() -> None:
    script = (ROOT / "infra/scripts/resolve-python.sh").read_text(encoding="utf-8")
    assert "--run" in script
    for candidate in ("python3.12", "python3", "python", "py -3.12", "py -3"):
        assert candidate in script
