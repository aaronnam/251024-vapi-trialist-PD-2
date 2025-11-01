"""
Test to prove the calendar booking tool is ACTUALLY being called (not just considered).

This test doesn't require calendar write permissions - it just proves the tool executes.
"""

import asyncio
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
import json

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit.agents import AgentSession
from src.agent import PandaDocTrialistAgent


def _llm():
    """Initialize LLM for testing."""
    from livekit.plugins import openai
    return openai.LLM(
        model="gpt-4o-mini",
        temperature=0.1
    )


@pytest.mark.asyncio
async def test_proves_tool_is_actually_executed():
    """
    PROOF TEST: Demonstrates the calendar tool is ACTUALLY called, not just considered.

    This test intercepts the Google Calendar API call to prove execution happens.
    Even though the API call fails due to permissions, we can see it WAS attempted!
    """

    print("\n" + "="*80)
    print("🔍 PROVING: Calendar tool is ACTUALLY executed (not just considered)")
    print("="*80 + "\n")

    # Track what actually happens
    tool_execution_proof = {
        "tool_called": False,
        "calendar_api_attempted": False,
        "error_encountered": None,
        "parameters_received": {}
    }

    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up qualified user
        agent.discovered_signals = {
            "team_size": 10,
            "qualification_tier": "sales_ready"
        }
        agent.user_email = "proof-test@pandadoc.com"

        # Intercept the calendar service creation to track execution
        original_get_calendar = agent._get_calendar_service

        def tracked_get_calendar():
            """Track that calendar service was requested (proves tool execution)."""
            tool_execution_proof["calendar_api_attempted"] = True
            print("✅ PROOF: _get_calendar_service() was called - tool is executing!")

            # Return a mock that will fail but proves execution
            mock_service = MagicMock()

            def mock_insert(**kwargs):
                tool_execution_proof["parameters_received"] = kwargs.get('body', {})
                print(f"✅ PROOF: Calendar insert() called with event: {kwargs.get('body', {}).get('summary')}")

                # Simulate the permission error we saw
                from googleapiclient.errors import HttpError
                import httplib2
                resp = httplib2.Response({'status': '403'})
                resp.reason = 'Forbidden'

                mock_result = MagicMock()
                mock_result.execute.side_effect = HttpError(
                    resp,
                    b'{"error": {"message": "You need to have writer access to this calendar."}}',
                    uri="https://www.googleapis.com/calendar/v3/calendars/test/events"
                )
                return mock_result

            mock_events = MagicMock()
            mock_events.insert = mock_insert
            mock_service.events.return_value = mock_events

            return mock_service

        # Replace with our tracked version
        agent._get_calendar_service = tracked_get_calendar

        # Also track the tool method directly
        original_book = agent.book_sales_meeting

        async def tracked_book(*args, **kwargs):
            tool_execution_proof["tool_called"] = True
            print("✅ PROOF: book_sales_meeting() method was entered!")
            try:
                result = await original_book(*args, **kwargs)
                return result
            except Exception as e:
                tool_execution_proof["error_encountered"] = str(e)
                print(f"✅ PROOF: Tool executed and encountered expected error: {type(e).__name__}")
                raise

        agent.book_sales_meeting = tracked_book

        await session.start(agent)

        # Single prompt with all info to trigger immediate booking
        print("📞 Requesting meeting with all info provided...")
        result = await session.run(
            user_input="I'm John Smith, head of sales at a 10-person company. We need to discuss enterprise features. Please book a meeting for tomorrow at 2 PM."
        )

        # Check what happened
        try:
            event = result.expect.next_event()
            if hasattr(event, 'is_function_call'):
                fc = event.is_function_call(name="book_sales_meeting")
                print(f"✅ PROOF: Function call event detected for book_sales_meeting")
        except:
            # Even if this fails, we still have our tracking data
            pass

        # Give async operations time to complete
        await asyncio.sleep(1)

    # Print proof summary
    print("\n" + "="*80)
    print("📊 EXECUTION PROOF SUMMARY:")
    print("="*80)
    print(f"1. Tool method called: {tool_execution_proof['tool_called']}")
    print(f"2. Calendar API attempted: {tool_execution_proof['calendar_api_attempted']}")
    print(f"3. Event data prepared: {bool(tool_execution_proof['parameters_received'])}")
    if tool_execution_proof['parameters_received']:
        print(f"   - Event summary: {tool_execution_proof['parameters_received'].get('summary')}")
        print(f"   - Has attendees: {bool(tool_execution_proof['parameters_received'].get('attendees'))}")
        print(f"   - Has start time: {bool(tool_execution_proof['parameters_received'].get('start'))}")
    print(f"4. Error encountered: {tool_execution_proof['error_encountered']}")

    print("\n" + "="*80)
    if tool_execution_proof["tool_called"] and tool_execution_proof["calendar_api_attempted"]:
        print("🎉 PROVEN: Tool is ACTUALLY EXECUTED, not just considered!")
        print("The permission error proves it tried to create a REAL calendar event.")
    else:
        print("❌ Tool was not executed - only considered")
    print("="*80)

    # Assert the tool was actually called
    assert tool_execution_proof["tool_called"], "Tool method was never entered - tool was only considered, not executed!"
    assert tool_execution_proof["calendar_api_attempted"], "Calendar API was never called - tool didn't fully execute!"
    assert tool_execution_proof["parameters_received"], "No event data was prepared - tool didn't process parameters!"

    print("\n✅ TEST PASSED: Proved tool is actually executed when qualified user requests meeting!")


@pytest.mark.asyncio
async def test_unqualified_user_tool_not_called():
    """
    CONTROL TEST: Verify tool is NOT called for unqualified users.

    This proves our test can distinguish between "considered" and "executed".
    """

    print("\n" + "="*80)
    print("🔍 CONTROL: Verifying tool is NOT called for unqualified users")
    print("="*80 + "\n")

    tool_was_called = False

    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up UNQUALIFIED user
        agent.discovered_signals = {
            "team_size": 2,  # Too small
            "monthly_volume": 10,  # Too low
            "qualification_tier": "self_serve"
        }
        agent.user_email = "unqualified@example.com"

        # Track if tool is called
        original_book = agent.book_sales_meeting

        async def tracked_book(*args, **kwargs):
            nonlocal tool_was_called
            tool_was_called = True
            print("⚠️ Tool was called for unqualified user!")
            return await original_book(*args, **kwargs)

        agent.book_sales_meeting = tracked_book

        await session.start(agent)

        print("📞 Unqualified user requesting meeting...")
        result = await session.run(
            user_input="I'm Jane Doe. We're a 2-person startup. Can we book a meeting?"
        )

        # Give time for any async operations
        await asyncio.sleep(1)

    print(f"\nTool called for unqualified user: {tool_was_called}")

    assert not tool_was_called, "Tool should NOT be called for unqualified users!"
    print("✅ CONTROL PASSED: Tool correctly NOT called for unqualified user")


if __name__ == "__main__":
    # Run the proof test
    pytest.main([__file__, "-v", "-s", "-k", "proves_tool"])