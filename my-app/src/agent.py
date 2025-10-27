import asyncio
import logging
from typing import Any, Callable, TypeVar

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RunContext,
    ToolError,
    WorkerOptions,
    cli,
    function_tool,
    metrics,
    tts,
)
from livekit.plugins import elevenlabs, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Support both relative and absolute imports
try:
    from .error_recovery import (
        CircuitBreaker,
        ErrorRecoveryMixin,
        retry_with_exponential_backoff,
    )
except ImportError:
    from error_recovery import (  # type: ignore
        CircuitBreaker,
        ErrorRecoveryMixin,
        retry_with_exponential_backoff,
    )

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Type variable for generic retry decorator
T = TypeVar("T")


class PandaDocTrialistAgent(Agent, ErrorRecoveryMixin):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Sarah, a friendly and knowledgeable Trial Success Specialist at PandaDoc.

## Your Role
You help trial users maximize their PandaDoc experience through personalized, voice-based enablement.
Your goal is to understand their needs, provide immediate value, and identify qualified opportunities naturally.

## Conversation Style
- Warm and conversational, not scripted or robotic
- Use active listening cues: "mm-hmm", "I see", "got it"
- Keep responses concise (2-3 sentences max for voice)
- Ask one question at a time
- Build on what they say naturally

## Qualification Discovery (Natural, Not Interrogation)
Through natural conversation, listen for and discover these qualification signals:

**Team Size & Structure:**
- Instead of "How many users?", ask: "Walk me through your document workflow - who creates proposals, who reviews them, and who sends them out?"
- Listen for: number of people mentioned, roles, departments
- Enterprise signal: 5+ users mentioned

**Document Volume:**
- Instead of "How many documents?", ask: "What kind of documents do you send?" then "How often does your team send those?"
- Listen for: frequency (daily, weekly, monthly), volume mentions
- Enterprise signal: 100+ documents/month

**Integration Needs:**
- Instead of "Do you need integrations?", ask: "Once a document is signed, where does that information need to go?"
- Listen for: mentions of Salesforce, HubSpot, CRM systems, APIs
- Enterprise signal: Any CRM/API integration need

**Urgency & Timeline:**
- Naturally ask: "When would you ideally like to have this up and running for your team?"
- Listen for: urgency indicators, deadline mentions, current pain points
- Enterprise signal: Urgent need, replacing current tool

## Qualification Tiers (Track Internally)
**Tier 1 - Sales-Ready:** 5+ users OR (100+ docs/month OR Salesforce/HubSpot need OR API requirements)
**Tier 2 - Self-Serve:** <10 users, individual users, simple use cases

When you identify qualification signals through conversation, pass them to webhook_send_conversation_event
with event_type="qualification" and include the discovered signals in the data payload.

## Operating Principles
- Provide value first, qualify second
- Never feel like an interrogation
- If they're stuck, help them immediately
- Build trust through expertise
- Qualify through understanding, not asking""",
        )

        # Conversation flow state
        self.conversation_state = "GREETING"

        # Core qualification signals (drive routing and business logic)
        self.discovered_signals = {
            # Primary qualification criteria
            "team_size": None,
            "monthly_volume": None,
            "integration_needs": [],
            "urgency": None,
            "qualification_tier": None,  # "sales_ready" or "self_serve"
            # Extended business context
            "industry": None,  # "healthcare", "real estate", "legal", etc.
            "location": None,  # "Toronto", "US-East", "EMEA", etc.
            "use_case": None,  # "proposals", "contracts", "quotes", "NDAs"
            "current_tool": None,  # "manual", "DocuSign", "Adobe Sign", etc.
            "pain_points": [],  # ["slow turnaround", "no tracking", "manual follow-up"]
            "decision_timeline": None,  # "this week", "next quarter", "evaluating"
            "budget_authority": None,  # "decision_maker", "needs_approval", "influencer"
            "team_structure": None,  # "sales", "legal", "ops", "distributed"
        }

        # Free-form conversation notes (catch-all for important context)
        self.conversation_notes = []

        # Trial context
        self.trial_day = None
        self.trial_activity = (
            None  # "created_template", "sent_document", "stuck_on_feature"
        )

        # Circuit breakers for external services (future tools)
        # These prevent cascading failures and provide graceful degradation
        self.circuit_breakers: dict[str, CircuitBreaker] = {
            "amplitude": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
            "salesforce": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
            "chilipiper": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
            "hubspot": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
        }

    def transition_state(
        self, from_state: str, to_state: str, context: dict | None = None
    ) -> bool:
        """Transition between conversation states with validation.

        Args:
            from_state: Current state
            to_state: Target state
            context: Optional dict with transition context (e.g., discovered signals)

        Returns:
            True if transition succeeded, False otherwise
        """
        valid_transitions = {
            "GREETING": ["DISCOVERY", "FRICTION_RESCUE"],
            "DISCOVERY": ["VALUE_DEMO", "QUALIFICATION", "FRICTION_RESCUE"],
            "VALUE_DEMO": ["QUALIFICATION", "NEXT_STEPS", "FRICTION_RESCUE"],
            "QUALIFICATION": [
                "NEXT_STEPS",
                "VALUE_DEMO",
            ],  # Can loop back for more demo
            "NEXT_STEPS": ["CLOSING", "QUALIFICATION"],  # Can clarify qualification
            "FRICTION_RESCUE": [
                "DISCOVERY",
                "VALUE_DEMO",
                "CLOSING",
            ],  # Flexible recovery
            "CLOSING": [],  # Terminal state
        }

        if to_state not in valid_transitions.get(from_state, []):
            logger.warning(f"Invalid transition: {from_state} → {to_state}")
            return False

        logger.info(f"State transition: {from_state} → {to_state}")

        # Log rich context if available
        if context:
            logger.info(f"Transition context: {context}")

        self.conversation_state = to_state
        return True

    def should_transition_to_qualification(self) -> bool:
        """Determine if enough context has been gathered to move to qualification.

        Returns:
            True if ready to transition to qualification
        """
        # Have we learned enough about their needs?
        has_use_case = self.discovered_signals.get("use_case") is not None
        has_pain_points = len(self.discovered_signals.get("pain_points", [])) > 0

        # Have we discovered any qualification signals?
        has_team_info = self.discovered_signals.get("team_size") is not None
        has_volume_info = self.discovered_signals.get("monthly_volume") is not None
        has_integration_needs = (
            len(self.discovered_signals.get("integration_needs", [])) > 0
        )

        # Transition when we have sufficient context
        return (has_use_case or has_pain_points) and (
            has_team_info or has_volume_info or has_integration_needs
        )

    def should_route_to_sales(self) -> bool:
        """Determine if this lead should be routed to sales vs self-serve.

        Returns:
            True if should route to sales, False for self-serve
        """
        # Primary qualification criteria (Tier 1)
        if self.discovered_signals.get("team_size", 0) >= 5:
            return True
        if self.discovered_signals.get("monthly_volume", 0) >= 100:
            return True
        if "salesforce" in self.discovered_signals.get("integration_needs", []):
            return True
        if "hubspot" in self.discovered_signals.get("integration_needs", []):
            return True

        # Secondary signals that indicate enterprise
        if (
            self.discovered_signals.get("budget_authority") == "decision_maker"
            and self.discovered_signals.get("urgency") == "high"
        ):
            return True

        # Complex use cases indicate enterprise
        complex_industries = ["healthcare", "finance", "legal"]
        return (
            self.discovered_signals.get("industry") in complex_industries
            and self.discovered_signals.get("team_size", 0) >= 3
        )

    async def call_with_retry_and_circuit_breaker(
        self,
        service_name: str,
        func: Callable[..., T],
        fallback_response: str | None = None,
        max_retries: int = 2,
    ) -> T | str | None:
        """Call a function with retry logic and circuit breaker protection.

        This method provides production-quality error handling for external service calls:
        - Circuit breaker prevents cascading failures
        - Exponential backoff retries transient errors
        - Graceful fallback when service is unavailable

        Args:
            service_name: Name of the service (for circuit breaker lookup)
            func: Async function to call
            fallback_response: Optional fallback response if all retries fail
            max_retries: Maximum number of retry attempts (default: 2, voice-optimized)

        Returns:
            Function result, fallback response, or None

        Example:
            result = await self.call_with_retry_and_circuit_breaker(
                service_name="amplitude",
                func=lambda: fetch_user_data(user_id),
                fallback_response="I'll continue without that data for now."
            )
        """
        # Get or create circuit breaker for this service
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()

        circuit_breaker = self.circuit_breakers[service_name]

        # Check if circuit breaker allows the call
        if not circuit_breaker.is_available():
            logger.warning(
                f"Circuit breaker open for {service_name}, using fallback response"
            )
            return fallback_response

        try:
            # Attempt call with retry logic (shorter delays for voice AI)
            result = await retry_with_exponential_backoff(
                func=func,
                max_retries=max_retries,
                base_delay=0.5,  # Voice-optimized: shorter initial delay
                max_delay=3.0,  # Voice-optimized: shorter max delay
            )

            # Mark success in circuit breaker
            circuit_breaker.call_succeeded()
            return result

        except Exception as e:
            # Mark failure in circuit breaker
            circuit_breaker.call_failed()

            logger.error(
                f"Failed to call {service_name} after retries: {e}", exc_info=True
            )

            # Return fallback response if provided
            return fallback_response

    async def handle_tool_with_error_recovery(
        self,
        context: RunContext,
        tool_name: str,
        tool_func: Callable[..., T],
        error_type: str = "tool_failure",
    ) -> T:
        """Wrap tool execution with graceful error handling.

        This method ensures tools fail gracefully with natural language responses
        and preserve conversation state even when errors occur.

        Args:
            context: RunContext from the tool
            tool_name: Name of the tool for logging
            tool_func: Async function that executes the tool logic
            error_type: Type of error for response generation

        Returns:
            Tool result

        Raises:
            ToolError: With user-friendly message if tool fails

        Example:
            return await self.handle_tool_with_error_recovery(
                context=context,
                tool_name="lookup_user_data",
                tool_func=lambda: self._fetch_user_data(user_id),
                error_type="connection_issue"
            )
        """
        try:
            # Preserve state before attempting tool call
            state_snapshot = {
                "signals": dict(self.discovered_signals),
                "notes": list(self.conversation_notes),
                "state": self.conversation_state,
            }

            # Execute tool
            result = await tool_func()

            # Tool succeeded, return result
            return result

        except asyncio.TimeoutError:
            # Handle timeout specifically
            logger.warning(f"Tool {tool_name} timed out")

            # Restore state
            self.preserve_conversation_state(state_snapshot)

            # Generate natural error response
            error_msg = self.get_error_response("timeout")

            raise ToolError(error_msg) from None

        except Exception as e:
            # Handle general errors
            logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)

            # Restore state
            self.preserve_conversation_state(state_snapshot)

            # Generate natural error response
            error_msg = self.get_error_response(error_type)

            raise ToolError(error_msg) from e

    # ========================================================================
    # Example Tool Implementations with Error Recovery
    # ========================================================================
    # These demonstrate the pattern for future tool implementations

    @function_tool()
    async def example_tool_with_timeout(
        self,
        context: RunContext,
        query: str,
    ) -> str:
        """Example tool showing timeout handling.

        This demonstrates how to implement timeout protection for long-running operations.
        When implementing real tools, replace this with actual API calls.

        Args:
            query: The query to process
        """
        return await self.handle_tool_with_error_recovery(
            context=context,
            tool_name="example_tool_with_timeout",
            tool_func=lambda: self._example_long_running_query(query),
            error_type="timeout",
        )

    async def _example_long_running_query(self, query: str) -> str:
        """Internal method with timeout protection.

        This would be replaced with actual API calls in production.
        """
        try:
            # Simulate long-running operation with timeout
            result = await asyncio.wait_for(
                self._simulate_slow_api_call(query), timeout=5.0
            )
            return result
        except asyncio.TimeoutError as e:
            raise asyncio.TimeoutError(
                f"Query '{query}' timed out after 5 seconds"
            ) from e

    async def _simulate_slow_api_call(self, query: str) -> str:
        """Simulate a slow API call for testing."""
        await asyncio.sleep(1.0)  # Simulate network latency
        return f"Results for: {query}"

    @function_tool()
    async def example_tool_with_circuit_breaker(
        self,
        context: RunContext,
        user_id: str,
    ) -> str:
        """Example tool showing circuit breaker usage.

        This demonstrates how to protect against cascading failures when
        external services become unavailable. The circuit breaker opens after
        repeated failures, preventing additional load on struggling services.

        Args:
            user_id: User ID to look up
        """
        result = await self.call_with_retry_and_circuit_breaker(
            service_name="amplitude",
            func=lambda: self._fetch_example_user_data(user_id),
            fallback_response="I'll continue helping you without that user data.",
            max_retries=2,
        )

        if isinstance(result, str):
            # Fallback response was returned
            return result

        # Normal response with data
        return f"Found user data: {result}"

    async def _fetch_example_user_data(self, user_id: str) -> dict[str, Any]:
        """Internal method to fetch user data.

        This would be replaced with actual API calls in production.
        """
        # Simulate API call
        await asyncio.sleep(0.5)
        return {"user_id": user_id, "status": "active"}

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # TTS Fallback Configuration
    # Using FallbackAdapter to ensure reliable speech synthesis
    # Primary: ElevenLabs Turbo v2.5 with Rachel voice (high quality, natural speech)
    # Fallback: OpenAI TTS tts-1 with nova voice (reliable backup)
    logger.info(
        "Initializing TTS with fallback: ElevenLabs (primary) -> OpenAI (fallback)"
    )

    tts_provider = tts.FallbackAdapter(
        [
            # Primary TTS: ElevenLabs Turbo v2.5 with Rachel voice
            # - High quality, natural-sounding voice
            # - Low latency for conversational AI
            elevenlabs.TTS(
                model="eleven_turbo_v2_5",
                voice="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
            ),
            # Fallback TTS: OpenAI TTS via LiveKit Inference
            # - Reliable backup when ElevenLabs is unavailable
            # - Nova voice provides warm, engaging tone
            # - Using LiveKit Inference (no plugin needed, automatically configured)
            "openai/tts-1:nova",
        ]
    )

    # Set up a voice AI pipeline using OpenAI, ElevenLabs, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        # Using Deepgram Nova-2 for high-quality transcription
        # Note: Use "deepgram/nova-2-phonecall" for telephony applications for optimized call quality
        stt="deepgram/nova-2:en",
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm="openai/gpt-4.1-mini",
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # Using FallbackAdapter for reliability: ElevenLabs (primary) with OpenAI (fallback)
        tts=tts_provider,
        # VAD (Voice Activity Detection) and turn detection work together for natural conversation flow
        # See more at https://docs.livekit.io/agents/build/turns
        #
        # turn_detection: LiveKit MultilingualModel provides contextually-aware turn detection
        # - Understands when a user has finished speaking vs. natural pauses
        # - Supports multiple languages and accents
        # - Uses semantic understanding to avoid premature interruptions
        turn_detection=MultilingualModel(),
        # vad: Pre-warmed Silero VAD (loaded in prewarm function for faster startup)
        # - Detects presence of human speech vs. silence/noise
        # - Uses 300ms silence threshold (default) for responsive turn-taking
        # - Enables interruption handling - user can interrupt agent mid-response
        vad=ctx.proc.userdata["vad"],
        # preemptive_generation: Begin generating LLM response before user finishes speaking
        # - Dramatically reduces perceived latency (target: <700ms total response time)
        # - Agent starts thinking while user is still completing their thought
        # - Combined with 300ms VAD threshold, enables natural conversation flow
        # - Critical for voice AI responsiveness - users expect human-like reaction times
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    # Error handling for TTS and other components
    # Logs when fallback mechanisms are triggered or unrecoverable errors occur
    @session.on("error")
    def _on_error(event):
        """Handle errors from STT, LLM, TTS, or other components.

        The FallbackAdapter automatically handles recoverable errors by switching
        to backup providers. This handler logs both recoverable and unrecoverable
        errors for monitoring and debugging.
        """
        error = event.error
        source = type(event.source).__name__

        if error.recoverable:
            # Recoverable error - FallbackAdapter will handle automatically
            logger.warning(
                f"TTS/STT/LLM error (recoverable, switching to fallback): "
                f"source={source}, error={error}"
            )
        else:
            # Unrecoverable error - all providers failed
            logger.error(
                f"TTS/STT/LLM error (unrecoverable, all providers failed): "
                f"source={source}, error={error}"
            )

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=PandaDocTrialistAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
