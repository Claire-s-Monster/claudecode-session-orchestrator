"""
Specific test to cover line 94 in placeholder_file_manager.py

The condition on line 94 requires:
1. Directory with only subdirectories (no files) - line 87 elif
2. rel_path in self.target_directories OR root in directories_to_process
3. AND root not in directories_to_process

This is achieved by creating a directory structure where a target directory
has subdirectories but no files, and ensuring it gets processed.
"""

import os
import tempfile

import pytest
from src.molecules.placeholder_file_manager import PlaceholderFileManager


class TestLine94Coverage:
    """Test specifically designed to achieve coverage of line 94."""

    def test_target_directory_with_only_subdirs_line_94(self):
        """
        Create a scenario that specifically triggers line 94:
        - A target directory that has only subdirectories (no files)
        - The directory is in target_directories
        - The directory is not yet in directories_to_process
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PlaceholderFileManager()
            
            # Create the exact directory structure that triggers line 94
            # Use a target directory that will have subdirectories but no files
            target_path = "src/recovery"  # This is in manager.target_directories
            full_target_path = os.path.join(temp_dir, target_path)
            
            # Create the main target directory
            os.makedirs(full_target_path, exist_ok=True)
            
            # Create subdirectories in the target directory (but no files)
            subdir1 = os.path.join(full_target_path, "submodule1")
            subdir2 = os.path.join(full_target_path, "submodule2") 
            os.makedirs(subdir1, exist_ok=True)
            os.makedirs(subdir2, exist_ok=True)
            
            # This creates the condition:
            # - full_target_path has subdirs but no files (triggers elif not files:)
            # - rel_path ("src/recovery") is in self.target_directories 
            # - root (full_target_path) is NOT in directories_to_process initially
            # - So it should be added via line 94
            
            result = manager.create_gitkeep_files(temp_dir)
            
            # Verify success
            assert result.success is True
            
            # The subdirectories should have gitkeep files
            assert os.path.exists(os.path.join(subdir1, ".gitkeep"))
            assert os.path.exists(os.path.join(subdir2, ".gitkeep"))
            
            # The main target directory might also get a gitkeep if it's considered empty
            # after processing subdirectories

    def test_alternative_line_94_trigger(self):
        """
        Alternative approach to trigger line 94 using a different target directory.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PlaceholderFileManager()
            
            # Use different target directory
            target_path = "docs"  # This is in target_directories
            full_target_path = os.path.join(temp_dir, target_path)
            
            # Create target directory with only subdirectories
            os.makedirs(full_target_path, exist_ok=True)
            
            # Create nested subdirectory structure
            nested_path = os.path.join(full_target_path, "api", "reference")
            os.makedirs(nested_path, exist_ok=True)
            
            # Create another target directory to ensure directories_to_process has entries
            other_target = os.path.join(temp_dir, "src", "orchestrator")
            os.makedirs(other_target, exist_ok=True)
            
            result = manager.create_gitkeep_files(temp_dir)
            
            assert result.success is True
            
            # Verify gitkeep files were created
            assert os.path.exists(os.path.join(nested_path, ".gitkeep"))
            assert os.path.exists(os.path.join(other_target, ".gitkeep"))

    def test_complex_directory_walk_scenario(self):
        """
        Create a complex scenario that walks through directories in a way
        that can trigger the line 94 condition during os.walk().
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PlaceholderFileManager()
            
            # Create multiple target directories with different structures
            targets = [
                "src/orchestrator",
                "src/monitoring", 
                "src/analytics",
                "tests/unit",
                "docs"
            ]
            
            for target in targets:
                full_path = os.path.join(temp_dir, target)
                os.makedirs(full_path, exist_ok=True)
                
                # For some directories, create subdirectories but no files
                if target in ["src/monitoring", "docs"]:
                    subdir = os.path.join(full_path, "submodule")
                    os.makedirs(subdir, exist_ok=True)
                    
                    # Create deeper nesting in subdir
                    deep_subdir = os.path.join(subdir, "deep")
                    os.makedirs(deep_subdir, exist_ok=True)
            
            # This should create conditions where some directories have only
            # subdirectories, triggering the elif not files: branch and potentially line 94
            result = manager.create_gitkeep_files(temp_dir)
            
            assert result.success is True
            assert len(result.created_files) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])