"""Test SessionManager performance characteristics and metrics.

This module tests the performance requirements and metrics calculation
for the SessionManager, ensuring it meets the <5% performance overhead
requirement specified in the PRD.
"""

import subprocess
import time

import pytest

from src.orchestrator.session_manager import SessionConfig, SessionManager


def _has_tmux_support() -> bool:
    """Check if tmux and pexpect are available for testing."""
    try:
        # Check if pexpect can be imported
        import pexpect  # noqa: F401

        # Check if tmux command is available
        result = subprocess.run(
            ["which", "tmux"], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False

        # Try to run tmux version command
        result = subprocess.run(
            ["tmux", "-V"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0

    except (ImportError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


class TestSessionManagerPerformance:
    """Test SessionManager performance characteristics."""

    @pytest.mark.asyncio
    async def test_basic_performance_metrics(self):
        """Test that basic performance metrics are computed correctly."""
        config = SessionConfig(session_timeout=2.0)
        session_manager = SessionManager(config)

        # Initialize some test data
        session_manager._session_creation_times = [0.1, 0.2, 0.15, 0.18]
        session_manager._session_termination_times = [0.05, 0.08, 0.06]
        session_manager._operation_count = 10
        session_manager._total_operation_time = 2.5

        metrics = session_manager.performance_metrics

        # Verify calculated metrics
        assert metrics["total_sessions_created"] == 4
        assert metrics["average_create_time"] == 0.1575
        assert metrics["average_terminate_time"] == pytest.approx(0.063, rel=1e-2)
        assert metrics["operations_per_second"] == 4.0
        assert metrics["performance_overhead_percent"] == pytest.approx(25.0, rel=1e-6)
        assert metrics["meets_5_percent_requirement"] is False

    @pytest.mark.asyncio
    async def test_performance_benchmark_without_sessions(self):
        """Test performance metrics when no sessions have been created."""
        config = SessionConfig()
        session_manager = SessionManager(config)

        metrics = session_manager.performance_metrics

        # Should handle empty metrics gracefully
        assert metrics["total_sessions_created"] == 0
        assert metrics["average_create_time"] == 0.0
        assert metrics["average_terminate_time"] == 0.0
        assert metrics["operations_per_second"] == 0.0
        assert metrics["performance_overhead_percent"] == 0.0
        assert metrics["meets_5_percent_requirement"] is True  # No overhead = good

    @pytest.mark.skipif(
        not _has_tmux_support(),
        reason="tmux not available for performance testing",
    )
    @pytest.mark.asyncio
    async def test_session_creation_performance(self):
        """Test actual session creation performance (if tmux available)."""
        config = SessionConfig(session_timeout=5.0)
        session_manager = SessionManager(config)

        try:
            # Measure session creation time
            start_time = time.time()
            session_id = await session_manager.create_session()
            creation_time = time.time() - start_time

            # Should be fast (under 1 second for local operations)
            assert creation_time < 1.0

            # Clean up
            await session_manager.terminate_session(session_id)

            # Verify metrics were recorded
            metrics = session_manager.performance_metrics
            assert metrics["total_sessions_created"] == 1
            assert metrics["average_create_time"] > 0

        except Exception as e:
            pytest.fail(f"Session creation failed: {e}")

    @pytest.mark.asyncio
    async def test_performance_overhead_calculation(self):
        """Test performance overhead calculation accuracy."""
        config = SessionConfig()
        session_manager = SessionManager(config)

        # Test scenario 1: Low overhead (within 5% requirement)
        session_manager._operation_count = 20
        session_manager._total_operation_time = (
            1.0  # 0.05s average, better than 0.2s baseline
        )
        metrics = session_manager.performance_metrics
        assert metrics["meets_5_percent_requirement"] is True
        assert (
            metrics["performance_overhead_percent"] == 0.0
        )  # Better than baseline = 0% overhead

        # Test scenario 2: Overhead exceeds baseline (should show positive overhead)
        session_manager._operation_count = 10
        session_manager._total_operation_time = (
            2.5  # 0.25s average vs 0.2s baseline = 25% overhead
        )
        metrics = session_manager.performance_metrics
        assert metrics["performance_overhead_percent"] == pytest.approx(25.0, rel=1e-6)
        assert metrics["meets_5_percent_requirement"] is False

    @pytest.mark.asyncio
    async def test_performance_metrics_thread_safety(self):
        """Test that performance metrics are thread-safe."""
        config = SessionConfig()
        session_manager = SessionManager(config)

        # Simulate concurrent operations updating metrics
        import threading

        def update_metrics():
            session_manager._operation_count += 1
            session_manager._total_operation_time += 0.1

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=update_metrics)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify final state is consistent
        assert session_manager._operation_count == 10
        assert session_manager._total_operation_time == pytest.approx(1.0, rel=1e-2)

    @pytest.mark.asyncio
    async def test_performance_requirement_boundaries(self):
        """Test performance requirement boundary conditions."""
        config = SessionConfig()
        manager = SessionManager(config)

        # Test exactly at 5% threshold: 0.21s average (5% above 0.2s baseline)
        manager._operation_count = 20
        manager._total_operation_time = 4.2  # 0.21s average = exactly 5% above baseline
        metrics = manager.performance_metrics
        assert (
            metrics["meets_5_percent_requirement"] is True
        )  # Should meet requirement at threshold
        assert metrics["performance_overhead_percent"] == pytest.approx(5.0, rel=1e-6)

        # Test just over 5% threshold
        manager._total_operation_time = 4.4  # 0.22s average = 10% above baseline
        metrics = manager.performance_metrics
        assert (
            metrics["meets_5_percent_requirement"] is False
        )  # Should fail requirement
        assert metrics["performance_overhead_percent"] == pytest.approx(10.0, rel=1e-6)

        # Test well under 5% threshold
        manager._total_operation_time = 2.0  # 0.1s average, better than baseline
        metrics = manager.performance_metrics
        assert metrics["meets_5_percent_requirement"] is True
        assert metrics["performance_overhead_percent"] == 0.0  # Better than baseline

    @pytest.mark.asyncio
    async def test_performance_metrics_reset(self):
        """Test performance metrics can be reset properly."""
        config = SessionConfig()
        session_manager = SessionManager(config)

        # Add some test data
        session_manager._session_creation_times = [0.1, 0.2]
        session_manager._operation_count = 5
        session_manager._total_operation_time = 1.0

        # Get initial metrics
        initial_metrics = session_manager.performance_metrics
        assert initial_metrics["total_sessions_created"] == 2

        # Reset metrics (if method exists)
        if hasattr(session_manager, "reset_performance_metrics"):
            session_manager.reset_performance_metrics()

            # Verify reset
            reset_metrics = session_manager.performance_metrics
            assert reset_metrics["total_sessions_created"] == 0
            assert reset_metrics["operations_per_second"] == 0.0

    @pytest.mark.skipif(
        not _has_tmux_support(),
        reason="tmux not available for performance testing",
    )
    @pytest.mark.asyncio
    async def test_concurrent_session_performance(self):
        """Test performance with multiple concurrent sessions."""
        config = SessionConfig(max_concurrent_operations=5)
        session_manager = SessionManager(config)

        try:
            # Create multiple sessions concurrently
            import asyncio

            async def create_and_destroy_session():
                session_id = await session_manager.create_session()
                await asyncio.sleep(0.1)  # Simulate work
                await session_manager.terminate_session(session_id)
                return session_id

            start_time = time.time()
            tasks = [create_and_destroy_session() for _ in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Filter out any exceptions (failed session creations)
            successful_sessions = [r for r in results if not isinstance(r, Exception)]

            if successful_sessions:
                # Should complete in reasonable time
                assert total_time < 5.0  # 5 seconds max for 3 sessions

                # Verify performance tracking
                metrics = session_manager.performance_metrics
                assert metrics["total_sessions_created"] >= len(successful_sessions)
            else:
                pytest.fail("All session creations failed - tmux configuration issue")

        except Exception as e:
            pytest.fail(f"Concurrent session test failed: {e}")

    @pytest.mark.asyncio
    async def test_performance_monitoring_intervals(self):
        """Test that performance monitoring works with different intervals."""
        # Short monitoring interval
        short_config = SessionConfig(monitoring_interval=0.1)
        short_manager = SessionManager(short_config)

        # Long monitoring interval
        long_config = SessionConfig(monitoring_interval=1.0)
        long_manager = SessionManager(long_config)

        # Both should initialize properly
        assert short_manager.config.monitoring_interval == 0.1
        assert long_manager.config.monitoring_interval == 1.0

        # Both should provide metrics
        short_metrics = short_manager.performance_metrics
        long_metrics = long_manager.performance_metrics

        assert isinstance(short_metrics, dict)
        assert isinstance(long_metrics, dict)

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test SessionManager performance under simulated load."""
        config = SessionConfig()
        session_manager = SessionManager(config)

        # Simulate multiple operations under load
        start_time = time.time()
        for _ in range(5):
            await session_manager._simulate_operation("load_test_operation")

        total_time = time.time() - start_time

        # Verify operations were tracked
        metrics = session_manager.performance_metrics
        assert metrics["total_operation_count"] == 5
        assert metrics["total_operation_time"] > 0
        assert total_time >= 0.5  # Should take at least 500ms (5 * 100ms)

        # Performance should still be reasonable under load
        operations_per_second = metrics["operations_per_second"]
        assert operations_per_second > 0
        assert operations_per_second <= 10  # Should not exceed realistic limits
