#!/usr/bin/env python3
"""Read the versions from a supported project descriptor.

This intentionally has a small, fixed surface.  Composite action wrappers
choose the mode so reusable workflow callers cannot select arbitrary files or
parsing behaviour.
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def get_npm_dependencies(root: Path) -> [str]:
    descriptor = root / "package.json"
    with open(descriptor, "r") as package:
        return [
            f"    {line.strip()}"
            for line in package
            if "@zepben" in line and "-dev-" in line
        ]


def get_maven_dependencies(root: Path) -> [str]:
    descriptor = root / "pom.xml"
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    tree = ET.parse(descriptor)
    root = tree.getroot()

    pkgs = []
    for dep in root.findall(".//m:dependencies/m:dependency", ns):
        groupId = dep.find("m:groupId", ns)
        artifact = dep.find("m:artifactId", ns)
        version = dep.find("m:version", ns)
        if (
            groupId is not None
            and groupId.text == "com.zepben"
            and version is not None
            and "-dev-" in version.text
        ):
            pkgs.append(f"    {groupId.text}:{artifact.text}:{version.text}")

    return pkgs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("npm", "maven"))
    return parser.parse_args()


def main() -> int:
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11 or newer is required for version extraction.")

    args = parse_args()
    root = Path.cwd()
    if args.mode == "npm":
        pkgs = get_npm_dependencies(root)
    elif args.mode == "maven":
        pkgs = get_maven_dependencies(root)

    if len(pkgs) > 0:
        # at python < 3.12, we can't use \n in the f-string, ie can't use f"{\n.join()}"
        # so predefine the list before using
        package_list = "\n".join(pkgs)
        msg = f"""❌ Build Failed! Found the following dev dependencies:\n\n{package_list}\n\nClear dev dependencies above when ready to merge."""
        print(msg)
    else:
        print("nothing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
