"""
Placeholder File Manager - Molecule Level Component

This module provides functionality for creating placeholder files in project directories
following atomic design principles. It implements two strategies:
1. GitKeep Strategy - creates .gitkeep files for git tracking
2. README Strategy - creates README.md files with descriptive content

The module handles git integration and provides comprehensive error handling.
"""

from dataclasses import dataclass, field
import os
import subprocess


@dataclass
class PlaceholderResult:
    """Result object for placeholder file operations."""

    success: bool = True
    created_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PlaceholderFileManager:
    """
    Manages creation of placeholder files in project directories.

    Provides two strategies for creating placeholder files:
    - GitKeep: Creates .gitkeep files for git tracking
    - README: Creates README.md files with descriptive content
    """

    def __init__(self) -> None:
        """Initialize the PlaceholderFileManager."""
        self.target_directories = [
            "src/orchestrator",
            "src/monitoring",
            "src/analytics",
            "src/intervention",
            "src/recovery",
            "tests/unit",
            "tests/integration",
            "tests/performance",
            "tests/fixtures",
            "scripts/emergency-fixes",
            "scripts/deployment",
            "scripts/compliance",
            "docs",
            ".github/workflows",
            ".taskmaster/tasks",
            ".taskmaster/docs",
        ]

    def create_gitkeep_files(self, base_path: str) -> PlaceholderResult:
        """
        Create .gitkeep files in all target directories.

        Args:
            base_path: Base project directory path

        Returns:
            PlaceholderResult with success status and file details
        """
        result = PlaceholderResult()

        # Validate base path exists
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"Base path does not exist: {base_path}")

        # Find all directories that need .gitkeep files
        directories_to_process = []

        # Check target directories
        for target_dir in self.target_directories:
            full_path = os.path.join(base_path, target_dir)
            if os.path.exists(full_path):
                directories_to_process.append(full_path)

        # Also find any empty directories recursively
        for root, dirs, files in os.walk(base_path):
            if not files and not dirs:  # Empty directory
                if root != base_path:  # Don't add base directory itself
                    directories_to_process.append(root)
            elif not files:  # Directory with only subdirectories
                # Check if this directory needs a gitkeep
                rel_path = os.path.relpath(root, base_path)
                if (
                    rel_path in self.target_directories
                    or root in directories_to_process
                ) and root not in directories_to_process:
                    directories_to_process.append(root)

        # Remove duplicates and sort
        directories_to_process = sorted(set(directories_to_process))

        # Create .gitkeep files
        for directory in directories_to_process:
            gitkeep_path = os.path.join(directory, ".gitkeep")

            try:
                # Don't overwrite existing .gitkeep files
                if os.path.exists(gitkeep_path):
                    continue

                # Create .gitkeep file
                with open(gitkeep_path, "w") as f:
                    f.write("# This file ensures the directory is tracked by git")

                result.created_files.append(gitkeep_path)

                # Try to add to git
                self._git_add_file(gitkeep_path, result)

            except PermissionError as e:
                result.errors.append(
                    f"Permission denied creating .gitkeep in {directory}: {e}"
                )
                result.success = True  # Continue processing other directories
            except Exception as e:
                result.errors.append(f"Error creating .gitkeep in {directory}: {e}")

        return result

    def create_readme_files(self, base_path: str) -> PlaceholderResult:
        """
        Create README.md files in all target directories.

        Args:
            base_path: Base project directory path

        Returns:
            PlaceholderResult with success status and file details
        """
        result = PlaceholderResult()

        # Validate base path exists
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"Base path does not exist: {base_path}")

        # Directory-specific content mapping
        directory_content = {
            "src/orchestrator": "# Orchestrator Module",
            "src/monitoring": "# Monitoring Module",
            "src/analytics": "# Analytics Module",
            "src/intervention": "# Intervention Module",
            "src/recovery": "# Recovery Module",
            "tests/unit": "# Unit Tests",
            "tests/integration": "# Integration Tests",
            "tests/performance": "# Performance Tests",
            "tests/fixtures": "# Test Fixtures",
            "scripts/emergency-fixes": "# Emergency Fix Scripts",
            "scripts/deployment": "# Deployment Scripts",
            "scripts/compliance": "# Compliance Scripts",
            "docs": "# Documentation",
            ".github/workflows": "# GitHub Workflows",
            ".taskmaster/tasks": "# Task Master Tasks",
            ".taskmaster/docs": "# Task Master Documentation",
        }

        # Create README.md files in target directories
        for target_dir in self.target_directories:
            full_path = os.path.join(base_path, target_dir)

            if not os.path.exists(full_path):
                continue

            readme_path = os.path.join(full_path, "README.md")

            try:
                # Don't overwrite existing README files
                if os.path.exists(readme_path):
                    continue

                # Get directory-specific title
                title = directory_content.get(
                    target_dir, f"# {os.path.basename(target_dir).title()}"
                )

                # Create README content
                content = f"""{title}

This directory is a placeholder and will be populated during development.

## Purpose

This directory is part of the project structure and will contain relevant files and modules as the project evolves.

## Status

- **Created**: Auto-generated placeholder
- **Populated**: Not yet

---
*This is an auto-generated placeholder file.*
"""

                with open(readme_path, "w") as f:
                    f.write(content)

                result.created_files.append(readme_path)

                # Try to add to git
                self._git_add_file(readme_path, result)

            except PermissionError as e:
                result.errors.append(
                    f"Permission denied creating README.md in {full_path}: {e}"
                )
                result.success = True  # Continue processing other directories
            except Exception as e:
                result.errors.append(f"Error creating README.md in {full_path}: {e}")

        return result

    def _git_add_file(self, file_path: str, result: PlaceholderResult) -> None:
        """
        Add a file to git tracking.

        Args:
            file_path: Path to file to add to git
            result: Result object to update with warnings/errors
        """
        try:
            # Run git add command
            cmd_result = subprocess.run(
                ["git", "add", file_path], capture_output=True, text=True, check=False
            )

            if cmd_result.returncode != 0:
                # Git command failed, but don't fail the whole operation
                result.warnings.append(
                    f"Git add failed for {file_path}: {cmd_result.stderr}"
                )

        except FileNotFoundError:
            # Git not available
            result.warnings.append(f"Git not available - {file_path} not tracked")
        except Exception as e:
            result.warnings.append(f"Git add error for {file_path}: {e}")
