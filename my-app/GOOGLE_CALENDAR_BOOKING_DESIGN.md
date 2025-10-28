# Google Calendar Meeting Booking Integration - Technical Design

> **📌 UPDATE: Google Calendar API is already configured and ready to use. Service account credentials and calendar ID are set up in `.env.local`. Skip directly to Phase 2 (Dependencies) for implementation.**

## Executive Summary
Add a simple, conditional meeting booking capability to the PandaDoc voice agent that **only** books sales meetings for qualified trial users. This design prioritizes simplicity and clear business logic over complex availability checking.

## Core Requirements
1. **Book meetings directly** without availability checking
2. **Only offer to qualified leads** (Tier 1: Sales-Ready)
3. **Never offer human assistance** in other circumstances
4. **Use Google Calendar API** for direct event creation

## Design Philosophy
- **Simplicity First**: Book immediately, no complex availability logic
- **Qualification-Driven**: Tool only activates for qualified leads
- **Clear Boundaries**: No human assistance fallback for unqualified users
- **Voice-Optimized**: Fast execution with immediate confirmation

## Technical Architecture

### 1. Authentication Setup ✅ ALREADY COMPLETED

```bash
# Environment variables (ALREADY CONFIGURED in .env.local)
GOOGLE_SERVICE_ACCOUNT_JSON=/.secrets/pandadoc-voice-agent-03fa518aa3d0.json  # Path relative to my-app/
GOOGLE_CALENDAR_ID=c_f81fc95409534f4983a4bbb949b1ea35989199a5ae73d8383a9e022dea44b816@group.calendar.google.com
```

**Service Account Setup: ✅ COMPLETE**
- Service account JSON key already stored in `/.secrets/`
- Calendar ID configured and ready
- No additional setup needed for authentication

### 2. Tool Implementation

```python
@function_tool()
async def book_sales_meeting(
    self,
    context: RunContext,
    customer_name: str,
    customer_email: str,
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None
) -> Dict[str, Any]:
    """Book a meeting with PandaDoc sales representative.

    CRITICAL: Only use this tool when:
    1. User has been qualified as Tier 1 (sales-ready)
    2. User explicitly agrees to book a meeting

    DO NOT use this tool for:
    - General support questions
    - Unqualified users
    - Any other type of assistance

    Args:
        customer_name: Full name of the customer
        customer_email: Email address for calendar invite
        preferred_date: Optional date preference (e.g., "tomorrow", "next Tuesday")
        preferred_time: Optional time preference (e.g., "2pm", "morning")

    Returns:
        Dict with booking_status, meeting_link, and meeting_time
    """

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
            'summary': f'PandaDoc Sales Consultation - {customer_name}',
            'description': (
                f"Sales consultation for qualified trial user\n\n"
                f"Customer: {customer_name}\n"
                f"Email: {customer_email}\n"
                f"Qualification Signals:\n"
                f"- Team Size: {self.discovered_signals.get('team_size', 'Unknown')}\n"
                f"- Monthly Volume: {self.discovered_signals.get('monthly_volume', 'Unknown')}\n"
                f"- Integration Needs: {', '.join(self.discovered_signals.get('integration_needs', []))}\n"
                f"- Industry: {self.discovered_signals.get('industry', 'Unknown')}"
            ),
            'start': {
                'dateTime': meeting_datetime.isoformat(),
                'timeZone': 'America/Toronto',  # Or use env variable
            },
            'end': {
                'dateTime': (meeting_datetime + timedelta(minutes=30)).isoformat(),
                'timeZone': 'America/Toronto',
            },
            'attendees': [
                {'email': customer_email},
            ],
            'conferenceData': {
                'createRequest': {
                    'requestId': f"pandadoc-{int(time.time())}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        # Create the event
        created_event = service.events().insert(
            calendarId=os.getenv('GOOGLE_CALENDAR_ID'),
            body=event,
            conferenceDataVersion=1,
            sendUpdates='all'  # Send invites to attendees
        ).execute()

        return {
            "booking_status": "confirmed",
            "meeting_time": meeting_datetime.strftime("%A, %B %d at %I:%M %p %Z"),
            "meeting_link": created_event.get('hangoutLink', created_event.get('htmlLink')),
            "calendar_event_id": created_event['id'],
            "action": "meeting_booked"
        }

    except HttpError as e:
        if e.resp.status == 401:
            logger.error("Google Calendar authentication failed")
            raise ToolError("I'm unable to book meetings right now. Please email sales@pandadoc.com directly.")
        else:
            logger.error(f"Google Calendar API error: {e}")
            raise ToolError("There was an issue booking your meeting. Please try again or email sales@pandadoc.com")

    except Exception as e:
        logger.error(f"Unexpected booking error: {e}")
        raise ToolError("I couldn't complete the booking. Please email sales@pandadoc.com with your availability.")
```

### 3. Helper Methods

```python
def _get_calendar_service(self):
    """Initialize Google Calendar service using service account."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    import os

    # Get the service account JSON path (relative to my-app directory)
    service_account_path = os.path.join(
        os.path.dirname(__file__),  # my-app/src/
        '..',  # my-app/
        os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON').lstrip('/')
    )

    # Use service account for server-to-server auth
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=['https://www.googleapis.com/auth/calendar']
    )

    return build('calendar', 'v3', credentials=credentials)

def _parse_meeting_time(self, date_pref: Optional[str], time_pref: Optional[str]) -> datetime:
    """Parse natural language date/time into datetime object.

    Simple parsing - defaults to next business day at 10am if not specified.
    """
    from datetime import datetime, timedelta
    import dateparser

    # Try to parse the date preference
    if date_pref:
        parsed_date = dateparser.parse(date_pref, settings={'PREFER_DATES_FROM': 'future'})
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
    from datetime import date, timedelta

    tomorrow = date.today() + timedelta(days=1)
    # If tomorrow is Saturday (5) or Sunday (6), jump to Monday
    if tomorrow.weekday() >= 5:
        days_ahead = 7 - tomorrow.weekday() + 1
        return tomorrow + timedelta(days=days_ahead)
    return tomorrow
```

### 4. Modified Action Determination Logic

```python
def _determine_next_action(self, query: str, results: list) -> str:
    """Determine next action - NEVER offer human help for unqualified users."""

    if not results:
        # Instead of "offer_human_help", check qualification
        if self.should_route_to_sales():
            return "offer_sales_meeting"  # Only for qualified
        else:
            return "explore_self_serve"  # Guide to self-service resources

    query_lower = query.lower()

    # Existing intent analysis
    if any(word in query_lower for word in ["how", "setup", "configure", "create"]):
        return "offer_walkthrough"
    elif any(word in query_lower for word in ["pricing", "cost", "plan", "tier"]):
        # For pricing questions, check if they're qualified for sales discussion
        if self.should_route_to_sales():
            return "discuss_enterprise_pricing"
        else:
            return "discuss_self_serve_pricing"
    elif any(word in query_lower for word in ["integration", "connect", "sync", "api"]):
        return "check_specific_integration"
    elif any(word in query_lower for word in ["error", "problem", "issue", "broken"]):
        return "troubleshoot_issue"
    else:
        return "clarify_needs"
```

### 5. System Prompt Modifications

```python
instructions="""You are Sarah, a friendly and knowledgeable Trial Success Specialist at PandaDoc.

## CRITICAL BOOKING RULES
1. ONLY offer to book sales meetings for users who meet qualification criteria (5+ users, 100+ docs/month, or enterprise needs)
2. NEVER offer "human assistance" or "talk to someone" for unqualified users
3. For unqualified users, guide them to self-serve resources and features
4. When booking is offered and accepted, use book_sales_meeting tool immediately

## Tool Usage Priority
1. unleash_search_knowledge - ALWAYS use for PandaDoc questions
2. book_sales_meeting - ONLY use for qualified leads who agree to meeting

## Qualification Signals to Track
Track these internally, never ask directly:
- Team size (5+ = qualified)
- Document volume (100+/month = qualified)
- Integration needs (Salesforce/HubSpot = qualified)
- Industry (healthcare/finance/legal with 3+ users = qualified)

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
"""
```

## Implementation Steps

### ~~Phase 1: Environment Setup~~ ✅ COMPLETE
Google Calendar API is already configured with:
- Service account JSON stored at `/.secrets/pandadoc-voice-agent-03fa518aa3d0.json`
- Calendar ID configured in `.env.local`
- Ready for immediate implementation

### Phase 2: Dependencies (15 minutes)
```bash
cd my-app
uv add google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib dateparser
```

### Phase 3: Core Implementation (1.5 hours)
1. Add `book_sales_meeting` tool to agent.py
2. Add helper methods for calendar service and time parsing
3. Modify `_determine_next_action` logic
4. Update system prompt with booking rules
5. Remove all "offer_human_help" references

### Phase 4: Testing (30 minutes)
1. Test with qualified user scenario
2. Test with unqualified user scenario
3. Test booking with various date/time preferences
4. Test error handling (auth failure, API errors)
5. Verify no human assistance offered to unqualified users

## Environment Variables ✅ ALREADY CONFIGURED

```bash
# Current configuration in .env.local
GOOGLE_SERVICE_ACCOUNT_JSON=/.secrets/pandadoc-voice-agent-03fa518aa3d0.json
GOOGLE_CALENDAR_ID=c_f81fc95409534f4983a4bbb949b1ea35989199a5ae73d8383a9e022dea44b816@group.calendar.google.com

# Optional additions you might want:
GOOGLE_CALENDAR_TIMEZONE=America/Toronto  # Default timezone (optional)
```

## Service Account Setup ✅ COMPLETE

Your Google Calendar integration is ready to use:
- Service account key: `/.secrets/pandadoc-voice-agent-03fa518aa3d0.json`
- Calendar configured and accessible
- No additional setup required

**Note**: Ensure the service account has "Make changes to events" permission on the calendar.

## Error Handling Strategy

| Scenario | Response |
|----------|----------|
| Unqualified user asks for help | Guide to self-serve features |
| Qualified user booking fails | Provide direct email fallback |
| Authentication error | Email fallback only |
| Invalid date/time | Default to next business day |
| Calendar API timeout | Graceful failure with email |

## Security Considerations

1. **Service Account Key**: Store securely, never commit to git
2. **Calendar Permissions**: Limit to specific calendar, not all calendars
3. **PII Handling**: Log customer data minimally
4. **Rate Limiting**: Google Calendar API has quotas (respect them)
5. **Validation**: Sanitize customer input before creating events

## Testing Checklist

- [ ] Qualified user → books successfully
- [ ] Unqualified user → gets self-serve guidance (no human offer)
- [ ] Missing customer info → tool requests it
- [ ] API failure → graceful email fallback
- [ ] Various date formats → parse correctly
- [ ] Weekend booking → moves to Monday
- [ ] Qualification during conversation → offers booking when qualified
- [ ] Never offers human help to unqualified users

## Minimal Implementation (Start Here)

If you want the absolute simplest version first:

```python
@function_tool()
async def book_sales_meeting(
    self,
    context: RunContext,
    customer_name: str,
    customer_email: str
) -> Dict[str, Any]:
    """Book meeting with sales - ONLY for qualified leads."""

    if not self.should_route_to_sales():
        raise ToolError("Let me help you explore PandaDoc features first.")

    # For MVP: Return booking link instead of creating event
    return {
        "booking_status": "link_provided",
        "booking_link": "https://calendly.com/pandadoc-sales",
        "instructions": f"I've prepared a booking link for {customer_name}. Please select a time that works for you.",
        "action": "booking_link_shared"
    }
```

This MVP version:
- Still checks qualification
- Provides Calendly link instead of creating event
- No Google Calendar API needed initially
- Can upgrade to full implementation later

## Summary

This design delivers exactly what's needed:
1. ✅ Books meetings without availability checking
2. ✅ Only for qualified leads
3. ✅ No human assistance for others
4. ✅ Simple, maintainable implementation
5. ✅ Clear error handling
6. ✅ Voice-optimized responses

The implementation avoids over-engineering by:
- No complex availability checking
- No multi-calendar coordination
- No round-trip confirmation flows
- Direct booking with sensible defaults
- Service account for simple auth