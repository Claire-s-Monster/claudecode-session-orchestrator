"""
Edge case tests to achieve 100% coverage for placeholder_file_manager.py

These tests specifically target the remaining uncovered lines:
- Line 94: Directory processing edge case in nested structure
- Lines 122-123: General exception handling in gitkeep creation
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from src.molecules.placeholder_file_manager import PlaceholderFileManager


class TestCoverageEdgeCases:
    """Tests for specific uncovered lines to achieve 100% coverage."""

    def test_nested_directory_processing_line_94(self):
        """
        Test the specific condition on line 94 where:
        rel_path in self.target_directories AND root in directories_to_process
        AND root not in directories_to_process (the third condition)

        This requires a directory that has files but not subdirectories,
        and is in the target list but not already processed.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PlaceholderFileManager()

            # Create a target directory structure
            target_dir = "src/orchestrator"  # This is in target_directories
            full_target_path = os.path.join(temp_dir, target_dir)
            os.makedirs(full_target_path, exist_ok=True)

            # Create a file in the directory (so it's not empty, has files but no dirs)
            test_file = os.path.join(full_target_path, "test_file.py")
            with open(test_file, "w") as f:
                f.write("# test file")

            # Now create subdirectories that will be processed first
            subdir = os.path.join(full_target_path, "subdir")
            os.makedirs(subdir, exist_ok=True)

            # This should trigger the logic on lines 90-94
            result = manager.create_gitkeep_files(temp_dir)

            # Verify the result and that the directory was processed
            assert result.success is True

            # The subdir should have a gitkeep file
            gitkeep_path = os.path.join(subdir, ".gitkeep")
            assert os.path.exists(gitkeep_path)

    def test_general_exception_handling_lines_122_123(self):
        """
        Test the general exception handling on lines 122-123
        by causing a general exception during file creation.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PlaceholderFileManager()

            # Create target directory
            target_dir = os.path.join(temp_dir, "src", "orchestrator")
            os.makedirs(target_dir, exist_ok=True)

            # Mock open to raise a general exception (not PermissionError)
            with patch("builtins.open", side_effect=OSError("General OS error")):
                result = manager.create_gitkeep_files(temp_dir)

                # Should handle the general exception gracefully
                assert len(result.errors) > 0, "General errors should be captured"
                assert any(
                    "error creating .gitkeep" in error.lower()
                    for error in result.errors
                )

                # The result should still indicate completion (success doesn't change for general exceptions)
                # Note: The success flag isn't explicitly set to False for general exceptions

    def test_complex_nested_structure_edge_case(self):
        """
        Test a complex nested structure that exercises the directory processing logic.
        This creates conditions that can trigger line 94.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PlaceholderFileManager()

            # Create a structure where we have:
            # 1. A directory with only subdirectories (no files)
            # 2. That directory is in target_directories
            # 3. The subdirectory is empty

            # Create main target directory
            main_dir = os.path.join(
                temp_dir, "src", "recovery"
            )  # This is in target_directories
            os.makedirs(main_dir, exist_ok=True)

            # Create nested empty subdirectories
            nested_dir1 = os.path.join(main_dir, "level1")
            nested_dir2 = os.path.join(nested_dir1, "level2")
            nested_dir3 = os.path.join(nested_dir2, "level3")
            os.makedirs(nested_dir3, exist_ok=True)

            # Also create another target directory that will be processed
            other_target = os.path.join(temp_dir, "docs")
            os.makedirs(other_target, exist_ok=True)

            result = manager.create_gitkeep_files(temp_dir)

            # All directories should get gitkeep files
            assert result.success is True

            # Check that gitkeep files were created in nested structure
            assert os.path.exists(os.path.join(nested_dir3, ".gitkeep"))
            assert os.path.exists(os.path.join(other_target, ".gitkeep"))

    def test_directory_with_subdirs_but_no_files_edge_case(self):
        """
        Test the specific case where a directory has subdirectories but no files,
        which can trigger the logic around line 94.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PlaceholderFileManager()

            # Create structure: parent dir with only subdirs, no files
            parent_dir = os.path.join(temp_dir, "src", "monitoring")  # Target directory
            subdir1 = os.path.join(parent_dir, "subsystem1")
            subdir2 = os.path.join(parent_dir, "subsystem2")

            os.makedirs(subdir1, exist_ok=True)
            os.makedirs(subdir2, exist_ok=True)

            # Parent has subdirs but no files - this triggers elif not files: condition
            result = manager.create_gitkeep_files(temp_dir)

            assert result.success is True

            # Both subdirectories should have gitkeep files
            assert os.path.exists(os.path.join(subdir1, ".gitkeep"))
            assert os.path.exists(os.path.join(subdir2, ".gitkeep"))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
