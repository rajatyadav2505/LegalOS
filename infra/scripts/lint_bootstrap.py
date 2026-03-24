#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    required_files = [
        "package.json",
        "pnpm-workspace.yaml",
        "pyproject.toml",
        "Makefile",
        ".pre-commit-config.yaml",
        "infra/compose/docker-compose.yml",
        "infra/env/dev.env.example",
        "infra/env/self-host.env.example",
        "infra/env/compose.env.example",
        ".github/workflows/ci.yml",
    ]

    for rel_path in required_files:
        read_text(ROOT / rel_path)

    package_json = json.loads(read_text(ROOT / "package.json"))
    if package_json.get("private") is not True:
        raise SystemExit("package.json must be private")
    if package_json.get("packageManager", "").split("@", 1)[0] != "pnpm":
        raise SystemExit("package.json must declare pnpm as the package manager")

    pyproject = tomllib.loads(read_text(ROOT / "pyproject.toml"))
    if pyproject.get("project", {}).get("requires-python") != ">=3.12":
        raise SystemExit("pyproject.toml must target Python 3.12+")

    makefile = read_text(ROOT / "Makefile")
    for target in ("bootstrap:", "lint:", "test:", "compose-up:", "compose-down:"):
        if target not in makefile:
            raise SystemExit(f"Makefile missing target {target}")

    compose = read_text(ROOT / "infra/compose/docker-compose.yml")
    for service in ("postgres:", "valkey:", "minio:", "tika:"):
        if service not in compose:
            raise SystemExit(f"compose file missing service {service}")

    print("Bootstrap configuration looks consistent.")


if __name__ == "__main__":
    main()
