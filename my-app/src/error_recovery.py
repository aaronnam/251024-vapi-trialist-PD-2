"""Error recovery infrastructure for LiveKit voice agents.

This module provides:
- Circuit breaker pattern for preventing cascading failures
- Retry logic with exponential backoff
- Natural language error responses for voice conversations
- State preservation during failures
"""

import asyncio
import logging
import random
from typing import Any, Callable, ClassVar, TypeVar

logger = logging.getLogger("error_recovery")

# Type variable for generic retry decorator
T = TypeVar("T")


# ============================================================================
# Circuit Breaker Pattern
# ============================================================================


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures.

    Opens after failure_threshold consecutive failures.
    Automatically transitions to half-open after recovery_timeout seconds.
    Closes after a successful call in half-open state.

    Example:
        circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

        if circuit_breaker.is_available():
            try:
                result = await make_api_call()
                circuit_breaker.call_succeeded()
            except Exception:
                circuit_breaker.call_failed()
    """

    def __init__(
        self, failure_threshold: int = 3, recovery_timeout: float = 30.0
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before transitioning to half-open
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "closed"  # closed, open, half_open
        self.last_failure_time = 0.0

    def call_succeeded(self) -> None:
        """Record a successful call."""
        self.failure_count = 0
        if self.state == "half_open":
            logger.info("Circuit breaker: Service recovered, closing circuit")
            self.state = "closed"

    def call_failed(self) -> None:
        """Record a failed call."""
        import time

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold and self.state == "closed":
            logger.warning(
                f"Circuit breaker: Opening circuit after {self.failure_count} failures"
            )
            self.state = "open"

    def is_available(self) -> bool:
        """Check if the circuit breaker allows calls through.

        Returns:
            True if calls are allowed, False if circuit is open
        """
        import time

        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if we should transition to half-open
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker: Transitioning to half-open state")
                self.state = "half_open"
                return True
            return False

        # half_open state allows calls through
        return True


# ============================================================================
# Retry Logic
# ============================================================================


async def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    jitter: bool = True,
) -> T:
    """Retry a function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        jitter: Add random jitter to delay to prevent thundering herd

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries exhausted

    Example:
        result = await retry_with_exponential_backoff(
            func=lambda: fetch_user_data(user_id),
            max_retries=3,
            base_delay=0.5,
            max_delay=5.0
        )
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e

            if attempt >= max_retries:
                logger.error(f"All {max_retries} retry attempts exhausted: {e}")
                raise

            # Calculate delay with exponential backoff
            delay = min(base_delay * (2**attempt), max_delay)

            # Add jitter to prevent synchronized retries
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)

            logger.warning(
                f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            await asyncio.sleep(delay)

    # Should never reach here, but satisfy type checker
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry loop completed without success or exception")


# ============================================================================
# Error Recovery Mixin
# ============================================================================


class ErrorRecoveryMixin:
    """Mixin providing error recovery utilities for voice agents.

    Provides graceful error responses, fallback phrases, and state preservation
    during tool failures and service disruptions.

    Usage:
        class MyAgent(Agent, ErrorRecoveryMixin):
            def __init__(self):
                super().__init__(...)

            @function_tool()
            async def my_tool(self, context: RunContext, query: str):
                try:
                    result = await fetch_data(query)
                    return result
                except Exception as e:
                    error_msg = self.get_error_response("connection_issue")
                    raise ToolError(error_msg)
    """

    # Natural language error responses for different scenarios
    ERROR_RESPONSES: ClassVar[dict[str, list[str]]] = {
        "tool_failure": [
            "Let me try finding that information another way.",
            "I'm having a slight hiccup with that lookup. Give me just a moment.",
            "Let me take a different approach to get that for you.",
        ],
        "connection_issue": [
            "I'm experiencing a brief connection issue. Bear with me for just a second.",
            "Looks like there's a momentary network hiccup. One moment please.",
            "Connection seems a bit spotty. Let me reconnect and continue.",
        ],
        "timeout": [
            "That's taking longer than expected. Let me try a quicker approach.",
            "This is running a bit slow. Let me see if there's a faster way.",
            "That query is timing out. Let me try something else.",
        ],
        "service_unavailable": [
            "That service appears to be temporarily unavailable. Let's continue without it for now.",
            "I can't reach that system right now, but I can still help you with other things.",
            "That integration is having issues at the moment. Let's work around it.",
        ],
        "data_not_found": [
            "I couldn't find that information. Can you clarify what you're looking for?",
            "Hmm, I'm not seeing that in the system. Could you provide a bit more detail?",
            "I don't have that data available. Let me help you with what I can access.",
        ],
        "generic": [
            "I encountered an issue, but I'm still here to help. What else can I do for you?",
            "Something went wrong on my end, but let's keep going. What would you like to know?",
            "I hit a snag there, but no worries. How else can I assist you?",
        ],
    }

    def get_error_response(self, error_type: str = "generic") -> str:
        """Get a natural language error response.

        Args:
            error_type: Type of error (tool_failure, connection_issue, timeout,
                       service_unavailable, data_not_found, generic)

        Returns:
            A conversational error message appropriate for voice AI
        """
        responses = self.ERROR_RESPONSES.get(
            error_type, self.ERROR_RESPONSES["generic"]
        )
        return random.choice(responses)

    def preserve_conversation_state(self, context: dict[str, Any]) -> None:
        """Preserve conversation state despite errors.

        This method restores discovered signals, notes, and conversation state
        so that errors don't cause the agent to lose context.

        Args:
            context: Dictionary of context to preserve with keys:
                    - "signals": dict of qualification signals
                    - "notes": list of conversation notes
                    - "state": current conversation state

        Example:
            state_snapshot = {
                "signals": dict(self.discovered_signals),
                "notes": list(self.conversation_notes),
                "state": self.conversation_state,
            }
            try:
                result = await risky_operation()
            except Exception:
                self.preserve_conversation_state(state_snapshot)
                raise
        """
        # Store discovered qualification signals
        if "signals" in context and hasattr(self, "discovered_signals"):
            for key, value in context["signals"].items():
                if value is not None:
                    self.discovered_signals[key] = value
            logger.info(f"Preserved qualification signals: {context['signals']}")

        # Store conversation notes
        if "notes" in context and hasattr(self, "conversation_notes"):
            self.conversation_notes.extend(context["notes"])
            logger.info(f"Preserved conversation notes: {context['notes']}")

        # Preserve conversation state
        if "state" in context and hasattr(self, "conversation_state"):
            self.conversation_state = context["state"]
            logger.info(f"Preserved conversation state: {context['state']}")
