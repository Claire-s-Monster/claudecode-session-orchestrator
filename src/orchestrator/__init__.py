"""Session orchestration and management module.

This module provides real-time monitoring, analysis, and optimization
of ClaudeCode sessions through live behavioral observation.
"""

from .session_manager import SessionConfig, SessionManager

__all__ = [
    "SessionConfig",
    "SessionManager",
]
