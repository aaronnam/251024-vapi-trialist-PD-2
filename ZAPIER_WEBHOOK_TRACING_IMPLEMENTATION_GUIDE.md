# Zapier Webhook Tracing: Implementation Guide

## Quick Start (Copy-Paste Ready)

### Step 1: Create Webhook Tracing Helper

Create `/my-app/src/utils/webhook_tracing.py`:

```python
"""
Webhook tracing utilities for third-party integrations (Zapier, etc).

Provides automatic span creation and cost tracking for webhook calls.
Ensures all HTTP integrations are properly traced in Langfuse.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

import httpx
from livekit.agents import ToolError
from opentelemetry import trace as otel_trace

logger = logging.getLogger("webhook_tracing")


async def call_zapier_webhook(
    event_type: str,
    data: Dict[str, Any],
    cost_estimate: float = 0.0,
    webhook_url: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Call Zapier webhook with automatic tracing and error handling.

    Features:
    - Automatic OpenTelemetry span creation
    - Cost tracking via span attributes
    - Error handling and logging
    - Langfuse-compatible attributes

    Args:
        event_type: Type of event (e.g., "booking_created", "qualified_lead")
        data: Payload to send to Zapier (dict)
        cost_estimate: Estimated cost for this call in USD (default: 0.0)
        webhook_url: Optional override for webhook URL (uses env var if None)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Response JSON from Zapier webhook

    Raises:
        ToolError: If webhook call fails (non-2xx status code)
        ValueError: If ZAPIER_WEBHOOK_URL not configured

    Example:
        >>> result = await call_zapier_webhook(
        ...     event_type="booking_created",
        ...     data={
        ...         "customer_name": "John Smith",
        ...         "customer_email": "john@example.com",
        ...         "meeting_time": "2025-11-01T10:00:00Z"
        ...     },
        ...     cost_estimate=0.01
        ... )
        >>> print(result["id"])  # Zapier action run ID
    """
    tracer = otel_trace.get_tracer(__name__)
    webhook_url = webhook_url or os.getenv("ZAPIER_WEBHOOK_URL")

    if not webhook_url:
        raise ValueError(
            "ZAPIER_WEBHOOK_URL not configured. "
            "Set environment variable or pass webhook_url parameter."
        )

    # Create span with event type in name for filtering in Langfuse
    span_name = f"zapier_{event_type}"

    with tracer.start_as_current_span(span_name) as span:
        # Set context attributes for filtering and analysis
        span.set_attribute("integration.vendor", "zapier")
        span.set_attribute("integration.operation", event_type)
        span.set_attribute("webhook.event_type", event_type)
        span.set_attribute("webhook.payload_size_bytes", len(json.dumps(data)))

        try:
            # Log outgoing request
            logger.debug(f"🔗 Calling Zapier webhook: {event_type}")

            # Make HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=data,
                    timeout=timeout,
                    headers={"Content-Type": "application/json"},
                )

            # Enrich span with response metadata
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_size_bytes", len(response.content))

            # Add cost tracking if provided
            if cost_estimate > 0:
                span.set_attribute("langfuse.cost.total", cost_estimate)
                span.set_attribute("gen_ai.usage.cost", cost_estimate)
                span.set_attribute("webhook.cost_unit", "per_call")
                logger.debug(f"📊 Cost estimated: ${cost_estimate:.4f}")

            # Check for HTTP errors
            if response.status_code >= 400:
                error_msg = response.text[:500]
                span.set_attribute("http.error_message", error_msg)
                span.set_attribute("error.type", "webhook_error")
                span.set_attribute("error.status_code", response.status_code)

                logger.error(
                    f"❌ Zapier webhook error ({response.status_code}): {error_msg}"
                )

                raise ToolError(
                    f"Zapier webhook failed with status {response.status_code}. "
                    f"Event: {event_type}"
                )

            # Success - parse response
            try:
                result = response.json()
            except json.JSONDecodeError:
                # Fallback if response isn't JSON
                result = {"raw_response": response.text[:500]}

            # Mark success in span
            span.set_attribute("http.success", True)
            span.set_attribute("webhook.response_id", result.get("id", "unknown"))

            logger.info(
                f"✅ Zapier webhook succeeded: {event_type} "
                f"(response_id: {result.get('id', 'unknown')})"
            )

            return result

        except httpx.TimeoutException as e:
            span.set_attribute("error.type", "timeout")
            span.set_attribute("error.timeout_seconds", timeout)
            logger.error(f"⏱️  Zapier webhook timeout after {timeout}s: {e}")

            raise ToolError(
                f"Zapier webhook timeout after {timeout} seconds. "
                f"Event: {event_type}"
            )

        except httpx.RequestError as e:
            span.set_attribute("error.type", "request_error")
            span.set_attribute("error.message", str(e)[:500])
            logger.error(f"🌐 Zapier webhook request error: {e}")

            raise ToolError(f"Zapier webhook request failed: {event_type}")

        except Exception as e:
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e)[:500])
            logger.error(f"❌ Unexpected error in Zapier webhook: {type(e).__name__}: {e}")

            raise


async def call_generic_webhook(
    webhook_name: str,
    event_type: str,
    data: Dict[str, Any],
    webhook_url: str,
    cost_estimate: float = 0.0,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Call any generic webhook with automatic tracing.

    Use this for non-Zapier webhooks (e.g., custom endpoints, Make.com, etc).

    Args:
        webhook_name: Name of the webhook service (e.g., "make", "custom_api")
        event_type: Type of event
        data: Payload dict
        webhook_url: Full webhook URL
        cost_estimate: Cost in USD
        timeout: Request timeout in seconds

    Returns:
        Response JSON from webhook

    Raises:
        ToolError: If webhook call fails

    Example:
        >>> result = await call_generic_webhook(
        ...     webhook_name="custom_booking_service",
        ...     event_type="booking_created",
        ...     data={"customer_id": "123"},
        ...     webhook_url="https://api.example.com/booking",
        ...     cost_estimate=0.05
        ... )
    """
    tracer = otel_trace.get_tracer(__name__)
    span_name = f"webhook_{webhook_name}_{event_type}"

    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("integration.vendor", webhook_name)
        span.set_attribute("integration.operation", event_type)
        span.set_attribute("webhook.url", webhook_url[:100])  # Sanitized
        span.set_attribute("webhook.payload_size_bytes", len(json.dumps(data)))

        try:
            logger.debug(f"🔗 Calling {webhook_name} webhook: {event_type}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=data,
                    timeout=timeout,
                )

            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_size_bytes", len(response.content))

            if cost_estimate > 0:
                span.set_attribute("langfuse.cost.total", cost_estimate)
                span.set_attribute("gen_ai.usage.cost", cost_estimate)

            if response.status_code >= 400:
                error_msg = response.text[:500]
                span.set_attribute("error.type", "webhook_error")
                raise ToolError(
                    f"{webhook_name} webhook failed ({response.status_code}): {error_msg}"
                )

            result = response.json() if response.text else {}
            span.set_attribute("http.success", True)

            logger.info(f"✅ {webhook_name} webhook succeeded: {event_type}")
            return result

        except Exception as e:
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e)[:500])
            logger.error(f"❌ {webhook_name} webhook error: {type(e).__name__}: {e}")
            raise
```

### Step 2: Update Agent Tool

Update `book_sales_meeting` in `/my-app/src/agent.py`:

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

    CALL THIS TOOL IMMEDIATELY when:
    - User says: "book a meeting", "schedule a call", "talk to sales"
    - AND user is qualified (team_size >= 5 OR monthly_volume >= 100)

    Args:
        customer_name: REQUIRED - The customer's full name
        customer_email: Optional - Will use stored email if not provided
        preferred_date: Optional - e.g., "tomorrow", "next Tuesday"
        preferred_time: Optional - e.g., "2pm", "morning"

    Returns:
        Dict with booking_status, meeting_time, webhook_id
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
        # Parse date/time preferences
        meeting_datetime = self._parse_meeting_time(preferred_date, preferred_time)

        # Prepare booking payload for Zapier
        booking_data = {
            "customer_name": customer_name,
            "customer_email": email_to_use,
            "meeting_time": meeting_datetime.isoformat(),
            "meeting_duration_minutes": 30,
            "qualification_signals": {
                "team_size": self.discovered_signals.get("team_size", 0),
                "monthly_volume": self.discovered_signals.get("monthly_volume", 0),
                "integration_needs": self.discovered_signals.get("integration_needs", []),
                "industry": self.discovered_signals.get("industry"),
                "urgency": self.discovered_signals.get("urgency"),
            },
            "source": "voice_agent",
            "timestamp": datetime.now().isoformat(),
        }

        # Call Zapier webhook via helper (TRACED)
        from utils.webhook_tracing import call_zapier_webhook

        webhook_result = await call_zapier_webhook(
            event_type="booking_created",
            data=booking_data,
            cost_estimate=0.01,  # Estimate: $0.01 per booking
        )

        # Analytics tracking
        self.session_data["tool_calls"].append(
            {
                "tool": "book_sales_meeting",
                "customer_name": customer_name,
                "customer_email": email_to_use,
                "booking_method": "zapier_webhook",
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "zapier_response_id": webhook_result.get("id"),
            }
        )

        logger.info(
            f"✅ Meeting booked via Zapier for {customer_name} "
            f"(webhook_id: {webhook_result.get('id')})"
        )

        return {
            "booking_status": "confirmed",
            "meeting_time": meeting_datetime.strftime("%A, %B %d at %I:%M %p"),
            "webhook_id": webhook_result.get("id"),
            "action": "meeting_booked",
            "message": f"Your meeting is confirmed for {meeting_datetime.strftime('%A at %I:%M %p')}. "
            f"You'll receive a calendar invite at {email_to_use}.",
        }

    except Exception as e:
        logger.error(f"❌ Meeting booking failed: {e}")

        # Analytics tracking for failure
        self.session_data["tool_calls"].append(
            {
                "tool": "book_sales_meeting",
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)[:200],
            }
        )

        # Re-raise to propagate to agent
        raise
```

### Step 3: Add Environment Variable

In `.env.local` (for local testing):

```bash
# Zapier webhook configuration
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/
```

In LiveKit Cloud secrets:

```bash
lk agent update-secrets \
  --secrets "ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/"
```

---

## Verification Checklist

### Local Testing

```bash
# 1. Start agent in console mode
uv run python src/agent.py console

# 2. Test conversation
# > I need to schedule a meeting with your sales team
# Agent should respond with booking flow

# 3. Check logs
# Look for: "✅ Zapier webhook succeeded"
# NOT: "❌ Zapier webhook error"

# 4. Check Langfuse (wait 30 seconds)
# - Session should appear
# - Find zapier_booking_created span
# - Verify span has attributes:
#   - integration.vendor: "zapier"
#   - http.status_code: 200 (or your status)
#   - langfuse.cost.total: 0.01
```

### Unit Test

Create `/my-app/tests/test_zapier_webhook_tracing.py`:

```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.utils.webhook_tracing import call_zapier_webhook
from livekit.agents import ToolError


@pytest.mark.asyncio
async def test_zapier_webhook_success():
    """Test successful webhook call with tracing"""
    with patch("src.utils.webhook_tracing.httpx.AsyncClient") as mock_client:
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "test-123", "status": "completed"}'
        mock_response.content = b'{"id": "test-123"}'
        mock_response.json.return_value = {"id": "test-123", "status": "completed"}

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        # Call webhook
        result = await call_zapier_webhook(
            event_type="booking_created",
            data={"customer_name": "John Smith"},
            cost_estimate=0.01,
            webhook_url="https://example.com/webhook",
        )

        # Verify result
        assert result["id"] == "test-123"
        assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_zapier_webhook_error():
    """Test webhook call with error"""
    with patch("src.utils.webhook_tracing.httpx.AsyncClient") as mock_client:
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.content = b"Bad request"

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        # Should raise ToolError
        with pytest.raises(ToolError):
            await call_zapier_webhook(
                event_type="booking_created",
                data={"customer_name": "John Smith"},
                webhook_url="https://example.com/webhook",
            )


@pytest.mark.asyncio
async def test_zapier_webhook_timeout():
    """Test webhook timeout"""
    with patch("src.utils.webhook_tracing.httpx.AsyncClient") as mock_client:
        import httpx

        # Mock timeout
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        # Should raise ToolError
        with pytest.raises(ToolError):
            await call_zapier_webhook(
                event_type="booking_created",
                data={"customer_name": "John Smith"},
                webhook_url="https://example.com/webhook",
                timeout=5.0,
            )
```

Run tests:

```bash
uv run pytest tests/test_zapier_webhook_tracing.py -v
```

---

## Langfuse Verification

### Check Spans Appear

1. Open Langfuse dashboard
2. Filter by session ID (your test session)
3. Look for observations of type TOOL
4. Should see: `zapier_booking_created`

### Check Cost Attributes

1. Click on the `zapier_booking_created` span
2. Go to "Attributes" tab
3. Verify:
   - `integration.vendor`: "zapier"
   - `langfuse.cost.total`: 0.01
   - `gen_ai.usage.cost`: 0.01
   - `http.status_code`: 200

### Check Error Handling

Test with bad webhook URL:

```bash
# In .env.local, set wrong URL
ZAPIER_WEBHOOK_URL=https://invalid-url.example.com/

# Run conversation
uv run python src/agent.py console

# Try to book meeting
# > Schedule a meeting

# Check logs for error
# Should see: "❌ Zapier webhook error"
# Agent should respond gracefully
```

---

## Troubleshooting

### Issue: "ZAPIER_WEBHOOK_URL not configured"

**Cause**: Environment variable not set

**Fix**:
```bash
# Add to .env.local
echo "ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR_ID/" >> .env.local

# For LiveKit Cloud
lk agent update-secrets --secrets "ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR_ID/"
lk agent restart
```

### Issue: Zapier webhook shows in logs but not in Langfuse

**Cause**: Tracing not enabled or export delay

**Fix**:
- Wait 30-60 seconds (batch export delay)
- Check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set
- Verify telemetry setup succeeded: look for "✅ Tracing enabled with LangFuse"

### Issue: Cost not showing in Langfuse

**Cause**: Cost attribute not set correctly

**Fix**:
```python
# Verify these attributes are set:
span.set_attribute("langfuse.cost.total", 0.01)  # Required
span.set_attribute("gen_ai.usage.cost", 0.01)    # Required for Model Usage tab
```

### Issue: Webhook calls blocked or timing out

**Cause**: Webhook URL unreachable or slow

**Fix**:
```bash
# Test webhook URL directly
curl -X POST https://your-webhook-url \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Check timeout setting (default: 30s)
# Adjust in call_zapier_webhook(timeout=60.0)
```

---

## Integration Patterns

### Pattern 1: Simple Webhook Call

```python
# Most basic usage
result = await call_zapier_webhook(
    event_type="booking_created",
    data={"customer_name": name}
)
```

### Pattern 2: With Cost Tracking

```python
# Track cost for billing
result = await call_zapier_webhook(
    event_type="booking_created",
    data=booking_data,
    cost_estimate=0.01  # Per-call cost
)
```

### Pattern 3: With Error Handling

```python
try:
    result = await call_zapier_webhook(
        event_type="booking_created",
        data=booking_data,
    )
except ToolError as e:
    logger.error(f"Booking failed: {e}")
    # Fallback logic
    await send_email_to_sales(booking_data)
```

### Pattern 4: Multiple Webhooks

```python
# Send to multiple destinations
result1 = await call_zapier_webhook(
    event_type="qualified_lead",
    data=lead_data,
)

result2 = await call_generic_webhook(
    webhook_name="slack",
    event_type="qualified_lead",
    data=lead_data,
    webhook_url=SLACK_WEBHOOK_URL,
)
```

---

## Performance Considerations

### Latency

- Webhook call: 100-2000ms typical
- Span creation: <1ms
- Attribute enrichment: <1ms
- **Total overhead**: ~1ms (negligible)

### Cost

- Zapier: ~$0.01-0.05 per call (verify with your plan)
- Langfuse tracing: Free (included in observability)
- **No extra cost** for tracing webhooks

### Concurrency

Handles concurrent webhook calls correctly:
- Each call gets its own span
- No race conditions
- Attributes isolated per span

---

## Advanced: Custom Webhook Analytics

Track custom metrics from webhook responses:

```python
# In webhook_tracing.py, after success
if "metrics" in result:
    span.set_attribute("webhook.response.metrics", json.dumps(result["metrics"]))

if "duration_ms" in result:
    span.set_attribute("webhook.response.duration_ms", result["duration_ms"])

if "api_calls_made" in result:
    span.set_attribute("webhook.cascading_calls", result["api_calls_made"])
```

Then query in Langfuse:
- Filter by `webhook.cascading_calls > 5` to find expensive workflows
- Track `webhook.response.duration_ms` to identify slow integrations
- Correlate cost with response metrics

---

## Summary

1. ✅ Copy `webhook_tracing.py` to utils
2. ✅ Update `book_sales_meeting` to use `call_zapier_webhook()`
3. ✅ Add `ZAPIER_WEBHOOK_URL` to environment
4. ✅ Test locally with `uv run python src/agent.py console`
5. ✅ Verify Langfuse shows `zapier_booking_created` spans
6. ✅ Deploy with `lk agent deploy`
7. ✅ Monitor production with `lk agent logs`

---

**Status**: Ready for implementation
**Time to integrate**: ~30 minutes
**Risk level**: Low (well-isolated, error handling included)
**Breaking changes**: None (fully backward compatible)
