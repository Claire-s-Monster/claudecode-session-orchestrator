"""Checkpoint Manager for State Recovery.

This module provides checkpoint creation and restoration functionality for the session
orchestrator, enabling recovery from failures.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import shutil
import subprocess  # nosec B404


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint."""

    checkpoint_id: str
    operation: str
    timestamp: datetime
    project_root: str
    git_ref: str | None
    file_count: int
    size_bytes: int
    description: str | None = None


class CheckpointManager:
    """Manages checkpoints for state recovery.

    This class provides functionality to create, store, and restore checkpoints of the
    session orchestrator state.
    """

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        """Initialize the CheckpointManager.

        Args:     checkpoint_dir: Directory to store checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def create_checkpoint(
        self,
        operation: str,
        project_root: str = ".",
        description: str | None = None,
    ) -> str:
        """Create a checkpoint of the current state.

        Args:     operation: Operation being performed     project_root: Root directory
        of the project     description: Optional description of the checkpoint

        Returns:     Checkpoint ID for reference
        """
        checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        checkpoint_path.mkdir(exist_ok=True)

        try:
            # Get git reference if available
            git_ref = self._get_git_ref(project_root)

            # Copy project files
            project_backup = checkpoint_path / "project"
            shutil.copytree(
                project_root,
                project_backup,
                ignore=shutil.ignore_patterns(".git"),
            )

            # Create metadata
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                operation=operation,
                timestamp=datetime.now(),
                project_root=project_root,
                git_ref=git_ref,
                file_count=sum(1 for _ in project_backup.rglob("*") if _.is_file()),
                size_bytes=sum(
                    f.stat().st_size for f in project_backup.rglob("*") if f.is_file()
                ),
                description=description,
            )

            # Save metadata
            metadata_file = checkpoint_path / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata.__dict__, f, default=str, indent=2)

            self.logger.info(
                f"Created checkpoint {checkpoint_id} for operation: {operation}",
            )
            return checkpoint_id

        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            if checkpoint_path.exists():
                shutil.rmtree(checkpoint_path)
            raise

    def restore_checkpoint(self, checkpoint_id: str, target_dir: str = ".") -> bool:
        """Restore a checkpoint.

        Args:     checkpoint_id: ID of checkpoint to restore     target_dir: Directory
        to restore to

        Returns:     True if restoration successful, False otherwise
        """
        checkpoint_path = self.checkpoint_dir / checkpoint_id

        if not checkpoint_path.exists():
            self.logger.error(f"Checkpoint {checkpoint_id} not found")
            return False

        try:
            # Load metadata
            metadata_file = checkpoint_path / "metadata.json"
            with open(metadata_file, encoding="utf-8") as f:
                json.load(f)

            # Restore project files
            project_backup = checkpoint_path / "project"
            target_path = Path(target_dir)

            # Backup current state first
            backup_name = (
                f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            current_backup = self.checkpoint_dir / backup_name
            if target_path.exists():
                shutil.copytree(target_path, current_backup)

            # Restore from checkpoint
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(project_backup, target_path)

            self.logger.info(f"Restored checkpoint {checkpoint_id} to {target_dir}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore checkpoint {checkpoint_id}: {e}")
            return False

    def list_checkpoints(self) -> list[CheckpointMetadata]:
        """List all available checkpoints.

        Returns:     List of checkpoint metadata
        """
        checkpoints = []

        try:
            for checkpoint_dir in self.checkpoint_dir.iterdir():
                if checkpoint_dir.is_dir():
                    metadata_file = checkpoint_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, encoding="utf-8") as f:
                                metadata_dict = json.load(f)

                            # Convert timestamp back to datetime
                            if isinstance(metadata_dict["timestamp"], str):
                                metadata_dict["timestamp"] = datetime.fromisoformat(
                                    metadata_dict["timestamp"],
                                )

                            checkpoints.append(CheckpointMetadata(**metadata_dict))
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to load metadata for {checkpoint_dir}: {e}",
                            )

        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {e}")

        return sorted(checkpoints, key=lambda c: c.timestamp, reverse=True)

    def cleanup_old_checkpoints(
        self,
        keep_count: int = 10,
        max_age_days: int = 30,
    ) -> int:
        """Clean up old checkpoints.

        Args:     keep_count: Number of most recent checkpoints to keep
        max_age_days: Maximum age of checkpoints to keep

        Returns:     Number of checkpoints removed
        """
        checkpoints = self.list_checkpoints()
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0

        try:
            # Remove old checkpoints beyond keep_count and max_age
            for i, checkpoint in enumerate(checkpoints):
                should_remove = i >= keep_count or checkpoint.timestamp < cutoff_date

                if should_remove:
                    checkpoint_path = self.checkpoint_dir / checkpoint.checkpoint_id
                    if checkpoint_path.exists():
                        shutil.rmtree(checkpoint_path)
                        removed_count += 1
                        self.logger.info(
                            f"Removed old checkpoint: {checkpoint.checkpoint_id}",
                        )

        except Exception as e:
            self.logger.error(f"Failed to cleanup checkpoints: {e}")

        return removed_count

    def _get_git_ref(self, project_root: str) -> str | None:
        """Get current git reference.

        Args:     project_root: Root directory of the project

        Returns:     Git reference string or None if not available
        """
        try:
            result = subprocess.run(  # nosec B603,B607
                ["git", "rev-parse", "HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def get_checkpoint_info(self, checkpoint_id: str) -> CheckpointMetadata | None:
        """Get information about a specific checkpoint.

        Args:     checkpoint_id: ID of the checkpoint

        Returns:     Checkpoint metadata or None if not found
        """
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        metadata_file = checkpoint_path / "metadata.json"

        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, encoding="utf-8") as f:
                metadata_dict = json.load(f)

            # Convert timestamp back to datetime
            if isinstance(metadata_dict["timestamp"], str):
                metadata_dict["timestamp"] = datetime.fromisoformat(
                    metadata_dict["timestamp"],
                )

            return CheckpointMetadata(**metadata_dict)
        except Exception as e:
            self.logger.error(
                f"Failed to load checkpoint info for {checkpoint_id}: {e}",
            )
            return None
