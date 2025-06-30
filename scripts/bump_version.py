#!/usr/bin/env python3
import re
import subprocess
import sys
from typing import Protocol, TypedDict

# Inspired by https://blog.danslimmon.com/2019/07/15/do-nothing-scripting-the-key-to-gradual-automation/

class Context(TypedDict):
    bump_type: str
    current_version: str


def get_current_version() -> str:
    """Retrieves the current version from the codebase."""
    try:
        result = subprocess.run(
            ["uv", "version", "--short"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get current version: {e}")


def wait_for_enter() -> None:
    """Waits for the user to press Enter."""
    input("Press Enter to continue...")


class Step(Protocol):
    """Protocol for version bump steps."""
    def run(self, context: Context) -> None:
        """Execute the step with the given context."""
        ...


class FailIfDirty:
    def run(self, context: Context) -> None:
        """Checks if the git repository is dirty (has uncommitted changes)."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            raise RuntimeError("Git repository is dirty. Please commit or stash changes before running this script.")

class BumpVersion:
    def run(self, context: Context) -> None:
        """Bumps the version number in the actual codebase. We use `uv version` to do so."""
        bump_type = context["bump_type"]
        result = subprocess.run(
            ["uv", "version", "--bump", bump_type],
            capture_output=True,
            text=True,
            check=True,
        )
        # Get the new version and update context
        context["current_version"] = get_current_version()

class CommitVersion:
    def run(self, context: Context) -> None:
        """Commits the new version number to the git repository."""
        subprocess.run(
            ["git", "commit", "-am", f"Bump version to {context['current_version']}"],
            check=True,
        )

class TagVersion:
    def run(self, context: Context) -> None:
        """Tags the new version in the git repository."""
        current_version = context["current_version"]
        subprocess.run(
            ["git", "tag", "-a", f"v{current_version}", "-m", f"Release version {current_version}"],
            check=True,
        )

class PushChanges:
    def run(self, context: Context) -> None:
        """Pushes the changes to the remote repository."""
        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)

class CreateRelease:
    def run(self, context: Context) -> None:
        """Creates a new release using GitHub CLI."""
        current_version = context["current_version"]
        subprocess.run(
            ["gh", "release", "create", "--generate-notes", f"v{current_version}"],
            check=True,
        )

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py <bump_type>")
        print("Example: python bump_version.py minor")
        sys.exit(1)
    bump_type = sys.argv[1]

    context: Context = {
        "bump_type": bump_type,
        "current_version": get_current_version(),
    }

    procedure = [
        FailIfDirty(),
        BumpVersion(),
        CommitVersion(),
        TagVersion(),
        PushChanges(),
        CreateRelease(),
    ]

    for step in procedure:
        step.run(context)

if __name__ == "__main__":
    main()
