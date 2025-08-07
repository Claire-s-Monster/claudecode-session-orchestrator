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


class CheckpointError(Exception):
    """Raised when checkpoint operations fail."""


class CheckpointManager:
    """
    Manages operation checkpoints for recovery.

    Provides atomic checkpoint creation, restoration, and cleanup
    with comprehensive metadata tracking and error handling.
    """

    def __init__(self, project_root: Path, checkpoint_dir: Path | None = None):
        self.project_root = Path(project_root).resolve()
        self.checkpoint_dir = checkpoint_dir or (self.project_root / ".checkpoints")
        self.logger = logging.getLogger(__name__)

        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Maximum number of checkpoints to keep
        self.max_checkpoints = 10
        # Maximum age for checkpoints (days)
        self.max_age_days = 30

    async def create_checkpoint(
        self, checkpoint_id: str, operation: str, description: str | None = None
    ) -> CheckpointMetadata:
        """
        Create a checkpoint of the current project state.

        Args:
            checkpoint_id: Unique identifier for the checkpoint
            operation: Operation being performed (for tracking)
            description: Optional description of the checkpoint

        Returns:
            CheckpointMetadata for the created checkpoint

        Raises:
            CheckpointError: If checkpoint creation fails
        """
        try:
            checkpoint_path = self.checkpoint_dir / checkpoint_id
            if checkpoint_path.exists():
                raise CheckpointError(f"Checkpoint {checkpoint_id} already exists")

            self.logger.info(
                f"Creating checkpoint {checkpoint_id} for operation: {operation}"
            )

            # Create checkpoint directory
            checkpoint_path.mkdir(parents=True, exist_ok=True)

            # Get current git ref if in git repository
            git_ref = await self._get_current_git_ref()

            # Create snapshot of project files
            await self._create_file_snapshot(checkpoint_path)

            # Calculate metadata
            file_count = await self._count_files(checkpoint_path)
            size_bytes = await self._calculate_size(checkpoint_path)

            # Create metadata
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                operation=operation,
                timestamp=datetime.now(),
                project_root=str(self.project_root),
                git_ref=git_ref,
                file_count=file_count,
                size_bytes=size_bytes,
                description=description,
            )

            # Save metadata
            metadata_file = checkpoint_path / "metadata.json"
            with open(metadata_file, "w") as f:
                # Convert dataclass to dict for JSON serialization
                metadata_dict = asdict(metadata)
                metadata_dict["timestamp"] = metadata.timestamp.isoformat()
                json.dump(metadata_dict, f, indent=2)

            self.logger.info(
                f"Created checkpoint {checkpoint_id} with {file_count} files ({size_bytes} bytes)"
            )
            return metadata

        except Exception as e:
            # Cleanup partial checkpoint on failure
            checkpoint_path = self.checkpoint_dir / checkpoint_id
            if checkpoint_path.exists():
                shutil.rmtree(checkpoint_path, ignore_errors=True)
            raise CheckpointError(
                f"Failed to create checkpoint {checkpoint_id}: {e}"
            ) from e

    async def restore_checkpoint(self, checkpoint_id: str) -> CheckpointMetadata:
        """
        Restore project state from a checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint to restore

        Returns:
            CheckpointMetadata of the restored checkpoint

        Raises:
            CheckpointError: If restoration fails
        """
        try:
            checkpoint_path = self.checkpoint_dir / checkpoint_id
            if not checkpoint_path.exists():
                raise CheckpointError(f"Checkpoint {checkpoint_id} not found")

            self.logger.info(f"Restoring checkpoint {checkpoint_id}")

            # Load metadata
            metadata = await self.get_checkpoint_metadata(checkpoint_id)

            # Create backup of current state before restoration
            backup_id = f"pre_restore_{checkpoint_id}_{int(datetime.now().timestamp())}"
            await self.create_checkpoint(backup_id, "pre_restore_backup")

            # Restore files
            await self._restore_file_snapshot(checkpoint_path)

            # Restore git ref if available
            if metadata.git_ref:
                await self._restore_git_ref(metadata.git_ref)

            self.logger.info(f"Successfully restored checkpoint {checkpoint_id}")
            return metadata

        except Exception as e:
            raise CheckpointError(
                f"Failed to restore checkpoint {checkpoint_id}: {e}"
            ) from e

    async def get_checkpoint_metadata(self, checkpoint_id: str) -> CheckpointMetadata:
        """
        Get metadata for a checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint

        Returns:
            CheckpointMetadata for the checkpoint

        Raises:
            CheckpointError: If checkpoint not found or metadata invalid
        """
        try:
            checkpoint_path = self.checkpoint_dir / checkpoint_id
            metadata_file = checkpoint_path / "metadata.json"

            if not metadata_file.exists():
                raise CheckpointError(
                    f"Metadata not found for checkpoint {checkpoint_id}"
                )

            with open(metadata_file) as f:
                metadata_dict = json.load(f)

            # Parse timestamp
            metadata_dict["timestamp"] = datetime.fromisoformat(
                metadata_dict["timestamp"]
            )

            return CheckpointMetadata(**metadata_dict)

        except Exception as e:
            raise CheckpointError(
                f"Failed to load metadata for checkpoint {checkpoint_id}: {e}"
            ) from e

    async def list_checkpoints(self) -> list[CheckpointMetadata]:
        """
        List all available checkpoints.

        Returns:
            List of CheckpointMetadata sorted by timestamp (newest first)
        """
        checkpoints = []
        try:
            for checkpoint_path in self.checkpoint_dir.iterdir():
                if checkpoint_path.is_dir():
                    try:
                        metadata = await self.get_checkpoint_metadata(
                            checkpoint_path.name
                        )
                        checkpoints.append(metadata)
                    except CheckpointError:
                        # Skip invalid checkpoints
                        self.logger.warning(
                            f"Skipping invalid checkpoint: {checkpoint_path.name}"
                        )
                        continue

            # Sort by timestamp (newest first)
            checkpoints.sort(key=lambda x: x.timestamp, reverse=True)
            return checkpoints

        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def delete_checkpoint(self, checkpoint_id: str) -> None:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint to delete

        Raises:
            CheckpointError: If deletion fails
        """
        try:
            checkpoint_path = self.checkpoint_dir / checkpoint_id
            if not checkpoint_path.exists():
                raise CheckpointError(f"Checkpoint {checkpoint_id} not found")

            shutil.rmtree(checkpoint_path)
            self.logger.info(f"Deleted checkpoint {checkpoint_id}")

        except Exception as e:
            raise CheckpointError(
                f"Failed to delete checkpoint {checkpoint_id}: {e}"
            ) from e

    async def cleanup_old_checkpoints(self) -> int:
        """
        Clean up old checkpoints based on age and count limits.

        Returns:
            Number of checkpoints deleted
        """
        try:
            checkpoints = await self.list_checkpoints()
            deleted_count = 0

            # Delete checkpoints exceeding count limit
            if len(checkpoints) > self.max_checkpoints:
                excess_checkpoints = checkpoints[self.max_checkpoints :]
                for checkpoint in excess_checkpoints:
                    await self.delete_checkpoint(checkpoint.checkpoint_id)
                    deleted_count += 1
                    self.logger.info(
                        f"Deleted checkpoint {checkpoint.checkpoint_id} (count limit exceeded)"
                    )

            # Delete checkpoints exceeding age limit
            cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
            for checkpoint in checkpoints:
                if checkpoint.timestamp < cutoff_date:
                    try:
                        await self.delete_checkpoint(checkpoint.checkpoint_id)
                        deleted_count += 1
                        self.logger.info(
                            f"Deleted checkpoint {checkpoint.checkpoint_id} (age limit exceeded)"
                        )
                    except CheckpointError:
                        # Checkpoint might have been deleted already
                        pass

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old checkpoints")

            return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup checkpoints: {e}")
            return 0

    async def _create_file_snapshot(self, checkpoint_path: Path) -> None:
        """Create snapshot of project files."""
        try:
            # Create a snapshot using git archive if in git repo
            git_result = await self._run_git_command(["rev-parse", "--git-dir"])
            if git_result.returncode == 0:
                # In git repository - use git archive for consistent snapshot
                archive_result = await self._run_git_command(
                    [
                        "archive",
                        "--format=tar",
                        "HEAD",
                        "-o",
                        str(checkpoint_path / "snapshot.tar"),
                    ]
                )
                if archive_result.returncode == 0:
                    return

            # Fallback to direct copy
            snapshot_dir = checkpoint_path / "snapshot"
            snapshot_dir.mkdir(exist_ok=True)

            # Copy key directories and files
            items_to_copy = [
                "src",
                "tests",
                "scripts",
                "docs",
                "pyproject.toml",
                "README.md",
            ]

            for item_name in items_to_copy:
                item_path = self.project_root / item_name
                if item_path.exists():
                    target_path = snapshot_dir / item_name
                    if item_path.is_dir():
                        shutil.copytree(
                            item_path,
                            target_path,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                        )
                    else:
                        shutil.copy2(item_path, target_path)

        except Exception as e:
            raise CheckpointError(f"Failed to create file snapshot: {e}") from e

    async def _restore_file_snapshot(self, checkpoint_path: Path) -> None:
        """Restore files from snapshot."""
        try:
            # Try to restore from git archive first
            archive_file = checkpoint_path / "snapshot.tar"
            if archive_file.exists():
                # Extract git archive
                result = await asyncio.create_subprocess_exec(
                    "tar", "-xf", str(archive_file), "-C", str(self.project_root)
                )
                await result.wait()
                if result.returncode == 0:
                    return

            # Fallback to directory copy
            snapshot_dir = checkpoint_path / "snapshot"
            if not snapshot_dir.exists():
                raise CheckpointError("No snapshot found in checkpoint")

            # Copy files back to project root
            for item in snapshot_dir.iterdir():
                target_path = self.project_root / item.name

                # Remove existing item if it exists
                if target_path.exists():
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()

                # Copy from snapshot
                if item.is_dir():
                    shutil.copytree(item, target_path)
                else:
                    shutil.copy2(item, target_path)

        except Exception as e:
            raise CheckpointError(f"Failed to restore file snapshot: {e}") from e

    async def _get_current_git_ref(self) -> str | None:
        """Get current git reference."""
        try:
            result = await self._run_git_command(["rev-parse", "HEAD"])
            if result.returncode == 0:
                # Fix: Ensure proper type annotation for stdout
                stdout: str = result.stdout
                return stdout.strip()
            return None
        except Exception:
            return None

    async def _restore_git_ref(self, git_ref: str) -> None:
        """Restore git reference."""
        try:
            result = await self._run_git_command(["checkout", git_ref])
            if result.returncode != 0:
                self.logger.warning(
                    f"Failed to restore git ref {git_ref}: {result.stderr}"
                )
        except Exception as e:
            self.logger.warning(f"Failed to restore git ref {git_ref}: {e}")

    async def _count_files(self, path: Path) -> int:
        """Count files in directory recursively."""
        try:
            count = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    count += 1
            return count
        except Exception as e:
            self.logger.warning(f"Failed to count files: {e}")
            return 0

    async def _calculate_size(self, path: Path) -> int:
        """Calculate total size of directory."""
        try:
            total_size = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception as e:
            self.logger.warning(f"Failed to calculate directory size: {e}")
            return 0

    async def _run_git_command(
        self, args: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """Run git command with proper error handling"""
        try:
            cmd = ["git"] + args
            result = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            # Fix: Handle None returncode
            return_code = result.returncode if result.returncode is not None else 1
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=return_code,
                stdout=stdout.decode("utf-8", errors="ignore"),
                stderr=stderr.decode("utf-8", errors="ignore"),
            )

        except Exception as e:
            self.logger.error(f"Failed to run git command {args}: {e}")
            return subprocess.CompletedProcess(
                args=["git"] + args, returncode=1, stdout="", stderr=str(e)
            )

    async def health_check(self) -> bool:
        """Perform health check of checkpoint system"""
        try:
            # Check if checkpoint directory is accessible
            if not self.checkpoint_dir.exists():
                return False

            # Check if we can create a test checkpoint
            test_checkpoint = await self.create_checkpoint("test", "health_check")
            await self.delete_checkpoint(test_checkpoint.checkpoint_id)

            return True

        except Exception as e:
            self.logger.error(f"Checkpoint system health check failed: {e}")
            return False
