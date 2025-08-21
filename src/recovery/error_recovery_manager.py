"""Error Recovery Manager.

Central coordinator for error handling and recovery across all sub-agent operations.
Implements the four-level error classification framework and manages recovery workflows.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Any

# Note: Import handlers will be implemented as separate files
# from .handlers.mcp_handler import MCPErrorHandler
# from .handlers.context_handler import ContextTransferHandler
# from .handlers.quality_handler import QualityGateHandler
# from .handlers.system_handler import SystemErrorHandler
# from .strategies.fallback import FallbackStrategy
# from .strategies.graceful_degradation import GracefulDegradationStrategy
# from .state.checkpoint_manager import CheckpointManager
# from .state.state_preservation import StatePreservationManager


class ErrorSeverity(Enum):
    """Error severity levels based on framework classification."""

    LOW = "low"  # Tool failures - recoverable
    MEDIUM = "medium"  # Context transfer failures - manageable
    HIGH = "high"  # Quality gate failures - critical
    CRITICAL = "critical"  # System failures - emergency


class ErrorType(Enum):
    """Error types aligned with framework classification."""

    MCP_TOOL_FAILURE = "mcp_tool_failure"
    CONTEXT_TRANSFER_FAILURE = "context_transfer_failure"
    QUALITY_GATE_FAILURE = "quality_gate_failure"
    SYSTEM_FAILURE = "system_failure"
    FRAMEWORK_VIOLATION = "framework_violation"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error recovery."""

    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    timestamp: datetime
    agent_type: str
    operation: str
    error_message: str
    system_state: dict[str, Any]
    recovery_attempts: list[str]
    escalation_required: bool = False


@dataclass
class RecoveryResult:
    """Result of error recovery attempt."""

    success: bool
    recovery_method: str
    time_taken: float
    state_preserved: bool
    side_effects: list[str]
    recommendation: str | None = None


class ErrorRecoveryManager:
    """Central manager for error recovery and resilience.

    Provides comprehensive error handling with graceful degradation, state preservation,
    and systematic recovery workflows.
    """

    def __init__(self, project_root: Path, config: dict[str, Any] | None = None):
        """Initialize the error recovery manager.

        Args:
            project_root: Root directory of the project
            config: Optional configuration dictionary for recovery settings
        """
        self.project_root = Path(project_root)
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Recovery infrastructure - will be initialized when handlers are implemented
        # self.checkpoint_manager = CheckpointManager(project_root)
        # self.state_preservation = StatePreservationManager(project_root)
        # self.fallback_strategy = FallbackStrategy(self.config.get('fallback', {}))
        # self.degradation_strategy = GracefulDegradationStrategy(self.config.get('degradation', {}))

        # Error handlers - will be initialized when handlers are implemented
        # self.mcp_handler = MCPErrorHandler(project_root, self.config.get('mcp', {}))
        # self.context_handler = ContextTransferHandler(project_root, self.config.get('context', {}))
        # self.quality_handler = QualityGateHandler(project_root, self.config.get('quality', {}))
        # self.system_handler = SystemErrorHandler(project_root, self.config.get('system', {}))

        # Recovery state
        self.recovery_history: list[ErrorContext] = []
        self.active_recoveries: dict[str, ErrorContext] = {}
        self.emergency_mode = False

        # Performance tracking
        self.bash_usage_count = 0
        self.total_operations = 0
        self.recovery_stats = {
            "total_errors": 0,
            "successful_recoveries": 0,
            "escalations": 0,
            "emergency_stops": 0,
        }

        # Initialize recovery directories
        self._setup_recovery_infrastructure()

    def _setup_recovery_infrastructure(self) -> None:
        """Initialize recovery directory structure and logging."""
        recovery_dir = self.project_root / ".recovery"
        recovery_dir.mkdir(exist_ok=True)

        (recovery_dir / "checkpoints").mkdir(exist_ok=True)
        (recovery_dir / "backups").mkdir(exist_ok=True)
        (recovery_dir / "error_reports").mkdir(exist_ok=True)
        (recovery_dir / "state_snapshots").mkdir(exist_ok=True)

        # Initialize emergency recovery scripts
        scripts_dir = self.project_root / "scripts" / "emergency-recovery"
        scripts_dir.mkdir(parents=True, exist_ok=True)

    async def handle_error(
        self,
        error_type: ErrorType,
        agent_type: str,
        operation: str,
        error_message: str,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> RecoveryResult:
        """Handle error and attempt recovery.

        Args:     error_type: Type of error encountered     agent_type: Sub-agent that
        encountered the error     operation: Operation being performed when error
        occurred     error_message: Detailed error message     context: Additional
        context information

        Returns:     RecoveryResult with recovery outcome and recommendations
        """
        error_id = f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.recovery_history)}"

        # Determine error severity
        severity = self._classify_error_severity(error_type, error_message)

        # Create error context
        error_ctx = ErrorContext(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            timestamp=datetime.now(),
            agent_type=agent_type,
            operation=operation,
            error_message=error_message,
            system_state=await self._capture_system_state(),
            recovery_attempts=[],
        )

        self.logger.error(
            f"Error detected: {error_id} - {error_type.value} in {agent_type}",
        )
        self.recovery_stats["total_errors"] += 1

        # Create checkpoint before recovery
        checkpoint_id = await self._create_checkpoint(
            agent_type,
            operation,
            error_ctx.error_id,
        )

        try:
            # Add to active recoveries
            self.active_recoveries[error_id] = error_ctx

            # Execute recovery based on severity
            recovery_result = await self._execute_recovery(error_ctx, checkpoint_id)

            # Update statistics
            if recovery_result.success:
                self.recovery_stats["successful_recoveries"] += 1
            else:
                self.recovery_stats["escalations"] += 1

            # Store recovery history
            self.recovery_history.append(error_ctx)

            # Generate error report
            await self._generate_error_report(error_ctx, recovery_result)

            return recovery_result

        except Exception as e:
            self.logger.critical(f"Recovery system failure: {e}")
            # Emergency fallback
            return await self._emergency_recovery(error_ctx, str(e))
        finally:
            # Clean up active recovery
            self.active_recoveries.pop(error_id, None)

    async def _execute_recovery(
        self,
        error_ctx: ErrorContext,
        checkpoint_id: str,
    ) -> RecoveryResult:
        """Execute recovery based on error type and severity."""
        start_time = datetime.now()

        try:
            # Basic recovery implementation (will be enhanced with handlers)
            if error_ctx.error_type == ErrorType.MCP_TOOL_FAILURE:
                result = await self._handle_mcp_error(error_ctx)
            elif error_ctx.error_type == ErrorType.CONTEXT_TRANSFER_FAILURE:
                result = await self._handle_context_error(error_ctx)
            elif error_ctx.error_type == ErrorType.QUALITY_GATE_FAILURE:
                result = await self._handle_quality_error(error_ctx)
            elif error_ctx.error_type == ErrorType.SYSTEM_FAILURE:
                result = await self._handle_system_error(error_ctx)
            else:
                # Unknown error - attempt graceful degradation
                result = await self._handle_unknown_error(error_ctx)

            # Check if escalation is needed
            if not result.success and error_ctx.severity in [
                ErrorSeverity.HIGH,
                ErrorSeverity.CRITICAL,
            ]:
                self.logger.warning(
                    f"Recovery failed for {error_ctx.severity.value} error - initiating escalation",
                )
                result = await self._escalate_error(error_ctx, checkpoint_id)

            return result

        except Exception as e:
            self.logger.error(f"Recovery execution failed: {e}")
            # Restore from checkpoint
            await self._restore_checkpoint(checkpoint_id)

            return RecoveryResult(
                success=False,
                recovery_method="checkpoint_restore",
                time_taken=(datetime.now() - start_time).total_seconds(),
                state_preserved=True,
                side_effects=["checkpoint_restoration"],
                recommendation="Manual intervention required - recovery system encountered internal error",
            )

    async def _handle_mcp_error(self, error_ctx: ErrorContext) -> RecoveryResult:
        """Handle MCP tool failures with strategic fallback."""
        self.logger.info(f"Handling MCP error: {error_ctx.error_id}")

        # Check strategic Bash allowance (5% target)
        bash_ratio = self._calculate_bash_usage_ratio()

        if bash_ratio < 5.0:
            # Attempt strategic Bash fallback
            self.bash_usage_count += 1
            self.total_operations += 1

            return RecoveryResult(
                success=True,
                recovery_method="strategic_bash_fallback",
                time_taken=0.1,
                state_preserved=True,
                side_effects=["bash_usage_incremented"],
                recommendation="MCP limitation bypassed with strategic Bash usage",
            )
        # Escalate to main context
        return RecoveryResult(
            success=False,
            recovery_method="mcp_fallback_limit_exceeded",
            time_taken=0.0,
            state_preserved=True,
            side_effects=["escalation_required"],
            recommendation="Strategic Bash limit exceeded - escalate to main context",
        )

    async def _handle_context_error(self, error_ctx: ErrorContext) -> RecoveryResult:
        """Handle context transfer failures with compression."""
        self.logger.info(f"Handling context error: {error_ctx.error_id}")

        # Attempt progressive compression
        compression_levels = ["selective", "aggressive", "minimal"]

        for level in compression_levels:
            if await self._attempt_context_compression(level):
                return RecoveryResult(
                    success=True,
                    recovery_method=f"context_compression_{level}",
                    time_taken=0.2,
                    state_preserved=True,
                    side_effects=[f"context_compressed_{level}"],
                    recommendation=f"Context transfer successful with {level} compression",
                )

        # All compression attempts failed
        return RecoveryResult(
            success=False,
            recovery_method="context_compression_failed",
            time_taken=0.5,
            state_preserved=True,
            side_effects=["compression_attempts_exhausted"],
            recommendation="Context transfer failed - manual intervention required",
        )

    async def _handle_quality_error(self, error_ctx: ErrorContext) -> RecoveryResult:
        """Handle quality gate failures with emergency fixes."""
        self.logger.info(f"Handling quality error: {error_ctx.error_id}")

        # Attempt emergency quality fixes
        fix_success = await self._attempt_emergency_quality_fixes()

        if fix_success:
            return RecoveryResult(
                success=True,
                recovery_method="emergency_quality_fixes",
                time_taken=1.0,
                state_preserved=True,
                side_effects=["automatic_fixes_applied"],
                recommendation="Quality gates restored with emergency fixes",
            )
        return RecoveryResult(
            success=False,
            recovery_method="quality_fixes_failed",
            time_taken=1.0,
            state_preserved=True,
            side_effects=["quality_degradation"],
            recommendation="STOP: Quality gates failing - manual investigation required",
        )

    async def _handle_system_error(self, error_ctx: ErrorContext) -> RecoveryResult:
        """Handle system failures with emergency protocols."""
        self.logger.critical(f"Handling system error: {error_ctx.error_id}")

        # Activate emergency mode
        await self._activate_emergency_mode()

        # Attempt repository integrity check
        integrity_ok = await self._check_repository_integrity()

        if integrity_ok:
            return RecoveryResult(
                success=True,
                recovery_method="emergency_recovery",
                time_taken=2.0,
                state_preserved=True,
                side_effects=["emergency_mode_activated"],
                recommendation="System integrity verified - emergency mode active",
            )
        await self._emergency_stop()
        return RecoveryResult(
            success=False,
            recovery_method="system_halt",
            time_taken=0.0,
            state_preserved=False,
            side_effects=["system_halt"],
            recommendation="CRITICAL: System integrity compromised - manual recovery required",
        )

    async def _handle_unknown_error(self, error_ctx: ErrorContext) -> RecoveryResult:
        """Handle unknown errors with graceful degradation."""
        self.logger.warning(f"Handling unknown error: {error_ctx.error_id}")

        return RecoveryResult(
            success=False,
            recovery_method="graceful_degradation",
            time_taken=0.1,
            state_preserved=True,
            side_effects=["unknown_error_logged"],
            recommendation="Unknown error encountered - investigate and categorize",
        )

    async def _escalate_error(
        self,
        error_ctx: ErrorContext,
        checkpoint_id: str,
    ) -> RecoveryResult:
        """Escalate error to higher-level recovery mechanisms."""
        self.logger.warning(f"Escalating error {error_ctx.error_id}")

        if error_ctx.severity == ErrorSeverity.CRITICAL:
            # Emergency protocols
            await self._activate_emergency_mode()

            # Attempt emergency recovery
            emergency_success = await self._attempt_emergency_recovery(error_ctx)

            if not emergency_success:
                # Complete system halt
                await self._emergency_stop()
                return RecoveryResult(
                    success=False,
                    recovery_method="emergency_stop",
                    time_taken=0,
                    state_preserved=True,
                    side_effects=["system_halt"],
                    recommendation="CRITICAL: Manual intervention required - system integrity compromised",
                )

            return RecoveryResult(
                success=True,
                recovery_method="emergency_escalation",
                time_taken=1.0,
                state_preserved=True,
                side_effects=["emergency_mode"],
                recommendation="Emergency recovery successful - monitor system closely",
            )

        # High severity - systematic recovery
        return await self._systematic_recovery(error_ctx, checkpoint_id)

    async def _systematic_recovery(
        self,
        error_ctx: ErrorContext,
        checkpoint_id: str,
    ) -> RecoveryResult:
        """Systematic recovery for high-severity errors."""
        self.logger.info(f"Initiating systematic recovery for {error_ctx.error_id}")

        # Step 1: Preserve current state
        await self._create_state_snapshot(f"pre_recovery_{error_ctx.error_id}")

        # Step 2: Restore to clean state
        restore_success = await self._restore_checkpoint(checkpoint_id)

        if not restore_success:
            return RecoveryResult(
                success=False,
                recovery_method="systematic_recovery_failed",
                time_taken=0,
                state_preserved=False,
                side_effects=["state_corruption"],
                recommendation="CRITICAL: Unable to restore to clean state - manual recovery required",
            )

        # Step 3: Re-run quality validation
        quality_status = await self._validate_system_quality()

        if not quality_status:
            return RecoveryResult(
                success=False,
                recovery_method="quality_validation_failed",
                time_taken=0,
                state_preserved=True,
                side_effects=["quality_degradation"],
                recommendation="Quality gates failing after recovery - investigate root cause",
            )

        return RecoveryResult(
            success=True,
            recovery_method="systematic_recovery",
            time_taken=0,
            state_preserved=True,
            side_effects=["state_restoration"],
            recommendation="Systematic recovery successful - monitor for recurring issues",
        )

    async def _emergency_recovery(
        self,
        error_ctx: ErrorContext,
        system_error: str,
    ) -> RecoveryResult:
        """Emergency recovery when recovery system itself fails."""
        self.logger.critical(
            f"EMERGENCY RECOVERY: {error_ctx.error_id} - {system_error}",
        )

        # Activate emergency mode
        await self._activate_emergency_mode()

        return RecoveryResult(
            success=False,
            recovery_method="emergency_fallback",
            time_taken=0,
            state_preserved=False,
            side_effects=["emergency_mode", "recovery_system_failure"],
            recommendation="EMERGENCY: Recovery system failure - immediate manual intervention required",
        )

    async def _activate_emergency_mode(self) -> None:
        """Activate emergency mode with minimal operations."""
        self.emergency_mode = True
        self.logger.critical("EMERGENCY MODE ACTIVATED")

        # Create emergency backup
        await self._create_emergency_backup()

        # Disable non-essential operations
        await self._disable_non_essential_operations()

    async def _emergency_stop(self) -> None:
        """Complete system halt for critical failures."""
        self.logger.critical("EMERGENCY STOP - SYSTEM HALT")
        self.recovery_stats["emergency_stops"] += 1

        # Create final state backup
        await self._create_emergency_backup("final_state")

        # Stop all active operations
        for error_id in list(self.active_recoveries.keys()):
            self.active_recoveries.pop(error_id)

    # Placeholder methods that will be enhanced with proper implementations

    async def _create_checkpoint(
        self,
        agent_type: str,
        operation: str,  # noqa: ARG002
        error_id: str,  # noqa: ARG002
    ) -> str:
        """Create operation checkpoint for recovery."""
        checkpoint_id = f"ckpt_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"Creating checkpoint: {checkpoint_id}")
        return checkpoint_id

    async def _restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore from checkpoint."""
        self.logger.info(f"Restoring from checkpoint: {checkpoint_id}")
        return True  # Placeholder

    async def _create_state_snapshot(self, snapshot_id: str) -> None:
        """Create state snapshot."""
        self.logger.info(f"Creating state snapshot: {snapshot_id}")

    async def _create_emergency_backup(self, backup_type: str = "emergency") -> None:
        """Create emergency backup of current state."""
        try:
            backup_id = f"{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"Emergency backup created: {backup_id}")
        except Exception as e:
            self.logger.error(f"Failed to create emergency backup: {e}")

    async def _disable_non_essential_operations(self) -> None:
        """Disable non-essential operations during emergency mode."""
        self.logger.info("Non-essential operations disabled")

    async def _attempt_context_compression(self, level: str) -> bool:
        """Attempt context compression at specified level."""
        self.logger.info(f"Attempting {level} context compression")
        return True  # Placeholder - will be implemented with actual compression logic

    async def _attempt_emergency_quality_fixes(self) -> bool:
        """Attempt automated quality fixes."""
        self.logger.info("Attempting emergency quality fixes")
        return True  # Placeholder - will be implemented with actual fix logic

    async def _check_repository_integrity(self) -> bool:
        """Check repository integrity."""
        self.logger.info("Checking repository integrity")
        return True  # Placeholder - will be implemented with git fsck and validation

    async def _attempt_emergency_recovery(self, error_ctx: ErrorContext) -> bool:
        """Attempt emergency recovery for critical errors."""
        self.logger.info(f"Attempting emergency recovery for {error_ctx.error_id}")
        return True  # Placeholder

    def _classify_error_severity(
        self,
        error_type: ErrorType,
        error_message: str,
    ) -> ErrorSeverity:
        """Classify error severity based on type and message content."""
        if error_type == ErrorType.SYSTEM_FAILURE:
            return ErrorSeverity.CRITICAL
        if error_type == ErrorType.QUALITY_GATE_FAILURE:
            return ErrorSeverity.HIGH
        if error_type == ErrorType.CONTEXT_TRANSFER_FAILURE:
            return ErrorSeverity.MEDIUM
        if error_type == ErrorType.MCP_TOOL_FAILURE:
            return ErrorSeverity.LOW
        # Analyze error message for severity indicators
        critical_keywords = ["corruption", "integrity", "security", "critical"]
        high_keywords = ["failure", "violation", "error"]

        error_lower = error_message.lower()

        if any(keyword in error_lower for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL
        if any(keyword in error_lower for keyword in high_keywords):
            return ErrorSeverity.HIGH
        return ErrorSeverity.MEDIUM

    async def _capture_system_state(self) -> dict[str, Any]:
        """Capture current system state for error context."""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "emergency_mode": self.emergency_mode,
                "active_recoveries": len(self.active_recoveries),
                "bash_usage_ratio": self._calculate_bash_usage_ratio(),
                "recovery_stats": self.recovery_stats.copy(),
                "quality_status": await self._get_quality_status(),
                "git_status": await self._get_git_status(),
            }
        except Exception as e:
            self.logger.warning(f"Failed to capture complete system state: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _calculate_bash_usage_ratio(self) -> float:
        """Calculate current bash usage ratio for MCP compliance."""
        if self.total_operations == 0:
            return 0.0
        return (self.bash_usage_count / self.total_operations) * 100

    async def _get_quality_status(self) -> dict[str, Any]:
        """Get current quality gate status."""
        return {
            "tests_passing": True,  # Placeholder
            "lint_clean": True,  # Placeholder
            "coverage": 95.0,  # Placeholder
        }

    async def _get_git_status(self) -> dict[str, Any]:
        """Get current git repository status."""
        return {
            "clean": True,  # Placeholder
            "branch": "main",  # Placeholder
            "commits_ahead": 0,  # Placeholder
        }

    async def _validate_system_quality(self) -> bool:
        """Validate system quality after recovery."""
        try:
            quality_status = await self._get_quality_status()
            return all(
                [
                    quality_status.get("tests_passing", False),
                    quality_status.get("lint_clean", False),
                    quality_status.get("coverage", 0) >= 90,
                ],
            )
        except Exception as e:
            self.logger.error(f"Quality validation failed: {e}")
            return False

    async def _generate_error_report(
        self,
        error_ctx: ErrorContext,
        recovery_result: RecoveryResult,
    ) -> None:
        """Generate comprehensive error report."""
        report = {
            "error_context": asdict(error_ctx),
            "recovery_result": asdict(recovery_result),
            "system_recommendations": self._generate_recommendations(
                error_ctx,
                recovery_result,
            ),
            "generated_at": datetime.now().isoformat(),
        }

        report_file = (
            self.project_root
            / ".recovery"
            / "error_reports"
            / f"error_report_{error_ctx.error_id}.json"
        )

        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Error report generated: {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to generate error report: {e}")

    def _generate_recommendations(
        self,
        error_ctx: ErrorContext,
        recovery_result: RecoveryResult,
    ) -> list[str]:
        """Generate system recommendations based on error and recovery."""
        recommendations = []

        if error_ctx.error_type == ErrorType.MCP_TOOL_FAILURE:
            recommendations.append(
                "Consider documenting MCP limitation for future improvement",
            )
            recommendations.append(
                "Review strategic Bash usage to ensure 5% compliance",
            )

        if error_ctx.severity == ErrorSeverity.HIGH:
            recommendations.append("Investigate root cause to prevent recurrence")
            recommendations.append(
                "Consider implementing additional preventive measures",
            )

        if not recovery_result.success:
            recommendations.append("Manual intervention required")
            recommendations.append("Review error patterns for systematic improvements")

        return recommendations

    def get_recovery_statistics(self) -> dict[str, Any]:
        """Get comprehensive recovery statistics."""
        return {
            "recovery_stats": self.recovery_stats.copy(),
            "bash_usage_ratio": self._calculate_bash_usage_ratio(),
            "emergency_mode": self.emergency_mode,
            "active_recoveries": len(self.active_recoveries),
            "recovery_history_count": len(self.recovery_history),
            "recent_errors": [
                {
                    "error_id": ctx.error_id,
                    "type": ctx.error_type.value,
                    "severity": ctx.severity.value,
                    "timestamp": ctx.timestamp.isoformat(),
                }
                for ctx in self.recovery_history[-10:]  # Last 10 errors
            ],
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check of recovery system."""
        return {
            "recovery_system_healthy": not self.emergency_mode,
            "error_handlers_ready": True,  # Will be enhanced with actual handler checks
            "statistics": self.get_recovery_statistics(),
        }
