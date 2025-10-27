import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class PandaDocTrialistAgent(Agent):
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
        self.trial_activity = None  # "created_template", "sent_document", "stuck_on_feature"

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
            "QUALIFICATION": ["NEXT_STEPS", "VALUE_DEMO"],  # Can loop back for more demo
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
        if (
            self.discovered_signals.get("industry") in complex_industries
            and self.discovered_signals.get("team_size", 0) >= 3
        ):
            return True

        return False

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

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt="assemblyai/universal-streaming:en",
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm="openai/gpt-4.1-mini",
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
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
