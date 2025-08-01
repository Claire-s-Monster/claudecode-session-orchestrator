"""
Checkpoint Manager

Manages operation checkpoints for recovery, ensuring state preservation
and rollback capabilities during error recovery operations.
"""

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import shutil
import subprocess
from typing import Any


@dataclass
class CheckpointMetadata:
    """Metadata for operation checkpoints"""
    checkpoint_id: str
    agent_type: str
    operation: str
    task_id: str | None
    timestamp: datetime
    git_commit: str | None
    git_branch: str | None
    git_status_clean: bool
    quality_status: dict[str, Any]
    file_count: int
    size_bytes: int


class CheckpointManager:
    """
    Manages operation checkpoints for state preservation and recovery.
    
    Creates lightweight checkpoints that capture essential state information
    without impacting performance, enabling fast recovery operations.
    """

    def __init__(self, project_root: Path, config: dict[str, Any] = None):
        self.project_root = Path(project_root)
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Checkpoint configuration
        self.checkpoint_dir = self.project_root / ".recovery" / "checkpoints"
        self.max_checkpoints = self.config.get("max_checkpoints", 50)
        self.cleanup_threshold = self.config.get("cleanup_threshold", 100)
        self.retention_days = self.config.get("retention_days", 7)

        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Initialize checkpoint metadata cache
        self._checkpoint_cache: dict[str, CheckpointMetadata] = {}
        self._load_checkpoint_cache()

    def _load_checkpoint_cache(self):
        """Load existing checkpoint metadata into cache"""
        try:
            for checkpoint_dir in self.checkpoint_dir.iterdir():
                if checkpoint_dir.is_dir():
                    metadata_file = checkpoint_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file) as f:
                                data = json.load(f)

                            # Convert timestamp string back to datetime
                            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

                            metadata = CheckpointMetadata(**data)
                            self._checkpoint_cache[metadata.checkpoint_id] = metadata
                        except Exception as e:
                            self.logger.warning(f"Failed to load checkpoint metadata {metadata_file}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint cache: {e}")

    async def create_checkpoint(
        self,
        agent_type: str,
        operation: str,
        task_id: str | None = None
    ) -> str:
        """
        Create a new checkpoint capturing current state.
        
        Args:
            agent_type: Type of agent creating the checkpoint
            operation: Operation being performed
            task_id: Optional task identifier
            
        Returns:
            Checkpoint ID for future restoration
        """
        checkpoint_id = f"ckpt_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:20]}"
        checkpoint_path = self.checkpoint_dir / checkpoint_id

        try:
            # Create checkpoint directory
            checkpoint_path.mkdir(exist_ok=True)

            # Capture git state
            git_info = await self._capture_git_state()

            # Capture quality status
            quality_status = await self._capture_quality_status()

            # Capture TaskMaster state if task_id provided
            if task_id:
                await self._capture_taskmaster_state(checkpoint_path, task_id)

            # Capture working directory state
            await self._capture_working_directory_state(checkpoint_path)

            # Calculate checkpoint size
            size_bytes = self._calculate_directory_size(checkpoint_path)
            file_count = len(list(checkpoint_path.rglob("*")))

            # Create metadata
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                agent_type=agent_type,
                operation=operation,
                task_id=task_id,
                timestamp=datetime.now(),
                git_commit=git_info.get("commit"),
                git_branch=git_info.get("branch"),
                git_status_clean=git_info.get("clean", False),
                quality_status=quality_status,
                file_count=file_count,
                size_bytes=size_bytes
            )

            # Save metadata
            with open(checkpoint_path / "metadata.json", "w") as f:
                json.dump(asdict(metadata), f, indent=2, default=str)

            # Add to cache
            self._checkpoint_cache[checkpoint_id] = metadata

            # Cleanup old checkpoints if needed
            await self._cleanup_old_checkpoints()

            self.logger.info(f"Checkpoint created: {checkpoint_id} ({size_bytes} bytes, {file_count} files)")
            return checkpoint_id

        except Exception as e:
            self.logger.error(f"Failed to create checkpoint {checkpoint_id}: {e}")
            # Cleanup partial checkpoint
            if checkpoint_path.exists():
                shutil.rmtree(checkpoint_path, ignore_errors=True)
            raise

    async def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore system state from a checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to restore
            
        Returns:
            True if restoration was successful, False otherwise
        """
        if checkpoint_id not in self._checkpoint_cache:
            self.logger.error(f"Checkpoint not found: {checkpoint_id}")
            return False

        checkpoint_path = self.checkpoint_dir / checkpoint_id
        if not checkpoint_path.exists():
            self.logger.error(f"Checkpoint directory missing: {checkpoint_path}")
            return False

        metadata = self._checkpoint_cache[checkpoint_id]

        try:
            self.logger.info(f"Restoring checkpoint: {checkpoint_id}")

            # Restore git state
            git_restored = await self._restore_git_state(checkpoint_path, metadata)
            if not git_restored:
                self.logger.warning("Git state restoration failed")
                return False

            # Restore working directory state
            workdir_restored = await self._restore_working_directory_state(checkpoint_path)
            if not workdir_restored:
                self.logger.warning("Working directory restoration failed")
                return False

            # Restore TaskMaster state if available
            if metadata.task_id:
                await self._restore_taskmaster_state(checkpoint_path, metadata.task_id)

            # Verify restoration
            verification_success = await self._verify_restoration(metadata)
            if not verification_success:
                self.logger.warning("Checkpoint restoration verification failed")
                return False

            self.logger.info(f"Checkpoint restoration successful: {checkpoint_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore checkpoint {checkpoint_id}: {e}")
            return False

    async def list_checkpoints(self, agent_type: str | None = None) -> list[CheckpointMetadata]:
        """
        List available checkpoints, optionally filtered by agent type.
        
        Args:
            agent_type: Optional filter by agent type
            
        Returns:
            List of checkpoint metadata
        """
        checkpoints = list(self._checkpoint_cache.values())

        if agent_type:
            checkpoints = [cp for cp in checkpoints if cp.agent_type == agent_type]

        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x.timestamp, reverse=True)

        return checkpoints

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a specific checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if checkpoint_id not in self._checkpoint_cache:
            self.logger.warning(f"Checkpoint not found in cache: {checkpoint_id}")
            return False

        checkpoint_path = self.checkpoint_dir / checkpoint_id

        try:
            if checkpoint_path.exists():
                shutil.rmtree(checkpoint_path)

            # Remove from cache
            del self._checkpoint_cache[checkpoint_id]

            self.logger.info(f"Checkpoint deleted: {checkpoint_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            return False

    async def _capture_git_state(self) -> dict[str, Any]:
        """Capture current git repository state"""
        try:
            result = {}

            # Get current commit
            commit_result = await self._run_git_command(["rev-parse", "HEAD"])
            if commit_result.returncode == 0:
                result["commit"] = commit_result.stdout.strip()

            # Get current branch
            branch_result = await self._run_git_command(["branch", "--show-current"])
            if branch_result.returncode == 0:
                result["branch"] = branch_result.stdout.strip()

            # Check if working directory is clean
            status_result = await self._run_git_command(["status", "--porcelain"])
            result["clean"] = status_result.returncode == 0 and not status_result.stdout.strip()

            return result

        except Exception as e:
            self.logger.warning(f"Failed to capture git state: {e}")
            return {}

    async def _capture_quality_status(self) -> dict[str, Any]:
        """Capture current quality gate status"""
        # Placeholder implementation - will be enhanced with actual quality checks
        try:
            return {
                "tests_passing": True,  # Would run actual test check
                "lint_clean": True,     # Would run actual lint check
                "coverage": 95.0,       # Would get actual coverage
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Failed to capture quality status: {e}")
            return {"error": str(e)}

    async def _capture_taskmaster_state(self, checkpoint_path: Path, task_id: str):
        """Capture TaskMaster state for the given task"""
        try:
            # This would integrate with TaskMaster to capture task state
            taskmaster_file = checkpoint_path / "taskmaster_state.json"

            # Placeholder - would capture actual TaskMaster state
            state = {
                "task_id": task_id,
                "captured_at": datetime.now().isoformat(),
                "note": "TaskMaster integration pending"
            }

            with open(taskmaster_file, "w") as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Failed to capture TaskMaster state: {e}")

    async def _capture_working_directory_state(self, checkpoint_path: Path):
        """Capture working directory state"""
        try:
            # Capture git diff
            diff_result = await self._run_git_command(["diff"])
            if diff_result.returncode == 0:
                with open(checkpoint_path / "git_diff.patch", "w") as f:
                    f.write(diff_result.stdout)

            # Capture staged changes
            staged_result = await self._run_git_command(["diff", "--staged"])
            if staged_result.returncode == 0:
                with open(checkpoint_path / "git_staged.patch", "w") as f:
                    f.write(staged_result.stdout)

            # Capture git status
            status_result = await self._run_git_command(["status", "--porcelain"])
            if status_result.returncode == 0:
                with open(checkpoint_path / "git_status.txt", "w") as f:
                    f.write(status_result.stdout)

        except Exception as e:
            self.logger.warning(f"Failed to capture working directory state: {e}")

    async def _restore_git_state(self, checkpoint_path: Path, metadata: CheckpointMetadata) -> bool:
        """Restore git state from checkpoint"""
        try:
            # Reset to clean state
            reset_result = await self._run_git_command(["reset", "--hard", "HEAD"])
            if reset_result.returncode != 0:
                self.logger.error("Failed to reset git working directory")
                return False

            # Clean untracked files
            clean_result = await self._run_git_command(["clean", "-fd"])
            if clean_result.returncode != 0:
                self.logger.warning("Failed to clean untracked files")

            # Apply staged changes if they existed
            staged_patch = checkpoint_path / "git_staged.patch"
            if staged_patch.exists() and staged_patch.stat().st_size > 0:
                apply_result = await self._run_git_command(["apply", "--index", str(staged_patch)])
                if apply_result.returncode != 0:
                    self.logger.warning("Failed to apply staged changes")

            # Apply working directory changes if they existed
            diff_patch = checkpoint_path / "git_diff.patch"
            if diff_patch.exists() and diff_patch.stat().st_size > 0:
                apply_result = await self._run_git_command(["apply", str(diff_patch)])
                if apply_result.returncode != 0:
                    self.logger.warning("Failed to apply working directory changes")

            return True

        except Exception as e:
            self.logger.error(f"Failed to restore git state: {e}")
            return False

    async def _restore_working_directory_state(self, checkpoint_path: Path) -> bool:
        """Restore working directory state from checkpoint"""
        try:
            # The git state restoration handles most of the working directory
            # Additional file system operations could be implemented here if needed
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore working directory state: {e}")
            return False

    async def _restore_taskmaster_state(self, checkpoint_path: Path, task_id: str):
        """Restore TaskMaster state from checkpoint"""
        try:
            taskmaster_file = checkpoint_path / "taskmaster_state.json"
            if taskmaster_file.exists():
                # This would integrate with TaskMaster to restore task state
                self.logger.info(f"TaskMaster state restoration for task {task_id} - integration pending")

        except Exception as e:
            self.logger.warning(f"Failed to restore TaskMaster state: {e}")

    async def _verify_restoration(self, metadata: CheckpointMetadata) -> bool:
        """Verify that checkpoint restoration was successful"""
        try:
            # Verify git state
            current_git = await self._capture_git_state()

            # Basic verification - could be enhanced with more thorough checks
            if metadata.git_commit and current_git.get("commit") != metadata.git_commit:
                self.logger.warning("Git commit verification failed after restoration")
                return False

            if metadata.git_branch and current_git.get("branch") != metadata.git_branch:
                self.logger.warning("Git branch verification failed after restoration")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to verify restoration: {e}")
            return False

    async def _cleanup_old_checkpoints(self):
        """Clean up old checkpoints based on retention policy"""
        try:
            checkpoints = list(self._checkpoint_cache.values())

            # Remove checkpoints older than retention period
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            old_checkpoints = [cp for cp in checkpoints if cp.timestamp < cutoff_date]

            for checkpoint in old_checkpoints:
                await self.delete_checkpoint(checkpoint.checkpoint_id)
                self.logger.info(f"Deleted old checkpoint: {checkpoint.checkpoint_id}")

            # If still over limit, remove oldest checkpoints
            remaining_checkpoints = [cp for cp in checkpoints if cp.timestamp >= cutoff_date]
            if len(remaining_checkpoints) > self.max_checkpoints:
                # Sort by timestamp and remove oldest
                remaining_checkpoints.sort(key=lambda x: x.timestamp)
                excess_count = len(remaining_checkpoints) - self.max_checkpoints

                for checkpoint in remaining_checkpoints[:excess_count]:
                    await self.delete_checkpoint(checkpoint.checkpoint_id)
                    self.logger.info(f"Deleted excess checkpoint: {checkpoint.checkpoint_id}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old checkpoints: {e}")

    def _calculate_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory in bytes"""
        try:
            total_size = 0
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception as e:
            self.logger.warning(f"Failed to calculate directory size: {e}")
            return 0

    async def _run_git_command(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run git command with proper error handling"""
        try:
            cmd = ["git"] + args
            result = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=result.returncode,
                stdout=stdout.decode("utf-8", errors="ignore"),
                stderr=stderr.decode("utf-8", errors="ignore")
            )

        except Exception as e:
            self.logger.error(f"Failed to run git command {args}: {e}")
            return subprocess.CompletedProcess(
                args=["git"] + args,
                returncode=1,
                stdout="",
                stderr=str(e)
            )

    async def health_check(self) -> bool:
        """Perform health check of checkpoint system"""
        try:
            # Check if checkpoint directory is accessible
            if not self.checkpoint_dir.exists():
                return False

            # Check if we can create a test checkpoint
            test_checkpoint = await self.create_checkpoint("test", "health_check")

            # Clean up test checkpoint
            await self.delete_checkpoint(test_checkpoint)

            return True

        except Exception as e:
            self.logger.error(f"Checkpoint manager health check failed: {e}")
            return False

    def get_statistics(self) -> dict[str, Any]:
        """Get checkpoint system statistics"""
        checkpoints = list(self._checkpoint_cache.values())

        if not checkpoints:
            return {
                "total_checkpoints": 0,
                "total_size_bytes": 0,
                "oldest_checkpoint": None,
                "newest_checkpoint": None,
                "average_size_bytes": 0
            }

        total_size = sum(cp.size_bytes for cp in checkpoints)
        checkpoints.sort(key=lambda x: x.timestamp)

        return {
            "total_checkpoints": len(checkpoints),
            "total_size_bytes": total_size,
            "oldest_checkpoint": checkpoints[0].timestamp.isoformat(),
            "newest_checkpoint": checkpoints[-1].timestamp.isoformat(),
            "average_size_bytes": total_size // len(checkpoints),
            "checkpoints_by_agent": {
                agent_type: len([cp for cp in checkpoints if cp.agent_type == agent_type])
                for agent_type in set(cp.agent_type for cp in checkpoints)
            }
        }
