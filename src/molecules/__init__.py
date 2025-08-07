"""
Molecules Package - Mid-level Components

This package contains molecule-level components following atomic design principles.
Molecules are combinations of atoms that function together as a unit.

Available modules:
- placeholder_file_manager: Manages creation of placeholder files in project directories
- component_registry: Thread-safe component registration and discovery system
"""

from .component_registry import (
    ComponentNotFoundError,
    ComponentRegistrationError,
    ComponentRegistry,
)
from .placeholder_file_manager import PlaceholderFileManager, PlaceholderResult

__all__ = [
    "PlaceholderFileManager",
    "PlaceholderResult",
    "ComponentRegistry",
    "ComponentRegistrationError",
    "ComponentNotFoundError",
]
