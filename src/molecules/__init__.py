"""
Molecules Package - Mid-level Components

This package contains molecule-level components following atomic design principles.
Molecules are combinations of atoms that function together as a unit.

Available modules:
- placeholder_file_manager: Manages creation of placeholder files in project directories
"""

from .placeholder_file_manager import PlaceholderFileManager, PlaceholderResult

__all__ = ["PlaceholderFileManager", "PlaceholderResult"]
