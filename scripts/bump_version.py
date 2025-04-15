#!/usr/bin/env python3
import subprocess
import sys
import re
from pathlib import Path
import json

def get_current_version() -> str:
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if match := re.search(r'version\s*=\s*"([^"]+)"', content):
            return match.group(1)

    raise FileNotFoundError("Could not find version in pyproject.toml")


def bump_version(current_version, bump_type):
    major, minor, patch = map(int, current_version.split("."))

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_version_in_files(new_version: str):
    # Update pyproject.toml if it exists
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        updated_content = re.sub(
            r'!(bump-)version\s*=\s*"[^"]+"', f'version = "{new_version}"', content
        )
        pyproject_path.write_text(updated_content)

    # Update __init__.py if it exists
    init_path = Path("src/find_404/__init__.py")
    if init_path.exists():
        content = init_path.read_text()
        updated_content = re.sub(
            r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"', content
        )
        init_path.write_text(updated_content)

    # Update uv.lock if it exists
    uv_lock = Path("uv.lock")
    if uv_lock.exists():
        content = uv_lock.read_text()
        updated_content = re.sub(
            r'!(bump-)version\s*=\s*"[^"]+"', f'version = "{new_version}"', content
        )
        uv_lock.write_text(updated_content)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ["major", "minor", "patch"]:
        print("Usage: bump_version.py [major|minor|patch]")
        sys.exit(1)

    bump_type = sys.argv[1]
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    new_version = bump_version(current_version, bump_type)

    # Update version in files
    update_version_in_files(new_version)

    # Git commands
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"Bump version to {new_version}"], check=True
    )
    subprocess.run(
        ["git", "tag", "-a", f"v{new_version}", "-m", f"Release version {new_version}"],
        check=True,
    )
    subprocess.run(["git", "push"], check=True)
    subprocess.run(["git", "push", "origin", f"v{new_version}"], check=True)
    subprocess.run(["uv", "sync"], check=True)

    print(f"Successfully bumped version to {new_version} and created release tag")

    # Create a new release
    print("You can create a new release with the following command:")
    print(f'gh release create v{new_version} -t "Release {new_version}" --notes-from-tag')


if __name__ == "__main__":
    main()
