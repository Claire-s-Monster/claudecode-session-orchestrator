"""Basic tests to verify the testing framework works."""

import pytest


def test_pixi_environment():
    """Test that the PIXI environment is working correctly."""
    import sys

    assert sys.version_info >= (3, 12), "Python version should be >= 3.12"
    assert sys.version_info < (3, 13), "Python version should be < 3.13"


def test_imports():
    """Test that core dependencies are importable."""
    import importlib.util

    required_packages = [
        "aiofiles",
        "click",
        "numpy",
        "pandas",
        "pexpect",
        "psutil",
        "rich",
        "toml",
        "yaml",
    ]

    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            pytest.fail(f"Required dependency not found: {package}")


def test_framework_compliance():
    """Test framework compliance basics."""
    from pathlib import Path

    # Verify PIXI-only compliance
    forbidden_files = [
        "requirements.txt",
        "setup.py",
        "Pipfile",
        "poetry.lock",
        "pip.conf",
    ]
    project_root = Path(__file__).parent.parent

    for forbidden_file in forbidden_files:
        assert not (project_root / forbidden_file).exists(), (
            f"PIXI-only violation: {forbidden_file} found"
        )

    # Verify pyproject.toml exists
    assert (project_root / "pyproject.toml").exists(), "pyproject.toml must exist"
