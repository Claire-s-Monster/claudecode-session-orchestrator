"""Placeholder File Manager.

This module provides functionality to create and manage placeholder files in project
directories, ensuring proper git integration and validation.
"""

from dataclasses import dataclass, field
import os
import subprocess  # nosec B404


@dataclass
class PlaceholderResult:
    """Result object for placeholder file operations."""

    success: bool = True
    created_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PlaceholderFileManager:
    """Manages creation of placeholder files in project directories.

    This class provides functionality to create placeholder files with proper git
    integration and validation, ensuring consistent project structure.
    """

    def __init__(self, root_directory: str = "."):
        """Initialize the PlaceholderFileManager.

        Args:     root_directory: Root directory for placeholder file operations
        """
        self.root_directory = root_directory
        self.target_directories: list[
            str
        ] = []  # List of target directories for processing
        self.placeholder_content = {
            "readme": "# {directory_name}\n\nPlaceholder directory for future development.\n",
            "gitkeep": "# Git keep file - maintains empty directory in version control\n",
            "init": '"""Package initialization file."""\n',
            "test_init": '"""Test package initialization."""\n',
        }

    def create_gitkeep_files(self, base_path: str) -> PlaceholderResult:
        """Create .gitkeep files in all subdirectories under base_path.

        Args:     base_path: Base directory path to scan for subdirectories

        Returns:     PlaceholderResult object with operation results

        Raises:     FileNotFoundError: If the base_path directory does not exist
        """
        result = PlaceholderResult()

        # Check if base path exists first
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"Directory does not exist: {base_path}")

        try:
            # Find all directories and handle both leaf directories and target directories
            all_directories = []
            directories_to_process = set()

            # Walk through all directories under base_path
            for root, _dirs, _files in os.walk(base_path):
                # Skip the base directory itself
                if root == base_path:
                    continue
                all_directories.append(root)

            # Filter to only leaf directories (no subdirectories inside them)
            leaf_directories = []
            for directory in all_directories:
                has_subdirs = any(
                    subdir.startswith(directory + os.sep)
                    for subdir in all_directories
                    if subdir != directory
                )
                if not has_subdirs:
                    leaf_directories.append(directory)
                    directories_to_process.add(directory)

            # Also check for target directories that should get gitkeep files
            # This covers line 94 test case where parent directories need gitkeep
            for directory in all_directories:
                rel_path = os.path.relpath(directory, base_path)
                if (
                    rel_path in self.target_directories
                    and directory not in directories_to_process
                ):
                    directories_to_process.add(directory)

            # Create .gitkeep files in all directories to process
            for directory in directories_to_process:
                gitkeep_path = os.path.join(directory, ".gitkeep")

                # Check if .gitkeep already exists
                if os.path.exists(gitkeep_path):
                    result.warnings.append(f".gitkeep already exists: {gitkeep_path}")
                    continue

                try:
                    # Create .gitkeep file with standard content
                    with open(gitkeep_path, "w", encoding="utf-8") as f:
                        f.write("# This file ensures the directory is tracked by git\n")

                    result.created_files.append(gitkeep_path)

                    # Try to add to git if available
                    try:
                        git_result = subprocess.run(  # nosec B603,B607
                            ["git", "add", gitkeep_path],
                            capture_output=True,
                            text=True,
                            check=False,
                            timeout=10,
                        )
                        # Check git command result
                        if git_result.returncode != 0:
                            result.warnings.append(
                                f"Git add failed for {gitkeep_path}: {git_result.stderr.strip()}",
                            )
                    except FileNotFoundError:
                        # Git not available
                        result.warnings.append(
                            f"git not available - could not add: {gitkeep_path}",
                        )
                    except (subprocess.SubprocessError, OSError):
                        # Git not available or failed, but don't fail the operation
                        result.warnings.append(f"Could not add to git: {gitkeep_path}")
                    except Exception as e:
                        # Handle any other git-related exceptions
                        result.warnings.append(
                            f"Git add error for {gitkeep_path}: {e!s}",
                        )

                except (PermissionError, OSError) as e:
                    if "permission" in str(e).lower():
                        result.errors.append(
                            f"Permission denied creating .gitkeep file {gitkeep_path}: {e!s}",
                        )
                    else:
                        result.errors.append(
                            f"Error creating .gitkeep file {gitkeep_path}: {e!s}",
                        )
                    # Continue processing other directories - don't fail entire operation
                except Exception as e:
                    # Handle general exceptions during file creation (line 122-123)
                    result.errors.append(
                        f"Error creating .gitkeep file {gitkeep_path}: {e!s}",
                    )
                    # Continue processing - maintain success = True for graceful handling

        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to create .gitkeep files: {e!s}")

        return result

    def create_readme_files(self, base_path: str) -> PlaceholderResult:
        """Create README.md files in all subdirectories under base_path.

        Creates README.md files with directory-specific content.

        Args:     base_path: Base directory path to scan for subdirectories

        Returns:     PlaceholderResult object with operation results

        Raises:     FileNotFoundError: If the base_path directory does not exist
        """
        result = PlaceholderResult()

        # Check if base path exists first
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"Directory does not exist: {base_path}")

        # Directory-specific title mapping
        title_mapping = {
            "orchestrator": "Orchestrator Module",
            "monitoring": "Monitoring Module",
            "analytics": "Analytics Module",
            "intervention": "Intervention Module",
            "recovery": "Recovery Module",
            "unit": "Unit Tests",
            "integration": "Integration Tests",
            "performance": "Performance Tests",
            "fixtures": "Test Fixtures",
            "emergency-fixes": "Emergency Fix Scripts",
            "deployment": "Deployment Scripts",
            "compliance": "Compliance Scripts",
            "docs": "Documentation",
            "workflows": "GitHub Workflows",
            "tasks": "Task Master Tasks",
        }

        try:
            # Find all leaf directories (directories that don't have subdirectories)
            all_directories = []

            # Walk through all directories under base_path
            for root, _dirs, _files in os.walk(base_path):
                # Skip the base directory itself
                if root == base_path:
                    continue
                all_directories.append(root)

            # Filter to only leaf directories (no subdirectories inside them)
            leaf_directories = []
            for directory in all_directories:
                has_subdirs = any(
                    subdir.startswith(directory + os.sep)
                    for subdir in all_directories
                    if subdir != directory
                )
                if not has_subdirs:
                    leaf_directories.append(directory)

            # Create README.md files only in leaf directories
            for directory in leaf_directories:
                readme_path = os.path.join(directory, "README.md")

                # Check if README.md already exists
                if os.path.exists(readme_path):
                    result.warnings.append(f"README.md already exists: {readme_path}")
                    continue

                try:
                    # Determine appropriate title for directory
                    dir_name = os.path.basename(directory)
                    title = title_mapping.get(
                        dir_name,
                        f"{dir_name.replace('-', ' ').replace('_', ' ').title()}",
                    )

                    # Create directory-specific README content with placeholder description
                    content = f"# {title}\n\nThis directory is a placeholder for future development.\n\n"
                    content += "This directory is part of the Claude Code Session Orchestrator project.\n"

                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    result.created_files.append(readme_path)

                    # Try to add to git if available
                    try:
                        subprocess.run(  # nosec B603,B607
                            ["git", "add", readme_path],
                            capture_output=True,
                            text=True,
                            check=False,
                            timeout=10,
                        )
                    except FileNotFoundError:
                        # Git not available
                        result.warnings.append(
                            f"git not available - could not add: {readme_path}",
                        )
                    except (subprocess.SubprocessError, OSError):
                        # Git not available or failed, but don't fail the operation
                        result.warnings.append(f"Could not add to git: {readme_path}")

                except (PermissionError, OSError) as e:
                    result.errors.append(
                        f"Error creating README.md file {readme_path}: {e!s}",
                    )
                    # Continue processing other directories - don't fail entire operation

        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to create README.md files: {e!s}")

        return result

    def create_directory_structure(
        self,
        directories: list[str],
        include_readme: bool = True,
        include_gitkeep: bool = True,
        include_init: bool = False,
        add_to_git: bool = True,
    ) -> PlaceholderResult:
        """Create directory structure with placeholder files.

        Args:     directories: List of directory paths to create     include_readme:
        Whether to include README.md files     include_gitkeep: Whether to include
        .gitkeep files     include_init: Whether to include __init__.py files
        add_to_
        git:
        Whether to add created files to git

        Returns:
        PlaceholderResult object with operation results
        """
        result = PlaceholderResult()

        try:
            for directory in directories:
                dir_result = self._create_single_directory(
                    directory,
                    include_readme,
                    include_gitkeep,
                    include_init,
                    add_to_git,
                )

                # Merge results
                result.created_files.extend(dir_result.created_files)
                result.warnings.extend(dir_result.warnings)
                result.errors.extend(dir_result.errors)

                if not dir_result.success:
                    result.success = False

        except Exception as e:
            result.success = False
            result.errors.append(f"Directory structure creation failed: {e!s}")

        return result

    def _create_single_directory(
        self,
        directory: str,
        include_readme: bool,
        include_gitkeep: bool,
        include_init: bool,
        add_to_git: bool,
    ) -> PlaceholderResult:
        """Create a single directory with specified placeholder files."""
        result = PlaceholderResult()

        try:
            # Create directory if it doesn't exist
            dir_path = os.path.join(self.root_directory, directory)
            os.makedirs(dir_path, exist_ok=True)

            # Create placeholder files
            files_to_create = []

            if include_readme:
                files_to_create.append(
                    (
                        "README.md",
                        self.placeholder_content["readme"].format(
                            directory_name=os.path.basename(directory).title(),
                        ),
                    ),
                )

            if include_gitkeep:
                files_to_create.append(
                    (".gitkeep", self.placeholder_content["gitkeep"]),
                )

            if include_init:
                if "test" in directory.lower():
                    files_to_create.append(
                        ("__init__.py", self.placeholder_content["test_init"]),
                    )
                else:
                    files_to_create.append(
                        ("__init__.py", self.placeholder_content["init"]),
                    )

            # Write files
            for filename, content in files_to_create:
                file_path = os.path.join(dir_path, filename)

                # Check if file already exists
                if os.path.exists(file_path):
                    result.warnings.append(f"File already exists: {file_path}")
                    continue

                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    result.created_files.append(file_path)

                    # Add to git if requested
                    if add_to_git:
                        self._add_to_git(file_path, result)

                except OSError as e:
                    result.errors.append(f"Failed to create {file_path}: {e!s}")
                    result.success = False

        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to create directory {directory}: {e!s}")

        return result

    def validate_placeholder_files(self, directories: list[str]) -> PlaceholderResult:
        """Validate that placeholder files exist in specified directories.

        Args:     directories: List of directory paths to validate

        Returns:     PlaceholderResult object with validation results
        """
        result = PlaceholderResult()

        try:
            for directory in directories:
                dir_path = os.path.join(self.root_directory, directory)

                if not os.path.exists(dir_path):
                    result.errors.append(f"Directory does not exist: {dir_path}")
                    result.success = False
                    continue

                # Check for common placeholder files
                expected_files = [".gitkeep", "README.md", "__init__.py"]
                found_files = []

                for expected_file in expected_files:
                    file_path = os.path.join(dir_path, expected_file)
                    if os.path.exists(file_path):
                        found_files.append(expected_file)

                if not found_files:
                    result.warnings.append(
                        f"No placeholder files found in directory: {dir_path}",
                    )
                else:
                    result.created_files.extend(
                        [os.path.join(dir_path, f) for f in found_files],
                    )

        except Exception as e:
            result.success = False
            result.errors.append(f"Validation failed: {e!s}")

        return result

    def cleanup_placeholder_files(self, directories: list[str]) -> PlaceholderResult:
        """Clean up placeholder files from specified directories.

        Args:     directories: List of directory paths to clean

        Returns:     PlaceholderResult object with cleanup results
        """
        result = PlaceholderResult()

        try:
            for directory in directories:
                dir_path = os.path.join(self.root_directory, directory)

                if not os.path.exists(dir_path):
                    result.warnings.append(f"Directory does not exist: {dir_path}")
                    continue

                # Remove common placeholder files
                placeholder_files = [".gitkeep", "README.md"]

                for placeholder_file in placeholder_files:
                    file_path = os.path.join(dir_path, placeholder_file)

                    if os.path.exists(file_path):
                        try:
                            # Check if file contains only placeholder content
                            with open(file_path, encoding="utf-8") as f:
                                content = f.read().strip()

                            # Only remove if it's clearly a placeholder
                            if (
                                "placeholder" in content.lower()
                                or "git keep file" in content.lower()
                                or len(content) < 100  # Short placeholder content
                            ):
                                os.remove(file_path)
                                result.created_files.append(f"Removed: {file_path}")
                            else:
                                result.warnings.append(
                                    f"Skipped non-placeholder file: {file_path}",
                                )

                        except OSError as e:
                            result.errors.append(
                                f"Failed to remove {file_path}: {e!s}",
                            )
                            result.success = False

        except Exception as e:
            result.success = False
            result.errors.append(f"Cleanup failed: {e!s}")

        return result

    def _add_to_git(self, file_path: str, result: PlaceholderResult) -> None:
        """Add a file to git tracking.

        Args:     file_path: Path to file to add to git     result: Result object to
        update with warnings/errors
        """
        try:
            # Run git add command
            cmd_result = subprocess.run(  # nosec B603,B607
                ["git", "add", file_path],
                capture_output=True,
                text=True,
                check=False,
            )

            if cmd_result.returncode != 0:
                result.warnings.append(
                    f"Git add failed for {file_path}: {cmd_result.stderr.strip()}",
                )
            else:
                result.warnings.append(f"Added to git: {file_path}")

        except Exception as e:
            result.warnings.append(f"Git add exception for {file_path}: {e!s}")

    def get_summary(self, result: PlaceholderResult) -> str:
        """Generate a human-readable summary of placeholder file operations.

        Args:     result: PlaceholderResult object to summarize

        Returns:     Formatted summary string
        """
        summary_lines = []

        if result.success:
            summary_lines.append(
                "✅ Placeholder file operations completed successfully",
            )
        else:
            summary_lines.append("❌ Placeholder file operations encountered errors")

        if result.created_files:
            summary_lines.append(
                f"📁 Files created/processed: {len(result.created_files)}",
            )
            for file_path in result.created_files[:5]:  # Show first 5
                summary_lines.append(f"   - {file_path}")
            if len(result.created_files) > 5:
                summary_lines.append(f"   ... and {len(result.created_files) - 5} more")

        if result.warnings:
            summary_lines.append(f"⚠️  Warnings: {len(result.warnings)}")
            for warning in result.warnings[:3]:  # Show first 3
                summary_lines.append(f"   - {warning}")
            if len(result.warnings) > 3:
                summary_lines.append(f"   ... and {len(result.warnings) - 3} more")

        if result.errors:
            summary_lines.append(f"❌ Errors: {len(result.errors)}")
            for error in result.errors:
                summary_lines.append(f"   - {error}")

        return "\n".join(summary_lines)
