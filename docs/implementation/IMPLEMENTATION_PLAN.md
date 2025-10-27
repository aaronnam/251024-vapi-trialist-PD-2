# PandaDoc Voice Agent Implementation Plan
*Comprehensive plan for building the Trial Success Voice Agent with LiveKit*

## Executive Summary

This implementation plan details the development of "Sarah," a voice AI agent for PandaDoc trial success. Based on extensive research of LiveKit capabilities, the PandaDoc specification, and best practices, this plan provides a structured approach with epics, tasks, and subtasks that can be executed by any Claude Code instance or developer.

**v1 Scope:** 3 core tools + Google Calendar sub-agent (Unleash knowledge search, calendar sub-agent with Google Calendar API integration, event tracking)
**Timeline:** 5 weeks (MVP with calendar) → 9 weeks (Production) → 13 weeks (Full Feature Set)
**Confidence:** 90%+ technical feasibility
**ROI:** $400K+ Q4 2025 revenue contribution

## Table of Contents

1. [Project Setup](#project-setup)
2. [Epic 1: Core Voice Agent Foundation](#epic-1-core-voice-agent-foundation)
3. [Epic 2: Tool Implementation](#epic-2-tool-implementation)
4. [Epic 3: Conversation Intelligence](#epic-3-conversation-intelligence)
5. [Epic 4: Testing & Quality](#epic-4-testing--quality)
6. [Epic 5: Calendar Management Sub-Agent](#epic-5-calendar-management-sub-agent)
7. [Epic 6: Integration & Deployment](#epic-6-integration--deployment)
8. [Reference Documentation](#reference-documentation)

---

## Project Setup

### Prerequisites
- Python 3.9+
- LiveKit Cloud account
- uv package manager
- Environment variables configured

### Initial Configuration

#### Install Dependencies
```bash
cd my-app
uv sync
uv add "livekit-agents[silero,turn-detector,elevenlabs,deepgram]~=1.2"
uv add google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
uv add httpx
uv add pytz
```

**Dependencies explanation:**
- `google-auth*` packages: Google Calendar API authentication
- `google-api-python-client`: Google Calendar API client library
- `httpx`: Async HTTP client for Unleash API
- `pytz`: Timezone handling for calendar operations

#### Google Calendar API Setup

**Required for v1 calendar sub-agent implementation**

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create a new project (e.g., "PandaDoc Voice Agent")
   - Note the project ID

2. **Enable Google Calendar API**
   - In Google Cloud Console, navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name: "pandadoc-voice-agent-calendar"
   - Grant role: "Editor" (or create custom role with calendar permissions)
   - Click "Done"

4. **Download Service Account Credentials**
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select "JSON" format
   - Download and save as `service-account.json`
   - Move to secure location: `my-app/.secrets/service-account.json`

5. **Share Calendar with Service Account**
   - Open Google Calendar (calendar.google.com)
   - Select the calendar to use for bookings (or create new "PandaDoc Demos" calendar)
   - Click Settings (gear icon) > "Settings for my calendars"
   - Select the calendar > "Share with specific people"
   - Add the service account email (found in JSON file: `client_email`)
   - Grant "Make changes to events" permission
   - Save

6. **Get Calendar ID**
   - In Calendar Settings, select your calendar
   - Scroll to "Integrate calendar" section
   - Copy the "Calendar ID" (usually looks like: `abc123@group.calendar.google.com` or `primary`)

#### Environment Variables

Add these to `my-app/.env.local`:

```bash
# LiveKit Cloud (from lk cloud auth)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Unleash Knowledge Base API
UNLEASH_API_KEY=your_unleash_api_key
UNLEASH_BASE_URL=https://api.unleash.com  # Optional, has default

# Google Calendar API
GOOGLE_SERVICE_ACCOUNT_JSON=.secrets/service-account.json  # Path relative to my-app/
GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com  # Or "primary"

# OpenAI (for LLM)
OPENAI_API_KEY=your_openai_api_key

# ElevenLabs (for TTS)
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Deepgram (for STT)
DEEPGRAM_API_KEY=your_deepgram_api_key
```

**Security Notes:**
- Never commit `.env.local` or `service-account.json` to version control
- Add `.secrets/` directory to `.gitignore`
- Use environment-specific credentials for dev/staging/production
- Rotate service account keys periodically

---

## Epic 1: Core Voice Agent Foundation
*Build the fundamental voice agent with Sarah persona and voice pipeline*

### Task 1.1: Transform Assistant Class to PandaDocTrialistAgent
**Owner:** Voice Pipeline Engineer
**Estimate:** 4 hours

#### Subtask 1.1.1: Create PandaDocTrialistAgent class with qualification-aware instructions
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md` (Section 8: Qualification Framework)
**Documentation:** `REQUIREMENTS_MAP.md` - Section 1
**LiveKit Docs:** `/agents/build/workflows` (Agent class structure, custom instructions), `/agents/build/nodes` (lifecycle hooks: `on_enter`, `on_user_turn_completed`)

```python
# Implementation location: my-app/src/agent.py
class PandaDocTrialistAgent(Agent):
    def __init__(self):
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
- Qualify through understanding, not asking
"""
        )
```

**Actions:**
1. Rename `Assistant` class to `PandaDocTrialistAgent`
2. Implement comprehensive system instructions including Sarah persona
3. Add natural qualification discovery patterns to the prompt
4. Include qualification tiers and thresholds in instructions
5. Add guidance on passing qualification signals to webhook tool

#### Subtask 1.1.2: Add conversation state management ✅ COMPLETED
**Reference:** `../research/livekit/function-tools.md` - Section 2 (RunContext)
**Documentation:** LiveKit Agent state management patterns
**LiveKit Docs:** `/agents/build/workflows` (userdata attribute, state with dataclasses), `/agents/build/nodes` (accessing turn_ctx and ChatContext)
**Implementation:** `my-app/src/agent.py:77-104`

**Memory Architecture:**
This subtask implements a **two-layer memory system**:
1. **LLM Conversation Memory** (automatic): The LLM maintains full chat history for conversational recall
2. **Structured Business State** (explicit): Agent tracks business-critical signals for external systems, routing decisions, and post-call workflows

```python
def __init__(self):
    super().__init__(instructions=...)

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
        "industry": None,           # "healthcare", "real estate", "legal", etc.
        "location": None,           # "Toronto", "US-East", "EMEA", etc.
        "use_case": None,           # "proposals", "contracts", "quotes", "NDAs"
        "current_tool": None,       # "manual", "DocuSign", "Adobe Sign", etc.
        "pain_points": [],          # ["slow turnaround", "no tracking", "manual follow-up"]
        "decision_timeline": None,  # "this week", "next quarter", "evaluating"
        "budget_authority": None,   # "decision_maker", "needs_approval", "influencer"
        "team_structure": None,     # "sales", "legal", "ops", "distributed"
    }

    # Free-form conversation notes (catch-all for important context)
    self.conversation_notes = []  # Agent can append: ["Previous bad DocuSign experience", "Compliance is critical"]

    # Trial context
    self.trial_day = None
    self.trial_activity = None  # "created_template", "sent_document", "stuck_on_feature"
```

**Actions:**
1. Add state tracking attributes with expanded business context fields
2. Initialize qualification signal tracking (not scoring) with core + extended fields
3. Add conversation_notes list for free-form important context that doesn't fit categories
4. Create state transition methods
5. Track discovered signals as they emerge naturally in conversation
6. Document that LLM handles conversational memory; structured state is for business operations

**Note on Memory:**
- **Conversational recall** (e.g., "you mentioned Toronto earlier") happens automatically via LLM context
- **Structured state** is for data that needs to:
  - Drive programmatic decisions (qualification routing)
  - Be passed to external systems (webhooks, Salesforce, analytics)
  - Persist beyond the conversation
  - Trigger specific workflows

#### Subtask 1.1.3: Implement state machine transitions ✅ COMPLETED
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 266-281)
**LiveKit Docs:** `/agents/build/workflows` (session state management), `/agents/build/nodes` (state transitions in lifecycle hooks)
**Implementation:** `my-app/src/agent.py:106-199`

**Purpose:** Control conversation flow progression and leverage rich discovered context for intelligent state transitions.

```python
# State flow: GREETING → DISCOVERY → VALUE_DEMO → QUALIFICATION → NEXT_STEPS → CLOSING
def transition_state(self, from_state: str, to_state: str, context: dict = None):
    """
    Transition between conversation states with validation.

    Args:
        from_state: Current state
        to_state: Target state
        context: Optional dict with transition context (e.g., discovered signals)
    """
    valid_transitions = {
        "GREETING": ["DISCOVERY", "FRICTION_RESCUE"],
        "DISCOVERY": ["VALUE_DEMO", "QUALIFICATION", "FRICTION_RESCUE"],
        "VALUE_DEMO": ["QUALIFICATION", "NEXT_STEPS", "FRICTION_RESCUE"],
        "QUALIFICATION": ["NEXT_STEPS", "VALUE_DEMO"],  # Can loop back for more demo
        "NEXT_STEPS": ["CLOSING", "QUALIFICATION"],     # Can clarify qualification
        "FRICTION_RESCUE": ["DISCOVERY", "VALUE_DEMO", "CLOSING"],  # Flexible recovery
        "CLOSING": []  # Terminal state
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
    """
    Determine if enough context has been gathered to move to qualification.

    Uses richer discovered_signals to make intelligent transition decisions.
    """
    # Have we learned enough about their needs?
    has_use_case = self.discovered_signals.get("use_case") is not None
    has_pain_points = len(self.discovered_signals.get("pain_points", [])) > 0

    # Have we discovered any qualification signals?
    has_team_info = self.discovered_signals.get("team_size") is not None
    has_volume_info = self.discovered_signals.get("monthly_volume") is not None
    has_integration_needs = len(self.discovered_signals.get("integration_needs", [])) > 0

    # Transition when we have sufficient context
    return (has_use_case or has_pain_points) and \
           (has_team_info or has_volume_info or has_integration_needs)

def should_route_to_sales(self) -> bool:
    """
    Determine if this lead should be routed to sales vs self-serve.

    Leverages expanded discovered_signals for routing decision.
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
    if self.discovered_signals.get("budget_authority") == "decision_maker" and \
       self.discovered_signals.get("urgency") == "high":
        return True

    # Complex use cases indicate enterprise
    complex_industries = ["healthcare", "finance", "legal"]
    if self.discovered_signals.get("industry") in complex_industries and \
       self.discovered_signals.get("team_size", 0) >= 3:
        return True

    return False
```

**Actions:**
1. Implement state validation logic with comprehensive transition map
2. Add transition logging with rich context
3. Handle invalid transitions gracefully
4. Create helper methods that leverage expanded discovered_signals:
   - `should_transition_to_qualification()` - Uses use_case, pain_points, qualification signals
   - `should_route_to_sales()` - Uses team_size, volume, integrations, authority, urgency, industry
5. Add context parameter to transitions for debugging/analytics
6. Document how richer state enables smarter conversation flow decisions

**State Transition Intelligence:**
The expanded `discovered_signals` enables context-aware transitions:
- **Discovery → Qualification**: Only when sufficient use_case/pain_points discovered
- **Qualification → Next Steps**: Different paths for sales_ready vs self_serve
- **Routing decisions**: Leverage industry, authority, timeline for better qualification

### Task 1.2: Configure Voice Pipeline
**Owner:** Audio Engineer
**Estimate:** 3 hours

#### Subtask 1.2.1: Set up Deepgram STT ✅ COMPLETED
**Reference:** `livekit_voice_pipeline_research.md` - Deepgram Configuration
**Documentation:** https://docs.livekit.io/agents/models/stt/inference/deepgram/
**LiveKit Docs:** `/agents/models/stt/plugins/deepgram` (model selection, eager_eot_threshold, keyterms)
**Implementation:** `my-app/src/agent.py:230-236`

```python
# Update entrypoint function
session = AgentSession(
    stt="deepgram/nova-2:en",  # or nova-2-phonecall for telephony
    # ... other config
)
```

**Actions:**
1. ✅ Replace AssemblyAI with Deepgram Nova-2
2. ✅ Add language specification (:en)
3. ✅ Add comment explaining telephony variant (nova-2-phonecall)
4. ✅ Update pipeline description comment

**Implementation Notes:**
- Changed from `assemblyai/universal-streaming:en` to `deepgram/nova-2:en`
- Added inline comment about using `deepgram/nova-2-phonecall` for telephony applications
- Updated session description comment to reflect Deepgram usage
- Using string descriptor format for simple configuration
- Advanced parameters (filler_words, etc.) can be configured via `inference.STT()` if needed later

#### Subtask 1.2.2: Configure ElevenLabs TTS with Rachel voice ✅ COMPLETED
**Reference:** Research document on ElevenLabs integration
**Documentation:** https://docs.livekit.io/agents/models/tts/inference/elevenlabs/
**LiveKit Docs:** `/agents/models/tts/plugins/elevenlabs` (voice_id, model, streaming_latency, voice_settings)
**Implementation:** `my-app/src/agent.py:230-242`, `my-app/pyproject.toml:14`

```python
session = AgentSession(
    tts="elevenlabs/eleven_turbo_v2_5:21m00Tcm4TlvDq8ikWAM",  # Rachel voice
)
```

**Actions:**
1. Add ElevenLabs to dependencies
2. Configure Rachel voice ID
3. Set Turbo v2.5 model
4. Test latency (<100ms target)

**Implementation Notes:**
- Changed from `cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc` to `elevenlabs/eleven_turbo_v2_5:21m00Tcm4TlvDq8ikWAM`
- Added `livekit-plugins-elevenlabs~=0.2` to dependencies in pyproject.toml
- Updated session description comment to reflect ElevenLabs usage
- Added inline comment indicating Rachel voice and Turbo v2.5 model
- Using string descriptor format for simple configuration (model and voice ID selection)

#### Subtask 1.2.3: Optimize VAD and turn detection ✅ COMPLETED
**Reference:** `livekit_voice_pipeline_research.md` - VAD Configuration
**LiveKit Docs:** `/agents/build/audio` (preemptive_generation), `/agents/build/turns` (VAD and turn detection)
**Implementation:** `my-app/src/agent.py:243-261`

```python
from livekit.plugins.turn_detector.multilingual import MultilingualModel

session = AgentSession(
    turn_detection=MultilingualModel(),
    vad=ctx.proc.userdata["vad"],  # Pre-warmed Silero VAD
    preemptive_generation=True,
)
```

**Actions:**
1. ✅ Configure 300ms VAD threshold (using default - Silero VAD comes with 300ms built-in)
2. ✅ Enable preemptive generation (line 261: preemptive_generation=True)
3. ✅ Set interruption handling (automatically enabled via VAD configuration)
4. ✅ Add comprehensive inline documentation explaining VAD behavior and latency targets
5. Test with background noise (deferred to integration testing phase)

**Implementation Status:**
- **MultilingualModel** (line 250): Already imported and configured for contextually-aware turn detection
- **Silero VAD** (line 255): Pre-warmed in `prewarm()` function, uses 300ms default threshold
- **Preemptive generation** (line 261): Already enabled for <700ms target latency
- **Interruption handling**: Automatically enabled through VAD, allows natural conversation flow
- **Documentation added**: Enhanced comments explain VAD threshold, turn detection, and preemptive generation benefits

**Verification:**
The current configuration follows best practices:
- VAD threshold of 300ms (default, optimized for conversational responsiveness)
- MultilingualModel for semantic turn detection (prevents premature interruptions)
- Preemptive generation reduces total latency to <700ms
- All three components work together for natural, responsive conversation flow

### Task 1.3: Implement Error Handling and Fallbacks
**Owner:** Reliability Engineer
**Estimate:** 2 hours

#### Subtask 1.3.1: Add TTS fallback to OpenAI
**Reference:** `/docs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (line 69)
**LiveKit Docs:** `/agents/build/events` (FallbackAdapter for automatic failover)

```python
try:
    session = AgentSession(
        tts="elevenlabs/eleven_turbo_v2_5:21m00Tcm4TlvDq8ikWAM",
    )
except Exception as e:
    logger.warning(f"ElevenLabs unavailable: {e}")
    session = AgentSession(
        tts="openai/tts-1",  # Fallback
    )
```

**Actions:**
1. Implement try-catch for TTS initialization
2. Add fallback configuration
3. Log fallback usage
4. Test fallback scenarios

#### Subtask 1.3.2: Implement graceful error recovery
**Reference:** `REQUIREMENTS_MAP.md` - Section 6
**LiveKit Docs:** `/agents/build/events` (ErrorEvent handling, recoverable field)

```python
# Error handling patterns
if tool_failed:
    await self.say("Let me find that information another way...")
    # Fallback logic
```

**Actions:**
1. Add error recovery phrases
2. Implement tool timeout handling
3. Add connection retry logic
4. Test with network failures

---

## Epic 2: Tool Implementation
*Implement the 3 core v1 tools for knowledge search, calendar management, and event tracking (9 hours + Epic 5 calendar sub-agent)*

**Before Starting Epic 2:** Read these sections from `@anthropic-agent-guides/250911-anthropic-building-effective-tools.md`:
- Lines 107-127: "Choosing the right tools for agents" - Understand tool consolidation patterns
- Lines 138-163: "Returning meaningful context" - Learn about response optimization
- Lines 187-195: "Prompt-engineering tool descriptions" - Critical for tool discoverability

### Task 2.1: Unleash Knowledge Base Integration
**Owner:** Backend Engineer
**Estimate:** 4 hours

#### Subtask 2.1.1: Implement unleash_search_knowledge tool with Unleash API
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 88-96)
**Documentation:** `../research/livekit/function-tools.md` - Section 1
**LiveKit Docs:** `/agents/build/tools` (@function_tool decorator, RunContext, async patterns, ToolError), `/agents/build/external-data` (external API calls)
**Design Principle:** Tool consolidation - This tool should handle search AND provide actionable next steps

```python
from livekit.agents import function_tool, RunContext
import os
import httpx

@function_tool
async def unleash_search_knowledge(self, context: RunContext, query: str, category: str = None, response_format: str = "concise"):
    """Search PandaDoc knowledge base and provide actionable guidance.

    Use this tool when the user asks about PandaDoc features, pricing, integrations, or needs help.
    This tool both searches for information AND suggests next steps.

    Args:
        query: Natural language question about PandaDoc
        category: Optional - "features", "pricing", "integrations", "troubleshooting"
        response_format: "concise" for essential info, "detailed" for comprehensive results
    """
    # Add "thinking" filler
    await context.llm.say("Let me find that for you...")

    try:
        # Connect to Unleash API
        unleash_api_key = os.getenv("UNLEASH_API_KEY")
        unleash_base_url = os.getenv("UNLEASH_BASE_URL", "https://api.unleash.com")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{unleash_base_url}/v1/search",
                headers={
                    "Authorization": f"Bearer {unleash_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": query,
                    "category": category,
                    "max_results": 3 if response_format == "concise" else 5
                },
                timeout=5.0
            )
            response.raise_for_status()
            results = response.json()

        # Format response based on response_format parameter
        if response_format == "concise":
            # Return only essential information for quick understanding
            return {
                "answer": results.get("results", [{}])[0].get("content", ""),
                "action": self._determine_next_action(query, results),
                "found": len(results.get("results", [])) > 0
            }
        else:
            # Return detailed results with all context
            return {
                "results": results.get("results", []),
                "suggested_followup": self._determine_next_action(query, results),
                "related_topics": results.get("related", [])
            }

    except httpx.TimeoutException:
        # Specific, actionable error message for timeout
        await context.llm.say("The knowledge base is taking longer than expected. Let me help you directly...")
        return {
            "answer": "I can walk you through this myself. What specific part would you like to start with?",
            "action": "offer_direct_help",
            "found": False
        }
    except Exception as e:
        # Graceful fallback with actionable next steps
        await context.llm.say("I'll help you another way...")
        return {
            "answer": "I can connect you with our support team or walk you through common solutions.",
            "action": "offer_alternatives",
            "found": False
        }

def _determine_next_action(self, query: str, results: dict) -> str:
    """Determine the best next action based on query and results."""
    if not results.get("results"):
        return "offer_human_help"

    query_lower = query.lower()
    if "how" in query_lower or "setup" in query_lower:
        return "offer_walkthrough"
    elif "pricing" in query_lower or "cost" in query_lower:
        return "discuss_roi"
    elif "integration" in query_lower:
        return "check_specific_integration"
    else:
        return "clarify_needs"
```

**Actions:**
1. Set up Unleash API credentials in environment
2. Implement API client with proper authentication
3. Add timeout and error handling
4. Create fallback responses for API failures
5. Test with various query types

**Environment Variables Required:**
```bash
UNLEASH_API_KEY=your_api_key_here
UNLEASH_BASE_URL=https://api.unleash.com  # Optional, has default
```

### Task 2.2: Calendar Sub-Agent Tool
**Owner:** Integration Engineer
**Estimate:** 3 hours

#### Subtask 2.2.1: Implement calendar_management_agent tool
**Reference:** LiveKit multi-agent patterns
**Documentation:** `../research/livekit/function-tools.md` - Section 3 (Sub-agent patterns)
**LiveKit Docs:** `/agents/build/workflows` (agent handoff via tool returns), `/agents/build/tools` (returning Agent from tools)
**Design Principle:** Single consolidated tool for ALL calendar operations (checking + booking)

```python
from livekit.agents import function_tool, RunContext, Agent

@function_tool
async def calendar_management_agent(
    self,
    context: RunContext,
    request: str,
    user_email: str = None
):
    """Handle all calendar operations - check availability AND book meetings.

    This single tool consolidates all calendar operations. Use it when the user wants to:
    - Check when they're available
    - Schedule a demo or meeting
    - Find a good time to meet
    - Book time on the calendar

    The tool determines the right action (check vs book) from the natural language request.

    Args:
        request: Natural language calendar request (e.g., "What times are free tomorrow?" or "Book a demo for 2pm")
        user_email: Email for calendar invites (optional - will prompt if needed for booking)
    """
    await context.llm.say("Let me check the calendar for you...")

    # Pass request to calendar sub-agent
    calendar_agent_response = await self._invoke_calendar_subagent(
        request=request,
        user_email=user_email,
        context=context
    )

    return calendar_agent_response

async def _invoke_calendar_subagent(self, request: str, user_email: str, context: RunContext):
    """Internal method to communicate with calendar sub-agent."""

    # TODO: Implement actual sub-agent invocation
    # For v1, return structured response indicating handoff
    return {
        "status": "handoff_initiated",
        "request": request,
        "message": "Calendar agent will handle this request",
        "subagent": "google_calendar_agent",
        "user_email": user_email
    }
```

**Actions:**
1. Create sub-agent invocation pattern
2. Define request/response interface
3. Add error handling for sub-agent failures
4. Test handoff flow

**Note:** The Google Calendar sub-agent implementation is part of v1 scope. Full implementation details are in Epic 5 below.

### Task 2.3: Conversation Event Tracking
**Owner:** Analytics Engineer
**Estimate:** 2 hours

#### Subtask 2.3.1: Implement webhook_send_conversation_event tool
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 136-145)
**Documentation:** `../research/livekit/function-tools.md` - Section 5 (Error handling)
**LiveKit Docs:** `/agents/build/events` (event handlers), `/agents/build/external-data` (fire-and-forget async), `/home/server/webhooks` (webhook integration)
**Design Principle:** Tool derives most data from agent state - minimize parameters

```python
from livekit.agents import function_tool, RunContext
from datetime import datetime
import json
import logging

@function_tool
async def log_qualification_signal(
    self,
    context: RunContext,
    signal_type: str,
    value: any,
    notes: str = None
):
    """Log a discovered qualification signal or important conversation event.

    This tool automatically derives context from the agent's internal state.
    Use it whenever you discover something important about the user's needs.

    Args:
        signal_type: What you discovered - "team_size", "volume", "integration", "urgency", "pain_point", etc.
        value: The actual value discovered (e.g., 12 for team_size, "Salesforce" for integration)
        notes: Optional context about how/why this was discovered
    """
    # Build event payload
    event_data = {
        "event_type": event_type,
        "call_id": call_id,
        "timestamp": datetime.now().isoformat(),
        "trialist": trialist,
        "data": data
    }

    # Log event for analytics
    logger = logging.getLogger("analytics")
    logger.info(f"Conversation event: {json.dumps(event_data)}")

    # Update agent's internal state with discovered signals
    if event_type == "qualification":
        signals = data.get("qualification_signals", {})

        # Core qualification signals
        if signals.get("team_size"):
            self.discovered_signals["team_size"] = signals["team_size"]
        if signals.get("monthly_volume"):
            self.discovered_signals["monthly_volume"] = signals["monthly_volume"]
        if signals.get("integration_needs"):
            self.discovered_signals["integration_needs"].extend(signals["integration_needs"])
        if signals.get("urgency"):
            self.discovered_signals["urgency"] = signals["urgency"]
        if signals.get("qualification_tier"):
            self.discovered_signals["qualification_tier"] = signals["qualification_tier"]

        # Extended business context signals
        if signals.get("industry"):
            self.discovered_signals["industry"] = signals["industry"]
        if signals.get("location"):
            self.discovered_signals["location"] = signals["location"]
        if signals.get("use_case"):
            self.discovered_signals["use_case"] = signals["use_case"]
        if signals.get("current_tool"):
            self.discovered_signals["current_tool"] = signals["current_tool"]
        if signals.get("pain_points"):
            self.discovered_signals["pain_points"].extend(signals["pain_points"])
        if signals.get("decision_timeline"):
            self.discovered_signals["decision_timeline"] = signals["decision_timeline"]
        if signals.get("budget_authority"):
            self.discovered_signals["budget_authority"] = signals["budget_authority"]
        if signals.get("team_structure"):
            self.discovered_signals["team_structure"] = signals["team_structure"]

        # Conversation notes (free-form catch-all)
        if data.get("conversation_notes"):
            self.conversation_notes.extend(data["conversation_notes"])

    if event_type == "discovery":
        discovered = data.get("discovered_needs", [])
        if not hasattr(self, 'discovered_needs'):
            self.discovered_needs = []
        self.discovered_needs.extend(discovered)

    if event_type == "context":
        # Handle free-form context updates
        notes = data.get("conversation_notes", [])
        self.conversation_notes.extend(notes)

    # Fire-and-forget async
    return {"logged": True, "event_type": event_type}
```

**Actions:**
1. Create event logging structure with expanded qualification_signals schema
2. Implement state updates for all qualification signals (core + extended)
3. Add handling for conversation_notes (free-form catch-all context)
4. Add "context" event type for tracking important details that don't fit other categories
5. Add structured logging format for all discovered signals
6. Test with various event types and comprehensive qualification data
7. Ensure Sarah can pass both structured signals and free-form notes naturally

**Note on Extended Signals:**
- **Core signals** (team_size, volume, integrations) still drive primary qualification
- **Extended signals** (industry, location, use_case, etc.) enable richer routing and personalization
- **conversation_notes** captures important context that doesn't fit structured fields
- All signals are optional - Sarah can log partial data as it's discovered naturally

---

## Epic 3: Conversation Intelligence
*Implement conversation flow, qualification patterns, and objection handling*

### Task 3.1: Conversation Flow Management
**Owner:** Conversation Designer
**Estimate:** 6 hours

#### Subtask 3.1.1: Implement opening patterns
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 284-298)
**Documentation:** `REQUIREMENTS_MAP.md` - Section 4

```python
def generate_greeting(self, context_data: dict) -> str:
    """Generate contextual greeting based on trigger type."""

    if context_data.get("trigger_type") == "inbound":
        return (
            f"Hi {context_data.get('name', 'there')}! This is Sarah from PandaDoc. "
            f"Thanks for reaching out! I can see you're on day {context_data.get('trial_day', 'X')} "
            f"of your trial and you've {context_data.get('activity', 'been exploring')}. "
            "What can I help you with today?"
        )
    else:  # Proactive
        return (
            f"Hi {context_data.get('name', 'there')}, this is Sarah from PandaDoc. "
            f"I noticed you've been working on {context_data.get('task', 'something')} "
            f"for about {context_data.get('time', '10 minutes')}. "
            "I can walk you through it in about 2 minutes if you'd like. Would that be helpful?"
        )
```

**Actions:**
1. Create greeting templates
2. Add context injection
3. Implement trigger detection
4. Test various scenarios

#### Subtask 3.1.2: Implement discovery questions
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 304-309)

```python
class DiscoveryQuestions:
    BROAD = [
        "What brings you to PandaDoc?",
        "What kind of documents do you send?",
        "What's your current document process like?"
    ]

    CLARIFYING = [
        "When you say proposals, are these for new clients or renewals?",
        "Is your team all in one location or distributed?",
        "Do you need documents to sync with your CRM?"
    ]

    QUANTIFYING = [
        "How many documents per month does your team send?",
        "How big is your sales team?",
        "How long does it typically take to create a proposal?"
    ]

    PRIORITIZING = [
        "What matters most: speed or tracking?",
        "Is template standardization important?",
        "Do you need approval workflows?"
    ]
```

**Actions:**
1. Create question bank
2. Implement progression logic
3. Add response parsing
4. Test discovery flow

#### Subtask 3.1.3: Implement objection handling
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 310-317)
**Documentation:** Voice agent guides for objection patterns

```python
def handle_objection(self, objection_type: str, context: dict) -> str:
    """Generate appropriate objection response."""

    objection_handlers = {
        "too_expensive": (
            "I understand budget is important... "
            f"With {context.get('volume', 'X')} documents monthly, "
            f"you'd save {context.get('hours', 'Y')} hours at ${context.get('rate', '50')}/hour. "
            f"The ROI is typically {context.get('payback', '2-3 months')}... "
            "Similar companies see 70% time reduction."
        ),
        "too_complex": (
            "It can feel overwhelming at first... "
            "Let's focus on just one thing to start... "
            "Once you nail this, the rest clicks... "
            "Takes most people about 15 minutes to get comfortable."
        ),
        "need_approval": (
            "That makes complete sense for a decision like this... "
            "I can prepare a summary with ROI specifics... "
            "Should we schedule time next week after you've synced with your team?"
        )
    }

    return objection_handlers.get(objection_type, "I understand your concern...")
```

**Actions:**
1. Create objection response templates
2. Add empathy patterns
3. Implement proof points
4. Test each objection type

### Task 3.2: Prompt-Based Qualification Logic
**Owner:** Conversation Designer
**Estimate:** 3 hours

**Overview:** Qualification happens through Sarah's natural conversation guided by her system prompt, not through explicit scoring functions. Sarah understands qualification criteria and tracks signals as they emerge.

#### Subtask 3.2.1: Enhance system prompt with qualification examples
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md` - Section 8
**Documentation:** `REQUIREMENTS_MAP.md` - Section 5

**Actions:**
1. Add example qualification conversations to Sarah's instructions
2. Include sample dialogue showing natural discovery
3. Add guidance on when to call webhook_send_conversation_event with qualification data
4. Provide examples of how to structure qualification_signals payload

**Example addition to system prompt:**
```python
# Add to PandaDocTrialistAgent instructions:
"""
## Example Qualification Conversations

**Example 1: Discovering Team Size Naturally**
User: "We need better proposal tracking."
Sarah: "That makes sense. Walk me through your current process - who creates the proposals, who reviews them, and who sends them out?"
User: "Well, our 12 sales reps create them, managers review, and reps send."
[Internal: team_size = 12+ → Tier 1 signal. Call webhook_send_conversation_event with qualification_signals]

**Example 2: Discovering Integration Needs**
User: "We just need to send documents faster."
Sarah: "Got it. Once someone signs a document, where does that information need to go?"
User: "It needs to update our Salesforce opportunities automatically."
[Internal: integration_needs = ["salesforce"] → Tier 1 signal]

**Example 3: Discovering Volume**
User: "Our proposals take forever to create."
Sarah: "I can help with that. What kind of proposals do you send?"
User: "Sales proposals and contracts."
Sarah: "How often is your team sending those out?"
User: "We're doing about 150-200 per month now."
[Internal: monthly_volume = 150+ → Tier 1 signal]

## When to Log Qualification Signals
Call webhook_send_conversation_event with event_type="qualification" when you discover:
- Team size indicators (5+ users = Tier 1)
- Document volume (100+ per month = Tier 1)
- Integration needs (Salesforce, HubSpot, API = Tier 1)
- Urgency indicators (replacing tool, deadline = elevated priority)

Example call:
webhook_send_conversation_event(
    event_type="qualification",
    call_id=current_call_id,
    trialist={"email": user_email, "company": company_name},
    data={
        "qualification_signals": {
            "team_size": 12,
            "monthly_volume": 175,
            "integration_needs": ["salesforce"],
            "urgency": "high",
            "qualification_tier": "sales_ready"
        }
    }
)
"""
```

#### Subtask 3.2.2: Document qualification signal extraction
**Reference:** Spec natural discovery patterns

**Actions:**
1. Document how Sarah should extract signals from user responses
2. Create mapping between user language and qualification data
3. Define when qualification tier should be determined (sales_ready, self_serve)
4. Add guidelines for incomplete qualification (partial signals discovered)

**Documentation to add:**
```python
"""
## Signal Extraction Guidelines

**Team Size Extraction:**
- User mentions "our team of 15" → team_size = 15
- User says "me and 3 other reps" → team_size = 4
- User describes workflow with roles → count mentioned roles
- User mentions departments → likely 5+

**Volume Extraction:**
- "About 20 per week" → monthly_volume = 80
- "2-3 deals per rep per month, 8 reps" → monthly_volume = 16-24
- "We do hundreds" → monthly_volume = 200+ (estimate conservatively)
- "Daily proposals" → monthly_volume = 150+ (assume ~5/day × 30)

**Integration Detection:**
- Mentions "Salesforce", "HubSpot", "our CRM" → integration_needs
- "Needs to sync with our system" → integration_needs
- "API access" → integration_needs = ["api"]
- "Automatic updates" → likely integration need, clarify

**Urgency Detection:**
- "Need this ASAP" → urgency = "high"
- "Evaluating options" → urgency = "medium"
- "Just exploring" → urgency = "low"
- Mentions deadline → urgency = "high"
- Mentions current tool problems → urgency = "medium" to "high"

## Partial Qualification
If you discover some signals but not all:
- Log what you have discovered so far
- Continue natural conversation, don't force remaining questions
- Value creation comes before complete qualification
- Can pass partial qualification_signals with fields set to None for unknowns
"""
```

#### Subtask 3.2.3: Test prompt-based qualification
**Reference:** `../research/quick-references/testing-quick-ref.md`

**Actions:**
1. Create test conversations with different qualification scenarios
2. Verify Sarah extracts correct signals from various user responses
3. Test that webhook is called with proper qualification_signals structure
4. Validate qualification tier determination logic
5. Test partial qualification scenarios (not all signals discovered)

**Test cases to implement:**
```python
@pytest.mark.asyncio
async def test_qualification_discovery_enterprise():
    """Test that Sarah discovers enterprise signals naturally."""
    agent = PandaDocTrialistAgent()

    # Simulate conversation
    user_responses = [
        "We need better proposal tracking",
        "Our 12 sales reps create them, managers review, reps send",
        "We do about 150-200 proposals per month",
        "Everything needs to sync with Salesforce"
    ]

    # After conversation, verify webhook was called with correct signals
    assert agent.discovered_signals["team_size"] >= 10
    assert agent.discovered_signals["monthly_volume"] >= 100
    assert "salesforce" in agent.discovered_signals["integration_needs"]
    assert agent.discovered_signals["qualification_tier"] == "sales_ready"

@pytest.mark.asyncio
async def test_qualification_discovery_self_serve():
    """Test that Sarah identifies self-serve users."""
    agent = PandaDocTrialistAgent()

    user_responses = [
        "I'm a freelance consultant",
        "Just me, sending a few contracts per month",
        "Maybe 5-10 documents monthly"
    ]

    assert agent.discovered_signals["team_size"] == 1
    assert agent.discovered_signals["monthly_volume"] < 50
    assert agent.discovered_signals["qualification_tier"] == "self_serve"
```

### Task 3.3: Active Listening and Backchanneling
**Owner:** Voice UX Designer
**Estimate:** 2 hours

#### Subtask 3.3.1: Implement active listening cues
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 300-301)

```python
import random
import asyncio

class ActiveListening:
    CUES = ["mm-hmm", "I see", "got it", "right", "exactly", "okay", "sure"]

    async def inject_listening_cue(self, context: RunContext):
        """Inject listening cue every 20-30 seconds."""
        await asyncio.sleep(random.uniform(20, 30))
        cue = random.choice(self.CUES)
        await context.llm.say(cue)
```

**Actions:**
1. Create cue bank
2. Implement timing logic
3. Add natural variation
4. Test in conversations

---

## Epic 4: Testing & Quality
*Implement comprehensive testing using LiveKit testing framework*

### Task 4.1: Unit Tests for Tools
**Owner:** Test Engineer
**Estimate:** 4 hours

#### Subtask 4.1.1: Create tool test fixtures
**Reference:** `../research/quick-references/testing-quick-ref.md` - Pattern 1
**Documentation:** `../research/livekit/testing-framework.md` - Section 4
**LiveKit Docs:** `/agents/build/testing` (test setup with AgentSession), `/agents/build/tools` (mocking tools)

```python
# tests/test_tools.py
import pytest
from livekit.agents import AgentSession, inference
from agent import PandaDocTrialistAgent

@pytest.fixture
def mock_llm():
    return inference.LLM(model="openai/gpt-4.1-mini")

@pytest.fixture
async def agent_session(mock_llm):
    async with AgentSession(llm=mock_llm) as session:
        yield session
```

**Actions:**
1. Create test fixtures
2. Set up mock LLM
3. Configure test session
4. Add helper utilities

#### Subtask 4.1.2: Test knowledge search tool
**Reference:** `TESTING_INTEGRATION_GUIDE.md` - Tool Testing
**LiveKit Docs:** `/agents/build/testing` (tool call assertions: is_function_call, is_function_call_output)

```python
@pytest.mark.asyncio
async def test_unleash_search_knowledge_tool(agent_session):
    """Test Unleash API knowledge search."""

    agent = PandaDocTrialistAgent()
    await agent_session.start(agent)

    # Test successful search
    result = await agent.unleash_search_knowledge(
        context=None,  # Mock context
        query="How do I create a template?",
        category="features"
    )

    assert "results" in result
    assert len(result["results"]) > 0
    assert "suggested_followup" in result

@pytest.mark.asyncio
async def test_unleash_search_knowledge_fallback(agent_session):
    """Test graceful fallback on API failure."""

    agent = PandaDocTrialistAgent()
    await agent_session.start(agent)

    # Test with invalid API key (should fallback)
    with patch.dict(os.environ, {"UNLEASH_API_KEY": "invalid"}):
        result = await agent.unleash_search_knowledge(
            context=None,
            query="test query"
        )

        assert "error" in result
        assert result["results"][0]["title"] == "Support Available"

@pytest.mark.asyncio
async def test_calendar_management_agent_tool(agent_session):
    """Test calendar sub-agent invocation."""

    agent = PandaDocTrialistAgent()
    await agent_session.start(agent)

    result = await agent.calendar_management_agent(
        context=None,
        request="Schedule a demo for tomorrow at 2pm",
        user_email="test@example.com"
    )

    assert result["status"] == "handoff_initiated"
    assert result["subagent"] == "google_calendar_agent"
    assert result["user_email"] == "test@example.com"

@pytest.mark.asyncio
async def test_webhook_send_conversation_event_tool(agent_session):
    """Test event tracking and state updates."""

    agent = PandaDocTrialistAgent()
    await agent_session.start(agent)

    result = await agent.webhook_send_conversation_event(
        context=None,
        event_type="qualification",
        call_id="test-call-123",
        trialist={"email": "test@example.com", "company": "Test Co"},
        data={
            "qualification_signals": {
                "team_size": 12,
                "monthly_volume": 150,
                "integration_needs": ["salesforce"],
                "urgency": "high",
                "qualification_tier": "sales_ready"
            }
        }
    )

    assert result["logged"] is True
    assert result["event_type"] == "qualification"
    assert agent.discovered_signals["team_size"] == 12
    assert agent.discovered_signals["monthly_volume"] == 150
    assert "salesforce" in agent.discovered_signals["integration_needs"]
    assert agent.discovered_signals["qualification_tier"] == "sales_ready"
```

**Actions:**
1. Write test for each v1 tool
2. Test API failure scenarios
3. Verify error handling and fallbacks
4. Check response format and state updates

### Task 4.2: Conversation Flow Tests
**Owner:** QA Engineer
**Estimate:** 6 hours

#### Subtask 4.2.1: Test greeting patterns
**Reference:** `../research/quick-references/testing-quick-ref.md` - Pattern 2
**Documentation:** LiveKit testing evaluation framework
**LiveKit Docs:** `/agents/build/testing` (judge-based evaluation with .judge(), test setup)

```python
@pytest.mark.asyncio
async def test_greeting_is_friendly():
    """Test that Sarah greets users warmly."""

    async with (
        inference.LLM(model="openai/gpt-4.1-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(PandaDocTrialistAgent())

        result = await session.run(user_input="Hello")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Greets as Sarah from PandaDoc.
                Mentions trial status or offers help.
                Uses friendly, professional tone.
                """,
            )
        )
```

**Actions:**
1. Test each conversation state
2. Verify transitions
3. Check tone consistency
4. Test edge cases

#### Subtask 4.2.2: Test prompt-based qualification flow
**Reference:** `../research/livekit/testing-framework.md` - Section 8
**LiveKit Docs:** `/agents/build/testing` (multiple turns testing, RunResult structure), `/agents/build/workflows` (userdata for state)

```python
@pytest.mark.asyncio
async def test_natural_qualification_discovery():
    """Test that Sarah discovers qualification signals through natural conversation."""

    async with (
        inference.LLM(model="openai/gpt-4.1-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()
        await session.start(agent)

        # Simulate natural discovery conversation
        conversation = [
            "We send about 200 proposals per month",
            "Our 12 sales reps handle them",
            "Everything needs to sync with Salesforce"
        ]

        for user_input in conversation:
            result = await session.run(user_input=user_input)

        # Check agent discovered qualification signals naturally
        assert agent.discovered_signals["monthly_volume"] >= 100
        assert agent.discovered_signals["team_size"] >= 10
        assert "salesforce" in agent.discovered_signals["integration_needs"]
        assert agent.discovered_signals["qualification_tier"] == "sales_ready"

@pytest.mark.asyncio
async def test_qualification_signal_extraction():
    """Test that Sarah extracts signals from various user phrasings."""

    async with (
        inference.LLM(model="openai/gpt-4.1-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()
        await session.start(agent)

        # Test different ways users describe team size
        test_cases = [
            ("We have a team of 15 people", {"team_size": 15}),
            ("Just me and 3 reps", {"team_size": 4}),
            ("Our sales org has about 20 reps", {"team_size": 20}),
        ]

        for user_input, expected_signals in test_cases:
            result = await session.run(user_input=user_input)
            # Verify Sarah extracted the signal correctly
            for key, value in expected_signals.items():
                assert agent.discovered_signals[key] == value
```

**Actions:**
1. Test qualification signal extraction from natural language
2. Verify Sarah identifies correct qualification tier
3. Test webhook is called with proper qualification_signals payload
4. Test edge cases (ambiguous responses, partial information)
5. Verify qualification happens without interrogation feel

### Task 4.3: Integration Tests
**Owner:** Integration Test Engineer
**Estimate:** 4 hours

#### Subtask 4.3.1: Test end-to-end conversation
**Reference:** `TESTING_INTEGRATION_GUIDE.md` - E2E Testing
**LiveKit Docs:** `/agents/build/testing` (multi-turn testing, loading history, agent handoff assertions)

```python
@pytest.mark.asyncio
async def test_full_conversation_flow():
    """Test complete conversation from greeting to booking."""

    async with (
        inference.LLM(model="openai/gpt-4.1-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()
        await session.start(agent)

        # Full conversation simulation
        conversations = [
            ("Hello", "greeting"),
            ("I need help with templates", "discovery"),
            ("We send 100 proposals monthly", "qualification"),
            ("We have 12 sales reps", "qualification"),
            ("Yes, book a demo", "booking")
        ]

        for user_input, expected_state in conversations:
            result = await session.run(user_input=user_input)
            # Verify state transitions
            assert agent.conversation_state in ["GREETING", "DISCOVERY", "QUALIFICATION", "NEXT_STEPS"]
```

**Actions:**
1. Create conversation scenarios
2. Test state transitions
3. Verify tool calls
4. Check final outcomes

---

## Epic 5: Calendar Management Sub-Agent
*Build the specialized calendar sub-agent for Google Calendar integration*

### Task 5.1: Create Calendar Sub-Agent Class
**Owner:** Integration Engineer
**Estimate:** 4 hours

#### Subtask 5.1.1: Implement CalendarManagementAgent class
**Reference:** LiveKit multi-agent architecture patterns
**Documentation:** https://docs.livekit.io/agents/build/workflows/
**LiveKit Docs:** `/agents/build/workflows` (extending Agent class, custom instructions, on_enter lifecycle)

```python
# Implementation location: my-app/src/calendar_agent.py
from livekit.agents import Agent, function_tool, RunContext
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

class CalendarManagementAgent(Agent):
    """Specialized sub-agent for Google Calendar operations."""

    def __init__(self):
        super().__init__(
            instructions="""You are a calendar management assistant that helps schedule meetings
            and check availability. Be efficient and accurate with date/time information.
            Always confirm details before creating events."""
        )

        # Initialize Google Calendar API client
        self.calendar_service = self._initialize_calendar_client()
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    def _initialize_calendar_client(self):
        """Initialize Google Calendar API client with service account credentials."""
        try:
            credentials_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            if not credentials_path:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")

            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/calendar']
            )

            service = build('calendar', 'v3', credentials=credentials)
            logger.info("Google Calendar API client initialized successfully")
            return service

        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar client: {e}")
            return None
```

**Actions:**
1. Create new file `my-app/src/calendar_agent.py`
2. Implement CalendarManagementAgent class extending Agent
3. Set up Google Calendar API authentication
4. Add initialization and configuration
5. Implement error handling for API client setup

**Environment Variables Required:**
```bash
GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
GOOGLE_CALENDAR_ID=primary  # Optional, defaults to "primary"
```

**Google Calendar API Setup:**
1. Create a Google Cloud project: https://console.cloud.google.com/
2. Enable Google Calendar API
3. Create a service account with Calendar API access
4. Download service account JSON key file
5. Share the target calendar with the service account email

### Task 5.2: Implement Google Calendar Tools
**Owner:** Backend Engineer
**Estimate:** 6 hours

#### Subtask 5.2.1: Implement check_availability tool
**Reference:** Google Calendar API Events.list documentation
**Documentation:** https://developers.google.com/calendar/api/v3/reference/events/list
**LiveKit Docs:** `/agents/build/tools` (async function tools, error handling with ToolError), `/agents/build/external-data` (external API integration)

```python
@function_tool
async def check_availability(
    self,
    context: RunContext,
    start_date: str,
    end_date: str,
    timezone: str = "America/New_York"
):
    """Check calendar availability for a date range.

    Args:
        start_date: ISO 8601 format (e.g., "2025-01-15T09:00:00")
        end_date: ISO 8601 format (e.g., "2025-01-15T17:00:00")
        timezone: IANA timezone (e.g., "America/New_York", "UTC")

    Returns:
        {
            "available_slots": [
                {"start": "2025-01-15T09:00:00-05:00", "end": "2025-01-15T10:00:00-05:00"},
                {"start": "2025-01-15T14:00:00-05:00", "end": "2025-01-15T15:00:00-05:00"}
            ],
            "busy_slots": [...],
            "timezone": "America/New_York"
        }
    """
    await context.llm.say("Checking the calendar...")

    try:
        if not self.calendar_service:
            raise ValueError("Calendar service not initialized")

        # Query for busy times using freebusy API
        body = {
            "timeMin": start_date,
            "timeMax": end_date,
            "timeZone": timezone,
            "items": [{"id": self.calendar_id}]
        }

        freebusy_result = self.calendar_service.freebusy().query(body=body).execute()
        busy_slots = freebusy_result['calendars'][self.calendar_id].get('busy', [])

        # Calculate available slots (assuming 9am-5pm working hours, 1-hour slots)
        available_slots = self._calculate_available_slots(
            start_date,
            end_date,
            busy_slots,
            timezone
        )

        return {
            "available_slots": available_slots,
            "busy_slots": busy_slots,
            "timezone": timezone,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        await context.llm.say("I'm having trouble accessing the calendar right now...")
        return {
            "available_slots": [],
            "busy_slots": [],
            "error": str(e),
            "success": False
        }

def _calculate_available_slots(
    self,
    start_date: str,
    end_date: str,
    busy_slots: list,
    timezone: str,
    slot_duration_minutes: int = 60
) -> list:
    """Calculate available time slots based on busy periods."""
    from datetime import datetime, timedelta
    import pytz

    # Parse dates
    tz = pytz.timezone(timezone)
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')).astimezone(tz)
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).astimezone(tz)

    # Business hours: 9am-5pm
    available = []
    current = start.replace(hour=9, minute=0, second=0, microsecond=0)
    end_of_day = start.replace(hour=17, minute=0, second=0, microsecond=0)

    while current < end and current < end_of_day:
        slot_end = current + timedelta(minutes=slot_duration_minutes)

        # Check if slot overlaps with any busy period
        is_available = True
        for busy in busy_slots:
            busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00')).astimezone(tz)
            busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00')).astimezone(tz)

            if (current < busy_end and slot_end > busy_start):
                is_available = False
                break

        if is_available:
            available.append({
                "start": current.isoformat(),
                "end": slot_end.isoformat()
            })

        current = slot_end

    return available
```

**Actions:**
1. Implement check_availability function tool
2. Add Google Calendar Freebusy API integration
3. Implement timezone conversion logic
4. Add available slot calculation algorithm
5. Handle edge cases (multi-day, holidays, etc.)
6. Test with various date ranges and timezones

**Estimate:** 3 hours

#### Subtask 5.2.2: Implement create_appointment tool
**Reference:** Google Calendar API Events.insert documentation
**Documentation:** https://developers.google.com/calendar/api/v3/reference/events/insert
**LiveKit Docs:** `/agents/build/tools` (function tools with complex return values), `/agents/build/external-data` (async operations)

```python
@function_tool
async def create_appointment(
    self,
    context: RunContext,
    title: str,
    start_time: str,
    end_time: str,
    attendee_emails: list[str],
    description: str = "",
    timezone: str = "America/New_York",
    meeting_type: str = "google_meet"
):
    """Create a calendar appointment and send invitations.

    Args:
        title: Meeting title (e.g., "PandaDoc Demo with Sarah")
        start_time: ISO 8601 format (e.g., "2025-01-15T14:00:00")
        end_time: ISO 8601 format (e.g., "2025-01-15T15:00:00")
        attendee_emails: List of email addresses to invite
        description: Meeting description/agenda
        timezone: IANA timezone (default: "America/New_York")
        meeting_type: "google_meet" or "phone" (default: "google_meet")

    Returns:
        {
            "event_id": "abc123...",
            "meeting_link": "https://meet.google.com/xxx-yyyy-zzz",
            "calendar_link": "https://calendar.google.com/event?eid=...",
            "attendees": ["user@example.com"],
            "confirmation": "Meeting scheduled for Jan 15 at 2pm ET"
        }
    """
    await context.llm.say("Creating the appointment...")

    try:
        if not self.calendar_service:
            raise ValueError("Calendar service not initialized")

        # Build event object
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone,
            },
            'attendees': [{'email': email} for email in attendee_emails],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 30},        # 30 min before
                ],
            },
        }

        # Add Google Meet conference if requested
        if meeting_type == "google_meet":
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"meet-{datetime.now().timestamp()}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }

        # Create the event
        created_event = self.calendar_service.events().insert(
            calendarId=self.calendar_id,
            body=event,
            conferenceDataVersion=1,
            sendUpdates='all'  # Send email invitations to all attendees
        ).execute()

        # Extract meeting link
        meeting_link = None
        if 'conferenceData' in created_event:
            meeting_link = created_event['conferenceData']['entryPoints'][0]['uri']

        # Format confirmation message
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_time)
        confirmation = f"Meeting scheduled for {start_dt.strftime('%B %d at %I:%M %p')} {timezone}"

        return {
            "event_id": created_event['id'],
            "meeting_link": meeting_link,
            "calendar_link": created_event.get('htmlLink'),
            "attendees": attendee_emails,
            "confirmation": confirmation,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        await context.llm.say("I encountered an issue creating the appointment...")
        return {
            "event_id": None,
            "error": str(e),
            "success": False
        }
```

**Actions:**
1. Implement create_appointment function tool
2. Add Google Calendar Events.insert API integration
3. Add Google Meet conference creation
4. Implement email invitation sending
5. Add confirmation message formatting
6. Handle errors and edge cases
7. Test event creation with various configurations

**Estimate:** 3 hours

### Task 5.3: Sub-Agent Communication Protocol
**Owner:** Architecture Engineer
**Estimate:** 3 hours

#### Subtask 5.3.1: Define handoff protocol
**Reference:** LiveKit multi-agent workflow patterns
**Documentation:** `../research/livekit/function-tools.md` - Section 3
**LiveKit Docs:** `/agents/build/workflows` (agent handoff, chat_ctx preservation), `/agents/build/tools` (return Agent from tools)

```python
# Update to my-app/src/agent.py

from calendar_agent import CalendarManagementAgent

class PandaDocTrialistAgent(Agent):
    def __init__(self):
        super().__init__(instructions=...)
        self.calendar_agent = CalendarManagementAgent()

    @function_tool
    async def calendar_management_agent(
        self,
        context: RunContext,
        request: str,
        user_email: str = None
    ):
        """Invoke calendar sub-agent for Google Calendar operations.

        This tool hands off calendar-related requests to a specialized sub-agent
        that handles Google Calendar API interactions.

        Args:
            request: Natural language calendar request (e.g., "Schedule a demo for tomorrow at 2pm")
            user_email: Email for calendar operations
        """
        await context.llm.say("Let me check the calendar for you...")

        try:
            # Parse the request to determine action
            if "check availability" in request.lower() or "available" in request.lower():
                # Extract date range from request (simplified example)
                result = await self.calendar_agent.check_availability(
                    context=context,
                    start_date="2025-01-15T09:00:00",  # Parse from request
                    end_date="2025-01-15T17:00:00",
                    timezone="America/New_York"
                )
                return result

            elif "schedule" in request.lower() or "book" in request.lower():
                # Extract meeting details from request
                result = await self.calendar_agent.create_appointment(
                    context=context,
                    title="PandaDoc Demo with Sarah",
                    start_time="2025-01-15T14:00:00",  # Parse from request
                    end_time="2025-01-15T15:00:00",
                    attendee_emails=[user_email] if user_email else [],
                    description="Demo of PandaDoc features",
                    timezone="America/New_York"
                )
                return result

            else:
                return {
                    "error": "Could not determine calendar action from request",
                    "success": False
                }

        except Exception as e:
            logger.error(f"Error in calendar sub-agent handoff: {e}")
            return {
                "error": str(e),
                "success": False
            }
```

**Actions:**
1. Update main agent to instantiate calendar sub-agent
2. Implement request parsing logic
3. Define handoff parameters and response structure
4. Add error propagation from sub-agent to main agent
5. Test handoff flow with various requests

**Estimate:** 1.5 hours

#### Subtask 5.3.2: Implement error handling for sub-agent failures
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` - Error handling patterns
**LiveKit Docs:** `/agents/build/tools` (ToolError exception), `/agents/build/events` (error propagation)

```python
async def _handle_calendar_error(self, context: RunContext, error: Exception):
    """Handle calendar sub-agent errors gracefully."""

    error_responses = {
        "authentication": "I'm having trouble connecting to the calendar system...",
        "authorization": "I don't have permission to access that calendar...",
        "not_found": "I couldn't find that calendar or event...",
        "quota_exceeded": "We've hit a temporary limit. Let's try again in a moment...",
        "network": "I'm having connectivity issues. Can we try again?"
    }

    # Determine error type
    error_type = self._classify_calendar_error(error)
    response = error_responses.get(error_type, "Something went wrong with the calendar...")

    await context.llm.say(response)

    # Offer alternative
    await context.llm.say(
        "Would you like me to note down your preferred time and have someone "
        "from our team reach out to confirm?"
    )

def _classify_calendar_error(self, error: Exception) -> str:
    """Classify calendar API errors for appropriate handling."""
    error_str = str(error).lower()

    if "authentication" in error_str or "credentials" in error_str:
        return "authentication"
    elif "permission" in error_str or "forbidden" in error_str:
        return "authorization"
    elif "not found" in error_str:
        return "not_found"
    elif "quota" in error_str or "rate limit" in error_str:
        return "quota_exceeded"
    elif "timeout" in error_str or "network" in error_str:
        return "network"
    else:
        return "unknown"
```

**Actions:**
1. Implement error classification logic
2. Add graceful error messages for each error type
3. Provide fallback options when calendar fails
4. Log errors for debugging
5. Test error scenarios

**Estimate:** 1.5 hours

### Task 5.4: Testing Calendar Sub-Agent
**Owner:** Test Engineer
**Estimate:** 4 hours

#### Subtask 5.4.1: Unit tests for calendar tools
**Reference:** `../research/quick-references/testing-quick-ref.md` - Tool testing patterns
**LiveKit Docs:** `/agents/build/testing` (mock_tools helper, testing async tools), `/agents/build/tools` (tool testing patterns)

```python
# tests/test_calendar_agent.py
import pytest
from datetime import datetime, timedelta
from calendar_agent import CalendarManagementAgent
from unittest.mock import Mock, patch

@pytest.fixture
def calendar_agent():
    """Create calendar agent with mocked Google Calendar API."""
    with patch('calendar_agent.build') as mock_build:
        agent = CalendarManagementAgent()
        return agent

@pytest.mark.asyncio
async def test_check_availability_success(calendar_agent):
    """Test successful availability check."""

    # Mock Google Calendar API response
    mock_response = {
        'calendars': {
            'primary': {
                'busy': [
                    {
                        'start': '2025-01-15T10:00:00-05:00',
                        'end': '2025-01-15T11:00:00-05:00'
                    }
                ]
            }
        }
    }

    calendar_agent.calendar_service.freebusy().query().execute.return_value = mock_response

    result = await calendar_agent.check_availability(
        context=Mock(),
        start_date="2025-01-15T09:00:00",
        end_date="2025-01-15T17:00:00",
        timezone="America/New_York"
    )

    assert result['success'] is True
    assert len(result['available_slots']) > 0
    assert len(result['busy_slots']) == 1

@pytest.mark.asyncio
async def test_create_appointment_success(calendar_agent):
    """Test successful appointment creation."""

    # Mock Google Calendar API response
    mock_event = {
        'id': 'event123',
        'htmlLink': 'https://calendar.google.com/event?eid=event123',
        'conferenceData': {
            'entryPoints': [
                {'uri': 'https://meet.google.com/xxx-yyyy-zzz'}
            ]
        }
    }

    calendar_agent.calendar_service.events().insert().execute.return_value = mock_event

    result = await calendar_agent.create_appointment(
        context=Mock(),
        title="Test Meeting",
        start_time="2025-01-15T14:00:00",
        end_time="2025-01-15T15:00:00",
        attendee_emails=["test@example.com"],
        timezone="America/New_York"
    )

    assert result['success'] is True
    assert result['event_id'] == 'event123'
    assert result['meeting_link'] is not None
    assert 'test@example.com' in result['attendees']

@pytest.mark.asyncio
async def test_calendar_error_handling(calendar_agent):
    """Test graceful error handling."""

    # Simulate API error
    calendar_agent.calendar_service.freebusy().query().execute.side_effect = Exception("API Error")

    result = await calendar_agent.check_availability(
        context=Mock(),
        start_date="2025-01-15T09:00:00",
        end_date="2025-01-15T17:00:00"
    )

    assert result['success'] is False
    assert 'error' in result
```

**Actions:**
1. Write unit tests for check_availability tool
2. Write unit tests for create_appointment tool
3. Test error handling and fallbacks
4. Test timezone conversions
5. Test edge cases (past dates, invalid inputs)
6. Mock Google Calendar API responses

**Estimate:** 4 hours

---

## Epic 6: Integration & Deployment
*Deploy the agent and integrate with production systems*

### Task 6.1: Environment Configuration
**Owner:** DevOps Engineer
**Estimate:** 3 hours

#### Subtask 6.1.1: Configure LiveKit Cloud
**Reference:** `my-app/README.md` - Dev Setup
**Documentation:** https://docs.livekit.io/home/cloud/
**LiveKit Docs:** `/agents/start/voice-ai` (LiveKit Cloud auth), `/agents/ops/deployment/secrets` (credentials management)

```bash
# Set up LiveKit CLI
lk cloud auth

# Configure environment
lk app env -w -d .env.local

# Verify configuration
lk app list
```

**Actions:**
1. Create LiveKit Cloud account
2. Generate API credentials
3. Configure environment
4. Test connectivity

#### Subtask 6.1.2: Set up dependencies
**Reference:** `my-app/pyproject.toml`
**LiveKit Docs:** `/agents/start/voice-ai` (dependencies setup), `/agents/ops/deployment/custom` (environment variables)

```toml
dependencies = [
    "livekit-agents[silero,turn-detector,elevenlabs,deepgram]~=1.2",
    "livekit-plugins-noise-cancellation~=0.2",
    "python-dotenv",
]
```

**Actions:**
1. Update pyproject.toml
2. Run uv sync
3. Download required models
4. Verify installations

### Task 6.2: Local Testing
**Owner:** Developer
**Estimate:** 2 hours

#### Subtask 6.2.1: Test in console mode
**Reference:** `my-app/README.md` - Run the agent
**LiveKit Docs:** `/agents/start/voice-ai` (console mode testing), `/agents/build/testing` (debugging verbose output)

```bash
# Download models first time
uv run python src/agent.py download-files

# Test in console
uv run python src/agent.py console
```

**Actions:**
1. Download VAD models
2. Test console interaction
3. Verify voice pipeline
4. Check tool execution

#### Subtask 6.2.2: Test with dev server
**Reference:** LiveKit development guide
**LiveKit Docs:** `/agents/start/playground` (web-based testing), `/agents/start/voice-ai` (dev mode)

```bash
# Run in dev mode
uv run python src/agent.py dev

# Connect with test client
# Use LiveKit playground or custom frontend
```

**Actions:**
1. Start dev server
2. Connect test client
3. Test full conversation
4. Monitor logs

### Task 6.3: Production Deployment
**Owner:** Platform Engineer
**Estimate:** 4 hours

#### Subtask 6.3.1: Dockerize application
**Reference:** `my-app/Dockerfile`
**Documentation:** LiveKit deployment guide
**LiveKit Docs:** `/agents/ops/deployment/builds` (Dockerfile templates, best practices)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync --frozen

CMD ["uv", "run", "python", "src/agent.py", "start"]
```

**Actions:**
1. Review Dockerfile
2. Build image
3. Test container locally
4. Push to registry

#### Subtask 6.3.2: Deploy to LiveKit Cloud
**Reference:** https://docs.livekit.io/agents/ops/deployment/
**LiveKit Docs:** `/agents/ops/deployment` (complete deployment workflow), `/agents/ops/deployment/logs` (monitoring), `/agents/build/metrics` (telemetry)

```bash
# Deploy agent
lk agent deploy

# Monitor deployment
lk agent logs -f

# Scale workers
lk agent scale --replicas 3
```

**Actions:**
1. Deploy to LiveKit Cloud
2. Configure scaling
3. Set up monitoring
4. Test production endpoints

---

## Reference Documentation

### Core Documentation Files Created

1. **Voice Pipeline Research**
   - `../research/livekit/voice-pipeline.md` - Complete STT/TTS configuration
   - `../research/quick-references/voice-pipeline-quick-ref.md` - Configuration templates

2. **Function Tools Research**
   - `../research/livekit/function-tools.md` - 34K comprehensive guide
   - `../research/quick-references/function-tools-summary.md` - Quick patterns reference

3. **Testing Framework**
   - `../research/livekit/testing-framework.md` - Complete testing guide
   - `../research/quick-references/testing-quick-ref.md` - Test patterns

4. **Requirements Mapping**
   - `REQUIREMENTS_MAP.md` - Full technical mapping
   - `REQUIREMENTS_MATRIX.csv` - Trackable requirements

5. **Implementation Guides**
   - `REQUIREMENTS_MAP.md` - Quick implementation reference
   - `ANALYSIS.md` - ROI and timeline analysis

### Key LiveKit Documentation Links

- **Models**: https://docs.livekit.io/agents/models/
- **Deployment**: https://docs.livekit.io/agents/ops/deployment/
- **Testing**: https://docs.livekit.io/agents/build/testing/
- **Workflows**: https://docs.livekit.io/agents/build/workflows/

### Source Files to Reference

- **Agent Implementation**: `my-app/src/agent.py`
- **Test Examples**: `my-app/tests/test_agent.py`
- **Configuration**: `my-app/pyproject.toml`
- **PandaDoc Spec**: `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md`

---

## Success Criteria

### MVP (Week 5)
- [ ] Sarah persona responding appropriately
- [ ] Voice pipeline < 700ms latency
- [ ] 3 tools + calendar sub-agent implemented (Unleash API, calendar sub-agent with Google Calendar API, event tracking)
- [ ] Google Calendar sub-agent functional
- [ ] Calendar availability checking working
- [ ] Appointment booking through Google Calendar API
- [ ] Prompt-based qualification discovering signals naturally (team size, volume, integrations)
- [ ] Qualification signals logged via webhook_send_conversation_event
- [ ] 75%+ conversation completion rate
- [ ] All tests passing

### Production (Week 9)
- [ ] Real API integrations
- [ ] Meeting booking functional
- [ ] Qualification accuracy > 85%
- [ ] Error recovery working
- [ ] Deployed to LiveKit Cloud
- [ ] Monitoring in place

### Full Feature Set (Week 13)
- [ ] Multi-agent support
- [ ] Salesforce integration
- [ ] Advanced analytics
- [ ] A/B testing capability
- [ ] 25%+ conversion rate
- [ ] $400K+ revenue impact

---

## Risk Mitigation

### Technical Risks
1. **Latency exceeds 700ms**
   - Mitigation: Use preemptive generation, optimize VAD
   - Fallback: Adjust user expectations

2. **API integrations fail**
   - Mitigation: Mock first, integrate gradually
   - Fallback: Provide manual alternatives

3. **Poor speech recognition**
   - Mitigation: Test multiple STT providers
   - Fallback: Offer text-based support

### Business Risks
1. **Low user adoption**
   - Mitigation: A/B test, gather feedback
   - Fallback: Make optional, not mandatory

2. **Qualification inaccuracy**
   - Mitigation: Start conservative, tune gradually
   - Fallback: Human review queue

---

## Next Steps

1. **Immediate Actions**
   - Review this plan with team
   - Set up LiveKit Cloud account
   - Create development environment
   - Assign epic owners

2. **Week 1 Focus**
   - Complete Epic 1 (Core Foundation)
   - Start Epic 2 (Tools)
   - Set up testing framework

3. **Daily Checklist**
   - Update task status
   - Run tests
   - Review conversation logs
   - Tune parameters

---

*This implementation plan is based on extensive research of LiveKit capabilities, PandaDoc requirements, and voice AI best practices. Each task includes specific references to documentation and code examples to ensure successful execution.*
