#!/usr/bin/env python3
"""Emergency Quality Fix Script.

Automatically fixes common quality issues in the codebase.
"""

from pathlib import Path
import subprocess  # nosec B404
import sys


def run_fix_command(name: str, cmd: str) -> bool:
    """Run a fix command and report results."""
    print(f"🔧 Running {name}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # nosec B602

        if result.returncode != 0:
            print(f"⚠️  {name} encountered issues:")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
        else:
            print(f"✅ {name} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
    except Exception as e:
        print(f"❌ {name} failed with exception: {e}")
        return False


def main() -> None:
    """Main emergency fix function."""
    print("🚨 EMERGENCY QUALITY FIX MODE ACTIVATED")
    print("=" * 45)
    print("Attempting to automatically fix common quality issues...")
    print()

    # Check if we're in a Python project
    has_python = any(
        Path(f).exists() for f in ["setup.py", "pyproject.toml", "requirements.txt"]
    ) or any(Path(".").glob("*.py"))

    if not has_python:
        print("❌ Not a Python project - no fixes to apply")
        sys.exit(1)

    # Common automatic fixes
    fixes = [
        ("Code Formatting", "pixi run format"),
        ("Import Sorting", "isort src/ scripts/ tests/"),
        ("Auto-fixable Lint Issues", "pixi run lint-fix"),
        (
            "Trailing Whitespace",
            "python -c \"import pathlib; [p.write_text(p.read_text().rstrip() + '\\n') for p in pathlib.Path('.').glob('**/*.py') if p.is_file()]\"",
        ),
    ]

    fixes_applied = 0
    successful_fixes = []

    for name, cmd in fixes:
        if run_fix_command(name, cmd):
            fixes_applied += 1
            successful_fixes.append(name)
        else:
            print(f"⚠️  {name} could not be auto-fixed")

    print()
    print("=" * 45)
    print(f"🔧 Emergency fixes completed: {fixes_applied}/{len(fixes)}")

    if successful_fixes:
        print("✅ Successfully applied fixes:")
        for fix in successful_fixes:
            print(f"  - {fix}")

    if fixes_applied < len(fixes):
        print("⚠️  Some fixes could not be applied automatically")
        print("Manual intervention may be required")

    # Re-run quality checks if any fixes were applied
    if fixes_applied > 0:
        print()
        print("🔄 Re-running quality checks...")
        result = subprocess.run(["python", "scripts/quality-check.py"])  # nosec B603,B607

        if result.returncode == 0:
            print("🎉 Quality checks now passing after emergency fixes!")
        else:
            print("⚠️  Some quality issues remain after emergency fixes")
            print("Consider running specific tools manually:")
            print("  - pixi run format")
            print("  - pixi run lint")
            print("  - pixi run type-check")
    else:
        print("❌ No fixes were successfully applied")
        print("Manual debugging required")

    sys.exit(0 if fixes_applied > 0 else 1)


if __name__ == "__main__":
    main()
