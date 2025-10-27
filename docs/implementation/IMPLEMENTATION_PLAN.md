# PandaDoc Voice Agent Implementation Plan
*Comprehensive plan for building the Trial Success Voice Agent with LiveKit*

## Executive Summary

This implementation plan details the development of "Sarah," a voice AI agent for PandaDoc trial success. Based on extensive research of LiveKit capabilities, the PandaDoc specification, and best practices, this plan provides a structured approach with epics, tasks, and subtasks that can be executed by any Claude Code instance or developer.

**Timeline:** 4 weeks (MVP) → 8 weeks (Production) → 12 weeks (Full Feature Set)
**Confidence:** 90%+ technical feasibility
**ROI:** $400K+ Q4 2025 revenue contribution

## Table of Contents

1. [Project Setup](#project-setup)
2. [Epic 1: Core Voice Agent Foundation](#epic-1-core-voice-agent-foundation)
3. [Epic 2: Tool Implementation](#epic-2-tool-implementation)
4. [Epic 3: Conversation Intelligence](#epic-3-conversation-intelligence)
5. [Epic 4: Testing & Quality](#epic-4-testing--quality)
6. [Epic 5: Integration & Deployment](#epic-5-integration--deployment)
7. [Reference Documentation](#reference-documentation)

---

## Project Setup

### Prerequisites
- Python 3.9+
- LiveKit Cloud account
- uv package manager
- Environment variables configured

### Initial Configuration
```bash
cd my-app
uv sync
uv add "livekit-agents[silero,turn-detector,elevenlabs,deepgram]~=1.2"
```

---

## Epic 1: Core Voice Agent Foundation
*Build the fundamental voice agent with Sarah persona and voice pipeline*

### Task 1.1: Transform Assistant Class to PandaDocTrialistAgent
**Owner:** Voice Pipeline Engineer
**Estimate:** 4 hours

#### Subtask 1.1.1: Create PandaDocTrialistAgent class
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 28-60)
**Documentation:** `REQUIREMENTS_MAP.md` - Section 1

```python
# Implementation location: my-app/src/agent.py
class PandaDocTrialistAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are Sarah, a friendly and knowledgeable Trial Success Specialist..."""
        )
```

**Actions:**
1. Rename `Assistant` class to `PandaDocTrialistAgent`
2. Copy Sarah persona instructions from spec (lines 31-42)
3. Add conversation style guidelines
4. Include operating principles

#### Subtask 1.1.2: Add conversation state management
**Reference:** `../research/livekit/function-tools.md` - Section 2 (RunContext)
**Documentation:** LiveKit Agent state management patterns

```python
def __init__(self):
    super().__init__(instructions=...)
    self.conversation_state = "GREETING"
    self.qualification_score = 0
    self.discovered_needs = []
    self.trial_day = None
```

**Actions:**
1. Add state tracking attributes
2. Initialize qualification tracking
3. Create state transition methods

#### Subtask 1.1.3: Implement state machine transitions
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 266-281)

```python
# State flow: GREETING → DISCOVERY → VALUE_DEMO → QUALIFICATION → NEXT_STEPS → CLOSING
def transition_state(self, from_state: str, to_state: str):
    valid_transitions = {
        "GREETING": ["DISCOVERY", "FRICTION_RESCUE"],
        "DISCOVERY": ["VALUE_DEMO", "FRICTION_RESCUE"],
        # ... etc
    }
```

**Actions:**
1. Implement state validation logic
2. Add transition logging
3. Handle invalid transitions

### Task 1.2: Configure Voice Pipeline
**Owner:** Audio Engineer
**Estimate:** 3 hours

#### Subtask 1.2.1: Set up Deepgram STT
**Reference:** `livekit_voice_pipeline_research.md` - Deepgram Configuration
**Documentation:** https://docs.livekit.io/agents/models/stt/inference/deepgram/

```python
# Update entrypoint function
session = AgentSession(
    stt="deepgram/nova-2",  # or nova-2-phonecall for telephony
    # ... other config
)
```

**Actions:**
1. Replace AssemblyAI with Deepgram
2. Configure sample rate (16kHz)
3. Add filler words detection
4. Test with various accents

#### Subtask 1.2.2: Configure ElevenLabs TTS with Rachel voice
**Reference:** Research document on ElevenLabs integration
**Documentation:** https://docs.livekit.io/agents/models/tts/inference/elevenlabs/

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

#### Subtask 1.2.3: Optimize VAD and turn detection
**Reference:** `livekit_voice_pipeline_research.md` - VAD Configuration

```python
from livekit.plugins.turn_detector.multilingual import MultilingualModel

session = AgentSession(
    turn_detection=MultilingualModel(),
    vad=ctx.proc.userdata["vad"],  # Pre-warmed Silero VAD
    preemptive_generation=True,
)
```

**Actions:**
1. Configure 300ms VAD threshold
2. Enable preemptive generation
3. Set interruption handling
4. Test with background noise

### Task 1.3: Implement Error Handling and Fallbacks
**Owner:** Reliability Engineer
**Estimate:** 2 hours

#### Subtask 1.3.1: Add TTS fallback to OpenAI
**Reference:** `/docs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (line 69)

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
*Implement the 8 MVP tools for knowledge, meetings, and qualification*

### Task 2.1: Knowledge Base Tools
**Owner:** Backend Engineer
**Estimate:** 6 hours

#### Subtask 2.1.1: Implement unleash_search_knowledge tool
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 88-96)
**Documentation:** `../research/livekit/function-tools.md` - Section 1

```python
from livekit.agents import function_tool, RunContext

@function_tool
async def unleash_search_knowledge(self, context: RunContext, query: str, category: str = None):
    """Search PandaDoc knowledge base for answers.

    Args:
        query: Natural language question
        category: Optional - "features", "pricing", "integrations", "troubleshooting"
    """
    # MVP: Return mock responses
    mock_kb = {
        "templates": "To create a template, go to Templates section...",
        "pricing": "Our Business plan starts at $59/month...",
    }

    # Add "thinking" filler
    await context.llm.say("Let me find that for you...")

    # Return structured response
    return {
        "results": [{
            "title": "Creating Templates",
            "content": mock_kb.get(category, "General help..."),
            "relevance_score": 0.95,
        }],
        "suggested_followup": "Would you like me to walk you through this?"
    }
```

**Actions:**
1. Create function with proper decorator
2. Add mock knowledge base responses
3. Implement search logic
4. Add error handling
5. Test with common queries

#### Subtask 2.1.2: Implement unleash_get_competitor_comparison tool
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 97-105)
**Documentation:** `../research/quick-references/function-tools-summary.md` - Pattern 2

```python
@function_tool
async def unleash_get_competitor_comparison(
    self,
    context: RunContext,
    competitor: str,
    feature_focus: str = None
):
    """Get competitive differentiation vs DocuSign, HelloSign, etc.

    Args:
        competitor: "docusign|hellosign|proposify|adobe_sign"
        feature_focus: Optional specific feature to compare
    """
    comparisons = {
        "docusign": {
            "advantage": "70% more cost-effective",
            "features": "Better template library, easier to use"
        }
    }
    return comparisons.get(competitor, {})
```

**Actions:**
1. Create competitor comparison data
2. Implement comparison logic
3. Add feature-specific comparisons
4. Test with each competitor

### Task 2.2: Meeting and Qualification Tools
**Owner:** Integration Engineer
**Estimate:** 8 hours

#### Subtask 2.2.1: Implement chilipiper_check_availability tool
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 106-113)
**Documentation:** `../research/livekit/function-tools.md` - Section 3 (Async patterns)

```python
@function_tool
async def chilipiper_check_availability(
    self,
    context: RunContext,
    meeting_type: str = "pandadoc_enterprise_demo",
    date_range: dict = None
):
    """Check rep availability before offering times.

    Args:
        meeting_type: Type of meeting to book
        date_range: Next 7 days by default
    """
    # MVP: Return mock availability
    from datetime import datetime, timedelta

    now = datetime.now()
    slots = []
    for i in range(1, 4):  # Next 3 days
        slot_time = now + timedelta(days=i, hours=14)  # 2 PM slots
        slots.append(slot_time.isoformat())

    return {
        "available_slots": slots,
        "next_available": slots[0] if slots else None
    }
```

**Actions:**
1. Create availability checking logic
2. Generate realistic time slots
3. Add timezone handling
4. Test with various date ranges

#### Subtask 2.2.2: Implement chilipiper_book_meeting tool
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 114-124)
**Documentation:** `REQUIREMENTS_MAP.md` - Tool 6

```python
@function_tool
async def chilipiper_book_meeting(
    self,
    context: RunContext,
    lead: dict,
    meeting_type: str,
    qualification: dict,
    preferred_times: list = None,
    notes: str = None
):
    """Schedule qualified meeting with sales team.

    Args:
        lead: {email, first_name, last_name, company, phone}
        meeting_type: "pandadoc_enterprise_demo"
        qualification: {team_size, monthly_volume, integration_needs, urgency}
        preferred_times: Array of ISO timestamps
        notes: Context for sales rep
    """
    # Validate qualification
    if qualification.get("team_size", 0) < 10:
        raise ToolError("Lead does not meet qualification criteria")

    # MVP: Generate mock booking
    import uuid
    from datetime import datetime, timedelta

    meeting_time = datetime.now() + timedelta(days=2, hours=14)

    await context.llm.say("Let me get that scheduled for you...")

    return {
        "booking_id": str(uuid.uuid4()),
        "meeting_time": meeting_time.isoformat(),
        "calendar_link": f"https://meet.pandadoc.com/{uuid.uuid4()}",
        "confirmation_sent": True
    }
```

**Actions:**
1. Implement qualification validation
2. Create booking logic
3. Generate calendar links
4. Add confirmation handling
5. Test with various lead types

#### Subtask 2.2.3: Implement check_enterprise_eligibility tool
**Reference:** `REQUIREMENTS_MAP.md` - Section 3.2

```python
@function_tool
async def check_enterprise_eligibility(
    self,
    context: RunContext,
    team_size: int,
    conversation_signals: list,
    monthly_volume: int
):
    """Determine if lead qualifies for enterprise sales track.

    Args:
        team_size: Number of users
        conversation_signals: ["integration_needs", "api_requirements", etc.]
        monthly_volume: Documents per month
    """
    # Qualification logic
    is_enterprise = (
        team_size >= 10 and (
            "integration_needs" in conversation_signals or
            "api_requirements" in conversation_signals or
            "security_questions" in conversation_signals
        )
    )

    score = 0
    if team_size >= 10: score += 40
    if team_size >= 50: score += 20
    if monthly_volume >= 100: score += 20
    if "integration_needs" in conversation_signals: score += 20

    return {
        "is_enterprise": is_enterprise,
        "qualification_score": score,
        "routing_recommendation": "enterprise" if is_enterprise else "smb"
    }
```

**Actions:**
1. Define qualification criteria
2. Implement scoring logic
3. Add routing recommendations
4. Test with edge cases

### Task 2.3: Value and Communication Tools
**Owner:** Product Engineer
**Estimate:** 6 hours

#### Subtask 2.3.1: Implement calculate_pandadoc_roi tool
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 125-135)
**Documentation:** `../research/quick-references/function-tools-summary.md` - Pattern 1

```python
@function_tool
async def calculate_pandadoc_roi(
    self,
    context: RunContext,
    team_size: int,
    documents_per_month: int,
    average_doc_value: float = 5000,
    current_process: dict = None,
    use_case: str = "sales"
):
    """Generate personalized ROI calculations.

    Args:
        team_size: Number of users
        documents_per_month: Volume
        average_doc_value: Dollar amount
        current_process: {hours_per_doc, approval_days, error_rate}
        use_case: "sales|hr|legal|procurement"
    """
    # Default assumptions if not provided
    if not current_process:
        current_process = {
            "hours_per_doc": 2,
            "approval_days": 3,
            "error_rate": 0.05
        }

    # Calculate savings
    hours_per_doc_saved = current_process["hours_per_doc"] * 0.7  # 70% reduction
    hours_saved_monthly = hours_per_doc_saved * documents_per_month

    # Assume $50/hour cost
    monthly_savings = hours_saved_monthly * 50
    annual_savings = monthly_savings * 12

    # Calculate ROI
    monthly_cost = 59 * team_size  # Business plan
    roi_percentage = ((annual_savings - (monthly_cost * 12)) / (monthly_cost * 12)) * 100
    payback_months = (monthly_cost * 12) / annual_savings if annual_savings > 0 else 999

    await context.llm.say("Based on those numbers...")

    return {
        "annual_savings": round(annual_savings),
        "hours_saved_weekly": round(hours_saved_monthly / 4),
        "roi_percentage": round(roi_percentage),
        "payback_months": round(payback_months, 1),
        "key_benefits": [
            f"Reduce document creation from {current_process['hours_per_doc']} hours to {round(current_process['hours_per_doc'] * 0.3, 1)} hours",
            f"Decrease approval time by 70%",
            f"Save ${round(monthly_savings)} per month"
        ]
    }
```

**Actions:**
1. Implement ROI calculation logic
2. Add industry-specific calculations
3. Create benefit statements
4. Test with various inputs

#### Subtask 2.3.2: Implement webhook_send_conversation_event tool
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 136-145)
**Documentation:** `../research/livekit/function-tools.md` - Section 5 (Error handling)

```python
@function_tool
async def webhook_send_conversation_event(
    self,
    context: RunContext,
    event_type: str,
    call_id: str,
    trialist: dict,
    data: dict
):
    """Track conversation events and qualification signals.

    Args:
        event_type: "qualification|objection|booking|support"
        call_id: UUID
        trialist: {email, company}
        data: {qualification_score, intent_signals, objections, topics}
    """
    import json
    import logging

    # Log event for analytics
    event_data = {
        "event_type": event_type,
        "call_id": call_id,
        "timestamp": datetime.now().isoformat(),
        "trialist": trialist,
        "data": data
    }

    logger = logging.getLogger("analytics")
    logger.info(f"Conversation event: {json.dumps(event_data)}")

    # Update agent's internal state
    if event_type == "qualification":
        self.qualification_score = data.get("qualification_score", 0)

    # This is async/fire-and-forget
    return {"logged": True}
```

**Actions:**
1. Create event logging structure
2. Implement state updates
3. Add async handling
4. Test event tracking

#### Subtask 2.3.3: Implement hubspot_send_resource tool
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` (lines 146-155)

```python
@function_tool
async def hubspot_send_resource(
    self,
    context: RunContext,
    to_email: str,
    template_id: str,
    dynamic_data: dict
):
    """Email relevant resources/guides post-call.

    Args:
        to_email: Email address
        template_id: "case_study_template|integration_guide_template|pricing_overview_template"
        dynamic_data: {first_name, resource_type, industry, resource_url}
    """
    # MVP: Log the email that would be sent
    import logging

    email_data = {
        "to": to_email,
        "template": template_id,
        "data": dynamic_data,
        "scheduled": datetime.now().isoformat()
    }

    logger = logging.getLogger("email")
    logger.info(f"Resource email scheduled: {json.dumps(email_data)}")

    await context.llm.say("I'll send that to your email...")

    return {
        "email_id": str(uuid.uuid4()),
        "send_status": "queued"
    }
```

**Actions:**
1. Create email templates
2. Implement scheduling logic
3. Add resource mapping
4. Test with various resources

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

### Task 3.2: Qualification Logic
**Owner:** Business Logic Engineer
**Estimate:** 4 hours

#### Subtask 3.2.1: Implement qualification scoring
**Reference:** `../PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` - Qualification Framework
**Documentation:** `REQUIREMENTS_MAP.md` - Section 5

```python
def calculate_qualification_score(self, discovered_data: dict) -> int:
    """Calculate lead qualification score 0-100."""

    score = 0

    # Team size scoring
    team_size = discovered_data.get("team_size", 0)
    if team_size >= 50:
        score += 40
    elif team_size >= 10:
        score += 30
    elif team_size >= 5:
        score += 15

    # Volume scoring
    monthly_volume = discovered_data.get("monthly_volume", 0)
    if monthly_volume >= 200:
        score += 30
    elif monthly_volume >= 100:
        score += 20
    elif monthly_volume >= 50:
        score += 10

    # Integration needs
    if discovered_data.get("needs_integration"):
        score += 15

    # Urgency
    if discovered_data.get("urgent_need"):
        score += 15

    return min(score, 100)
```

**Actions:**
1. Define scoring criteria
2. Implement calculation logic
3. Add threshold definitions
4. Test scoring accuracy

#### Subtask 3.2.2: Implement natural discovery patterns
**Reference:** Spec lines on natural qualification

```python
def ask_qualification_question(self, topic: str) -> str:
    """Generate natural qualification questions."""

    natural_questions = {
        "team_size": (
            "Walk me through your document workflow - "
            "who creates proposals, who needs to review them, "
            "and who sends them out?"
        ),
        "budget": (
            "What are you using today and what made you "
            "look for something better?"
        ),
        "integration": (
            "Once a document is signed, where does that "
            "information need to go?"
        ),
        "timeline": (
            "When would you ideally like to have this "
            "up and running for your team?"
        )
    }

    return natural_questions.get(topic, "Tell me more about that...")
```

**Actions:**
1. Create natural question bank
2. Map to qualification criteria
3. Add follow-up questions
4. Test conversation flow

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
**Estimate:** 8 hours

#### Subtask 4.1.1: Create tool test fixtures
**Reference:** `../research/quick-references/testing-quick-ref.md` - Pattern 1
**Documentation:** `../research/livekit/testing-framework.md` - Section 4

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

#### Subtask 4.1.2: Test ROI calculation tool
**Reference:** `TESTING_INTEGRATION_GUIDE.md` - Tool Testing

```python
@pytest.mark.asyncio
async def test_calculate_roi_tool(agent_session):
    """Test ROI calculation produces accurate results."""

    agent = PandaDocTrialistAgent()
    await agent_session.start(agent)

    # Mock tool call
    result = await agent.calculate_pandadoc_roi(
        context=None,  # Mock context
        team_size=10,
        documents_per_month=100,
        average_doc_value=5000
    )

    assert result["annual_savings"] > 0
    assert result["roi_percentage"] > 100
    assert result["payback_months"] < 12
    assert len(result["key_benefits"]) >= 3
```

**Actions:**
1. Write test for each tool
2. Test edge cases
3. Verify error handling
4. Check response format

### Task 4.2: Conversation Flow Tests
**Owner:** QA Engineer
**Estimate:** 6 hours

#### Subtask 4.2.1: Test greeting patterns
**Reference:** `../research/quick-references/testing-quick-ref.md` - Pattern 2
**Documentation:** LiveKit testing evaluation framework

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

#### Subtask 4.2.2: Test qualification flow
**Reference:** `../research/livekit/testing-framework.md` - Section 8

```python
@pytest.mark.asyncio
async def test_qualification_discovery():
    """Test natural qualification discovery."""

    async with (
        inference.LLM(model="openai/gpt-4.1-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()
        await session.start(agent)

        # Simulate discovery conversation
        result = await session.run(
            user_input="We send about 200 proposals per month"
        )

        # Check agent updates qualification
        assert agent.qualification_score > 0
        assert "monthly_volume" in agent.discovered_needs
```

**Actions:**
1. Test qualification scoring
2. Verify data extraction
3. Check routing logic
4. Test edge cases

### Task 4.3: Integration Tests
**Owner:** Integration Test Engineer
**Estimate:** 4 hours

#### Subtask 4.3.1: Test end-to-end conversation
**Reference:** `TESTING_INTEGRATION_GUIDE.md` - E2E Testing

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

## Epic 5: Integration & Deployment
*Deploy the agent and integrate with production systems*

### Task 5.1: Environment Configuration
**Owner:** DevOps Engineer
**Estimate:** 3 hours

#### Subtask 5.1.1: Configure LiveKit Cloud
**Reference:** `my-app/README.md` - Dev Setup
**Documentation:** https://docs.livekit.io/home/cloud/

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

#### Subtask 5.1.2: Set up dependencies
**Reference:** `my-app/pyproject.toml`

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

### Task 5.2: Local Testing
**Owner:** Developer
**Estimate:** 2 hours

#### Subtask 5.2.1: Test in console mode
**Reference:** `my-app/README.md` - Run the agent

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

#### Subtask 5.2.2: Test with dev server
**Reference:** LiveKit development guide

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

### Task 5.3: Production Deployment
**Owner:** Platform Engineer
**Estimate:** 4 hours

#### Subtask 5.3.1: Dockerize application
**Reference:** `my-app/Dockerfile`
**Documentation:** LiveKit deployment guide

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

#### Subtask 5.3.2: Deploy to LiveKit Cloud
**Reference:** https://docs.livekit.io/agents/ops/deployment/

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

### MVP (Week 4)
- [ ] Sarah persona responding appropriately
- [ ] Voice pipeline < 700ms latency
- [ ] 8 tools implemented (can be mocked)
- [ ] Basic qualification working
- [ ] 75%+ conversation completion rate
- [ ] All tests passing

### Production (Week 8)
- [ ] Real API integrations
- [ ] Meeting booking functional
- [ ] Qualification accuracy > 85%
- [ ] Error recovery working
- [ ] Deployed to LiveKit Cloud
- [ ] Monitoring in place

### Full Feature Set (Week 12)
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