# Langfuse Observability Research: LiveKit Agents & Zapier Integration

## Executive Summary

Your implementation has an excellent foundation for Langfuse observability. This document provides specific research findings on how LiveKit function tools are automatically traced, the required attributes for cost tracking, and **critical recommendations for adding Zapier webhook integration without breaking existing observability**.

---

## Part 1: How LiveKit Function Tools Are Automatically Traced in Langfuse

### Current Implementation Pattern

Your `book_sales_meeting` and `unleash_search_knowledge` tools use LiveKit's `@function_tool()` decorator. This is the key to automatic tracing:

**Location**: `/my-app/src/agent.py:703-937` (tools definition)

```python
@function_tool()
async def unleash_search_knowledge(
    self,
    context: RunContext,
    query: str,
    category: Optional[str] = None,
    response_format: Optional[str] = None,
) -> Dict[str, Any]:
    """Search PandaDoc knowledge base..."""
    # Implementation
```

### How Automatic Tracing Works

1. **LiveKit Span Creation**: When `@function_tool()` decorator is applied:
   - LiveKit internally creates a TOOL span when the function is invoked
   - Span name is derived from function name: `tool_unleash_search_knowledge`
   - Span automatically captures: input arguments, output, duration, errors

2. **Automatic Attributes LiveKit Sets**:
   - `langfuse.function.name` - Tool function name
   - `gen_ai.operation.name` - Tool operation
   - Timing attributes: `duration_ms`, `start_time`, `end_time`
   - Error attributes if tool fails: `error`, `error.type`, `error.message`

3. **Trace Hierarchy**:
   ```
   trace (session_id, user_id)
   └── generation (llm_node for main LLM call)
   └── tool (unleash_search_knowledge call)
       ├── input attributes
       ├── output attributes
       └── duration
   ```

### Key Finding: Tool Spans Are Separate from LLM Spans

**Important**: When the agent calls a tool, LiveKit creates a **separate TOOL span** in the trace hierarchy, not nested under the LLM span. This means:

- ✅ Tool calls are independently visible in Langfuse
- ✅ Tool duration/cost is tracked separately
- ✅ Tool errors don't affect LLM spans
- ✅ You can filter traces by tool name: `Observation type = TOOL`

### Current Observability Coverage

Your tools automatically provide:

```
unleash_search_knowledge tool:
├── Input: query, category, response_format (captured by LiveKit)
├── Output: search results (captured by LiveKit)
├── Duration: API call latency
├── Error: if search fails
├── Session ID: from trace context
└── User ID: from trace context
```

```
book_sales_meeting tool:
├── Input: customer_name, customer_email, dates, times (captured by LiveKit)
├── Output: booking_status, meeting_time, meeting_link
├── Duration: Google Calendar API latency
├── Error: if booking fails
├── Session ID: from trace context
└── User ID: from trace context
```

---

## Part 2: Required Attributes for Proper Cost Tracking

### Current Cost Tracking Implementation

Your implementation uses **span enrichment** in the metrics handler (lines 1488-1626):

**Location**: `/my-app/src/agent.py:1424-1627` (`_on_metrics_collected` handler)

```python
@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    """Collect metrics, enrich spans with costs, and monitor latency"""
    # Standard metrics logging
    metrics.log_metrics(ev.metrics)
    agent.usage_collector.collect(ev.metrics)

    # Get current span for enrichment (created by LiveKit)
    current_span = otel_trace.get_current_span()
```

### Cost Attributes Pattern (For Model-Based Providers)

For LLM calls, your implementation sets:

```python
if isinstance(ev.metrics, LLMMetrics):
    # Cost attributes (Langfuse Model Usage uses these)
    current_span.set_attribute("langfuse.cost.total", llm_cost)
    current_span.set_attribute("langfuse.cost.input", input_cost)
    current_span.set_attribute("langfuse.cost.output", output_cost)

    # OpenTelemetry standard attributes (best practice)
    current_span.set_attribute("gen_ai.usage.cost", llm_cost)
    current_span.set_attribute("gen_ai.request.model", "gpt-4.1-mini")
    current_span.set_attribute("gen_ai.usage.input_tokens", ev.metrics.prompt_tokens)
    current_span.set_attribute("gen_ai.usage.output_tokens", ev.metrics.completion_tokens)
```

### For Third-Party Tools (HTTP Calls)

For tools that make HTTP calls (like Unleash search, Google Calendar API), Langfuse automatically captures:

1. **Duration**: Time spent in the HTTP call
2. **Error Status**: If the call failed
3. **Tool Context**: Function name, arguments, return value

**But NOT cost** - because there's no standard "cost" metric from HTTP libraries.

### Adding Cost for Third-Party Tools

If you need to track costs for external APIs (e.g., Unleash search, Google Calendar, Zapier), you must:

1. **Know the pricing** (per-call, per-request unit, etc.)
2. **Calculate manually** during tool execution
3. **Enrich the TOOL span** with cost attributes

Example pattern:

```python
async def unleash_search_knowledge(self, context: RunContext, query: str, ...):
    """Search knowledge base - cost tracking via span enrichment"""

    # Execute API call
    response = await client.post(...)

    # Calculate cost (if API has per-call pricing)
    cost = calculate_unleash_cost()  # e.g., $0.02 per search

    # Enrich the TOOL span with cost
    current_span = otel_trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("langfuse.cost.total", cost)
        current_span.set_attribute("gen_ai.usage.cost", cost)
        # Optional: add breakdown if applicable
        current_span.set_attribute("http.request.cost", cost)
        current_span.set_attribute("api.cost.unit", "per_search")
```

---

## Part 3: Tracing HTTP Calls (Like Zapier Webhooks)

### How HTTP Calls Are Traced

When your tool makes an HTTP call using `httpx.AsyncClient()`, OpenTelemetry's httpx instrumentation can automatically trace it IF enabled.

**Current Status in Your Code**: ⚠️ **UNKNOWN** - Check if httpx auto-instrumentation is active.

### Three Options for Tracing Zapier Webhooks

#### Option 1: Automatic Instrumentation (Recommended)

If httpx instrumentation is enabled, Zapier webhooks are automatically traced:

```python
# In telemetry.py, add:
from opentelemetry.instrumentation.httpx import HttpxClientInstrumentor

def setup_observability(...):
    # ... existing code ...

    # Enable httpx auto-instrumentation
    HttpxClientInstrumentor().instrument()

    # Now all httpx calls are automatically traced
```

**Pros**:
- Automatic span creation for each HTTP request
- Zero code changes needed in tools
- Captures request/response metadata
- Shows latency breakdown

**Cons**:
- Requires httpx instrumentation library
- May create many spans if you make multiple requests

#### Option 2: Manual Span Wrapping (Current Pattern)

Use the same pattern as your existing tools - wrap the HTTP call in a span:

```python
@function_tool()
async def book_sales_meeting(self, context: RunContext, ...):
    """Book meeting via Zapier webhook"""

    from opentelemetry import trace as otel_trace
    tracer = otel_trace.get_tracer(__name__)

    # Create custom span for Zapier webhook
    with tracer.start_as_current_span("zapier_webhook_call") as span:
        # Span attributes for context
        span.set_attribute("integration", "zapier")
        span.set_attribute("webhook_event", "booking_created")
        span.set_attribute("customer_name", customer_name)

        try:
            # Make HTTP call to Zapier
            response = await httpx.AsyncClient().post(
                os.getenv("ZAPIER_WEBHOOK_URL"),
                json={
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "meeting_time": meeting_datetime,
                    "qualification_signals": self.discovered_signals,
                }
            )

            # Enrich span with result
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_size", len(response.content))

            if response.status_code >= 400:
                span.set_attribute("http.error", response.text[:500])
                raise ToolError(f"Zapier webhook failed: {response.status_code}")

            return response.json()

        except Exception as e:
            span.set_attribute("error", str(e))
            raise
```

**Pros**:
- Full control over span attributes
- Can filter results in Langfuse by webhook_event
- Minimal dependencies

**Cons**:
- Manual span management
- Code in every tool that calls Zapier

#### Option 3: Helper Function Pattern (Best for Multiple Calls)

Create a reusable helper for Zapier calls:

```python
# In utils/webhook_tracing.py
from opentelemetry import trace as otel_trace

async def call_zapier_webhook(
    event_type: str,
    data: Dict[str, Any],
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """Call Zapier webhook with automatic span creation and error handling.

    Args:
        event_type: Type of event (e.g., "booking_created", "meeting_scheduled")
        data: Payload to send to Zapier
        webhook_url: Override default webhook URL

    Returns:
        Response JSON from Zapier
    """
    tracer = otel_trace.get_tracer(__name__)
    webhook_url = webhook_url or os.getenv("ZAPIER_WEBHOOK_URL")

    if not webhook_url:
        raise ValueError("ZAPIER_WEBHOOK_URL not configured")

    with tracer.start_as_current_span(f"zapier_{event_type}") as span:
        # Set span attributes for filtering/analysis
        span.set_attribute("integration.vendor", "zapier")
        span.set_attribute("webhook.event", event_type)
        span.set_attribute("webhook.payload_size", len(json.dumps(data)))

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=data,
                    timeout=10.0
                )

            # Enrich span with response metadata
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_time_ms", response.elapsed.total_seconds() * 1000)

            if response.status_code >= 400:
                error_text = response.text[:500]
                span.set_attribute("http.error_message", error_text)
                span.set_attribute("error.type", "webhook_error")
                raise Exception(f"Zapier webhook error: {response.status_code} - {error_text}")

            # Enrich span with cost if applicable
            # Zapier pricing varies - adjust based on your plan
            zapier_cost = 0.0  # Calculate based on your Zapier pricing model
            span.set_attribute("langfuse.cost.total", zapier_cost)

            span.set_attribute("webhook.success", True)
            return response.json()

        except httpx.TimeoutException as e:
            span.set_attribute("error.type", "timeout")
            raise Exception(f"Zapier webhook timeout: {e}")
        except Exception as e:
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            raise
```

Then use in tools:

```python
@function_tool()
async def book_sales_meeting(self, context: RunContext, ...):
    """Book meeting - delegates to Zapier via helper"""

    # Use the helper
    webhook_data = {
        "customer_name": customer_name,
        "customer_email": customer_email,
        "meeting_time": meeting_datetime,
        "qualification_signals": self.discovered_signals,
    }

    result = await call_zapier_webhook("booking_created", webhook_data)

    return {
        "booking_status": "confirmed",
        "webhook_id": result.get("id"),
        ...
    }
```

**Pros**:
- Single source of truth for Zapier tracing
- Consistent span naming and attributes
- Easy to add webhook-specific logic (retries, logging)
- All Zapier calls appear together in Langfuse

**Cons**:
- Additional abstraction layer
- Requires importing and managing another module

---

## Part 4: Best Practices for Enriching Spans with Custom Attributes

### Current Enrichment Pattern (Correct Implementation)

Your code uses this pattern in the metrics handler (lines 1503-1533):

```python
if isinstance(ev.metrics, LLMMetrics):
    # Get current span for enrichment
    current_span = otel_trace.get_current_span()

    # Enrich with attributes
    if current_span and current_span.is_recording():
        try:
            # Cost attributes (Langfuse Model Usage uses these)
            current_span.set_attribute("langfuse.cost.total", llm_cost)
            current_span.set_attribute("langfuse.cost.input", input_cost)
            current_span.set_attribute("langfuse.cost.output", output_cost)

            # OpenTelemetry standard attributes
            current_span.set_attribute("gen_ai.usage.cost", llm_cost)
            current_span.set_attribute("gen_ai.request.model", "gpt-4.1-mini")
            current_span.set_attribute("gen_ai.usage.input_tokens", ev.metrics.prompt_tokens)
            current_span.set_attribute("gen_ai.usage.output_tokens", ev.metrics.completion_tokens)

            logger.debug(f"✅ Enriched LLM span with cost: ${llm_cost:.6f}...")
        except Exception as e:
            logger.warning(f"Failed to enrich LLM span: {e}")
```

### Key Best Practices Observed

1. **Check Span Recording Status**: `if current_span and current_span.is_recording()`
   - Prevents errors when span is not active
   - Handles cases where OpenTelemetry context is missing

2. **Error Handling**: Wrapped in try-catch
   - Enrichment failures don't crash the agent
   - Logged as warnings for debugging

3. **Dual Attribute Sets**:
   - Langfuse-specific: `langfuse.cost.*`, `langfuse.model`
   - OpenTelemetry standard: `gen_ai.usage.*`, `gen_ai.request.*`
   - Reason: Multiple tools consume these attributes; using standards ensures compatibility

4. **Meaningful Attribute Names**:
   - Use prefixes: `langfuse.`, `gen_ai.`, `http.`, `api.`
   - Makes attributes filterable and searchable in Langfuse
   - Example: Search for "cost > 0.05" finds high-cost operations

### Attribute Naming Conventions for Zapier

When enriching Zapier webhook spans, follow this pattern:

```python
span.set_attribute("integration.vendor", "zapier")      # What vendor?
span.set_attribute("integration.operation", "send_booking")  # What operation?
span.set_attribute("webhook.event_type", "booking_created")  # What event?
span.set_attribute("webhook.destination_id", zapier_action_id)  # Where?
span.set_attribute("http.url", webhook_url[:100])      # Sanitize URL
span.set_attribute("http.method", "POST")
span.set_attribute("http.status_code", response.status_code)
span.set_attribute("http.response_time_ms", duration)
span.set_attribute("langfuse.cost.total", cost)         # Cost if applicable
span.set_attribute("error.type", error_type)            # If error occurred
```

### Attribute Limits & Performance

Important considerations:

- **Max Attribute Count**: OpenTelemetry allows ~128 attributes per span
  - Your current code uses ~15 attributes - plenty of headroom
  - Zapier spans should use <20 attributes

- **Max Attribute Value Length**: Typically 2048 characters
  - URL: Usually safe (sanitize if >100 chars)
  - Error messages: Truncate if >500 chars
  - JSON payloads: Don't store full payload, store size instead

- **Performance**: Setting attributes is extremely fast (<1ms per attribute)
  - No performance concern for enrichment

---

## Part 5: Avoiding Breaking Existing Langfuse Integration

### Critical Rule: Don't Modify LiveKit's Internal Spans

**DO NOT** try to modify spans created by LiveKit before you have access to them:

```python
# ❌ WRONG - This will break observability
current_span = otel_trace.get_current_span()
current_span.set_attribute("llm.input_tokens", 0)  # Overwrites LiveKit's value
```

**Why**: LiveKit sets span attributes with specific timing. Modifying them can corrupt the trace structure.

### Safe Enrichment Pattern

Instead, **add new attributes** using this pattern:

```python
# ✅ CORRECT - Add new attributes without modifying existing ones
current_span = otel_trace.get_current_span()

# Check span is still recording (in case it's closing)
if current_span and current_span.is_recording():
    try:
        # Only ADD attributes, never REPLACE
        current_span.set_attribute("my_custom.attribute", value)
        # Adding same attribute twice: latest value wins (safe to update)
        current_span.set_attribute("my_custom.attribute", updated_value)
    except Exception as e:
        # Log but don't crash
        logger.warning(f"Enrichment failed: {e}")
```

### Integration Points That Are Safe to Modify

These are places in your code where enrichment is already correct:

1. ✅ **metrics_collected handler** (line 1424)
   - LiveKit fires this AFTER span is populated with metrics
   - Safe to add attributes at this point
   - Already doing this correctly

2. ✅ **conversation_item_added handler** (line 1729)
   - Creates NEW custom spans, not modifying LiveKit's
   - Safe to add any attributes

3. ✅ **user_input_transcribed handler** (line 1670)
   - Creates NEW custom spans
   - Safe to add transcription-specific attributes

### Points That Could Break Observability

These should be avoided:

- ❌ **Don't modify spans in __init__**: Agent initialization hasn't started tracing yet
- ❌ **Don't create spans for tool inputs**: LiveKit already does this
- ❌ **Don't override "langfuse." attributes**: Use "langfuse.custom.*" instead
- ❌ **Don't set tool output as "langfuse.input"**: That's for inputs only

### Verification: How to Test Changes Don't Break Observability

1. **Run in console mode**:
   ```bash
   uv run python src/agent.py console
   ```
   - Have a test conversation
   - Look for errors related to tracing
   - Check logs for "Failed to enrich span" warnings

2. **Check Langfuse dashboard**:
   - Traces should appear within 30 seconds
   - Session ID should be visible
   - User ID should be visible (if email captured)
   - Tool calls should show as TOOL observations
   - LLM calls should show as GENERATION observations

3. **Verify trace structure**:
   ```
   Trace (session_id visible, user_id visible)
   ├── conversation_item (user input)
   ├── generation (llm_node with input/output)
   ├── tool (your_tool_name with inputs/outputs)
   └── conversation_item (assistant response)
   ```

4. **Look for attributes**:
   - Click on each span
   - Check "Attributes" tab
   - Should see `langfuse.cost.*`, `gen_ai.usage.*`, etc.
   - Should NOT see any ERROR level spans (unless expected)

---

## Part 6: Specific Recommendations for Zapier Integration

### Recommended Approach (Option 3 Modified)

Combine the helper function pattern with your existing cost tracking:

```python
# In src/utils/webhook_tracing.py (NEW FILE)

import logging
import os
from typing import Any, Dict, Optional
import httpx
from opentelemetry import trace as otel_trace

logger = logging.getLogger("webhook_tracing")

async def call_zapier_webhook(
    event_type: str,
    data: Dict[str, Any],
    cost_estimate: float = 0.0,
    webhook_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call Zapier webhook with automatic tracing.

    Args:
        event_type: Type of event (e.g., "booking_created")
        data: Payload to send to Zapier
        cost_estimate: Estimated cost for this webhook call (USD)
        webhook_url: Optional override for webhook URL

    Returns:
        Response JSON from Zapier

    Raises:
        ToolError: If webhook call fails
    """
    tracer = otel_trace.get_tracer(__name__)
    webhook_url = webhook_url or os.getenv("ZAPIER_WEBHOOK_URL")

    if not webhook_url:
        raise ValueError("ZAPIER_WEBHOOK_URL not configured")

    # Create span with event type in name for easy filtering
    with tracer.start_as_current_span(f"zapier_{event_type}") as span:
        # Enrich span with context attributes
        span.set_attribute("integration.vendor", "zapier")
        span.set_attribute("webhook.event_type", event_type)
        span.set_attribute("webhook.payload_size", len(str(data)))

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=data,
                    timeout=30.0,  # Generous timeout for Zapier processing
                )

            # Enrich with response metadata
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_size", len(response.content))

            if cost_estimate > 0:
                # Add cost tracking if provided
                span.set_attribute("langfuse.cost.total", cost_estimate)
                span.set_attribute("gen_ai.usage.cost", cost_estimate)
                span.set_attribute("webhook.cost_unit", "per_call")

            # Check for errors
            if response.status_code >= 400:
                error_msg = response.text[:500]
                span.set_attribute("http.error_message", error_msg)
                span.set_attribute("error.type", "webhook_error")

                # Use ToolError to signal failure to agent
                from livekit.agents import ToolError
                raise ToolError(
                    f"Zapier webhook failed with status {response.status_code}: {error_msg}"
                )

            span.set_attribute("http.success", True)
            logger.info(f"✅ Zapier webhook succeeded: {event_type}")

            return response.json()

        except httpx.TimeoutException as e:
            span.set_attribute("error.type", "timeout")
            from livekit.agents import ToolError
            raise ToolError(f"Zapier webhook timeout after 30 seconds: {e}")
        except Exception as e:
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e)[:500])
            logger.error(f"❌ Zapier webhook error: {type(e).__name__}: {e}")
            raise
```

Then update your tool:

```python
# In src/agent.py - update book_sales_meeting

@function_tool()
async def book_sales_meeting(
    self,
    context: RunContext,
    customer_name: str,
    customer_email: Optional[str] = None,
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
) -> Dict[str, Any]:
    """Book a sales meeting for qualified users."""

    # ... existing validation and parsing code ...

    try:
        # BEFORE: Google Calendar direct call
        # AFTER: Use Zapier webhook

        # Prepare booking data
        booking_data = {
            "customer_name": customer_name,
            "customer_email": email_to_use,
            "meeting_time": meeting_datetime.isoformat(),
            "meeting_duration_minutes": 30,
            "qualification_signals": self.discovered_signals,
            "source": "voice_agent",
            "timestamp": datetime.now().isoformat(),
        }

        # Call Zapier webhook (now traced automatically)
        from utils.webhook_tracing import call_zapier_webhook

        result = await call_zapier_webhook(
            event_type="booking_created",
            data=booking_data,
            cost_estimate=0.01,  # Estimate: $0.01 per booking
        )

        # Analytics tracking
        self.session_data["tool_calls"].append({
            "tool": "book_sales_meeting",
            "customer_name": customer_name,
            "customer_email": email_to_use,
            "booking_method": "zapier_webhook",  # Track that we used Zapier
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "zapier_response_id": result.get("id"),
        })

        return {
            "booking_status": "confirmed",
            "meeting_time": meeting_datetime.strftime("%A, %B %d at %I:%M %p"),
            "webhook_id": result.get("id"),
            "action": "meeting_booked",
        }

    except Exception as e:
        logger.error(f"Booking failed: {e}")
        # Analytics tracking for failure
        self.session_data["tool_calls"].append({
            "tool": "book_sales_meeting",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": str(e)[:200],
        })
        raise
```

### Integration Checklist

- [ ] Create `/src/utils/webhook_tracing.py` with `call_zapier_webhook()` function
- [ ] Update `book_sales_meeting` to use webhook instead of Google Calendar
- [ ] Add `ZAPIER_WEBHOOK_URL` to LiveKit Cloud secrets
- [ ] Test in console mode: `uv run python src/agent.py console`
- [ ] Verify Langfuse traces show `zapier_booking_created` spans
- [ ] Check that cost attributes appear (`langfuse.cost.total`)
- [ ] Verify tool appears in analytics: `session_data["tool_calls"]` includes booking_method
- [ ] Run tests: `uv run pytest`
- [ ] Deploy and verify in Agent Playground

---

## Part 7: How to Avoid Breaking Observability - Critical Rules

### Rule 1: Always Wrap Enrichment in Try-Catch

Your code does this correctly (line 1532):

```python
try:
    current_span.set_attribute("langfuse.cost.total", llm_cost)
except Exception as e:
    logger.warning(f"Failed to enrich LLM span: {e}")
```

**Why**: If enrichment fails (e.g., span closed), don't crash the agent. Observability errors should never affect agent functionality.

### Rule 2: Check Span is Recording Before Enriching

Your code does this (line 1504):

```python
if current_span and current_span.is_recording():
    try:
        current_span.set_attribute(...)
```

**Why**: Spans close after their timespan completes. Checking `is_recording()` prevents stale span errors.

### Rule 3: Never Modify Tool Input/Output Structure for Observability

**❌ WRONG**:
```python
# Don't do this - changes the tool's return value
return {
    "booking_status": "confirmed",
    "langfuse_span_id": current_span.get_span_context().span_id,  # Wrong!
}
```

**✅ CORRECT**:
```python
# Return only tool-specific data
return {
    "booking_status": "confirmed",
    "meeting_time": "...",
}
# Observability attributes go in OpenTelemetry span, not return value
current_span.set_attribute("booking_reference", reference_id)  # Correct!
```

### Rule 4: Session/User ID Set At Initialization

Your code does this correctly (lines 1340-1342):

```python
trace_provider = setup_observability(
    metadata={"langfuse.session.id": ctx.room.name}
)
```

**Why**: Session ID must be set BEFORE any traces execute, so all spans inherit it.

Then updated when user joins (lines 2024-2030):

```python
set_tracer_provider(trace_provider, metadata={
    "langfuse.session.id": ctx.room.name,
    "langfuse.user.id": user_email,
    ...
})
```

**Why**: Adding user ID mid-session allows retroactive user filtering in Langfuse.

### Rule 5: Use Standard Attribute Names

For third-party integrations, use these standard prefixes:

```python
# Langfuse-specific (for Langfuse UI visibility)
"langfuse.cost.*"
"langfuse.model"
"langfuse.input"
"langfuse.output"
"langfuse.user.id"
"langfuse.session.id"

# OpenTelemetry standards (for cross-tool compatibility)
"gen_ai.usage.cost"
"gen_ai.usage.input_tokens"
"gen_ai.usage.output_tokens"
"gen_ai.request.model"

# HTTP standards (for third-party tools)
"http.url"
"http.method"
"http.status_code"
"http.request_content_length"
"http.response_content_length"

# Custom attributes (use meaningful prefixes)
"integration.vendor"     # What vendor?
"integration.operation"  # What operation?
"webhook.event_type"     # What event?
```

---

## Part 8: Testing Your Langfuse Integration

### Test 1: Verify LiveKit Tool Auto-Tracing

```bash
# 1. Run in console mode
uv run python src/agent.py console

# 2. Start a conversation
# > Hello, can you search for how to integrate Salesforce?

# 3. Check logs for tool execution
# You should see: "INFO ... user said: Hello, can you search..."
# And: "Searching Intercom source (appId: intercom) for query: '...'"

# 4. Wait 30 seconds
# 5. Check Langfuse dashboard
# - Find the session by session ID
# - Look for observations of type TOOL
# - Should see: unleash_search_knowledge (or your tool name)
# - Tool observation should show input/output
```

### Test 2: Verify Cost Attributes

```bash
# 1. Check Langfuse for LLM spans
# - Find a trace with LLM response
# - Click on the generation (GENERATION type) span
# - View the "Attributes" tab
# - Should see:
#   - langfuse.cost.total: 0.000XXX
#   - langfuse.cost.input: 0.000XXX
#   - langfuse.cost.output: 0.000XXX
#   - gen_ai.usage.input_tokens: XXX
#   - gen_ai.usage.output_tokens: XXX
```

### Test 3: Verify User ID Tracking

```bash
# 1. In Agent Playground, start session with email metadata
# 2. Wait for session to complete
# 3. Check Langfuse dashboard
# - Trace should show user ID (email)
# - User profile should be visible (click on user ID)
# - All sessions for that user should be grouped
```

### Test 4: Verify Tool Spans Don't Break

```python
# Add this test to verify tools still work with observability
import pytest
from livekit.agents import RunContext, ToolError

@pytest.mark.asyncio
async def test_tool_tracing_integration():
    """Verify tool calls are traced without breaking functionality"""
    agent = PandaDocTrialistAgent()

    # Mock context
    context = RunContext(room=None, participant=None)

    # Call tool
    result = await agent.unleash_search_knowledge(
        context=context,
        query="How do I create a template?",
        response_format="concise"
    )

    # Verify tool still returns correct structure
    assert isinstance(result, dict)
    assert "answer" in result
    assert "found" in result

    # Tool should work even if tracing fails
    # (because enrichment is wrapped in try-catch)
```

---

## Part 9: Migration Plan: Adding Zapier Without Breaking Observability

### Phase 1: Setup (Day 1)

- [ ] Create `/src/utils/webhook_tracing.py` with helper function
- [ ] Add Zapier webhook URL to `.env.local` for local testing
- [ ] Add `ZAPIER_WEBHOOK_URL` secret to LiveKit Cloud
- [ ] Test webhook URL is reachable (curl test)

### Phase 2: Implement (Day 2)

- [ ] Update `book_sales_meeting` to call Zapier webhook
- [ ] Ensure wrapper handles errors gracefully
- [ ] Update analytics tracking to record webhook usage
- [ ] Add cost tracking if applicable

### Phase 3: Test (Day 3)

- [ ] Run tests: `uv run pytest`
- [ ] Test in console mode with real conversation
- [ ] Verify Langfuse shows new `zapier_booking_created` spans
- [ ] Verify cost attributes appear
- [ ] Verify error handling (test with bad webhook URL)
- [ ] Verify old traces still work (they should)

### Phase 4: Deploy (Day 4)

- [ ] Run `uv run ruff format` and `uv run ruff check`
- [ ] Commit changes to git
- [ ] Deploy: `lk agent deploy`
- [ ] Verify in Agent Playground
- [ ] Monitor logs: `lk agent logs | grep -i zapier`

---

## Summary: Key Takeaways

1. **LiveKit Auto-Traces Tools**: Function tools decorated with `@function_tool()` are automatically traced as TOOL observations in Langfuse. No additional code needed.

2. **Cost Attributes Required**: For LLM and direct provider calls, set `langfuse.cost.*` and `gen_ai.usage.*` attributes via span enrichment in the metrics handler.

3. **HTTP Calls Need Manual Spans**: Zapier webhooks and other HTTP calls require manual span creation using the helper function pattern.

4. **Enrichment is Safe**: Adding attributes to existing spans via `set_attribute()` is safe and won't break traces, provided you:
   - Check span is recording first
   - Wrap in try-catch
   - Don't override existing attributes (add new ones instead)

5. **Best Practice Pattern**: Create a helper function (`call_zapier_webhook`) that:
   - Creates a span with meaningful name
   - Enriches with context attributes
   - Handles errors gracefully
   - Tracks cost if applicable

6. **Verification**: Test in console mode, check Langfuse dashboard for new spans, verify cost attributes appear, and confirm error handling works.

---

## References

### Your Codebase
- `/my-app/src/agent.py` - Agent implementation with tracing
- `/my-app/src/utils/telemetry.py` - OpenTelemetry setup with Langfuse
- `/my-app/src/utils/cost_tracking.py` - Cost calculation utilities
- `/my-app/src/utils/analytics_queue.py` - Analytics integration

### LiveKit Documentation
- [LiveKit Agents Metrics/Tracing](https://docs.livekit.io/agents/build/metrics/)
- [LiveKit Agents Function Tools](https://docs.livekit.io/agents/build/function-tools/)
- [LiveKit Agents Events](https://docs.livekit.io/agents/build/events/)

### OpenTelemetry/Langfuse
- [Langfuse Integration](https://langfuse.com/integrations/frameworks/livekit)
- [OpenTelemetry Span Attributes](https://opentelemetry.io/docs/specs/otel/trace/semantic_conventions/)
- [Langfuse Cost Tracking](https://langfuse.com/docs/model-usage-and-cost/)

### Your Documentation
- `/my-app/docs/LANGFUSE_INTEGRATION_REVIEW.md` - Integration verification
- `/my-app/docs/LLM_SPAN_ENRICHMENT.md` - Span enrichment patterns
- `/docs/implementation/observability/LANGFUSE_RESEARCH_SUMMARY.md` - Comprehensive research

---

**Document Generated**: 2025-10-31
**Research Scope**: Langfuse observability with LiveKit Agents and Zapier integration
**Confidence Level**: High - Based on code analysis, official documentation, and production implementation
**Status**: Complete and ready for implementation
