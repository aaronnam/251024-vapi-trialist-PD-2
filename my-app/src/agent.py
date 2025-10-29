import asyncio
import json
import logging
import os
import re
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Optional

import dateparser
import httpx
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
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
from livekit.plugins import deepgram, elevenlabs, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Import analytics queue utility
# Note: Import after load_dotenv to ensure environment variables are loaded
try:
    from utils.analytics_queue import send_to_analytics_queue
    from utils.telemetry import setup_observability
except ImportError:
    # Fallback for different import contexts
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from utils.analytics_queue import send_to_analytics_queue
    from utils.telemetry import setup_observability


class PandaDocTrialistAgent(Agent):
    def __init__(self, user_email: Optional[str] = None) -> None:
        # Build instructions with optional email context
        base_instructions = """You are Sarah, a friendly and knowledgeable Trial Success Specialist voice AI agent at PandaDoc. - currently in beta.

## CRITICAL: CONSENT PROTOCOL
The initial greeting asks for transcription consent. You MUST handle the response appropriately.

### LISTEN FOR CONSENT RESPONSE
After the opening greeting, the user will respond with consent or decline.

Affirmative consent (proceed with conversation):
- ✅ "Yes" / "Yeah" / "Sure" / "Okay" / "Fine" / "Go ahead" / "That's fine" / "Yep"

Decline or unclear (end conversation gracefully):
- ❌ "No" / "Not really" / "I'd rather not" / "Can we skip that?" / Unclear response

### IF USER CONSENTS:
Respond warmly: "Great! Thanks for that. I'm here to help you get the most out of PandaDoc. How's your trial going? Any roadblocks I can help clear up?"

Then proceed with normal conversation flow.

### IF USER DECLINES:
"I completely understand. Unfortunately, I'm not able to assist without transcription enabled, as it's required for our service quality. I'd be happy to have you reach out to our support team via email at support@pandadoc.com, or you can visit our Help Center at help.pandadoc.com. Have a great day!"

Then remain silent - do not continue the conversation.

### IF USER ASKS QUESTIONS ABOUT TRANSCRIPTION:
Be prepared to answer:
- "Why do you need to transcribe?" → "It helps us improve the AI assistant and ensure we're giving you accurate information about PandaDoc."
- "What happens to the transcription?" → "It's used internally for quality assurance and training our AI. We don't share it with third parties."
- "How long do you keep it?" → "We retain it according to our privacy policy for quality review purposes."
- "Can I get a copy?" → "Yes, you can request your conversation data by emailing support@pandadoc.com."

After answering their question, re-ask: "Are you comfortable proceeding with the transcription?"

### IMPORTANT:
- NEVER proceed with PandaDoc questions until consent is obtained
- If consent is unclear, ask once more: "Just to confirm - are you okay with our conversation being transcribed?"
- Track consent in conversation state

## SMARTER TOOL USAGE
Use unleash_search_knowledge() selectively - NOT for everything.

**DO NOT search for:**
- Simple greetings: "Hello", "Hi", "Hey", "Good morning", "Good afternoon"
- Thank you messages: "Thanks", "Thank you", "Appreciate it"
- Acknowledgments: "Okay", "Got it", "I see", "Understood"
- Casual chat: "How are you?", "What's up?", "Nice to meet you"
- Goodbyes: "Bye", "Goodbye", "Talk soon"
- Non-PandaDoc topics: "weather", "news", "jokes", "general knowledge"

For these, respond warmly and naturally WITHOUT calling tools.

**DO search for:**
- Any feature/product question: "How do I create a template?", "What integrations do you support?"
- Troubleshooting requests: "I'm stuck on...", "How do I fix..."
- Pricing/plan questions: "How much does it cost?", "What's included in the plan?"
- Use case questions: "Can I use PandaDoc for contracts?", "Do you support e-signatures?"
- Capability questions: "What can PandaDoc do?", "Does it integrate with Salesforce?"

When searching, use:
```
unleash_search_knowledge(query="[user's exact question]", response_format="concise")
```

RESPONSE PATTERNS:
• Successful search with results → "Based on what I found: [provide the answer]"
• Search error/timeout → "I couldn't reach the knowledge base, but I can help you with [topic]: [provide guidance]"
• No results found → "I didn't find specific docs on that, but here's how PandaDoc handles [topic]..."
• For ANY failed search → acknowledge the search status before offering direct help

## CRITICAL BOOKING RULES
1. ONLY offer to book sales meetings for users who meet qualification criteria (5+ users, 100+ docs/month, or enterprise needs)
2. NEVER offer "human assistance" or "talk to someone" for unqualified users
3. For unqualified users, guide them to self-serve resources and features
4. When a QUALIFIED user requests a meeting ("schedule a call", "book a meeting", "talk to sales"), you MUST use book_sales_meeting tool IMMEDIATELY

## Tool Usage Priority
1. unleash_search_knowledge - ALWAYS use for ANY PandaDoc questions
2. book_sales_meeting - MANDATORY for qualified users requesting meetings

IMPORTANT: When a QUALIFIED user says "let's schedule a meeting", "I'd like to talk to sales", "can we book a call", or similar:
→ You MUST call book_sales_meeting() immediately
→ Do NOT just acknowledge - actually call the tool to book the meeting

## Your Role
You help Pandadoc trial users maximize their PandaDoc experience through personalized, voice-based enablement.
Your goal is to understand their needs, provide immediate value through knowledge base search, and identify qualified opportunities naturally.

## Conversation Style
- Warm and conversational, not scripted or robotic
- Use active listening cues: "mm-hmm", "I see", "got it"
- Keep responses concise (2-3 sentences max for voice)
- Ask one question at a time ONLY during qualification discovery
- Build on what they say naturally

## Error Handling Patterns (CRITICAL)
When unleash_search_knowledge returns an error or no results:
1. If error: Say "I had trouble searching, but I can help you with [topic]" then provide direct guidance
2. If no results: Say "I didn't find specific documentation on that, but here's how PandaDoc handles [topic]"
3. For non-PandaDoc topics (like quantum computing): Redirect - "That's outside PandaDoc's scope, but I can help you with document management, templates, or integrations"
4. ALWAYS provide PandaDoc-specific guidance, never general information
5. Reference that guidance came "from what I know" when search fails

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
- Listen for: mentions of Salesforce, HubSpot, CRM systems, APIs, embedded workflows, webhooks
- Also listen for: "programmatic", "automated", "volume", "bulk", "API", "embedded", "white-label"
- Enterprise signal: Any CRM integration, API usage, or embedded document workflows

**Urgency & Timeline:**
- Naturally ask: "When would you ideally like to have this up and running for your team?"
- Listen for: urgency indicators, deadline mentions, current pain points
- Enterprise signal: Urgent need, replacing current tool

## Qualification Tiers (Track Internally)
**Tier 1 - Sales-Ready:** 5+ users OR 100+ docs/month OR Salesforce/HubSpot integration needs OR API/embedded volume workflows (programmatic document generation)
**Tier 2 - Self-Serve:** <5 users, individual users, simple use cases

## Response Patterns

For QUALIFIED users experiencing friction:
"I can see PandaDoc would be valuable for your team. Would you like me to book a quick call with our sales team to discuss enterprise features and pricing?"

For UNQUALIFIED users needing help:
"Let me show you how to do that in PandaDoc. [provide specific guidance]. Would you like to try that now?"

NEVER say:
- "Let me connect you with someone"
- "A human can help you with that"
- "Contact support"
- "Reach out to our team"

UNLESS the user is qualified for sales (Tier 1).

## Operating Principles
- Provide value first, qualify second
- Never feel like an interrogation
- If they're stuck, help them immediately
- Build trust through expertise
- Qualify through understanding, not asking"""

        # Add email context if available
        email_context = ""
        if user_email:
            email_context = f"""

## USER EMAIL CONTEXT
You have the user's email from their registration: {user_email}

When booking meetings with book_sales_meeting, you can use this email automatically.
If you need their email for any reason, you already have it - don't ask for it again."""

        # Combine instructions
        full_instructions = base_instructions + email_context

        super().__init__(instructions=full_instructions)

        # Store user email for use in tools
        self.user_email = user_email

        # Conversation flow state
        self.conversation_state = "GREETING"

        # Core qualification signals (drive routing and business logic)
        self.discovered_signals = {
            # Primary qualification criteria
            "team_size": 0,
            "monthly_volume": 0,
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

        # Consent tracking (for legal compliance)
        self.consent_given = False
        self.consent_timestamp = None

        # Analytics: Session data collection (Phase 1 - Lightweight Collection)
        # This data is exported via shutdown callback - minimal overhead during conversation
        self.session_data = {
            "start_time": datetime.now().isoformat(),
            "tool_calls": [],  # Track tool usage for analytics
        }
        self.usage_collector = metrics.UsageCollector()  # LiveKit built-in metrics

        # Cost tracking for direct provider APIs (Priority 4, Task 4.1)
        self.session_costs = {
            "openai_tokens": 0,
            "openai_cost": 0.0,
            "deepgram_minutes": 0.0,
            "deepgram_cost": 0.0,
            "elevenlabs_characters": 0,
            "elevenlabs_cost": 0.0,
            "unleash_searches": 0,  # Keep existing Unleash tracking
            "total_estimated_cost": 0.0,
        }

        # Cost limits (configurable via environment)
        self.cost_limits = {
            "session_max": float(os.getenv("SESSION_COST_LIMIT", "5.0")),
            "daily_max": float(os.getenv("DAILY_COST_LIMIT", "100.0")),
        }

        # Provider pricing (as of 2025-10, update periodically)
        self.provider_pricing = {
            "openai_gpt4_mini_input": 0.000150 / 1000,  # $0.150 per 1M input tokens
            "openai_gpt4_mini_output": 0.000600 / 1000,  # $0.600 per 1M output tokens
            "deepgram_nova2": 0.0043 / 60,  # $0.0043 per minute
            "elevenlabs_turbo": 0.15 / 1000000,  # $150 per 1M characters
        }

        # Circuit breakers for direct provider APIs (Priority 4, Task 4.2)
        self.circuit_breakers = {
            "openai": {"failures": 0, "last_failure": None, "state": "closed"},
            "deepgram": {"failures": 0, "last_failure": None, "state": "closed"},
            "elevenlabs": {"failures": 0, "last_failure": None, "state": "closed"},
            "unleash": {"failures": 0, "last_failure": None, "state": "closed"},
        }

        self.circuit_config = {
            "failure_threshold": 3,  # Open circuit after N failures
            "cooldown_seconds": 60,  # Reset after 1 minute
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

    def check_circuit_breaker(self, provider: str) -> bool:
        """Check if provider circuit breaker allows requests.

        Args:
            provider: Provider name ("openai", "deepgram", "elevenlabs", "unleash")

        Returns:
            True if circuit is closed (requests allowed), False if open (blocked)
        """
        if provider not in self.circuit_breakers:
            logger.warning(f"Unknown provider for circuit breaker: {provider}")
            return True  # Fail open for unknown providers

        breaker = self.circuit_breakers[provider]

        # Reset if cooldown period has passed
        if breaker["last_failure"]:
            time_since_failure = (
                datetime.now() - breaker["last_failure"]
            ).total_seconds()
            if time_since_failure > self.circuit_config["cooldown_seconds"]:
                logger.info(
                    f"Circuit breaker reset for {provider} after {time_since_failure:.1f}s cooldown"
                )
                breaker["failures"] = 0
                breaker["state"] = "closed"
                breaker["last_failure"] = None

        # Check if circuit is open
        if breaker["failures"] >= self.circuit_config["failure_threshold"]:
            breaker["state"] = "open"
            logger.warning(
                f"Circuit breaker OPEN for {provider}: {breaker['failures']} consecutive failures"
            )
            return False

        return True

    def record_provider_failure(self, provider: str, error: Exception):
        """Record a failure from a provider API.

        Args:
            provider: Provider name ("openai", "deepgram", "elevenlabs", "unleash")
            error: The exception that occurred
        """
        if provider not in self.circuit_breakers:
            logger.warning(f"Unknown provider for circuit breaker: {provider}")
            return

        breaker = self.circuit_breakers[provider]
        breaker["failures"] += 1
        breaker["last_failure"] = datetime.now()

        logger.error(
            f"Provider failure recorded for {provider}: {error} "
            f"(failures: {breaker['failures']}/{self.circuit_config['failure_threshold']})"
        )

    def record_provider_success(self, provider: str):
        """Record a successful API call, resetting failure count.

        Args:
            provider: Provider name ("openai", "deepgram", "elevenlabs", "unleash")
        """
        if provider not in self.circuit_breakers:
            return

        breaker = self.circuit_breakers[provider]
        if breaker["failures"] > 0:
            logger.info(
                f"Circuit breaker reset for {provider} after successful request"
            )
            breaker["failures"] = 0
            breaker["state"] = "closed"
            breaker["last_failure"] = None

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

        # API or embedded volume flows (technical integration signal)
        integration_needs = self.discovered_signals.get("integration_needs", [])
        if "api" in integration_needs or "embedded" in integration_needs:
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

    def _detect_signals(self, message: str) -> None:
        """Lightweight signal detection using simple pattern matching.

        No heavy NLP - just regex patterns and keyword matching.
        Defer complex analysis to the analytics pipeline.

        Args:
            message: User message to analyze for signals
        """
        message_lower = message.lower()

        # Team size detection (simple regex)
        team_patterns = [
            r"\b(\d+)\s*(?:people|users|team|employees|members)\b",
            r"\bteam\s+of\s+(\d+)\b",
            r"\b(\d+)\s+person\s+team\b",
        ]
        for pattern in team_patterns:
            if match := re.search(pattern, message_lower):
                self.discovered_signals["team_size"] = int(match.group(1))
                break

        # Document volume detection
        volume_patterns = [
            r"\b(\d+)\s*(?:documents?|docs?|contracts?|proposals?)\s*(?:per|a|every)?\s*(?:month|week|day)\b",
            r"\b(?:send|create|process)\s*about\s*(\d+)\b",
        ]
        for pattern in volume_patterns:
            if match := re.search(pattern, message_lower):
                volume = int(match.group(1))
                # Normalize to monthly if needed
                if "week" in message_lower:
                    volume *= 4
                elif "day" in message_lower:
                    volume *= 20  # ~20 business days/month
                self.discovered_signals["monthly_volume"] = volume
                break

        # Integration mentions (keyword matching)
        integrations = [
            "salesforce",
            "hubspot",
            "zapier",
            "api",
            "crm",
            "embedded",
            "webhook",
        ]
        mentioned = [i for i in integrations if i in message_lower]
        if mentioned:
            existing = self.discovered_signals.get("integration_needs", [])
            self.discovered_signals["integration_needs"] = list(
                set(existing + mentioned)
            )

        # Urgency detection (simple keywords)
        urgency_keywords = {
            "high": ["urgent", "asap", "immediately", "this week", "right away"],
            "medium": ["soon", "this month", "next week"],
            "low": ["eventually", "sometime", "future", "down the road"],
        }
        for level, keywords in urgency_keywords.items():
            if any(word in message_lower for word in keywords):
                self.discovered_signals["urgency"] = level
                break

        # Industry detection (simple keyword matching)
        industries = ["healthcare", "legal", "real estate", "finance", "sales", "hr"]
        for industry in industries:
            if industry in message_lower:
                self.discovered_signals["industry"] = industry
                break

    def preserve_conversation_state(self, snapshot: dict) -> None:
        """Restore conversation state from snapshot (for error recovery).

        This method allows the agent to resume from a saved state after
        failures or interruptions, maintaining conversation continuity.

        Args:
            snapshot: Dictionary containing saved conversation state with keys:
                - "signals": discovered_signals dict
                - "notes": conversation_notes list
                - "state": conversation_state string
        """
        if "signals" in snapshot:
            self.discovered_signals.update(snapshot["signals"])
        if "notes" in snapshot:
            self.conversation_notes = snapshot.get("notes", [])
        if "state" in snapshot:
            self.conversation_state = snapshot.get("state", "GREETING")

        logger.info(
            f"Restored conversation state from snapshot: {snapshot.get('state', 'UNKNOWN')}"
        )

    async def call_with_retry_and_circuit_breaker(
        self,
        service_name: str,
        func: callable,
        fallback_response: Any,
        max_retries: int = 3,
    ) -> Any:
        """Call external service with retry logic and circuit breaker.

        Implements exponential backoff retry strategy for resilient external
        service calls. Returns fallback response if all retries fail.

        Args:
            service_name: Name of the service being called (for logging)
            func: Async callable to execute
            fallback_response: Response to return if all retries fail
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Result from func() on success, or fallback_response on failure
        """
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"{service_name} failed after {max_retries} attempts: {e}"
                    )
                    return fallback_response
                await asyncio.sleep(2**attempt)  # Exponential backoff: 1s, 2s, 4s
        return fallback_response

    @function_tool()
    async def unleash_search_knowledge(
        self,
        context: RunContext,
        query: str,
        category: Optional[str] = None,
        response_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search PandaDoc knowledge base - REQUIRED for ALL PandaDoc questions.

        THIS IS A MANDATORY TOOL. You MUST call this for:
        - ANY question starting with: how, what, when, where, why, can, does, is
        - ANY mention of: documents, templates, signing, sending, pricing, features, integrations
        - ANY request for help, guidance, or troubleshooting
        - LITERALLY ANYTHING related to PandaDoc functionality

        DO NOT attempt to answer from memory. ALWAYS search first.

        Args:
            query: The user's exact question - pass it VERBATIM, do not modify
            category: Optional - ONLY for "features", "pricing", "integrations", or "troubleshooting"
            response_format: Use "concise" (default) for voice - never use "detailed"

        Returns:
            Dict with search results to interpret for the user
        """
        # Note: Tools in LiveKit should not speak directly - they return data for the agent to interpret

        # Validate and normalize response_format - default to concise for voice
        if not response_format or response_format not in ["concise", "detailed"]:
            if response_format:
                logger.warning(
                    f"Invalid response_format '{response_format}', defaulting to 'concise'"
                )
            response_format = "concise"

        try:
            # ============================================================================
            # Get Unleash configuration
            #
            # CRITICAL: LiveKit Cloud secrets OVERRIDE these defaults!
            #
            # Even though this code has correct fallback values (like the URL below),
            # if you set these as secrets in LiveKit Cloud, the Cloud values will
            # override the defaults. This means:
            #
            # 1. UNLEASH_BASE_URL in LiveKit Cloud MUST be: https://e-api.unleash.so
            #    (NOT https://api.unleash.so - the "e-" prefix is required)
            #
            # 2. After updating secrets in LiveKit Cloud, you MUST restart the agent:
            #    `lk agent restart`
            #
            # 3. Old worker processes will continue using old secret values until restarted
            #
            # See AGENTS.md for complete secrets management documentation.
            # ============================================================================
            unleash_api_key = os.getenv("UNLEASH_API_KEY")
            if not unleash_api_key:
                raise ToolError(
                    "PandaDoc knowledge base is not configured. Let me help you directly instead."
                )

            unleash_base_url = os.getenv("UNLEASH_BASE_URL", "https://e-api.unleash.so")
            unleash_assistant_id = os.getenv("UNLEASH_ASSISTANT_ID")  # Optional

            # Get Intercom app ID - defaults to "intercom" if not configured
            intercom_app_id = os.getenv("UNLEASH_INTERCOM_APP_ID", "intercom")

            # Priority 4, Task 4.2: Check circuit breaker before making API call
            if not self.check_circuit_breaker("unleash"):
                logger.warning("Unleash circuit breaker is open, skipping search")
                raise ToolError(
                    "I'm having trouble accessing the knowledge base right now. "
                    "Let me connect you with our team who can help directly."
                )

            # Build request payload (Unleash API structure)
            request_payload = {
                "query": query,
                "contentSearch": True,  # Search content, not just titles
                "semanticSearch": True,  # Enable AI-powered semantic search
                "paging": {
                    "pageSize": 3 if response_format == "concise" else 5,
                    "pageNumber": 0,
                },
            }

            # Build filters - always include Intercom source filter
            filters = {
                "appId": [intercom_app_id]  # Filter to Intercom source only
            }

            # Add optional category filter if provided
            if category:
                filters["type"] = [category]

            # Apply filters to request
            request_payload["filters"] = filters
            logger.info(
                f"Searching Intercom source (appId: {intercom_app_id}) for query: '{query}'"
            )

            # Add assistant ID if configured
            if unleash_assistant_id:
                request_payload["assistantId"] = unleash_assistant_id

            # Make API request with proper error handling
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{unleash_base_url}/search",
                    headers={
                        "Authorization": f"Bearer {unleash_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_payload,
                    timeout=10.0,  # 10 second timeout balanced for voice response
                )

                # Check for API errors
                if response.status_code == 400:
                    logger.warning(f"Unleash API bad request: {response.text}")
                    raise ToolError(
                        "I couldn't understand that search. Could you rephrase your question?"
                    )
                elif response.status_code == 401:
                    logger.error("Unleash API authentication failed")
                    raise ToolError(
                        "I'm having trouble accessing the knowledge base. Let me help you directly."
                    )
                elif response.status_code >= 500:
                    logger.error(f"Unleash API server error: {response.status_code}")
                    raise ToolError(
                        "The knowledge base is temporarily unavailable. I can still help you though!"
                    )

                response.raise_for_status()
                data = response.json()  # httpx returns dict directly, not a coroutine

            # Priority 4, Task 4.2: Record successful API call
            self.record_provider_success("unleash")

            # Extract results
            results = data.get("results", [])
            total_results = data.get("totalResults", 0)

            # Analytics: Track tool usage (Phase 1 - Lightweight Collection)
            self.session_data["tool_calls"].append(
                {
                    "tool": "unleash_search_knowledge",
                    "query": query,
                    "category": category,
                    "timestamp": datetime.now().isoformat(),
                    "results_found": bool(results),
                    "total_results": total_results,
                }
            )

            # Priority 4, Task 4.1: Track Unleash search count
            self.session_costs["unleash_searches"] += 1

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
                        "total_results": total_results,
                    }
                else:
                    return {
                        "answer": None,
                        "action": "offer_human_help",
                        "found": False,
                        "total_results": 0,
                    }
            else:
                # Return detailed results for follow-up
                return {
                    "results": [
                        {
                            "title": r.get("resource", {}).get("title"),
                            "snippet": r.get("snippet"),
                            "highlights": r.get("highlights", []),
                        }
                        for r in results
                    ],
                    "total_results": total_results,
                    "suggested_followup": self._determine_next_action(query, results),
                    "request_id": data.get("requestId"),  # For debugging
                }

        except httpx.TimeoutException as e:
            # Timeout - offer alternative help
            logger.warning("Unleash API timeout after 10 seconds")
            # Priority 4, Task 4.2: Record failure
            self.record_provider_failure("unleash", e)
            raise ToolError(
                "The search is taking longer than expected. "
                "Let me help you directly - what specific part of PandaDoc would you like to explore?"
            )
        except httpx.HTTPError as e:
            # Network or HTTP error
            logger.error(f"Unleash API HTTP error: {e}")
            # Priority 4, Task 4.2: Record failure
            self.record_provider_failure("unleash", e)
            raise ToolError(
                "I'm having trouble reaching the knowledge base right now. "
                "But I can still walk you through PandaDoc - what would you like to know?"
            )
        except Exception as e:
            # Unexpected error - log for debugging but don't expose to user
            logger.error(f"Unexpected Unleash API error: {type(e).__name__}: {e}")
            # Priority 4, Task 4.2: Record failure
            self.record_provider_failure("unleash", e)
            raise ToolError(
                "Something went wrong with the search. "
                "Let me help you another way - what's your question about PandaDoc?"
            )

    @function_tool()
    async def book_sales_meeting(
        self,
        context: RunContext,
        customer_name: str,
        customer_email: Optional[str] = None,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """MANDATORY: Book sales meetings for QUALIFIED users only.

        THIS IS A MANDATORY TOOL FOR QUALIFIED USERS. You MUST call this when:
        - User explicitly requests a meeting: "schedule a call", "book a meeting", "talk to sales", "meet with your team"
        - User is QUALIFIED (team_size >= 5 OR monthly_volume >= 100 OR Salesforce/HubSpot integration needs)
        - User agrees to booking after you offer

        Examples where you MUST use this tool:
        - "Can we schedule a meeting to discuss enterprise features?" → book_sales_meeting(customer_name="...")
        - "I'd like to talk to someone on your sales team" → book_sales_meeting(customer_name="...")
        - "Let's book a call for tomorrow at 2pm" → book_sales_meeting(customer_name="...", preferred_date="tomorrow", preferred_time="2pm")

        DO NOT use this tool for:
        - UNQUALIFIED users (team_size < 5, monthly_volume < 100, no CRM needs)
        - General support questions
        - Users who haven't agreed to book

        For UNQUALIFIED users: Guide them to self-serve resources instead.

        Args:
            customer_name: Full name of the customer
            customer_email: Optional email address for calendar invite (defaults to user's registration email)
            preferred_date: Optional date preference (e.g., "tomorrow", "next Tuesday")
            preferred_time: Optional time preference (e.g., "2pm", "morning")

        Returns:
            Dict with booking_status, meeting_link, and meeting_time
        """

        # Use stored email if not provided
        email_to_use = customer_email or self.user_email

        if not email_to_use:
            raise ToolError(
                "I need your email address to send the meeting invite. What's your email?"
            )

        # CRITICAL: Qualification check
        if not self.should_route_to_sales():
            raise ToolError(
                "I can help you explore PandaDoc features yourself. "
                "What specific capability would you like to learn about?"
            )

        try:
            # Initialize Google Calendar client
            service = self._get_calendar_service()

            # Parse date/time preferences (default to next business day 10am)
            meeting_datetime = self._parse_meeting_time(preferred_date, preferred_time)

            # Create event
            event = {
                "summary": f"PandaDoc Sales Consultation - {customer_name}",
                "description": (
                    f"Sales consultation for qualified trial user\n\n"
                    f"Customer: {customer_name}\n"
                    f"Email: {email_to_use}\n"
                    f"Qualification Signals:\n"
                    f"- Team Size: {self.discovered_signals.get('team_size', 'Unknown')}\n"
                    f"- Monthly Volume: {self.discovered_signals.get('monthly_volume', 'Unknown')}\n"
                    f"- Integration Needs: {', '.join(self.discovered_signals.get('integration_needs', []))}\n"
                    f"- Industry: {self.discovered_signals.get('industry', 'Unknown')}"
                ),
                "start": {
                    "dateTime": meeting_datetime.isoformat(),
                    "timeZone": os.getenv(
                        "GOOGLE_CALENDAR_TIMEZONE", "America/Toronto"
                    ),
                },
                "end": {
                    "dateTime": (meeting_datetime + timedelta(minutes=30)).isoformat(),
                    "timeZone": os.getenv(
                        "GOOGLE_CALENDAR_TIMEZONE", "America/Toronto"
                    ),
                },
                "attendees": [
                    {"email": email_to_use},
                ],
                "conferenceData": {
                    "createRequest": {
                        "requestId": f"pandadoc-{int(datetime.now().timestamp())}",
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 60},
                        {"method": "popup", "minutes": 10},
                    ],
                },
            }

            # Create the event
            created_event = (
                service.events()
                .insert(
                    calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
                    body=event,
                    conferenceDataVersion=1,
                    sendUpdates="all",  # Send invites to attendees
                )
                .execute()
            )

            # Analytics: Track tool usage (Phase 1 - Lightweight Collection)
            self.session_data["tool_calls"].append(
                {
                    "tool": "book_sales_meeting",
                    "customer_name": customer_name,
                    "customer_email": email_to_use,
                    "email_source": "provided" if customer_email else "stored",
                    "preferred_date": preferred_date,
                    "preferred_time": preferred_time,
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                    "meeting_time": meeting_datetime.isoformat(),
                    "calendar_event_id": created_event["id"],
                }
            )

            return {
                "booking_status": "confirmed",
                "meeting_time": meeting_datetime.strftime("%A, %B %d at %I:%M %p %Z"),
                "meeting_link": created_event.get(
                    "hangoutLink", created_event.get("htmlLink")
                ),
                "calendar_event_id": created_event["id"],
                "action": "meeting_booked",
            }

        except HttpError as e:
            if e.resp.status == 401:
                logger.error("Google Calendar authentication failed")
                raise ToolError(
                    "I'm unable to book meetings right now. Please email sales@pandadoc.com directly."
                )
            else:
                logger.error(f"Google Calendar API error: {e}")
                raise ToolError(
                    "There was an issue booking your meeting. Please try again or email sales@pandadoc.com"
                )

        except Exception as e:
            logger.error(f"Unexpected booking error: {e}")
            raise ToolError(
                "I couldn't complete the booking. Please email sales@pandadoc.com with your availability."
            )

    def _get_calendar_service(self):
        """Initialize Google Calendar service using service account.

        Supports both local development (file path) and cloud deployment (JSON as env var).
        """
        # For LiveKit Cloud: Store JSON content as environment variable
        if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT"):
            # Parse JSON from environment variable (for cloud deployment)
            service_account_info = json.loads(
                os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
            )
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
        else:
            # Fall back to file path (for local development)
            base_dir = os.path.dirname(os.path.dirname(__file__))
            service_account_path = base_dir + os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )

        return build("calendar", "v3", credentials=credentials)

    def _parse_meeting_time(
        self, date_pref: Optional[str], time_pref: Optional[str]
    ) -> datetime:
        """Parse natural language date/time into datetime object.

        Simple parsing - defaults to next business day at 10am if not specified.
        """
        # Try to parse the date preference
        if date_pref:
            parsed_date = dateparser.parse(
                date_pref, settings={"PREFER_DATES_FROM": "future"}
            )
            if parsed_date:
                base_date = parsed_date.date()
            else:
                base_date = self._next_business_day()
        else:
            base_date = self._next_business_day()

        # Parse time preference (default 10am)
        if time_pref:
            parsed_time = dateparser.parse(time_pref)
            if parsed_time:
                meeting_time = parsed_time.time()
            else:
                meeting_time = time(10, 0)  # Default 10am
        else:
            meeting_time = time(10, 0)

        return datetime.combine(base_date, meeting_time)

    def _next_business_day(self) -> date:
        """Get next business day (skip weekends)."""
        tomorrow = date.today() + timedelta(days=1)
        # If tomorrow is Saturday (5) or Sunday (6), jump to Monday
        if tomorrow.weekday() >= 5:
            days_ahead = 7 - tomorrow.weekday()
            return tomorrow + timedelta(days=days_ahead)
        return tomorrow

    def _determine_next_action(self, query: str, results: list) -> str:
        """Determine the best next action based on query and results.

        This helper method analyzes the user's query and search results to determine
        the most appropriate follow-up action for the conversation flow.

        IMPORTANT: Always return actions that provide direct value, not questions.
        """
        if not results:
            # No results found - provide direct help instead of asking questions
            return "provide_direct_guidance"  # Always help directly when no results

        query_lower = query.lower()

        # Analyze query intent and return action-oriented responses
        if any(word in query_lower for word in ["how", "setup", "configure", "create"]):
            return (
                "provide_step_by_step_guide"  # Direct guidance, not "offer_walkthrough"
            )
        elif any(word in query_lower for word in ["pricing", "cost", "plan", "tier"]):
            # For pricing questions, provide information directly
            if self.should_route_to_sales():
                return "explain_enterprise_pricing_and_offer_call"
            else:
                return "explain_pricing_tiers"  # Direct info, not discussion
        elif any(
            word in query_lower for word in ["integration", "connect", "sync", "api"]
        ):
            return "explain_integration_steps"  # Direct steps, not "check_specific"
        elif any(
            word in query_lower for word in ["error", "problem", "issue", "broken"]
        ):
            return (
                "provide_troubleshooting_steps"  # Direct help, not just "troubleshoot"
            )
        else:
            return "provide_relevant_information"  # Direct info, not "clarify_needs"

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

    # Initialize tracing with session metadata
    trace_provider = setup_observability(
        metadata={"langfuse.session.id": ctx.room.name}
    )

    if trace_provider:
        logger.info(f"✅ Tracing enabled for session {ctx.room.name}")
        # Register shutdown callback to flush traces
        ctx.add_shutdown_callback(lambda: trace_provider.force_flush())
    else:
        logger.warning("⚠️ Tracing DISABLED - Add LangFuse keys for production debugging!")

    # Set up a voice AI pipeline using direct provider plugins (OpenAI, ElevenLabs, Deepgram)
    # This bypasses LiveKit Inference and uses your own API keys
    session = AgentSession(
        # Note: Use "nova-2-phonecall" model for telephony applications for optimized call quality
        stt=deepgram.STT(
            model="nova-2",
            language="en",
        ),
        llm=openai.LLM(
            model="gpt-4.1-mini",
            temperature=0.7,
        ),
        tts=elevenlabs.TTS(
            voice="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
            model="eleven_turbo_v2_5",
        ),
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
        # user_away_timeout: Detect prolonged silence to prevent "dead air" charges
        # - Marks user as "away" after 30 seconds of no speech
        # - Allows graceful disconnection to save costs
        user_away_timeout=30,  # 30 seconds of silence before marking user "away"
    )

    # Create agent instance (we'll need access to it for data export)
    agent = PandaDocTrialistAgent()

    # Simple session limits to prevent runaway costs
    session_start_time = datetime.now()
    max_session_minutes = 30  # Maximum 30-minute sessions
    max_session_cost = 5.0  # Maximum $5 per session
    silence_warning_given = False

    # Metrics collection using the agent's built-in UsageCollector
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        """Collect metrics, track costs, and monitor latency for observability."""
        from livekit.agents.metrics import LLMMetrics, STTMetrics, TTSMetrics

        # Standard metrics logging
        metrics.log_metrics(ev.metrics)
        agent.usage_collector.collect(ev.metrics)

        # Build structured metric data for CloudWatch observability
        metric_data = {
            "_event_type": "voice_metrics",
            "_timestamp": datetime.now().isoformat(),
            "_session_id": ctx.room.name,
        }

        # Calculate total latency when all components are present
        if ev.metrics.eou and ev.metrics.llm and ev.metrics.tts:
            total_latency = (
                ev.metrics.eou.end_of_utterance_delay
                + (ev.metrics.llm.ttft or 0)
                + (ev.metrics.tts.ttfb or 0)
            )
            metric_data["total_latency"] = total_latency
            metric_data["eou_delay"] = ev.metrics.eou.end_of_utterance_delay
            metric_data["llm_ttft"] = ev.metrics.llm.ttft
            metric_data["tts_ttfb"] = ev.metrics.tts.ttfb

            # Alert on high latency (>1.5s target from observability guide)
            if total_latency > 1.5:
                logger.warning(
                    f"⚠️ High latency: {total_latency:.2f}s "
                    f"(EOU: {ev.metrics.eou.end_of_utterance_delay:.2f}s, "
                    f"LLM: {ev.metrics.llm.ttft:.2f}s, "
                    f"TTS: {ev.metrics.tts.ttfb:.2f}s)"
                )

        # Log to CloudWatch via analytics queue
        try:
            send_to_analytics_queue(metric_data)
        except Exception as e:
            logger.error(f"Failed to send metrics to analytics queue: {e}")

        # Real-time cost calculation from direct provider usage (Priority 4, Task 4.1)
        if isinstance(ev.metrics, LLMMetrics):
            # OpenAI LLM costs (gpt-4.1-mini)
            input_cost = (
                ev.metrics.prompt_tokens
                * agent.provider_pricing["openai_gpt4_mini_input"]
            )
            output_cost = (
                ev.metrics.completion_tokens
                * agent.provider_pricing["openai_gpt4_mini_output"]
            )
            llm_cost = input_cost + output_cost

            agent.session_costs["openai_tokens"] += ev.metrics.total_tokens
            agent.session_costs["openai_cost"] += llm_cost
            agent.session_costs["total_estimated_cost"] += llm_cost

        elif isinstance(ev.metrics, STTMetrics):
            # Deepgram STT costs (nova-2, charged per minute)
            stt_minutes = ev.metrics.audio_duration / 60.0
            stt_cost = stt_minutes * agent.provider_pricing["deepgram_nova2"]

            agent.session_costs["deepgram_minutes"] += stt_minutes
            agent.session_costs["deepgram_cost"] += stt_cost
            agent.session_costs["total_estimated_cost"] += stt_cost

        elif isinstance(ev.metrics, TTSMetrics):
            # ElevenLabs TTS costs (eleven_turbo_v2_5, charged per character)
            tts_cost = (
                ev.metrics.characters_count * agent.provider_pricing["elevenlabs_turbo"]
            )

            agent.session_costs["elevenlabs_characters"] += ev.metrics.characters_count
            agent.session_costs["elevenlabs_cost"] += tts_cost
            agent.session_costs["total_estimated_cost"] += tts_cost

        # Cost limit enforcement
        if (
            agent.session_costs["total_estimated_cost"]
            > agent.cost_limits["session_max"]
        ):
            logger.warning(
                f"Session cost limit exceeded: ${agent.session_costs['total_estimated_cost']:.4f} "
                f"(limit: ${agent.cost_limits['session_max']})"
            )
            # TODO: Implement graceful session termination or warning to user

    # Handle user silence/inactivity to prevent dead air charges
    @session.on("user_state_changed")
    async def on_user_state(ev):
        """Handle user state changes - detect prolonged silence."""
        nonlocal silence_warning_given

        if ev.new_state == "away":
            # User has been silent for 30 seconds
            if not silence_warning_given:
                await session.say(
                    "Hello? Are you still there? I'll disconnect in a moment if I don't hear from you.",
                    allow_interruptions=True,
                )
                silence_warning_given = True
                # Give them 10 more seconds to respond
                await asyncio.sleep(10)

                # Check if they're still away
                if session.user_state == "away":
                    await session.say(
                        "I'm disconnecting now due to inactivity. Feel free to call back anytime!"
                    )
                    agent.session_data["disconnect_reason"] = "silence_timeout"
                    await asyncio.sleep(2)
                    await session.aclose()

        elif ev.new_state == "speaking":
            # User is speaking again - reset warning flag
            silence_warning_given = False

    # Check session limits periodically
    async def check_session_limits():
        """Check time and cost limits every 30 seconds."""
        while True:
            await asyncio.sleep(30)

            # Check time limit
            session_duration = (
                datetime.now() - session_start_time
            ).total_seconds() / 60
            if session_duration > max_session_minutes:
                logger.warning(f"Session exceeded {max_session_minutes} minute limit")
                await session.say(
                    f"We've reached our {max_session_minutes} minute session limit. "
                    "Please call back if you need more assistance!"
                )
                agent.session_data["disconnect_reason"] = "time_limit"
                await asyncio.sleep(2)
                await session.aclose()
                break

            # Check cost limit
            if agent.session_costs["total_estimated_cost"] > max_session_cost:
                logger.warning(f"Session exceeded ${max_session_cost} cost limit")
                await session.say(
                    "We've reached the session limit. Feel free to call back to continue!"
                )
                agent.session_data["disconnect_reason"] = "cost_limit"
                await asyncio.sleep(2)
                await session.aclose()
                break

    # Start the session limit checker
    limit_checker = asyncio.create_task(check_session_limits())

    # Analytics: Enhanced shutdown callback for data export (Phase 1 - Lightweight Collection)
    async def export_session_data():
        """Export session data to analytics queue on shutdown.

        This follows LiveKit's recommended pattern for post-processing:
        - Collect data during the session with minimal overhead
        - Export everything in one batch at session end
        - Use shutdown callback with appropriate timeout
        """
        # Cancel the limit checker task to prevent orphaned tasks
        limit_checker.cancel()

        try:
            # Get final metrics summary from LiveKit's UsageCollector
            usage_summary = agent.usage_collector.get_summary()

            # Compile complete session data
            session_payload = {
                # Session metadata
                "session_id": ctx.room.name,
                "user_email": agent.session_data.get("user_email", ""),
                "user_metadata": agent.session_data.get("user_metadata", {}),
                "start_time": agent.session_data["start_time"],
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (
                    datetime.now()
                    - datetime.fromisoformat(agent.session_data["start_time"])
                ).total_seconds(),
                # Discovered business signals
                "discovered_signals": agent.discovered_signals,
                # Tool usage tracking
                "tool_calls": agent.session_data["tool_calls"],
                # LiveKit performance metrics
                "metrics_summary": usage_summary,
                # Cost tracking (Priority 4, Task 4.1)
                "cost_summary": agent.session_costs,
                # Conversation notes
                "conversation_notes": agent.conversation_notes,
                "conversation_state": agent.conversation_state,
                # Consent tracking (CRITICAL for legal compliance audit trail)
                "consent_obtained": agent.consent_given,
                "consent_timestamp": agent.consent_timestamp,
            }

            # Log summary for debugging
            logger.info(f"Session data ready for export: {ctx.room.name}")
            if session_payload.get("user_email"):
                logger.info(f"  - User email: {session_payload['user_email']}")
            logger.info(f"  - Duration: {session_payload['duration_seconds']:.1f}s")
            logger.info(
                f"  - Total cost: ${agent.session_costs['total_estimated_cost']:.4f}"
            )
            logger.info(f"  - Tool calls: {len(session_payload['tool_calls'])}")
            logger.info(
                f"  - Qualification: {agent.discovered_signals.get('qualification_tier', 'Unknown')}"
            )
            logger.info(
                f"  - Disconnect reason: {agent.session_data.get('disconnect_reason', 'user_initiated')}"
            )

            # Send to analytics queue
            # Phase 1: Logs the data (placeholder implementation)
            # Phase 2: Will send to actual queue (Google Pub/Sub or AWS SQS)
            await send_to_analytics_queue(session_payload)

            logger.info(
                f"Analytics data collection complete for session {ctx.room.name}"
            )

        except Exception as e:
            # Log error but don't crash - analytics failures shouldn't affect the agent
            logger.error(f"Failed to export session data: {e}", exc_info=True)

    ctx.add_shutdown_callback(export_session_data)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=agent,  # Use the agent instance we created above
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Extract user email from participant metadata
    try:
        # Wait for first participant (the user who triggered the agent)
        participant = await ctx.wait_for_participant()

        if participant.metadata:
            # Parse the JSON metadata
            metadata = json.loads(participant.metadata)
            logger.info(f"Participant metadata received: {metadata}")

            # Extract email and store it
            user_email = metadata.get("user_email", "")
            agent.user_email = user_email
            agent.session_data["user_email"] = user_email
            agent.session_data["user_metadata"] = metadata

            if user_email:
                logger.info(f"✅ Session started for email: {user_email}")
            else:
                logger.info("⚠️  No email in metadata (user may have skipped form)")
        else:
            logger.info("⚠️  No participant metadata available")
            agent.user_email = ""
            agent.session_data["user_email"] = ""
            agent.session_data["user_metadata"] = {}

    except Exception as e:
        logger.warning(f"Could not extract participant metadata: {e}")
        # Graceful fallback - session continues without email
        agent.user_email = ""
        agent.session_data["user_email"] = ""
        agent.session_data["user_metadata"] = {}

    # Initial greeting
    await session.say(
        "Hi! I'm your AI Pandadoc Trial Success Specialist. How's your trial going? Any roadblocks I can help clear up?"
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
