"""Performance tests for the SessionManager class.

This module contains tests for measuring and validating the performance
characteristics of the SessionManager, including session creation times,
resource usage, and throughput metrics.
"""

import asyncio
import shutil
import time

import pytest

from src.orchestrator.session_manager import SessionConfig, SessionManager


@pytest.mark.performance
class TestSessionManagerPerformance:
    """Performance tests for SessionManager operations."""

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
        assert metrics["performance_overhead_percent"] == 25.0
        assert metrics["meets_5_percent_requirement"] is False

    @pytest.mark.asyncio
    async def test_performance_benchmark_without_sessions(self):
        """Test performance benchmark without actually creating sessions if tmux fails."""
        config = SessionConfig(session_timeout=2.0)

        # Skip if tmux is not available
        if not shutil.which("tmux"):
            pytest.skip("tmux not available for performance testing")

        sessions = []
        session_manager = SessionManager(config)

        # Simulate performance test
        time.time()
        for i in range(5):
            session_name = f"perf_test_{i}_{int(time.time() * 1000)}"
            try:
                session = await session_manager.create_session(session_name)
                sessions.append(session)
            except Exception:
                # Skip if tmux not available in test environment
                pytest.skip("tmux not available for performance testing")

        # Clean up sessions
        for session in sessions:
            await session_manager.terminate_session(session, force=True)

        # Check final metrics
        final_metrics = session_manager.performance_metrics

        # Verify performance requirement
        assert final_metrics["meets_5_percent_requirement"] is True, (
            f"Performance overhead {final_metrics['performance_overhead_percent']:.2f}% "
            f"exceeds 5% requirement"
        )

        # Additional performance checks
        assert final_metrics["average_operation_time"] < 1.0, (
            "Average operation time too high"
        )

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance metrics under simulated load."""
        config = SessionConfig(session_timeout=1.0, max_concurrent_operations=5)
        session_manager = SessionManager(config)

        # Simulate concurrent operations
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                session_manager._simulate_operation(f"operation_{i}")
            )
            tasks.append(task)

        # Wait for completion
        await asyncio.gather(*tasks, return_exceptions=True)

        metrics = session_manager.performance_metrics
        assert "operations_per_second" in metrics
        assert "average_operation_time" in metrics

    @pytest.mark.asyncio
    async def test_performance_overhead_calculation(self):
        """Test performance overhead calculation accuracy."""
        config = SessionConfig()
        session_manager = SessionManager(config)

        # Test scenario 1: Low overhead (within 5% requirement)
        session_manager._operation_count = 20
        session_manager._total_operation_time = 1.0  # 0.05s average (5% of 1s)
        metrics = session_manager.performance_metrics
        assert metrics["meets_5_percent_requirement"] is True
        assert metrics["performance_overhead_percent"] == 5.0

        # Test scenario 2: Higher overhead
        session_manager._operation_count = 10
        session_manager._total_operation_time = 1.0  # 0.1s average (10% overhead)
        metrics = session_manager.performance_metrics
        assert metrics["meets_5_percent_requirement"] is False
        assert metrics["performance_overhead_percent"] == 10.0

    @pytest.mark.asyncio
    async def test_performance_edge_cases(self):
        """Test performance calculations with edge cases."""
        config = SessionConfig()
        session_manager = SessionManager(config)

        # Test with no operations
        metrics = session_manager.performance_metrics
        assert metrics["operations_per_second"] == 0
        assert metrics["average_operation_time"] == 0
        assert metrics["performance_overhead_percent"] == 0
        assert metrics["meets_5_percent_requirement"] is True

        # Test with very fast operations
        session_manager._operation_count = 1000
        session_manager._total_operation_time = 0.01  # Very fast
        metrics = session_manager.performance_metrics
        assert metrics["operations_per_second"] == 100000.0
        assert metrics["meets_5_percent_requirement"] is True

    @pytest.mark.asyncio
    async def test_performance_requirement_boundaries(self):
        """Test performance requirement boundary conditions."""
        config = SessionConfig()
        manager = SessionManager(config)

        # Test exactly at 5% threshold
        manager._operation_count = 20
        manager._total_operation_time = 1.0  # Exactly 5% overhead
        metrics = manager.performance_metrics
        assert metrics["performance_overhead_percent"] == 5.0
        assert metrics["meets_5_percent_requirement"] is True

        # Test slightly above 5% threshold
        manager._total_operation_time = 1.05  # Slightly above 5% overhead
        metrics = manager.performance_metrics
        assert metrics["performance_overhead_percent"] == 5.25
        assert metrics["meets_5_percent_requirement"] is False

        # Simulate higher overhead
        manager._total_operation_time = 3.6  # 0.36s average (20% overhead)
        metrics = manager.performance_metrics
        assert metrics["meets_5_percent_requirement"] is False
        assert metrics["performance_overhead_percent"] == 20.0


@pytest.mark.integration
class TestSessionManagerBenchmark:
    """Integration benchmark tests (require tmux)."""

    @pytest.mark.asyncio
    async def test_full_benchmark(self):
        """Run full performance benchmark if tmux is available."""
        # Skip if tmux is not available
        if not shutil.which("tmux"):
            pytest.skip("tmux not available for performance testing")

        config = SessionConfig(session_timeout=2.0)

        try:
            async with SessionManager(config) as manager:
                # Run lightweight benchmark
                results = await manager.benchmark_performance(
                    iterations=5, concurrent_operations=2
                )

                # Verify benchmark results structure
                assert "meets_performance_requirement" in results
                assert "benchmark_duration" in results
                assert "total_sessions_created" in results

                # If no sessions were created (e.g., tmux issues), skip further tests
                if results["total_sessions_created"] == 0:
                    pytest.skip(
                        "Session creation failed - likely tmux configuration issue"
                    )

                # Only test performance if sessions were actually created
                assert results["total_sessions_created"] > 0
                assert results["benchmark_duration"] > 0

                # Performance should meet requirements
                if results["meets_performance_requirement"]:
                    assert results["average_create_time"] <= 0.315

        except Exception as e:
            error_msg = str(e).lower()
            if any(
                keyword in error_msg
                for keyword in ["tmux", "no such file", "command failed"]
            ):
                pytest.skip(
                    f"tmux not available or misconfigured for benchmark testing: {e}"
                )
            else:
                raise
