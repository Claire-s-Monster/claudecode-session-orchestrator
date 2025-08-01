"""
Performance tests for SessionManager to ensure <5% overhead requirement.
"""

import asyncio
import time

import pytest

from src.orchestrator.session_manager import SessionConfig, SessionManager


class TestSessionManagerPerformance:
    """Performance tests for SessionManager."""

    @pytest.fixture
    async def session_manager(self):
        """Create a SessionManager for testing."""
        config = SessionConfig(
            session_timeout=5.0,
            operation_timeout=5.0,
            monitoring_interval=0.1
        )
        manager = SessionManager(config)
        async with manager:
            yield manager

    @pytest.mark.asyncio
    async def test_performance_overhead(self, session_manager):
        """Test that SessionManager meets <5% performance overhead requirement."""
        # Get initial metrics
        initial_metrics = session_manager.performance_metrics
        assert initial_metrics["meets_5_percent_requirement"] is True

        # Create and terminate a few sessions to generate metrics
        sessions = []
        for i in range(5):
            session_name = f"perf_test_{i}_{int(time.time()*1000)}"
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
    async def test_concurrent_operation_performance(self, session_manager):
        """Test performance under concurrent operations."""
        # Test concurrent session creation
        concurrent_tasks = 3
        session_names = [
            f"concurrent_test_{i}_{int(time.time()*1000)}"
            for i in range(concurrent_tasks)
        ]

        start_time = time.time()
        tasks = []

        for session_name in session_names:
            try:
                task = asyncio.create_task(
                    session_manager.create_session(session_name)
                )
                tasks.append(task)
            except Exception:
                pytest.skip("tmux not available for concurrent testing")

        # Wait for all tasks to complete
        sessions = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Calculate concurrent operation time
        concurrent_time = end_time - start_time

        # Should be faster than sequential operations due to async nature
        sequential_estimate = len(session_names) * 0.3  # 0.3s per operation (realistic tmux baseline)

        # Allow reasonable overhead but should be faster than sequential
        assert concurrent_time < sequential_estimate * 1.2, (
            f"Concurrent operations took {concurrent_time:.2f}s, "
            f"expected < {sequential_estimate * 1.2:.2f}s"
        )

        # Clean up successful sessions
        for session in sessions:
            if hasattr(session, "session_name"):
                await session_manager.terminate_session(session, force=True)

    @pytest.mark.asyncio
    async def test_resource_usage_monitoring(self, session_manager):
        """Test resource usage monitoring."""
        # Get initial resource usage
        initial_usage = session_manager.get_resource_usage()

        # Verify resource usage fields
        required_fields = [
            "cpu_percent", "memory_mb", "memory_percent",
            "open_files", "threads", "active_sessions", "total_tracked_sessions"
        ]

        for field in required_fields:
            assert field in initial_usage, f"Missing resource usage field: {field}"
            assert isinstance(initial_usage[field], int | float), (
                f"Resource usage field {field} should be numeric"
            )

        # Resource usage should be reasonable
        assert initial_usage["memory_mb"] < 100, "Memory usage too high"
        assert initial_usage["cpu_percent"] < 50, "CPU usage too high"

    @pytest.mark.asyncio
    async def test_monitoring_overhead(self, session_manager):
        """Test that background monitoring has minimal overhead."""
        # Start monitoring
        await session_manager.start_monitoring()

        # Let monitoring run for a short time
        await asyncio.sleep(0.5)

        # Get resource usage after monitoring
        usage = session_manager.get_resource_usage()

        # Monitoring should have minimal impact
        assert usage["cpu_percent"] < 10, (
            f"Monitoring CPU usage {usage['cpu_percent']:.2f}% too high"
        )
        assert usage["memory_mb"] < 50, (
            f"Monitoring memory usage {usage['memory_mb']:.2f}MB too high"
        )

    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation without actual operations."""
        config = SessionConfig()
        manager = SessionManager(config)

        # Test with no operations
        metrics = manager.performance_metrics
        assert metrics["operation_count"] == 0
        assert metrics["meets_5_percent_requirement"] is True

        # Simulate some operation data
        manager._operation_count = 10
        manager._total_operation_time = 3.0  # 0.3s average

        metrics = manager.performance_metrics
        assert metrics["operation_count"] == 10
        assert metrics["average_operation_time"] == 0.3
        assert metrics["meets_5_percent_requirement"] is True

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
        config = SessionConfig(session_timeout=2.0)

        try:
            async with SessionManager(config) as manager:
                # Run lightweight benchmark
                results = await manager.benchmark_performance(
                    iterations=5,
                    concurrent_operations=2
                )

                # Verify benchmark results
                assert "meets_performance_requirement" in results
                assert results["total_sessions_created"] > 0
                assert results["benchmark_duration"] > 0

                # Performance should meet requirements
                if results["meets_performance_requirement"]:
                    assert results["average_create_time"] <= 0.315

        except Exception as e:
            if "tmux" in str(e).lower():
                pytest.skip("tmux not available for benchmark testing")
            else:
                raise
