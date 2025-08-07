# \!/usr/bin/env python3
"""
Emergency Fix Protocol Script
Attempts automatic fixes for common quality violations.
"""

from pathlib import Path
import subprocess


def run_fix(name, cmd):
    """Run an emergency fix command."""
    print(f"🔧 {name}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {name} completed successfully")
        return True
    else:
        print(f"❌ {name} failed:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False


def main():
    """Main emergency fix function."""
    print("🚨 EMERGENCY FIX PROTOCOL ACTIVATED")
    print("🔧 Attempting automatic fixes...")
    print("=" * 50)

    # Check project type
    has_python = any(
        Path(f).exists() for f in ["setup.py", "pyproject.toml", "requirements.txt"]
    ) or any(Path(".").glob("*.py"))
    has_node = Path("package.json").exists()

    fixes_applied = []
    fixes_failed = []

    # Python fixes
    if has_python:
        python_fixes = [
            ("Auto-formatting with Black", "black ."),
            ("Import sorting with isort", "isort ."),
            (
                "Remove unused imports",
                "autoflake --remove-all-unused-imports --in-place --recursive .",
            ),
        ]

        for name, cmd in python_fixes:
            if run_fix(name, cmd):
                fixes_applied.append(name)
            else:
                fixes_failed.append(name)

    # Node.js fixes
    if has_node:
        node_fixes = [
            ("Prettier formatting", "npx prettier --write ."),
            ("ESLint auto-fix", "npx eslint . --fix"),
        ]

        for name, cmd in node_fixes:
            if run_fix(name, cmd):
                fixes_applied.append(name)
            else:
                fixes_failed.append(name)

    print("=" * 50)
    print("🔧 Emergency fix summary:")

    if fixes_applied:
        print("✅ Fixes applied:")
        for fix in fixes_applied:
            print(f"  - {fix}")

    if fixes_failed:
        print("❌ Fixes failed:")
        for fix in fixes_failed:
            print(f"  - {fix}")

    if fixes_applied:
        print()
        print("🔄 Re-running quality checks...")
        result = subprocess.run(["python", "scripts/quality-check.py"])

        if result.returncode == 0:
            print(r"🎉 Quality checks now passing after emergency fixes\!")
        else:
            print("⚠️  Some quality issues remain after emergency fixes")
            print("📋 Manual intervention may be required")
    else:
        print("⚠️  No automatic fixes were successful")
        print("📋 Manual intervention required")


if __name__ == "__main__":
    main()
