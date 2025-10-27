import logging
import os
from typing import Dict, Any, Optional

import httpx
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

    @function_tool()
    async def unleash_search_knowledge(
        self,
        context: RunContext,
        query: str,
        category: Optional[str] = None,
        response_format: str = "concise"
    ) -> Dict[str, Any]:
        """Search PandaDoc knowledge base and provide actionable guidance.

        Use this tool when the user asks about PandaDoc features, pricing, integrations, or needs help.
        This tool both searches for information AND suggests next steps.

        Args:
            query: Natural language question about PandaDoc
            category: Optional - filter by "features", "pricing", "integrations", "troubleshooting"
            response_format: "concise" for essential info (voice-optimized), "detailed" for comprehensive results
        """
        # Voice-optimized filler (keep it short for low latency)
        await context.say("Let me find that for you...")

        try:
            # Get Unleash configuration
            unleash_api_key = os.getenv("UNLEASH_API_KEY")
            if not unleash_api_key:
                raise ToolError("PandaDoc knowledge base is not configured. Let me help you directly instead.")

            unleash_base_url = os.getenv("UNLEASH_BASE_URL", "https://e-api.unleash.so")
            unleash_assistant_id = os.getenv("UNLEASH_ASSISTANT_ID")  # Optional

            # Build request payload (Unleash API structure)
            request_payload = {
                "query": query,
                "contentSearch": True,  # Search content, not just titles
                "semanticSearch": True,  # Enable AI-powered semantic search
                "paging": {
                    "pageSize": 3 if response_format == "concise" else 5,
                    "pageNumber": 0
                }
            }

            # Add optional filters if category provided
            if category:
                request_payload["filters"] = {
                    "type": [category]  # Filter by resource type
                }

            # Add assistant ID if configured
            if unleash_assistant_id:
                request_payload["assistantId"] = unleash_assistant_id

            # Make API request with proper error handling
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{unleash_base_url}/search",
                    headers={
                        "Authorization": f"Bearer {unleash_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_payload,
                    timeout=5.0  # 5 second timeout for voice responsiveness
                )

                # Check for API errors
                if response.status_code == 400:
                    logger.warning(f"Unleash API bad request: {response.text}")
                    raise ToolError("I couldn't understand that search. Could you rephrase your question?")
                elif response.status_code == 401:
                    logger.error("Unleash API authentication failed")
                    raise ToolError("I'm having trouble accessing the knowledge base. Let me help you directly.")
                elif response.status_code >= 500:
                    logger.error(f"Unleash API server error: {response.status_code}")
                    raise ToolError("The knowledge base is temporarily unavailable. I can still help you though!")

                response.raise_for_status()
                data = response.json()

            # Extract results
            results = data.get("results", [])
            total_results = data.get("totalResults", 0)

            # Voice-optimized response formatting
            if response_format == "concise":
                # Return only the most relevant result for voice
                if results:
                    top_result = results[0]
                    resource = top_result.get("resource", {})
                    snippet = top_result.get("snippet", "")

                    return {
                        "answer": snippet or resource.get("title", ""),
                        "details": resource.get("description", ""),
                        "action": self._determine_next_action(query, results),
                        "found": True,
                        "total_results": total_results
                    }
                else:
                    return {
                        "answer": None,
                        "action": "offer_human_help",
                        "found": False,
                        "total_results": 0
                    }
            else:
                # Return detailed results for follow-up
                return {
                    "results": [
                        {
                            "title": r.get("resource", {}).get("title"),
                            "snippet": r.get("snippet"),
                            "highlights": r.get("highlights", [])
                        }
                        for r in results
                    ],
                    "total_results": total_results,
                    "suggested_followup": self._determine_next_action(query, results),
                    "request_id": data.get("requestId")  # For debugging
                }

        except httpx.TimeoutException:
            # Timeout - offer alternative help
            logger.warning("Unleash API timeout after 5 seconds")
            raise ToolError(
                "The search is taking longer than expected. "
                "Let me help you directly - what specific part of PandaDoc would you like to explore?"
            )
        except httpx.HTTPError as e:
            # Network or HTTP error
            logger.error(f"Unleash API HTTP error: {e}")
            raise ToolError(
                "I'm having trouble reaching the knowledge base right now. "
                "But I can still walk you through PandaDoc - what would you like to know?"
            )
        except Exception as e:
            # Unexpected error - log for debugging but don't expose to user
            logger.error(f"Unexpected Unleash API error: {type(e).__name__}: {e}")
            raise ToolError(
                "Something went wrong with the search. "
                "Let me help you another way - what's your question about PandaDoc?"
            )

    def _determine_next_action(self, query: str, results: list) -> str:
        """Determine the best next action based on query and results.

        This helper method analyzes the user's query and search results to determine
        the most appropriate follow-up action for the conversation flow.
        """
        if not results:
            return "offer_human_help"

        query_lower = query.lower()

        # Analyze query intent
        if any(word in query_lower for word in ["how", "setup", "configure", "create"]):
            return "offer_walkthrough"
        elif any(word in query_lower for word in ["pricing", "cost", "plan", "tier"]):
            return "discuss_roi"
        elif any(word in query_lower for word in ["integration", "connect", "sync", "api"]):
            return "check_specific_integration"
        elif any(word in query_lower for word in ["error", "problem", "issue", "broken"]):
            return "troubleshoot_issue"
        else:
            return "clarify_needs"

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
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts="elevenlabs/eleven_turbo_v2_5:21m00Tcm4TlvDq8ikWAM",  # Rachel voice, Turbo v2.5
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
