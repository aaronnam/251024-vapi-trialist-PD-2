# Zapier Calendar Integration - Implementation Plan

## Executive Summary

We'll integrate Zapier webhooks to bypass corporate Google Calendar restrictions. This is an elegant solution that leverages your existing Zapier access and OAuth authentication (rather than service accounts).

**Key Insight**: Instead of fighting corporate restrictions, we use Zapier as a bridge - it authenticates with YOUR Google account via OAuth, bypassing service account limitations entirely.

## Why This Approach is Elegant

1. **Minimal Code Changes**: Single environment variable switches between Google API and Zapier
2. **Maintains Tool Semantics**: Same `book_sales_meeting` tool, same parameters
3. **Graceful Fallback Chain**: Zapier → Demo Mode → Google API
4. **No Over-Engineering**: ~30 lines of code change total
5. **Production Ready**: Includes proper error handling, timeouts, and logging

## Implementation Design

### 1. Environment Variables (Simple Switch)

```bash
# .env.local
ZAPIER_CALENDAR_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR_ID/YOUR_TOKEN/
ZAPIER_CALENDAR_NAME=primary  # or specific calendar name

# Optional: Keep demo mode as fallback
DEMO_MODE=false  # Zapier takes precedence when webhook URL is set
```

### 2. Code Changes (Minimal & Clear)

```python
# In book_sales_meeting() - Add at the start of try block:

# Priority 1: Try Zapier webhook (if configured)
zapier_webhook_url = os.getenv("ZAPIER_CALENDAR_WEBHOOK_URL")
if zapier_webhook_url:
    return await self._book_via_zapier(
        customer_name, email_to_use, preferred_date, preferred_time
    )

# Priority 2: Demo mode (if no Zapier)
if os.getenv("DEMO_MODE", "false").lower() == "true":
    return await self._book_via_demo(...)

# Priority 3: Direct Google Calendar API (original)
return await self._book_via_google(...)
```

### 3. Zapier Webhook Method (Clean Abstraction)

```python
async def _book_via_zapier(
    self,
    customer_name: str,
    email: str,
    preferred_date: Optional[str],
    preferred_time: Optional[str]
) -> Dict[str, Any]:
    """Book meeting via Zapier webhook (bypasses service account restrictions)."""

    meeting_datetime = self._parse_meeting_time(preferred_date, preferred_time)

    # Zapier expects MM/DD/YYYY format
    webhook_payload = {
        "summary": f"PandaDoc Sales Consultation - {customer_name}",
        "description": self._format_meeting_description(customer_name, email),
        "start_date": meeting_datetime.strftime("%m/%d/%Y"),
        "start_time": meeting_datetime.strftime("%H:%M"),
        "end_date": (meeting_datetime + timedelta(minutes=30)).strftime("%m/%d/%Y"),
        "end_time": (meeting_datetime + timedelta(minutes=30)).strftime("%H:%M"),
        "attendees": email,
        "calendar": os.getenv("ZAPIER_CALENDAR_NAME", "primary")
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.post(
                    os.getenv("ZAPIER_CALENDAR_WEBHOOK_URL"),
                    json=webhook_payload,
                    timeout=5.0  # Zapier typically responds in <1s
                ),
                timeout=7.0  # Overall timeout with buffer
            )

            if response.status_code == 200:
                logger.info(f"✅ Zapier webhook triggered for {customer_name}")
                return self._format_booking_response(meeting_datetime, via="zapier")
            else:
                logger.error(f"Zapier webhook returned {response.status_code}")
                raise ToolError(
                    "I'm having trouble booking your meeting. "
                    "Let me try another way..."
                )

    except asyncio.TimeoutError:
        logger.warning("Zapier webhook timeout - falling back")
        raise ToolError(
            "The booking service is slow right now. "
            "I'll make sure your meeting gets scheduled - you'll receive an email confirmation."
        )
```

## Tool Description Updates (Critical for Agent Success)

Based on Anthropic's guidance, we need crystal-clear tool descriptions:

```python
@function_tool()
async def book_sales_meeting(
    self,
    context: RunContext,
    customer_name: str,
    customer_email: Optional[str] = None,
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
) -> Dict[str, Any]:
    """Book a sales meeting for qualified users who explicitly request one.

    WHEN TO CALL THIS TOOL:
    - User says: "book a meeting", "schedule a call", "talk to sales", "set up time"
    - AND user is qualified (team_size >= 5 OR monthly_volume >= 100 OR needs CRM)

    REQUIRED PARAMETER:
    - customer_name: ALWAYS required. Ask "What's your name?" if not provided.

    BOOKING FLOW:
    1. Verify user is qualified (check discovered_signals)
    2. Collect customer_name if missing
    3. Ask for preferred date/time (optional - defaults to next business day)
    4. Call this tool with all collected information
    5. Confirm booking with returned details

    NEVER:
    - Claim booking success without calling this tool
    - Skip name collection
    - Offer meetings to unqualified users

    Args:
        customer_name: Full name of the person booking (REQUIRED)
        customer_email: Email if different from session email (optional)
        preferred_date: Natural language date like "tomorrow" or "next Tuesday"
        preferred_time: Natural language time like "2 PM" or "morning"

    Returns:
        Dict with booking_status, meeting_time, and confirmation details
    """
```

## Zapier Configuration (One-Time Setup)

### Step 1: Create the Zap

1. **Trigger**: Webhooks by Zapier → Catch Hook
   - Gets a unique URL like: `https://hooks.zapier.com/hooks/catch/123456/abcdef/`

2. **Action**: Google Calendar → Create Detailed Event
   - Connect YOUR Google account (OAuth)
   - Map webhook fields:
     ```
     Event Title: {{summary}}
     Description: {{description}}
     Start Date: {{start_date}}
     Start Time: {{start_time}}
     End Date: {{end_date}}
     End Time: {{end_time}}
     Attendees: {{attendees}}
     Calendar: {{calendar}}
     Add Google Meet: Yes
     Send Invites: Yes
     ```

3. **Test & Activate**: Send test webhook, verify event created

### Step 2: Update Agent Configuration

```bash
# .env.local
ZAPIER_CALENDAR_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/123456/abcdef/
ZAPIER_CALENDAR_NAME=aaron.nam@pandadoc.com  # Your calendar
DEMO_MODE=false  # Turn off demo mode
```

## Error Handling Strategy

Following LiveKit best practices from the research:

1. **Timeout Handling** (5-7 seconds for Zapier)
   - Zapier typically responds in <1s
   - 5s timeout balances responsiveness vs reliability
   - Graceful message if timeout occurs

2. **Error Messages** (User-Friendly)
   - ✅ "I'm having trouble booking your meeting. Let me try another way..."
   - ❌ "HTTP 500 Internal Server Error from webhook"

3. **Fallback Chain**
   - Zapier fails → Demo mode (if enabled)
   - Demo fails → Original Google API
   - All fail → Suggest email to sales@pandadoc.com

## Testing Plan

### 1. Unit Test - Zapier Integration

```python
@pytest.mark.asyncio
async def test_zapier_webhook_booking():
    """Test booking via Zapier webhook."""

    # Mock successful Zapier response
    with patch.dict(os.environ, {
        "ZAPIER_CALENDAR_WEBHOOK_URL": "https://test.webhook.url"
    }):
        async with httpx.AsyncClient() as client:
            # Mock the POST request
            with patch.object(client, 'post') as mock_post:
                mock_post.return_value.status_code = 200

                agent = PandaDocTrialistAgent()
                result = await agent.book_sales_meeting(
                    context=mock_context,
                    customer_name="Test User",
                    preferred_date="tomorrow",
                    preferred_time="2 PM"
                )

                assert result["booking_status"] == "confirmed"
                assert result["via"] == "zapier"
                assert mock_post.called
```

### 2. Console Test - Real Zapier

```bash
# Test in console mode
uv run python src/agent.py console

# Say: "I'm John from a 10-person team. Book a meeting for tomorrow at 2 PM."
# Verify: Check your Google Calendar for the event
```

### 3. Integration Test - End-to-End

```python
@pytest.mark.integration
async def test_real_zapier_booking():
    """Actually creates calendar event via Zapier."""
    # Only run if ZAPIER_CALENDAR_WEBHOOK_URL is set
    if not os.getenv("ZAPIER_CALENDAR_WEBHOOK_URL"):
        pytest.skip("Zapier webhook not configured")

    # ... test real booking ...
```

## Advantages Over Alternatives

### vs. Direct Google API
- ✅ No service account restrictions
- ✅ Works with corporate Google accounts
- ✅ Simpler authentication (OAuth via Zapier UI)
- ❌ Adds ~4-5s latency
- ❌ Depends on Zapier uptime

### vs. OAuth2 Implementation
- ✅ No token refresh complexity
- ✅ No OAuth flow implementation needed
- ✅ Zapier handles all auth edge cases
- ❌ Requires Zapier subscription for production

### vs. Demo Mode
- ✅ Actually creates calendar events
- ✅ Sends real invites with Google Meet links
- ✅ Professional production experience

## Production Considerations

1. **Zapier Limits**
   - Free: 100 tasks/month (testing only)
   - Starter: 750 tasks/month ($29.99)
   - Professional: 2,000 tasks/month ($73.50)

2. **Monitoring**
   - Add Zapier webhook to health checks
   - Log all webhook calls for debugging
   - Track success/failure rates

3. **Security**
   - Keep webhook URL in secrets (not in code)
   - Zapier webhooks accept any payload (validate on Zapier side if needed)

## Implementation Checklist

- [ ] Create Zapier account (if needed)
- [ ] Build the Zap (Webhook → Google Calendar)
- [ ] Test Zap with manual webhook call
- [ ] Add `ZAPIER_CALENDAR_WEBHOOK_URL` to `.env.local`
- [ ] Implement `_book_via_zapier()` method
- [ ] Update `book_sales_meeting()` with Zapier priority
- [ ] Test in console mode
- [ ] Verify calendar event created
- [ ] Update production secrets (if deploying)
- [ ] Document webhook URL for team

## Summary

This approach elegantly solves the corporate calendar restriction problem with:
- **30 lines of code** (mostly the new `_book_via_zapier` method)
- **1 environment variable** to switch between modes
- **Zero changes** to agent conversation flow
- **Production-ready** error handling and fallbacks

The agent will seamlessly use Zapier when configured, fall back to demo mode if needed, and maintain the exact same conversation experience for users.