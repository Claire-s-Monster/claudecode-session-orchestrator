"""
Error Recovery System for ClaudeCode Session Orchestrator

This module provides comprehensive error handling and recovery capabilities
for sub-agent operations, ensuring system resilience, state preservation,
and clear recovery pathways.
"""

from .error_recovery_manager import ErrorRecoveryManager
from .handlers.mcp_handler import MCPErrorHandler
from .handlers.context_handler import ContextTransferHandler
from .handlers.quality_handler import QualityGateHandler
from .handlers.system_handler import SystemErrorHandler
from .strategies.fallback import FallbackStrategy
from .strategies.graceful_degradation import GracefulDegradationStrategy
from .state.checkpoint_manager import CheckpointManager
from .state.state_preservation import StatePreservationManager

__all__ = [
    'ErrorRecoveryManager',
    'MCPErrorHandler',
    'ContextTransferHandler', 
    'QualityGateHandler',
    'SystemErrorHandler',
    'FallbackStrategy',
    'GracefulDegradationStrategy',
    'CheckpointManager',
    'StatePreservationManager'
]