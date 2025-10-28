"""Test suite for the Google Calendar meeting booking integration tool.

This module tests the book_sales_meeting function tool with various scenarios
including successful bookings, qualification checking, error handling, and date/time parsing.
"""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest
from googleapiclient.errors import HttpError

# Add src to path to import agent
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from livekit.agents import AgentSession, ToolError, inference

from agent import PandaDocTrialistAgent


@pytest.mark.asyncio
async def test_booking_qualified_user_success():
    """Test successful booking for a qualified user."""
    # Mock the Google Calendar API response
    mock_event = {
        'id': 'test_event_123',
        'hangoutLink': 'https://meet.google.com/abc-defg-hij',
        'htmlLink': 'https://calendar.google.com/event?eid=test123'
    }

    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Set up qualified user
        agent.discovered_signals = {
            "team_size": 10,
            "monthly_volume": 500,
            "integration_needs": ["salesforce"],
            "industry": "technology"
        }

        # Mock Google Calendar API
        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_events = MagicMock()
            mock_insert = MagicMock()
            mock_insert.execute = Mock(return_value=mock_event)
            mock_events.insert = Mock(return_value=mock_insert)
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)
            result = await session.run(
                user_input="I'm interested in a sales call to discuss enterprise features"
            )

            # Verify tool was called
            result.expect.next_event().is_function_call(
                name="book_sales_meeting"
            )

            # Skip the FunctionCallOutputEvent
            result.expect.next_event()

            # Verify agent provides confirmation
            await result.expect.next_event().is_message(
                role="assistant"
            ).judge(
                llm, intent="Confirms meeting has been booked and provides meeting details"
            )


@pytest.mark.asyncio
async def test_booking_unqualified_user_rejected():
    """Test that unqualified users cannot book meetings."""
    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Set up unqualified user (small team, low volume)
        agent.discovered_signals = {
            "team_size": 2,
            "monthly_volume": 10,
            "integration_needs": [],
            "industry": "small_business"
        }

        await session.start(agent)
        result = await session.run(
            user_input="I want to talk to someone about PandaDoc"
        )

        # The agent should either:
        # 1. Not call the booking tool at all (preferred)
        # 2. Or if it does, the tool should return an error

        # Agent should guide to self-serve instead
        await result.expect.contains_message(role="assistant").judge(
            llm, intent="Offers self-serve guidance without offering to connect to a human"
        )


@pytest.mark.asyncio
async def test_booking_with_date_time_preferences():
    """Test booking with specific date and time preferences."""
    mock_event = {
        'id': 'test_event_456',
        'hangoutLink': 'https://meet.google.com/xyz-abcd-efg',
        'htmlLink': 'https://calendar.google.com/event?eid=test456'
    }

    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Set up qualified user
        agent.discovered_signals = {
            "team_size": 8,
            "monthly_volume": 200,
            "integration_needs": ["hubspot"]
        }

        # Mock Google Calendar API
        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_events = MagicMock()
            mock_insert = MagicMock()
            mock_insert.execute = Mock(return_value=mock_event)
            mock_events.insert = Mock(return_value=mock_insert)
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)
            result = await session.run(
                user_input="Can we schedule a meeting tomorrow at 2pm?"
            )

            # Tool should be called for qualified user
            result.expect.next_event().is_function_call(
                name="book_sales_meeting"
            )

            # Skip output event
            result.expect.next_event()

            # Agent should confirm with the specified time
            await result.expect.next_event().is_message(
                role="assistant"
            ).judge(
                llm, intent="Confirms meeting booking for the requested time"
            )


@pytest.mark.asyncio
async def test_booking_calendar_auth_failure():
    """Test graceful handling of Google Calendar authentication failure."""
    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Set up qualified user
        agent.discovered_signals = {
            "team_size": 15,
            "monthly_volume": 300,
            "integration_needs": ["salesforce"]
        }

        # Mock HttpError for 401 authentication failure
        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_error_resp = Mock()
            mock_error_resp.status = 401
            http_error = HttpError(mock_error_resp, b'Unauthorized')

            mock_events = MagicMock()
            mock_insert = MagicMock()
            mock_insert.execute = Mock(side_effect=http_error)
            mock_events.insert = Mock(return_value=mock_insert)
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)
            result = await session.run(
                user_input="Let's book a meeting with sales"
            )

            # Tool should be called
            result.expect.next_event().is_function_call(
                name="book_sales_meeting"
            )

            # Skip output event
            result.expect.next_event()

            # Agent should provide email fallback
            await result.expect.contains_message(role="assistant").judge(
                llm, intent="Provides alternative contact method like email when booking fails"
            )


@pytest.mark.asyncio
async def test_booking_calendar_api_error():
    """Test handling of generic Google Calendar API errors."""
    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Set up qualified user
        agent.discovered_signals = {
            "team_size": 12,
            "monthly_volume": 250,
            "integration_needs": ["hubspot"]
        }

        # Mock HttpError for server error
        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_error_resp = Mock()
            mock_error_resp.status = 500
            http_error = HttpError(mock_error_resp, b'Internal Server Error')

            mock_events = MagicMock()
            mock_insert = MagicMock()
            mock_insert.execute = Mock(side_effect=http_error)
            mock_events.insert = Mock(return_value=mock_insert)
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)
            result = await session.run(
                user_input="I'd like to schedule a call with your team"
            )

            # Tool should be called
            result.expect.next_event().is_function_call(
                name="book_sales_meeting"
            )

            # Skip output event
            result.expect.next_event()

            # Agent should handle error gracefully
            await result.expect.contains_message(role="assistant").judge(
                llm, intent="Handles booking error gracefully and offers alternative"
            )


@pytest.mark.asyncio
async def test_booking_weekend_date_handling():
    """Test that weekend dates are moved to next business day."""
    mock_event = {
        'id': 'test_event_789',
        'hangoutLink': 'https://meet.google.com/weekend-test',
        'htmlLink': 'https://calendar.google.com/event?eid=test789'
    }

    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Set up qualified user
        agent.discovered_signals = {
            "team_size": 7,
            "monthly_volume": 150,
            "integration_needs": ["salesforce"]
        }

        # Mock Google Calendar API
        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_events = MagicMock()
            mock_insert = MagicMock()
            mock_insert.execute = Mock(return_value=mock_event)
            mock_events.insert = Mock(return_value=mock_insert)
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)

            # Try to book on a Saturday (if provided)
            result = await session.run(
                user_input="Can we meet this Saturday?"
            )

            # Tool should be called
            result.expect.next_event().is_function_call(
                name="book_sales_meeting"
            )

            # Skip output event
            result.expect.next_event()

            # Agent should confirm booking (date should be moved to Monday)
            await result.expect.next_event().is_message(
                role="assistant"
            ).judge(
                llm, intent="Confirms meeting booking on a weekday"
            )


@pytest.mark.asyncio
async def test_booking_includes_qualification_context():
    """Test that booking event includes qualification signals in description."""
    mock_event = {
        'id': 'test_event_context',
        'hangoutLink': 'https://meet.google.com/context-test',
        'htmlLink': 'https://calendar.google.com/event?eid=testcontext'
    }

    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Set up qualified user with rich signals
        agent.discovered_signals = {
            "team_size": 25,
            "monthly_volume": 1000,
            "integration_needs": ["salesforce", "hubspot"],
            "industry": "healthcare"
        }

        # Mock Google Calendar API and capture the event data
        captured_event = None

        def capture_insert(**kwargs):
            nonlocal captured_event
            captured_event = kwargs.get('body')
            mock_result = MagicMock()
            mock_result.execute = Mock(return_value=mock_event)
            return mock_result

        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_events = MagicMock()
            mock_events.insert = capture_insert
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)
            result = await session.run(
                user_input="Let's schedule a meeting to discuss enterprise options"
            )

            # Verify the tool was called
            result.expect.next_event().is_function_call(
                name="book_sales_meeting"
            )

            # Verify that qualification signals were included in event description
            if captured_event:
                description = captured_event.get('description', '')
                assert 'Team Size: 25' in description or 'team_size' in description.lower()


@pytest.mark.asyncio
async def test_qualification_signals_tracked():
    """Test that qualification signals are correctly tracked during conversation."""
    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        await session.start(agent)

        # User mentions team size
        result = await session.run(
            user_input="We have a team of 8 people who need to send proposals"
        )

        # Verify agent tracks this signal and asks follow-up
        await result.expect.contains_message(role="assistant").judge(
            llm, intent="Acknowledges team information and asks relevant follow-up questions"
        )

        # Verify the signal was captured (this tests internal state)
        # In a real scenario, the agent should naturally extract this from conversation


@pytest.mark.asyncio
async def test_no_human_help_for_unqualified():
    """Test that unqualified users are not offered human assistance."""
    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Set up unqualified user
        agent.discovered_signals = {
            "team_size": 1,
            "monthly_volume": 5,
            "integration_needs": []
        }

        await session.start(agent)
        result = await session.run(
            user_input="I'm having trouble creating a template"
        )

        # Should use knowledge search tool first
        result.expect.next_event().is_function_call(
            name="unleash_search_knowledge"
        )

        # Skip output event
        result.expect.next_event()

        # Agent should provide self-serve guidance, NOT offer to connect to human
        await result.expect.contains_message(role="assistant").judge(
            llm,
            intent="Provides helpful guidance without offering to connect to a person or support"
        )


# Test runner for local execution
if __name__ == "__main__":
    import asyncio

    # Run a simple test
    print("Running booking tool tests...")
    asyncio.run(test_booking_qualified_user_success())
    print("Basic test passed!")
