#!/usr/bin/env python3
"""Read the release version from a supported project descriptor.

This intentionally has a small, fixed surface.  Composite action wrappers
choose the mode so reusable workflow callers cannot select arbitrary files or
parsing behaviour.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
import xml.etree.ElementTree as element_tree
from pathlib import Path


MISSING = object()


def validate_version(value: object, source: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Version in {source} must be a string.")
    if not value.strip():
        raise ValueError(f"Version in {source} must not be empty.")
    if "\n" in value or "\r" in value:
        raise ValueError(f"Version in {source} must be a single line.")
    return value





def read_npm_version(root: Path) -> str:
    descriptor = root / "package.json"
    with descriptor.open(encoding="utf-8") as file:
        package = json.load(file)

    version = package.get("version", MISSING) if isinstance(package, dict) else MISSING
    if version is MISSING:
        raise ValueError("Missing expected field package.json .version.")
    return validate_version(version, "package.json .version")


def read_python_version(root: Path) -> str:
    descriptor = root / "pyproject.toml"
    with descriptor.open("rb") as file:
        project_file = tomllib.load(file)

    project = project_file.get("project")
    if not isinstance(project, dict):
        raise ValueError("Missing expected table [project] in pyproject.toml.")

    dynamic = project.get("dynamic", [])
    if isinstance(dynamic, list) and "version" in dynamic:
        raise ValueError("pyproject.toml [project].dynamic includes version; static [project].version is required.")
    version = project.get("version", MISSING)
    if version is MISSING:
        raise ValueError("Missing expected field pyproject.toml [project].version.")
    return validate_version(version, "pyproject.toml [project].version")


def read_maven_version(root: Path) -> str:
    def local_name(tag: str) -> str:
        _, _, name = tag.partition("}")
        return name or tag

    descriptor = root / "pom.xml"
    project = element_tree.parse(descriptor).getroot()
    versions = [child for child in project if local_name(child.tag) == "version"]
    if len(versions) != 1:
        raise ValueError(f"Expected one root pom.xml project version, found {len(versions)}.")
    version = versions[0]
    return validate_version(version.text, "pom.xml project.version")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("npm", "python", "maven"))
    return parser.parse_args()


def main() -> int:
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11 or newer is required for version extraction.")

    args = parse_args()
    root = Path.cwd()
    if args.mode == "npm":
        version = read_npm_version(root)
    elif args.mode == "python":
        version = read_python_version(root)
    elif args.mode == "maven":
        version = read_maven_version(root)

    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
