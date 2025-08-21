"""Test fixtures for placeholder file creation tests.

This module provides reusable fixtures for testing placeholder file creation
functionality across different test scenarios.
"""

import os
import shutil
import tempfile
from typing import NamedTuple
from unittest.mock import MagicMock, patch

import pytest


class PlaceholderResult(NamedTuple):
    """Result object for placeholder file operations."""

    success: bool
    created_files: list[str]
    directories_processed: list[str]
    errors: list[str]
    warnings: list[str]


@pytest.fixture(scope="session")
def project_directory_structure():
    """Define the complete project directory structure for testing."""
    return {
        "core_directories": [
            "src/orchestrator",
            "src/monitoring",
            "src/analytics",
            "src/intervention",
            "src/recovery",
        ],
        "test_directories": [
            "tests/unit",
            "tests/integration",
            "tests/performance",
            "tests/fixtures",
        ],
        "script_directories": [
            "scripts/emergency-fixes",
            "scripts/deployment",
            "scripts/compliance",
        ],
        "meta_directories": [
            "docs",
            ".github/workflows",
            ".taskmaster/tasks",
            ".taskmaster/docs",
        ],
    }


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    temp_dir = tempfile.mkdtemp()

    # Initialize git repo
    os.chdir(temp_dir)
    os.system("git init")
    os.system('git config user.email "test@example.com"')
    os.system('git config user.name "Test User"')

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_file_operations():
    """Mock file system operations for isolated testing."""
    with (
        patch("builtins.open", mock_open()) as mock_file,
        patch("os.makedirs") as mock_makedirs,
        patch("os.path.exists") as mock_exists,
        patch("os.listdir") as mock_listdir,
    ):
        mock_exists.return_value = True
        mock_listdir.return_value = []  # Empty directories
        mock_makedirs.return_value = None

        yield {
            "open": mock_file,
            "makedirs": mock_makedirs,
            "exists": mock_exists,
            "listdir": mock_listdir,
        }


@pytest.fixture
def gitkeep_content_template():
    """Standard .gitkeep file content template."""
    return "# This file ensures the directory is tracked by git"


@pytest.fixture
def readme_content_templates():
    """README.md content templates for different directory types."""
    return {
        "src": {
            "orchestrator": "# Orchestrator Module\n\nThis directory is a placeholder for orchestrator components.",
            "monitoring": "# Monitoring Module\n\nThis directory is a placeholder for monitoring components.",
            "analytics": "# Analytics Module\n\nThis directory is a placeholder for analytics components.",
            "intervention": "# Intervention Module\n\nThis directory is a placeholder for intervention components.",
            "recovery": "# Recovery Module\n\nThis directory is a placeholder for recovery components.",
        },
        "tests": {
            "unit": "# Unit Tests\n\nThis directory is a placeholder for unit test files.",
            "integration": "# Integration Tests\n\nThis directory is a placeholder for integration test files.",
            "performance": "# Performance Tests\n\nThis directory is a placeholder for performance test files.",
            "fixtures": "# Test Fixtures\n\nThis directory is a placeholder for test fixture files.",
        },
        "scripts": {
            "emergency-fixes": "# Emergency Fix Scripts\n\nThis directory is a placeholder for emergency fix scripts.",
            "deployment": "# Deployment Scripts\n\nThis directory is a placeholder for deployment scripts.",
            "compliance": "# Compliance Scripts\n\nThis directory is a placeholder for compliance scripts.",
        },
        "default": "# Directory Placeholder\n\nThis directory is a placeholder and will be populated with content.",
    }


@pytest.fixture
def mock_placeholder_manager():
    """Mock placeholder file manager for testing without implementation."""

    class MockPlaceholderFileManager:
        def create_gitkeep_files(self, base_path: str) -> PlaceholderResult:
            """Mock method that should be implemented."""
            raise NotImplementedError(
                "TDD RED phase - PlaceholderFileManager not implemented",
            )

        def create_readme_files(self, base_path: str) -> PlaceholderResult:
            """Mock method that should be implemented."""
            raise NotImplementedError(
                "TDD RED phase - PlaceholderFileManager not implemented",
            )

        def scan_empty_directories(self, base_path: str) -> list[str]:
            """Mock method that should be implemented."""
            raise NotImplementedError(
                "TDD RED phase - PlaceholderFileManager not implemented",
            )

    return MockPlaceholderFileManager()


@pytest.fixture
def coverage_metrics():
    """Define coverage metrics and goals for placeholder file tests."""
    return {
        "target_directories": 17,
        "required_line_coverage": 100,
        "required_branch_coverage": 95,
        "required_function_coverage": 100,
        "test_categories": {
            "gitkeep_strategy": 3,
            "readme_strategy": 3,
            "git_integration": 3,
            "edge_cases": 4,
            "file_system_mocking": 2,
        },
        "total_tests": 16,  # Excluding the TDD RED phase test
    }


def mock_open(read_data=""):
    """Enhanced mock_open that supports write operations."""
    mock = MagicMock(spec=open)
    handle = MagicMock()
    handle.read.return_value = read_data
    handle.write.return_value = None
    handle.__enter__.return_value = handle
    handle.__exit__.return_value = None
    mock.return_value = handle
    return mock
