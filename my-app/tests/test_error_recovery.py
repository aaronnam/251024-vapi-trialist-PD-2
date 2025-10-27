"""Tests for error recovery infrastructure.

This test suite verifies:
- Circuit breaker behavior (closed -> open -> half-open -> closed)
- Retry logic with exponential backoff
- Natural language error responses
- Conversation state preservation during errors
- Tool error handling patterns
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from livekit.agents import RunContext, ToolError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent import PandaDocTrialistAgent
from error_recovery import (
    CircuitBreaker,
    ErrorRecoveryMixin,
    retry_with_exponential_backoff,
)

# ============================================================================
# Circuit Breaker Tests
# ============================================================================


def test_circuit_breaker_starts_closed():
    """Circuit breaker should start in closed state allowing calls."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    assert cb.state == "closed"
    assert cb.is_available()


def test_circuit_breaker_opens_after_threshold():
    """Circuit breaker should open after reaching failure threshold."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

    # Record failures below threshold
    cb.call_failed()
    cb.call_failed()
    assert cb.state == "closed"
    assert cb.is_available()

    # Third failure should open circuit
    cb.call_failed()
    assert cb.state == "open"
    assert not cb.is_available()


def test_circuit_breaker_resets_on_success():
    """Circuit breaker should reset failure count on successful call."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

    # Record failures
    cb.call_failed()
    cb.call_failed()
    assert cb.failure_count == 2

    # Success resets counter
    cb.call_succeeded()
    assert cb.failure_count == 0
    assert cb.state == "closed"


def test_circuit_breaker_half_open_transition():
    """Circuit breaker should transition to half-open after recovery timeout."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)  # Short timeout for testing

    # Open the circuit
    for _ in range(3):
        cb.call_failed()
    assert cb.state == "open"
    assert not cb.is_available()

    # Wait for recovery timeout
    import time
    time.sleep(0.15)

    # Should transition to half-open
    assert cb.is_available()
    assert cb.state == "half_open"


def test_circuit_breaker_closes_after_successful_half_open():
    """Circuit breaker should close after successful call in half-open state."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)

    # Open the circuit
    for _ in range(3):
        cb.call_failed()

    # Wait for half-open
    import time
    time.sleep(0.15)
    cb.is_available()  # Trigger transition to half-open

    # Success in half-open should close circuit
    cb.call_succeeded()
    assert cb.state == "closed"


# ============================================================================
# Retry Logic Tests
# ============================================================================


@pytest.mark.asyncio
async def test_retry_succeeds_on_first_attempt():
    """Retry should return immediately if first attempt succeeds."""
    async def successful_func():
        return "success"

    result = await retry_with_exponential_backoff(successful_func, max_retries=3)
    assert result == "success"


@pytest.mark.asyncio
async def test_retry_succeeds_after_failures():
    """Retry should eventually succeed after transient failures."""
    attempt_count = 0

    async def flaky_func():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError("Transient error")
        return "success"

    result = await retry_with_exponential_backoff(
        flaky_func,
        max_retries=3,
        base_delay=0.01,  # Fast for testing
        max_delay=0.1,
    )
    assert result == "success"
    assert attempt_count == 3


@pytest.mark.asyncio
async def test_retry_exhausts_attempts():
    """Retry should raise exception after exhausting all attempts."""
    async def always_fails():
        raise ValueError("Permanent error")

    with pytest.raises(ValueError, match="Permanent error"):
        await retry_with_exponential_backoff(
            always_fails,
            max_retries=2,
            base_delay=0.01,
            max_delay=0.1,
        )


@pytest.mark.asyncio
async def test_retry_exponential_backoff_timing():
    """Retry should use exponential backoff delays."""
    attempt_times = []

    async def track_attempts():
        attempt_times.append(asyncio.get_event_loop().time())
        raise ConnectionError("Error")

    with pytest.raises(ConnectionError):
        await retry_with_exponential_backoff(
            track_attempts,
            max_retries=2,
            base_delay=0.1,
            max_delay=1.0,
            jitter=False,  # Disable jitter for predictable timing
        )

    # Verify we had 3 attempts (initial + 2 retries)
    assert len(attempt_times) == 3

    # Verify exponential backoff (approximately 0.1s, 0.2s delays)
    delays = [attempt_times[i+1] - attempt_times[i] for i in range(len(attempt_times)-1)]
    assert 0.08 < delays[0] < 0.15  # ~0.1s delay
    assert 0.18 < delays[1] < 0.25  # ~0.2s delay


# ============================================================================
# ErrorRecoveryMixin Tests
# ============================================================================


def test_get_error_response_returns_string():
    """get_error_response should return a natural language string."""
    class TestAgent(ErrorRecoveryMixin):
        pass

    agent = TestAgent()
    response = agent.get_error_response("tool_failure")

    assert isinstance(response, str)
    assert len(response) > 0


def test_get_error_response_varies():
    """get_error_response should return different responses (randomized)."""
    class TestAgent(ErrorRecoveryMixin):
        pass

    agent = TestAgent()
    responses = {agent.get_error_response("generic") for _ in range(20)}

    # Should have multiple unique responses (with 20 samples, very likely)
    assert len(responses) > 1


def test_get_error_response_all_types():
    """get_error_response should work for all error types."""
    class TestAgent(ErrorRecoveryMixin):
        pass

    agent = TestAgent()
    error_types = [
        "tool_failure",
        "connection_issue",
        "timeout",
        "service_unavailable",
        "data_not_found",
        "generic",
    ]

    for error_type in error_types:
        response = agent.get_error_response(error_type)
        assert isinstance(response, str)
        assert len(response) > 0


def test_preserve_conversation_state_signals():
    """preserve_conversation_state should restore qualification signals."""
    agent = PandaDocTrialistAgent()

    # Set initial state
    agent.discovered_signals["team_size"] = 10
    agent.discovered_signals["use_case"] = "proposals"

    # Create snapshot and modify state
    snapshot = {
        "signals": {"team_size": 5, "industry": "healthcare"},
        "notes": ["Important note"],
        "state": "DISCOVERY",
    }
    agent.discovered_signals["team_size"] = 1  # Modify
    agent.conversation_state = "CLOSING"  # Modify

    # Restore from snapshot
    agent.preserve_conversation_state(snapshot)

    # Verify restoration
    assert agent.discovered_signals["team_size"] == 5
    assert agent.discovered_signals["industry"] == "healthcare"
    assert agent.conversation_state == "DISCOVERY"


# ============================================================================
# Agent Helper Method Tests
# ============================================================================


@pytest.mark.asyncio
async def test_call_with_retry_and_circuit_breaker_success():
    """call_with_retry_and_circuit_breaker should return result on success."""
    agent = PandaDocTrialistAgent()

    async def successful_call():
        return {"status": "success"}

    result = await agent.call_with_retry_and_circuit_breaker(
        service_name="test_service",
        func=successful_call,
        fallback_response="Fallback",
    )

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_call_with_retry_and_circuit_breaker_fallback():
    """call_with_retry_and_circuit_breaker should return fallback on failure."""
    agent = PandaDocTrialistAgent()

    async def failing_call():
        raise ConnectionError("Service unavailable")

    result = await agent.call_with_retry_and_circuit_breaker(
        service_name="test_service",
        func=failing_call,
        fallback_response="Using fallback",
        max_retries=1,  # Fast failure for testing
    )

    assert result == "Using fallback"


@pytest.mark.asyncio
async def test_call_with_retry_respects_circuit_breaker():
    """call_with_retry_and_circuit_breaker should respect open circuit."""
    agent = PandaDocTrialistAgent()

    # Create service with circuit breaker
    service_name = "test_service_cb"

    async def failing_call():
        raise ConnectionError("Service down")

    # Fail enough times to open circuit
    for _ in range(3):
        await agent.call_with_retry_and_circuit_breaker(
            service_name=service_name,
            func=failing_call,
            fallback_response="Fallback",
            max_retries=0,  # No retries
        )

    # Circuit should now be open
    circuit = agent.circuit_breakers[service_name]
    assert circuit.state == "open"

    # Next call should immediately return fallback without calling func
    call_count = 0

    async def count_calls():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Should not be called")

    result = await agent.call_with_retry_and_circuit_breaker(
        service_name=service_name,
        func=count_calls,
        fallback_response="Circuit open fallback",
    )

    assert result == "Circuit open fallback"
    assert call_count == 0  # Function should not have been called


@pytest.mark.asyncio
async def test_handle_tool_with_error_recovery_success():
    """handle_tool_with_error_recovery should return result on success."""
    agent = PandaDocTrialistAgent()
    mock_context = MagicMock(spec=RunContext)

    async def successful_tool():
        return "Tool result"

    result = await agent.handle_tool_with_error_recovery(
        context=mock_context,
        tool_name="test_tool",
        tool_func=successful_tool,
    )

    assert result == "Tool result"


@pytest.mark.asyncio
async def test_handle_tool_with_error_recovery_timeout():
    """handle_tool_with_error_recovery should raise ToolError on timeout."""
    agent = PandaDocTrialistAgent()
    mock_context = MagicMock(spec=RunContext)

    async def timeout_tool():
        raise asyncio.TimeoutError("Operation timed out")

    with pytest.raises(ToolError) as exc_info:
        await agent.handle_tool_with_error_recovery(
            context=mock_context,
            tool_name="test_tool",
            tool_func=timeout_tool,
            error_type="timeout",
        )

    # Should contain natural language error message
    error_msg = str(exc_info.value)
    assert len(error_msg) > 0
    # Should be conversational (not technical) - verify it's from our error responses
    assert any(
        keyword in error_msg.lower()
        for keyword in ["timeout", "slow", "taking longer", "expected", "quicker", "approach"]
    )


@pytest.mark.asyncio
async def test_handle_tool_preserves_state_on_error():
    """handle_tool_with_error_recovery should preserve state on error."""
    agent = PandaDocTrialistAgent()
    mock_context = MagicMock(spec=RunContext)

    # Set initial state
    agent.discovered_signals["team_size"] = 5
    agent.conversation_notes = ["Note 1"]
    agent.conversation_state = "DISCOVERY"

    async def failing_tool():
        # Simulate state corruption before failure
        agent.discovered_signals["team_size"] = None
        agent.conversation_notes = []
        raise ValueError("Tool failed")

    with pytest.raises(ToolError):
        await agent.handle_tool_with_error_recovery(
            context=mock_context,
            tool_name="test_tool",
            tool_func=failing_tool,
        )

    # State should be preserved despite error
    assert agent.discovered_signals["team_size"] == 5
    assert agent.conversation_notes == ["Note 1"]
    assert agent.conversation_state == "DISCOVERY"


# ============================================================================
# Example Tool Tests
# ============================================================================


@pytest.mark.asyncio
async def test_example_tool_with_timeout_success():
    """example_tool_with_timeout should return results within timeout."""
    agent = PandaDocTrialistAgent()
    mock_context = MagicMock(spec=RunContext)

    result = await agent.example_tool_with_timeout(mock_context, "test query")

    assert "test query" in result
    assert "Results for:" in result


@pytest.mark.asyncio
async def test_example_tool_with_circuit_breaker_success():
    """example_tool_with_circuit_breaker should return user data."""
    agent = PandaDocTrialistAgent()
    mock_context = MagicMock(spec=RunContext)

    result = await agent.example_tool_with_circuit_breaker(mock_context, "user123")

    assert "user123" in result or "user data" in result.lower()


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_end_to_end_retry_and_circuit_breaker():
    """Integration test: retry + circuit breaker + state preservation."""
    agent = PandaDocTrialistAgent()

    # Set initial state
    agent.discovered_signals["team_size"] = 10
    agent.conversation_state = "QUALIFICATION"

    call_count = 0

    async def flaky_service():
        nonlocal call_count
        call_count += 1

        # Fail first 2 times, succeed on 3rd
        if call_count < 3:
            raise ConnectionError("Transient error")
        return {"data": "success"}

    # Should succeed with retries
    result = await agent.call_with_retry_and_circuit_breaker(
        service_name="flaky_service",
        func=flaky_service,
        fallback_response="Fallback",
        max_retries=3,
    )

    assert result == {"data": "success"}
    assert call_count == 3

    # Circuit should be closed (success resets it)
    assert agent.circuit_breakers["flaky_service"].state == "closed"

    # State should be preserved
    assert agent.discovered_signals["team_size"] == 10
    assert agent.conversation_state == "QUALIFICATION"
