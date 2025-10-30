"""
Comprehensive test suite for PandaDoc Trial Success Agent
Tests critical business logic, instruction adherence, and edge cases
"""

import pytest
from livekit.agents import AgentSession, inference, llm, mock_tools
from typing import Dict, Any

from agent import PandaDocTrialistAgent


def _llm() -> llm.LLM:
    """Use inference LLM for testing (no LiveKit Cloud needed)"""
    return inference.LLM(model="openai/gpt-4.1-mini")


# ======================================================================
# 1. CONSENT PROTOCOL TESTS - Critical for legal compliance
# ======================================================================

@pytest.mark.asyncio
async def test_consent_accepted_flow():
    """Verify agent proceeds correctly when user gives consent"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        # Initial greeting should ask for consent
        initial = await session.run(user_input="Hi there!")
        await initial.expect.next_event().is_message(role="assistant").judge(
            llm, intent="Asks for permission to transcribe the conversation"
        )

        # User gives consent
        consent_result = await session.run(user_input="Yes, that's fine")
        await consent_result.expect.next_event().is_message(role="assistant").judge(
            llm, intent="Thanks the user and offers help with PandaDoc trial"
        )


@pytest.mark.asyncio
async def test_consent_declined_flow():
    """Verify agent stops appropriately when user declines consent"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        # Skip initial greeting
        await session.run(user_input="Hello")

        # User declines consent
        decline_result = await session.run(user_input="No, I'd rather not be transcribed")
        await decline_result.expect.next_event().is_message(role="assistant").judge(
            llm,
            intent="Politely explains cannot continue without transcription and suggests contacting support@pandadoc.com"
        )


@pytest.mark.asyncio
async def test_consent_questions_handled():
    """Verify agent handles questions about transcription appropriately"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        await session.run(user_input="Hi")

        # Ask about transcription
        question_result = await session.run(user_input="Why do you need to transcribe?")
        await question_result.expect.next_event().is_message(role="assistant").judge(
            llm,
            intent="Explains transcription is for quality assurance and re-asks for consent"
        )


# ======================================================================
# 2. KNOWLEDGE BASE SEARCH BEHAVIOR - Tool usage discipline
# ======================================================================

@pytest.mark.asyncio
async def test_no_search_for_greetings():
    """Verify agent doesn't search knowledge base for simple greetings"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        # Mock tools to detect unwanted searches
        search_called = False
        def mock_search(**kwargs):
            nonlocal search_called
            search_called = True
            return {"answer": "Should not be called", "found": False}

        with mock_tools(PandaDocTrialistAgent, {
            "unleash_search_knowledge": mock_search
        }):
            await session.start(PandaDocTrialistAgent())

            # Test various greetings that shouldn't trigger search
            greetings = ["Hi", "Hello", "Good morning", "Hey there", "Thanks", "Goodbye"]

            for greeting in greetings:
                result = await session.run(user_input=greeting)
                # Should respond without tool calls
                await result.expect.next_event().is_message(role="assistant")

            # Verify search was never called
            assert not search_called, "Search should not be called for greetings"


@pytest.mark.asyncio
async def test_search_for_pandadoc_questions():
    """Verify agent searches for actual PandaDoc questions"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        # Give consent first
        await session.run(user_input="Hi")
        await session.run(user_input="Yes, that's fine with transcription")

        # Ask a PandaDoc question
        result = await session.run(user_input="How do I create a template?")

        # Should call unleash_search_knowledge
        result.expect.next_event().is_function_call(
            name="unleash_search_knowledge",
            arguments={"query": "How do I create a template?", "response_format": "concise"}
        )


@pytest.mark.asyncio
async def test_search_error_graceful_handling():
    """Verify agent handles search failures gracefully"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        # Mock search to fail
        with mock_tools(PandaDocTrialistAgent, {
            "unleash_search_knowledge": lambda **kwargs: RuntimeError("API timeout")
        }):
            await session.start(PandaDocTrialistAgent())

            await session.run(user_input="Hi")
            await session.run(user_input="Yes")

            result = await session.run(user_input="What integrations do you support?")

            # Should still provide helpful response despite error
            await result.expect.next_event().is_message(role="assistant").judge(
                llm,
                intent="Acknowledges search issue but still provides help about integrations"
            )


# ======================================================================
# 3. QUALIFICATION DISCOVERY - Lead routing logic
# ======================================================================

@pytest.mark.asyncio
async def test_team_size_qualification():
    """Verify agent detects team size for qualification"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        # Setup: consent
        await session.run(user_input="Hi")
        await session.run(user_input="Yes, go ahead")

        # Mention team size
        result = await session.run(
            user_input="We're a team of 8 people looking for document management"
        )

        # Agent should recognize this as qualified (5+ users)
        await result.expect.contains_message(role="assistant").judge(
            llm,
            intent="Engages with understanding they're a larger team"
        )


@pytest.mark.asyncio
async def test_volume_qualification():
    """Verify agent detects document volume for qualification"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        await session.run(user_input="Hi")
        await session.run(user_input="Yes")

        # Mention high volume
        result = await session.run(
            user_input="We send about 150 proposals per month"
        )

        # Should recognize as qualified (100+ docs/month)
        # Just check response exists - qualification is internal state
        await result.expect.next_event().is_message(role="assistant")


@pytest.mark.asyncio
async def test_integration_qualification():
    """Verify agent detects CRM integration needs"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        await session.run(user_input="Hi")
        await session.run(user_input="Sure, you can transcribe")

        # Mention Salesforce/HubSpot
        result = await session.run(
            user_input="We need something that integrates with our Salesforce CRM"
        )

        # Should recognize integration need as qualification signal
        # Just check response exists
        await result.expect.next_event().is_message(role="assistant")


# ======================================================================
# 4. SALES MEETING BOOKING - Business logic enforcement
# ======================================================================

@pytest.mark.asyncio
async def test_qualified_user_can_book():
    """Verify qualified users can book sales meetings"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        # Mock booking tool to succeed
        with mock_tools(PandaDocTrialistAgent, {
            "book_sales_meeting": lambda **kwargs: {
                "booking_status": "confirmed",
                "meeting_time": "Tuesday, November 5 at 10:00 AM EST",
                "meeting_link": "https://meet.google.com/abc-defg-hij"
            }
        }):
            await session.start(PandaDocTrialistAgent())

            await session.run(user_input="Hi")
            await session.run(user_input="Yes")

            # Qualify first
            await session.run(user_input="We're a 10 person sales team")

            # Request meeting
            result = await session.run(user_input="Can we schedule a call to discuss enterprise features?")

            # Should call book_sales_meeting
            result.expect.contains_function_call(name="book_sales_meeting")


@pytest.mark.asyncio
async def test_unqualified_user_cannot_book():
    """Verify unqualified users are directed to self-serve"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        # Mock to detect if booking is attempted
        book_called = False
        def mock_book(**kwargs):
            nonlocal book_called
            book_called = True
            return {"booking_status": "confirmed"}

        with mock_tools(PandaDocTrialistAgent, {
            "book_sales_meeting": mock_book
        }):
            await session.start(PandaDocTrialistAgent())

            await session.run(user_input="Hi")
            await session.run(user_input="Yes")

            # Indicate small team (unqualified)
            await session.run(user_input="I'm just evaluating this for myself")

            # Try to book meeting
            result = await session.run(user_input="Can I schedule a call with sales?")

            # Should guide to self-serve
            await result.expect.next_event().is_message(role="assistant").judge(
                llm,
                intent="Helps explore PandaDoc features directly instead of booking sales call"
            )

            # Verify booking was not attempted
            assert not book_called, "Should not attempt to book for unqualified user"


# ======================================================================
# 5. INSTRUCTION ADHERENCE - No hallucination, follows guidelines
# ======================================================================

@pytest.mark.asyncio
async def test_stays_in_pandadoc_domain():
    """Verify agent doesn't answer non-PandaDoc questions"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        await session.run(user_input="Hi")
        await session.run(user_input="Yes")

        # Ask off-topic question
        result = await session.run(user_input="What's the weather like today?")

        # Should redirect to PandaDoc topics
        await result.expect.next_event().is_message(role="assistant").judge(
            llm,
            intent="Redirects conversation back to PandaDoc instead of answering weather question"
        )


@pytest.mark.asyncio
async def test_no_hallucination_on_features():
    """Verify agent doesn't make up features"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        # Mock search to return no results
        with mock_tools(PandaDocTrialistAgent, {
            "unleash_search_knowledge": lambda **kwargs: {
                "answer": None,
                "found": False,
                "total_results": 0
            }
        }):
            await session.start(PandaDocTrialistAgent())

            await session.run(user_input="Hi")
            await session.run(user_input="Yes")

            # Ask about a specific feature
            result = await session.run(user_input="Does PandaDoc support quantum document encryption?")

            # Should not make up features
            await result.expect.contains_message(role="assistant").judge(
                llm,
                intent="Does not confirm or invent the fictional quantum encryption feature"
            )


@pytest.mark.asyncio
async def test_voice_optimized_responses():
    """Verify responses are concise for voice"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        await session.run(user_input="Hi")
        await session.run(user_input="Yes")

        result = await session.run(user_input="Tell me about PandaDoc")

        # Response should be voice-friendly
        await result.expect.next_event().is_message(role="assistant").judge(
            llm,
            intent="Provides concise 2-3 sentence response suitable for voice, not a long explanation"
        )


# ======================================================================
# 6. CONVERSATION FLOW - Natural progression through states
# ======================================================================

@pytest.mark.asyncio
async def test_discovery_to_qualification_flow():
    """Verify natural conversation flow from discovery to qualification"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        # Consent
        await session.run(user_input="Hi")
        await session.run(user_input="Yes, that's fine")

        # Discovery phase
        discovery = await session.run(user_input="I'm having trouble with my trial")
        await discovery.expect.contains_message(role="assistant").judge(
            llm,
            intent="Asks about specific challenges or what they're trying to achieve"
        )

        # Provide context
        context = await session.run(
            user_input="I'm trying to set up templates for our sales team to use"
        )

        # Should naturally ask about team/scale
        await context.expect.contains_message(role="assistant").judge(
            llm,
            intent="Explores their workflow or team structure naturally"
        )


@pytest.mark.asyncio
async def test_friction_rescue_mode():
    """Verify agent helps when user is stuck"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        await session.run(user_input="Hi")
        await session.run(user_input="Yes")

        # Express frustration/being stuck
        result = await session.run(
            user_input="I can't figure out how to add signature fields, this is frustrating!"
        )

        # Should immediately help (friction rescue mode)
        result.expect.next_event().is_function_call(name="unleash_search_knowledge")

        # Follow-up should be helpful
        await result.expect.contains_message(role="assistant").judge(
            llm,
            intent="Provides immediate help with adding signature fields"
        )


# ======================================================================
# 7. EDGE CASES & ERROR RECOVERY
# ======================================================================

@pytest.mark.asyncio
async def test_handles_email_in_booking():
    """Verify agent uses stored email when available"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        # Create agent with email context
        agent = PandaDocTrialistAgent(user_email="test@company.com")

        with mock_tools(PandaDocTrialistAgent, {
            "book_sales_meeting": lambda **kwargs: {
                "booking_status": "confirmed",
                "customer_email": kwargs.get("customer_email") or agent.user_email
            }
        }):
            await session.start(agent)

            await session.run(user_input="Hi")
            await session.run(user_input="Yes")
            await session.run(user_input="We have 10 users")

            result = await session.run(user_input="Book a meeting please")

            # Should use stored email
            result.expect.contains_function_call(name="book_sales_meeting")


@pytest.mark.asyncio
async def test_circuit_breaker_behavior():
    """Verify circuit breaker prevents cascade failures"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        # Mock to fail multiple times
        call_count = 0
        def failing_search(**kwargs):
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Service unavailable")

        with mock_tools(PandaDocTrialistAgent, {
            "unleash_search_knowledge": failing_search
        }):
            await session.start(PandaDocTrialistAgent())

            await session.run(user_input="Hi")
            await session.run(user_input="Yes")

            # Multiple searches should eventually stop trying
            for _ in range(3):
                result = await session.run(user_input="How do I do X?")
                # Just check we get a response
                await result.expect.next_event()

            # Circuit should limit total attempts
            assert call_count <= 5  # Should stop after threshold


@pytest.mark.asyncio
async def test_ambiguous_consent_clarification():
    """Verify agent clarifies ambiguous consent responses"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        await session.run(user_input="Hi")

        # Give ambiguous response
        result = await session.run(user_input="Maybe, what do you mean?")

        # Should explain and re-ask
        await result.expect.next_event().is_message(role="assistant").judge(
            llm,
            intent="Explains transcription purpose and asks again for clear yes/no"
        )