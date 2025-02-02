#!/usr/bin/env python3
import subprocess
import sys
import re
from pathlib import Path
import json

def get_current_version():
    # Try to read from pyproject.toml first
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if match := re.search(r'version\s*=\s*"([^"]+)"', content):
            return match.group(1)
    
    # Try package.json next
    package_json = Path("package.json")
    if package_json.exists():
        data = json.loads(package_json.read_text())
        return data.get("version", "0.0.0")
    
    return "0.0.0"

def bump_version(current_version, bump_type):
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"

def update_version_in_files(new_version):
    # Update pyproject.toml if it exists
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        updated_content = re.sub(
            r'version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            content
        )
        pyproject_path.write_text(updated_content)
    
    # Update package.json if it exists
    package_json = Path("package.json")
    if package_json.exists():
        data = json.loads(package_json.read_text())
        data["version"] = new_version
        package_json.write_text(json.dumps(data, indent=2) + "\n")

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ["major", "minor", "patch"]:
        print("Usage: bump_version.py [major|minor|patch]")
        sys.exit(1)

    bump_type = sys.argv[1]
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)
    
    # Update version in files
    update_version_in_files(new_version)
    
    # Git commands
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"Bump version to {new_version}"], check=True)
    subprocess.run(["git", "tag", "-a", f"v{new_version}", "-m", f"Release version {new_version}"], check=True)
    subprocess.run(["git", "push"], check=True)
    subprocess.run(["git", "push", "origin", f"v{new_version}"], check=True)
    
    print(f"Successfully bumped version to {new_version} and created release tag")

    # Create a new release
    print("You can create a new release with the following command:")
    print(f"gh release create v{new_version} -t \"Release {new_version}\" -n \"Release notes for {new_version}\"")

if __name__ == "__main__":
    main() 