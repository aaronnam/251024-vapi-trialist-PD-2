"""
Integration tests for calendar booking tool.

THESE TESTS CREATE REAL CALENDAR EVENTS!
Run with: uv run pytest tests/test_calendar_tool_integration.py -v -s

Requirements:
1. Valid Google service account credentials configured
2. GOOGLE_CALENDAR_ID environment variable set
3. Calendar API enabled for the service account
"""

import asyncio
import os
import sys
import pytest
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit.agents import AgentSession, inference
from src.agent import PandaDocTrialistAgent


def _llm():
    """Initialize LLM for testing."""
    from livekit.plugins import openai
    # Use the same LLM configuration as the agent
    return openai.LLM(
        model="gpt-4o-mini",
        temperature=0.1
    )


def get_real_calendar_service():
    """Get a real Google Calendar service client for verification."""
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT"):
        service_account_info = json.loads(
            os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
        )
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
    else:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        service_account_path = base_dir + os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )

    return build("calendar", "v3", credentials=credentials)


def list_recent_calendar_events(minutes_back=5):
    """List calendar events created in the last N minutes."""
    service = get_real_calendar_service()

    # Calculate time range
    now = datetime.utcnow()
    time_min = (now - timedelta(minutes=minutes_back)).isoformat() + 'Z'
    time_max = (now + timedelta(days=30)).isoformat() + 'Z'  # Look ahead 30 days

    # Get events created recently
    events_result = service.events().list(
        calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
        timeMin=time_min,
        timeMax=time_max,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Filter to events created recently (by checking creation time if available)
    recent_events = []
    for event in events:
        # Check if this is a PandaDoc meeting
        if 'PandaDoc' in event.get('summary', ''):
            recent_events.append(event)

    return recent_events


def delete_calendar_event(event_id):
    """Delete a calendar event by ID (for cleanup)."""
    service = get_real_calendar_service()
    try:
        service.events().delete(
            calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
            eventId=event_id
        ).execute()
        print(f"✅ Deleted test event: {event_id}")
    except Exception as e:
        print(f"⚠️ Could not delete event {event_id}: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_calendar_booking_creates_actual_event():
    """
    INTEGRATION TEST: Actually creates a real calendar event!

    This test:
    1. Runs the agent with a qualified user
    2. Books a real meeting on your calendar
    3. Verifies the event exists in Google Calendar
    4. Cleans up the test event afterward
    """

    print("\n" + "="*80)
    print("🚨 INTEGRATION TEST: This will create a REAL calendar event!")
    print("="*80 + "\n")

    # Track events created during test
    created_event_ids = []

    try:
        async with _llm() as llm, AgentSession(llm=llm) as session:
            agent = PandaDocTrialistAgent()

            # Set up qualified user
            agent.discovered_signals = {
                "team_size": 10,
                "monthly_volume": 150,
                "integration_needs": ["salesforce"],
                "qualification_tier": "sales_ready"
            }
            agent.user_email = "test-integration@pandadoc.com"

            await session.start(agent)

            # Step 1: Request meeting with qualification info
            print("📅 Step 1: Requesting meeting...")
            result1 = await session.run(
                user_input="I'm the head of sales at a 10-person company. We need Salesforce integration. Can we schedule a meeting to discuss enterprise features?"
            )

            # Check if agent asks for name
            response1 = result1.expect.next_event()
            print(f"Agent response: {response1}")

            # Step 2: Provide name
            print("\n📅 Step 2: Providing name...")
            result2 = await session.run(user_input="Test User Integration")

            # Agent might ask for date/time or book immediately
            first_event = result2.expect.next_event()

            if hasattr(first_event, 'is_message'):
                # Agent asks for date/time
                print("Agent asks for date/time preference")

                # Provide date/time
                print("\n📅 Step 3: Providing date/time...")
                tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%B %d")
                result3 = await session.run(
                    user_input=f"Tomorrow ({tomorrow_date}) at 3 PM Pacific would be perfect"
                )

                # Now check for function call
                event = result3.expect.next_event()
                if hasattr(event, 'is_function_call'):
                    fc = event.is_function_call(name="book_sales_meeting")
                    if fc and fc.result:
                        # Extract event ID from result
                        event_id = fc.result.get("calendar_event_id")
                        if event_id:
                            created_event_ids.append(event_id)
                            print(f"✅ Tool called! Event ID: {event_id}")
            else:
                # Agent called tool immediately
                if hasattr(first_event, 'is_function_call'):
                    fc = first_event.is_function_call(name="book_sales_meeting")
                    if fc and fc.result:
                        event_id = fc.result.get("calendar_event_id")
                        if event_id:
                            created_event_ids.append(event_id)
                            print(f"✅ Tool called immediately! Event ID: {event_id}")

        # Step 4: Verify event exists in real calendar
        print("\n📅 Step 4: Verifying event in Google Calendar...")
        await asyncio.sleep(2)  # Give API time to propagate

        recent_events = list_recent_calendar_events(minutes_back=5)

        test_event_found = False
        for event in recent_events:
            print(f"Found event: {event.get('summary')} (ID: {event.get('id')})")
            if "Test User Integration" in event.get('summary', ''):
                test_event_found = True
                print(f"✅ TEST EVENT VERIFIED IN CALENDAR!")
                print(f"   Summary: {event.get('summary')}")
                print(f"   Start: {event.get('start', {}).get('dateTime')}")
                print(f"   Meet Link: {event.get('hangoutLink', 'No link')}")

                # Track for cleanup
                if event.get('id') not in created_event_ids:
                    created_event_ids.append(event.get('id'))

        # Assert that event was created
        assert test_event_found, "Test event was not found in actual Google Calendar!"
        assert len(created_event_ids) > 0, "No calendar event ID was returned by the tool!"

        print("\n" + "="*80)
        print("🎉 SUCCESS: Real calendar event was created and verified!")
        print("="*80)

    finally:
        # Cleanup: Delete test events
        if created_event_ids:
            print("\n🧹 Cleaning up test events...")
            for event_id in created_event_ids:
                delete_calendar_event(event_id)
        else:
            print("\n⚠️ No events to clean up")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_verify_calendar_api_credentials():
    """
    INTEGRATION TEST: Verify Google Calendar API credentials are working.

    This test simply lists events to verify API access without creating anything.
    """
    print("\n" + "="*80)
    print("🔑 Testing Google Calendar API credentials...")
    print("="*80 + "\n")

    try:
        service = get_real_calendar_service()

        # Try to list calendar info
        calendar = service.calendars().get(
            calendarId=os.getenv("GOOGLE_CALENDAR_ID")
        ).execute()

        print(f"✅ Connected to calendar: {calendar.get('summary', 'Primary')}")
        print(f"   Time Zone: {calendar.get('timeZone')}")
        print(f"   Calendar ID: {os.getenv('GOOGLE_CALENDAR_ID')}")

        # List recent events to verify read access
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
            timeMin=now,
            maxResults=3,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        print(f"\n📅 Upcoming events: {len(events)} found")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"   - {event.get('summary', 'No title')} at {start}")

        print("\n✅ Google Calendar API credentials are working!")

    except Exception as e:
        pytest.fail(f"❌ Calendar API error: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_bookings_create_separate_events():
    """
    INTEGRATION TEST: Verify multiple bookings create separate calendar events.

    This test books 2 meetings and verifies both appear on the calendar.
    """
    print("\n" + "="*80)
    print("🚨 INTEGRATION TEST: Creating MULTIPLE real calendar events!")
    print("="*80 + "\n")

    created_event_ids = []

    try:
        # Book first meeting
        async with _llm() as llm, AgentSession(llm=llm) as session:
            agent = PandaDocTrialistAgent()
            agent.discovered_signals = {
                "team_size": 15,
                "qualification_tier": "sales_ready"
            }
            agent.user_email = "first-test@pandadoc.com"

            await session.start(agent)

            print("📅 Booking FIRST meeting...")
            result1 = await session.run(
                user_input="I'm Alice Johnson from a 15-person team. Book a sales meeting please."
            )

            # Extract first event ID
            event = result1.expect.next_event()
            if hasattr(event, 'is_function_call'):
                fc = event.is_function_call(name="book_sales_meeting")
                if fc and fc.result:
                    event_id = fc.result.get("calendar_event_id")
                    if event_id:
                        created_event_ids.append(event_id)
                        print(f"✅ First meeting booked: {event_id}")

        # Short delay between bookings
        await asyncio.sleep(2)

        # Book second meeting
        async with _llm() as llm, AgentSession(llm=llm) as session:
            agent = PandaDocTrialistAgent()
            agent.discovered_signals = {
                "monthly_volume": 200,
                "qualification_tier": "sales_ready"
            }
            agent.user_email = "second-test@pandadoc.com"

            await session.start(agent)

            print("\n📅 Booking SECOND meeting...")
            result2 = await session.run(
                user_input="I'm Bob Smith. We process 200 documents monthly. Schedule a call for next week."
            )

            # Extract second event ID
            event = result2.expect.next_event()
            if hasattr(event, 'is_function_call'):
                fc = event.is_function_call(name="book_sales_meeting")
                if fc and fc.result:
                    event_id = fc.result.get("calendar_event_id")
                    if event_id:
                        created_event_ids.append(event_id)
                        print(f"✅ Second meeting booked: {event_id}")

        # Verify both events exist
        print("\n📅 Verifying both events in calendar...")
        await asyncio.sleep(2)

        service = get_real_calendar_service()

        for event_id in created_event_ids:
            try:
                event = service.events().get(
                    calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
                    eventId=event_id
                ).execute()
                print(f"✅ Verified: {event.get('summary')}")
            except Exception as e:
                pytest.fail(f"❌ Could not find event {event_id}: {e}")

        assert len(created_event_ids) == 2, f"Expected 2 events, got {len(created_event_ids)}"

        print("\n🎉 SUCCESS: Multiple bookings created separate events!")

    finally:
        # Cleanup
        if created_event_ids:
            print("\n🧹 Cleaning up test events...")
            for event_id in created_event_ids:
                delete_calendar_event(event_id)


if __name__ == "__main__":
    # Run integration tests directly
    pytest.main([__file__, "-v", "-s", "-m", "integration"])