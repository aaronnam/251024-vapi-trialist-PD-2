"""
Silence Detection and Rate Limiting for LiveKit Voice Agent

This module provides elegant solutions for:
1. Detecting and disconnecting after prolonged silence
2. Rate limiting session duration
3. Cost-based rate limiting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from livekit.agents import (
    AgentSession,
    JobContext,
    UserStateChangedEvent,
)

logger = logging.getLogger("silence_timeout")


class SilenceTimeoutManager:
    """Manages silence detection and automatic disconnection."""

    def __init__(
        self,
        session: AgentSession,
        ctx: JobContext,
        silence_timeout_seconds: int = 30,
        warning_before_disconnect: int = 10,
    ):
        """
        Initialize silence timeout manager.

        Args:
            session: The AgentSession to monitor
            ctx: JobContext for room access
            silence_timeout_seconds: Seconds of silence before disconnecting (default: 30)
            warning_before_disconnect: Warn user N seconds before disconnect (default: 10)
        """
        self.session = session
        self.ctx = ctx
        self.silence_timeout = silence_timeout_seconds
        self.warning_time = silence_timeout_seconds - warning_before_disconnect

        # Track silence state
        self.silence_start_time: Optional[datetime] = None
        self.silence_timer_task: Optional[asyncio.Task] = None
        self.has_warned = False

        # Session limits
        self.session_start = datetime.now()
        self.max_session_duration = timedelta(minutes=30)  # Max 30 min sessions

        # Cost limits (using the cost tracking we implemented earlier)
        self.max_session_cost = 10.0  # $10 max per session

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register event handlers for monitoring user state."""
        self.session.on("user_state_changed")(self._on_user_state_changed)

    async def _on_user_state_changed(self, event: UserStateChangedEvent):
        """Handle user state changes to detect silence/inactivity."""
        logger.info(f"User state changed: {event.old_state} -> {event.new_state}")

        if event.new_state == "away" or event.new_state == "listening":
            # User stopped speaking or went away - start silence timer
            if not self.silence_start_time:
                self.silence_start_time = datetime.now()
                self.has_warned = False

                # Cancel any existing timer
                if self.silence_timer_task:
                    self.silence_timer_task.cancel()

                # Start new silence timer
                self.silence_timer_task = asyncio.create_task(
                    self._handle_silence_timeout()
                )
                logger.info(f"Started silence timer ({self.silence_timeout}s)")

        elif event.new_state == "speaking":
            # User is speaking - reset silence timer
            if self.silence_timer_task:
                self.silence_timer_task.cancel()
                self.silence_timer_task = None

            self.silence_start_time = None
            self.has_warned = False
            logger.info("Silence timer reset - user is speaking")

    async def _handle_silence_timeout(self):
        """Handle the silence timeout with warning and disconnection."""
        try:
            # First, wait for warning time
            await asyncio.sleep(self.warning_time)

            # Check if still silent
            if self.silence_start_time:
                # Warn the user
                if not self.has_warned:
                    await self.session.say(
                        "Hello? Are you still there? I'll disconnect in a few seconds if I don't hear from you.",
                        allow_interruptions=True
                    )
                    self.has_warned = True
                    logger.warning(f"Warning user about impending disconnect")

                # Wait remaining time
                remaining_time = self.silence_timeout - self.warning_time
                await asyncio.sleep(remaining_time)

                # Check again if still silent
                if self.silence_start_time:
                    # Disconnect due to silence
                    await self._disconnect_due_to_silence()

        except asyncio.CancelledError:
            # Timer was cancelled (user started speaking)
            logger.debug("Silence timer cancelled")

    async def _disconnect_due_to_silence(self):
        """Disconnect the session due to prolonged silence."""
        logger.warning(f"Disconnecting due to {self.silence_timeout}s of silence")

        try:
            # Polite goodbye
            await self.session.say(
                "I'm disconnecting now due to inactivity. Feel free to call back anytime!"
            )

            # Log the reason for analytics
            if hasattr(self.session, 'session_data'):
                self.session.session_data["disconnect_reason"] = "silence_timeout"
                self.session.session_data["silence_duration"] = self.silence_timeout

            # Close the session
            await asyncio.sleep(2)  # Give time for goodbye message
            await self.session.aclose()

        except Exception as e:
            logger.error(f"Error during silence disconnect: {e}")

    async def check_session_limits(self) -> bool:
        """
        Check if session has exceeded time or cost limits.

        Returns:
            True if limits exceeded, False otherwise
        """
        # Check time limit
        session_duration = datetime.now() - self.session_start
        if session_duration > self.max_session_duration:
            logger.warning(f"Session exceeded max duration: {session_duration}")
            await self._disconnect_due_to_limit("time")
            return True

        # Check cost limit (if agent has cost tracking)
        if hasattr(self.session, 'session_costs'):
            total_cost = self.session.session_costs.get("total_estimated_cost", 0)
            if total_cost > self.max_session_cost:
                logger.warning(f"Session exceeded max cost: ${total_cost:.2f}")
                await self._disconnect_due_to_limit("cost")
                return True

        return False

    async def _disconnect_due_to_limit(self, limit_type: str):
        """Disconnect due to rate limit (time or cost)."""
        if limit_type == "time":
            message = f"We've reached our {int(self.max_session_duration.total_seconds()/60)} minute session limit. Please call back if you need more help!"
        else:  # cost
            message = "We've reached the session limit. Please call back to continue!"

        await self.session.say(message)
        await asyncio.sleep(2)
        await self.session.aclose()

    def cleanup(self):
        """Clean up timers when session ends."""
        if self.silence_timer_task:
            self.silence_timer_task.cancel()


# Integration with your existing agent
def integrate_silence_timeout(session: AgentSession, ctx: JobContext, agent):
    """
    Integrate silence timeout with your existing agent.

    Add this to your entrypoint function after creating the AgentSession.
    """

    # Create silence manager with custom settings
    silence_manager = SilenceTimeoutManager(
        session=session,
        ctx=ctx,
        silence_timeout_seconds=30,  # Disconnect after 30s of silence
        warning_before_disconnect=10,  # Warn at 20s
    )

    # Optional: Set user_away_timeout on session for additional detection
    # This detects when user is completely absent (not just silent)
    # session.user_away_timeout = 15  # Mark as "away" after 15s

    # Add periodic limit checking (every 30 seconds)
    async def periodic_limit_check():
        while True:
            await asyncio.sleep(30)
            if await silence_manager.check_session_limits():
                break

    # Start the periodic check
    asyncio.create_task(periodic_limit_check())

    # Add cleanup on session close
    @session.on("close")
    def on_close(_):
        silence_manager.cleanup()

    return silence_manager


# Advanced: Adaptive timeout based on conversation context
class AdaptiveSilenceTimeout(SilenceTimeoutManager):
    """
    Adaptive silence timeout that adjusts based on conversation context.

    - Longer timeout during thinking/processing
    - Shorter timeout during small talk
    - Extended timeout if user said "let me think"
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_timeout = self.silence_timeout
        self.context_multipliers = {
            "thinking": 2.0,      # 2x timeout if user is thinking
            "complex_task": 1.5,  # 1.5x for complex questions
            "small_talk": 0.5,    # 0.5x for casual conversation
            "default": 1.0,
        }
        self.current_context = "default"

    def adjust_timeout_for_context(self, user_message: str):
        """Adjust timeout based on what the user said."""
        thinking_phrases = [
            "let me think", "give me a moment", "hold on",
            "one second", "hmm", "umm", "uh"
        ]

        complex_indicators = [
            "calculate", "explain", "describe", "analyze",
            "compare", "evaluate"
        ]

        message_lower = user_message.lower()

        if any(phrase in message_lower for phrase in thinking_phrases):
            self.current_context = "thinking"
            logger.info("Detected thinking context - extending timeout")
        elif any(word in message_lower for word in complex_indicators):
            self.current_context = "complex_task"
            logger.info("Detected complex task - moderately extending timeout")
        else:
            self.current_context = "default"

        # Update the timeout
        multiplier = self.context_multipliers[self.current_context]
        self.silence_timeout = int(self.base_timeout * multiplier)
        self.warning_time = self.silence_timeout - 10

        logger.info(f"Adjusted silence timeout to {self.silence_timeout}s for {self.current_context}")


# Rate limiting with token bucket algorithm
class RateLimiter:
    """
    Token bucket rate limiter for controlling request rates.

    Useful for limiting:
    - API calls per minute
    - Transcription requests
    - Tool usage frequency
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize rate limiter.

        Args:
            rate: Tokens refill rate per second
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = datetime.now()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.

        Returns:
            True if tokens acquired, False if rate limited
        """
        async with self.lock:
            # Refill tokens based on elapsed time
            now = datetime.now()
            elapsed = (now - self.last_refill).total_seconds()
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def wait_and_acquire(self, tokens: int = 1):
        """Wait until tokens are available, then acquire."""
        while not await self.acquire(tokens):
            await asyncio.sleep(0.1)