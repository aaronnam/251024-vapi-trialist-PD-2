"""
Focused test suite for calendar booking tool invocation.
These tests specifically verify that the book_sales_meeting tool is ACTUALLY CALLED
when qualified users request meetings.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from livekit.agents import AgentSession, inference, llm
from typing import List, Dict, Any

from agent import PandaDocTrialistAgent


def _llm() -> llm.LLM:
    """Use inference LLM for testing"""
    return inference.LLM(model="openai/gpt-4o-mini")


class ToolCallTracker:
    """Track tool calls made during agent execution"""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self.book_sales_meeting_called = False
        self.last_booking_params = {}

    def track_call(self, tool_name: str, params: Dict[str, Any]):
        """Record a tool call"""
        self.calls.append({
            "tool": tool_name,
            "params": params,
            "timestamp": datetime.now().isoformat()
        })

        if tool_name == "book_sales_meeting":
            self.book_sales_meeting_called = True
            self.last_booking_params = params

    def reset(self):
        """Reset tracker for next test"""
        self.calls.clear()
        self.book_sales_meeting_called = False
        self.last_booking_params = {}


# Global tracker instance
tool_tracker = ToolCallTracker()


@pytest.mark.asyncio
async def test_qualified_team_size_books_meeting():
    """
    CRITICAL TEST: Verify tool is called for team size >= 5
    Test prompt: Explicit meeting request from qualified team
    """
    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up QUALIFIED user (team size >= 5)
        agent.discovered_signals = {
            "team_size": 8,
            "monthly_volume": 50,
            "integration_needs": [],
            "qualification_tier": "sales_ready"
        }
        agent.user_email = "aaron.nam@pandadoc.com"

        # Mock the Google Calendar service
        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_event = {
                'id': 'test_event_team_size',
                'hangoutLink': 'https://meet.google.com/abc-defg-hij',
                'htmlLink': 'https://calendar.google.com/event?eid=test123'
            }

            # Track when the calendar API is actually called
            calendar_api_called = False

            def track_insert(*args, **kwargs):
                nonlocal calendar_api_called
                calendar_api_called = True
                mock_result = MagicMock()
                mock_result.execute = Mock(return_value=mock_event)
                return mock_result

            mock_events = MagicMock()
            mock_events.insert = track_insert
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)

            # EXPLICIT meeting request that MUST trigger tool
            test_prompt = "We have 8 sales reps using PandaDoc. Let's schedule a call to discuss enterprise features."

            result = await session.run(user_input=test_prompt)

            # Method 1: Check for function call event
            tool_was_called = False
            try:
                # Expect the tool to be called
                event = result.expect.next_event()
                if hasattr(event, 'is_function_call'):
                    fc_event = event.is_function_call(name="book_sales_meeting")
                    if fc_event:
                        tool_was_called = True
                        print(f"✅ Tool call detected: book_sales_meeting")
            except Exception as e:
                print(f"⚠️ No function call event found: {e}")

            # Method 2: Check if calendar API was invoked
            assert calendar_api_called, "Calendar API was not called - tool did not execute!"

            # Method 3: Verify the response mentions booking
            await result.expect.contains_message(role="assistant").judge(
                llm,
                intent="Confirms that a meeting has been scheduled or is being scheduled"
            )

            print(f"✅ TEST PASSED: Tool was called for qualified user (team_size=8)")


@pytest.mark.asyncio
async def test_qualified_volume_books_meeting():
    """
    CRITICAL TEST: Verify tool is called for volume >= 100
    Test prompt: High volume user requesting meeting
    """
    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up QUALIFIED user (volume >= 100)
        agent.discovered_signals = {
            "team_size": 3,
            "monthly_volume": 200,
            "integration_needs": [],
            "qualification_tier": "sales_ready"
        }
        agent.user_email = "aaron.nam@pandadoc.com"

        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_event = {
                'id': 'test_event_volume',
                'hangoutLink': 'https://meet.google.com/volume-test',
                'htmlLink': 'https://calendar.google.com/event?eid=volumetest'
            }

            calendar_api_called = False

            def track_insert(*args, **kwargs):
                nonlocal calendar_api_called
                calendar_api_called = True
                mock_result = MagicMock()
                mock_result.execute = Mock(return_value=mock_event)
                return mock_result

            mock_events = MagicMock()
            mock_events.insert = track_insert
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)

            test_prompt = "We process over 200 contracts monthly. I'd like to schedule a meeting about enterprise pricing."

            result = await session.run(user_input=test_prompt)

            # Check for function call
            event = result.expect.next_event()
            if hasattr(event, 'is_function_call'):
                event.is_function_call(name="book_sales_meeting")
                print(f"✅ Tool call detected for high volume user")

            assert calendar_api_called, "Tool was not invoked for qualified high-volume user!"

            print(f"✅ TEST PASSED: Tool was called for high volume (200 docs/month)")


@pytest.mark.asyncio
async def test_qualified_salesforce_books_meeting():
    """
    CRITICAL TEST: Verify tool is called for Salesforce integration needs
    Test prompt: Salesforce user requesting meeting
    """
    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up QUALIFIED user (Salesforce integration)
        agent.discovered_signals = {
            "team_size": 3,
            "monthly_volume": 30,
            "integration_needs": ["salesforce"],
            "qualification_tier": "sales_ready"
        }
        agent.user_email = "aaron.nam@pandadoc.com"

        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_event = {
                'id': 'test_event_salesforce',
                'hangoutLink': 'https://meet.google.com/sf-test',
                'htmlLink': 'https://calendar.google.com/event?eid=sftest'
            }

            calendar_api_called = False
            booking_params = {}

            def track_insert(*args, **kwargs):
                nonlocal calendar_api_called, booking_params
                calendar_api_called = True
                booking_params = kwargs.get('body', {})
                mock_result = MagicMock()
                mock_result.execute = Mock(return_value=mock_event)
                return mock_result

            mock_events = MagicMock()
            mock_events.insert = track_insert
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)

            test_prompt = "We use Salesforce CRM. Can we book a call to discuss the integration?"

            result = await session.run(user_input=test_prompt)

            # Verify tool was called
            event = result.expect.next_event()
            if hasattr(event, 'is_function_call'):
                event.is_function_call(name="book_sales_meeting")

            assert calendar_api_called, "Tool not called for Salesforce integration request!"

            # Verify Salesforce was included in meeting description
            if booking_params:
                description = booking_params.get('description', '')
                assert 'salesforce' in description.lower(), "Salesforce not mentioned in booking!"

            print(f"✅ TEST PASSED: Tool called for Salesforce integration need")


@pytest.mark.asyncio
async def test_qualified_api_needs_books_meeting():
    """
    CRITICAL TEST: Verify tool is called for API/embedded integration needs
    Test prompt: API integration request
    """
    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up QUALIFIED user (API integration)
        agent.discovered_signals = {
            "team_size": 2,
            "monthly_volume": 50,
            "integration_needs": ["api"],
            "qualification_tier": "sales_ready"
        }
        agent.user_email = "aaron.nam@pandadoc.com"

        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_event = {
                'id': 'test_event_api',
                'hangoutLink': 'https://meet.google.com/api-test',
                'htmlLink': 'https://calendar.google.com/event?eid=apitest'
            }

            calendar_api_called = False

            def track_insert(*args, **kwargs):
                nonlocal calendar_api_called
                calendar_api_called = True
                mock_result = MagicMock()
                mock_result.execute = Mock(return_value=mock_event)
                return mock_result

            mock_events = MagicMock()
            mock_events.insert = track_insert
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)

            test_prompt = "We need API access for programmatic document generation. Schedule a technical discussion?"

            result = await session.run(user_input=test_prompt)

            event = result.expect.next_event()
            if hasattr(event, 'is_function_call'):
                event.is_function_call(name="book_sales_meeting")

            assert calendar_api_called, "Tool not called for API integration request!"

            print(f"✅ TEST PASSED: Tool called for API integration needs")


@pytest.mark.asyncio
async def test_qualified_with_datetime_preferences():
    """
    CRITICAL TEST: Verify tool is called with correct date/time parameters
    Test prompt: Meeting request with specific time preference
    """
    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up QUALIFIED user
        agent.discovered_signals = {
            "team_size": 10,
            "monthly_volume": 150,
            "integration_needs": ["hubspot"],
            "qualification_tier": "sales_ready"
        }
        agent.user_email = "aaron.nam@pandadoc.com"

        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_event = {
                'id': 'test_event_datetime',
                'hangoutLink': 'https://meet.google.com/datetime-test',
                'htmlLink': 'https://calendar.google.com/event?eid=datetimetest'
            }

            calendar_api_called = False
            captured_params = {}

            def track_insert(*args, **kwargs):
                nonlocal calendar_api_called, captured_params
                calendar_api_called = True
                captured_params = kwargs.get('body', {})
                mock_result = MagicMock()
                mock_result.execute = Mock(return_value=mock_event)
                return mock_result

            mock_events = MagicMock()
            mock_events.insert = track_insert
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)

            test_prompt = "Our 10-person team uses HubSpot. Can we book a meeting tomorrow at 2pm?"

            result = await session.run(user_input=test_prompt)

            # Check tool was called
            event = result.expect.next_event()
            if hasattr(event, 'is_function_call'):
                fc = event.is_function_call(name="book_sales_meeting")
                # Try to extract parameters if possible
                if hasattr(fc, 'args') or hasattr(fc, 'parameters'):
                    params = getattr(fc, 'args', getattr(fc, 'parameters', {}))
                    print(f"Tool parameters: {params}")

            assert calendar_api_called, "Tool not called despite qualified user and clear meeting request!"

            # Verify time preference was captured (even if parsing varies)
            if captured_params:
                start_time = captured_params.get('start', {}).get('dateTime', '')
                assert start_time, "No meeting time was set!"
                print(f"Meeting scheduled for: {start_time}")

            print(f"✅ TEST PASSED: Tool called with datetime preferences")


@pytest.mark.asyncio
async def test_multiple_qualification_signals():
    """
    CRITICAL TEST: Verify tool is called when multiple qualification signals present
    Test prompt: User with team size + Salesforce + high urgency
    """
    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up HIGHLY QUALIFIED user (multiple signals)
        agent.discovered_signals = {
            "team_size": 15,
            "monthly_volume": 500,
            "integration_needs": ["salesforce", "api", "hubspot"],
            "urgency": "high",
            "industry": "technology",
            "qualification_tier": "sales_ready"
        }
        agent.user_email = "aaron.nam@pandadoc.com"

        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_event = {
                'id': 'test_event_multiple',
                'hangoutLink': 'https://meet.google.com/multi-test',
                'htmlLink': 'https://calendar.google.com/event?eid=multitest'
            }

            calendar_api_called = False

            def track_insert(*args, **kwargs):
                nonlocal calendar_api_called
                calendar_api_called = True
                mock_result = MagicMock()
                mock_result.execute = Mock(return_value=mock_event)
                return mock_result

            mock_events = MagicMock()
            mock_events.insert = track_insert
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)

            test_prompt = "Our 15-person tech team needs Salesforce integration urgently. Book a call ASAP."

            result = await session.run(user_input=test_prompt)

            event = result.expect.next_event()
            if hasattr(event, 'is_function_call'):
                event.is_function_call(name="book_sales_meeting")

            assert calendar_api_called, "Tool not called for highly qualified user with urgent need!"

            print(f"✅ TEST PASSED: Tool called for multi-signal qualified user")


@pytest.mark.asyncio
async def test_booking_flow_with_name_collection():
    """
    CRITICAL TEST: Verify agent collects name and actually books meeting (not just claims to)
    This test recreates the exact failure scenario from the user's conversation where
    the agent said "I've scheduled your meeting" without actually calling the tool.
    """
    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()
        agent.user_email = "aaron.nam@pandadoc.com"

        # Start with qualified signals already discovered
        # (simulating a conversation where user mentioned team size)
        agent.discovered_signals = {
            "team_size": 10,
            "monthly_volume": 50,
            "integration_needs": [],
            "qualification_tier": "sales_ready"
        }

        # Mock the Google Calendar service
        with patch.object(agent, '_get_calendar_service') as mock_service:
            mock_event = {
                'id': 'test_event_name_collection',
                'hangoutLink': 'https://meet.google.com/name-test',
                'htmlLink': 'https://calendar.google.com/event?eid=nametest'
            }

            calendar_api_called = False
            captured_customer_name = None

            def track_insert(*args, **kwargs):
                nonlocal calendar_api_called, captured_customer_name
                calendar_api_called = True
                event_body = kwargs.get('body', {})
                # Extract customer name from event summary
                summary = event_body.get('summary', '')
                if 'PandaDoc Sales Consultation - ' in summary:
                    captured_customer_name = summary.split(' - ')[1]
                mock_result = MagicMock()
                mock_result.execute = Mock(return_value=mock_event)
                return mock_result

            mock_events = MagicMock()
            mock_events.insert = track_insert
            mock_service.return_value.events = Mock(return_value=mock_events)

            await session.start(agent)

            # Step 1: User mentions they're qualified (team size) and requests meeting
            result1 = await session.run(
                user_input="We have a 10-person team using PandaDoc. Can I book a meeting with a sales representative to discuss enterprise features?"
            )

            # Agent should ask for name (qualification is implied by asking for name)
            await result1.expect.contains_message(role="assistant").judge(
                llm,
                intent="Asks for the user's name to schedule the meeting"
            )

            # Step 2: User provides name
            result2 = await session.run(user_input="Aaron Nam")

            # Agent may either book immediately or ask for date/time first
            # Check if it's asking for date/time or calling the tool
            first_event = result2.expect.next_event()

            if hasattr(first_event, 'is_message'):
                # Agent asked for date/time, provide it
                await first_event.is_message(role="assistant").judge(
                    llm,
                    intent="Asks for preferred date and time"
                )

                # Step 3: User provides date/time
                result3 = await session.run(user_input="November 3rd at 5 PM Pacific")

                # NOW the tool must be called
                event = result3.expect.next_event()
                event.is_function_call(name="book_sales_meeting")
                print(f"✅ Tool called after collecting date/time")

                # Verify calendar API was invoked
                assert calendar_api_called, "CRITICAL: Agent claimed to book meeting but never called the tool!"

                # Verify customer name
                assert captured_customer_name is not None
                assert "Aaron Nam" in captured_customer_name

                # Skip function output event
                result3.expect.next_event()

                # Confirm booking
                await result3.expect.next_event().is_message(role="assistant").judge(
                    llm,
                    intent="Confirms the meeting is scheduled with date, time, and link"
                )
            else:
                # Agent called tool immediately
                first_event.is_function_call(name="book_sales_meeting")
                print(f"✅ Tool called immediately after getting name")

                assert calendar_api_called, "CRITICAL: Agent claimed to book meeting but never called the tool!"
                assert captured_customer_name is not None
                assert "Aaron Nam" in captured_customer_name

                # Skip function output event
                result2.expect.next_event()

                # Confirm booking
                await result2.expect.next_event().is_message(role="assistant").judge(
                    llm,
                    intent="Confirms the meeting is scheduled with date, time, and link"
                )

            print(f"✅ TEST PASSED: Agent collected name, called tool, and confirmed booking correctly")
            print(f"✅ Customer name captured: {captured_customer_name}")




# Test runner with detailed output
async def run_all_tests():
    """Run all critical tests and report results"""
    tests = [
        test_qualified_team_size_books_meeting,
        test_qualified_volume_books_meeting,
        test_qualified_salesforce_books_meeting,
        test_qualified_api_needs_books_meeting,
        test_qualified_with_datetime_preferences,
        test_multiple_qualification_signals,
        test_booking_flow_with_name_collection,
    ]

    results = []
    for test in tests:
        test_name = test.__name__
        try:
            await test()
            results.append((test_name, "PASSED ✅"))
            print(f"\n✅ {test_name}: PASSED")
        except AssertionError as e:
            results.append((test_name, f"FAILED ❌: {e}"))
            print(f"\n❌ {test_name}: FAILED - {e}")
        except Exception as e:
            results.append((test_name, f"ERROR 🔥: {e}"))
            print(f"\n🔥 {test_name}: ERROR - {e}")

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, status in results:
        print(f"{name}: {status}")

    passed = sum(1 for _, s in results if "PASSED" in s)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    # Run the focused test suite
    print("Running Calendar Tool Invocation Tests...")
    print("="*60)
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)