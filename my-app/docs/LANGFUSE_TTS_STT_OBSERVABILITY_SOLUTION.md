# Langfuse TTS/STT Observability Solution

## Executive Summary

**Root Cause**: Langfuse Model Usage dashboard only displays "generation" type observations, but LiveKit creates generic "span" type observations for TTS/STT. Your cost enrichment adds attributes to these generic spans, which Langfuse ignores for Model Usage tracking.

**Solution**: Create separate "generation" spans with standard OpenTelemetry attributes that Langfuse recognizes for model usage tracking.

## The Problem: Why TTS/STT Don't Appear in Model Usage

### What's Happening Now
```
LiveKit Creates → Generic "span" observations (tts_node, stt_node)
You Enrich → Add langfuse.* attributes to these spans
Langfuse → Ignores these for Model Usage (only looks at "generation" type)
Result → Only gpt-4.1-mini appears (special-cased by Langfuse)
```

### Why Only GPT-4 mini Shows Up
- OpenAI models are pre-registered in Langfuse's model registry
- Langfuse special-cases OpenAI model names even on generic spans
- Custom models like "Cartesia-3" and "deepgram-nova-2" aren't recognized

## The Solution: Create Generation Spans

### Implementation Approach

Instead of enriching LiveKit's existing spans, create new "generation" type spans that Langfuse Model Usage understands:

```python
# In agent.py - Enhanced metrics handler
import base64
import json
from opentelemetry import trace
from opentelemetry.trace import SpanKind

@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    """Handle metrics and create Langfuse-compatible generation spans."""
    metrics = ev.metrics
    tracer = trace.get_tracer(__name__)

    # Get session context for linking
    session_id = ctx.room.name if hasattr(ctx, 'room') else "unknown"
    user_id = getattr(ctx, 'user_id', None)

    # TTS Metrics → Generation Span
    if isinstance(metrics, TTSMetrics):
        with tracer.start_as_current_span(
            "tts_generation",
            kind=SpanKind.INTERNAL
        ) as span:
            # CRITICAL: Use gen_ai.* attributes for Model Usage visibility
            span.set_attribute("gen_ai.request.model", "Cartesia-3")
            span.set_attribute("gen_ai.usage.input_tokens", metrics.characters_count)
            # Audio duration in ms as proxy for output tokens
            span.set_attribute("gen_ai.usage.output_tokens", int(metrics.audio_duration * 1000))

            # Calculate cost
            tts_cost = metrics.characters_count * agent.provider_pricing["cartesia_sonic"]
            span.set_attribute("gen_ai.usage.cost", tts_cost)

            # Session linking
            span.set_attribute("langfuse.session.id", session_id)
            if user_id:
                span.set_attribute("langfuse.user.id", user_id)

            # Provider metadata
            span.set_attribute("tts.provider", "cartesia")
            span.set_attribute("tts.audio_duration_seconds", metrics.audio_duration)
            span.set_attribute("tts.characters", metrics.characters_count)
            span.set_attribute("tts.ttfb_seconds", metrics.ttfb)

            # Mark as generation for Langfuse
            span.set_attribute("langfuse.observation.type", "generation")

            logger.info(f"📊 TTS Cost: ${tts_cost:.6f} ({metrics.characters_count} chars)")

    # STT Metrics → Generation Span
    elif isinstance(metrics, STTMetrics):
        with tracer.start_as_current_span(
            "stt_generation",
            kind=SpanKind.INTERNAL
        ) as span:
            # CRITICAL: Use gen_ai.* attributes
            span.set_attribute("gen_ai.request.model", "deepgram-nova-2")

            # Normalize audio seconds to token-like units for consistency
            # Use 1 second = 100 tokens as normalization factor
            input_tokens = int(metrics.audio_duration * 100)
            span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
            span.set_attribute("gen_ai.usage.output_tokens", 0)  # STT has no output tokens

            # Calculate cost (Deepgram charges per minute)
            stt_minutes = metrics.audio_duration / 60.0
            stt_cost = stt_minutes * agent.provider_pricing["deepgram_nova2"]
            span.set_attribute("gen_ai.usage.cost", stt_cost)

            # Session linking
            span.set_attribute("langfuse.session.id", session_id)
            if user_id:
                span.set_attribute("langfuse.user.id", user_id)

            # Provider metadata
            span.set_attribute("stt.provider", "deepgram")
            span.set_attribute("stt.audio_duration_seconds", metrics.audio_duration)
            span.set_attribute("stt.duration_seconds", metrics.duration)

            # Mark as generation
            span.set_attribute("langfuse.observation.type", "generation")

            logger.info(f"📊 STT Cost: ${stt_cost:.6f} ({metrics.audio_duration:.2f}s)")

    # LLM Metrics → Enhance existing span
    elif isinstance(metrics, LLMMetrics):
        # LLM already tracked, but enhance with cost
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            # Standard attributes
            current_span.set_attribute("gen_ai.request.model", "gpt-4.1-mini")
            current_span.set_attribute("gen_ai.usage.input_tokens", metrics.prompt_tokens)
            current_span.set_attribute("gen_ai.usage.output_tokens", metrics.completion_tokens)

            # Calculate cost
            input_cost = metrics.prompt_tokens * agent.provider_pricing["gpt_4_mini_input"]
            output_cost = metrics.completion_tokens * agent.provider_pricing["gpt_4_mini_output"]
            total_cost = input_cost + output_cost
            current_span.set_attribute("gen_ai.usage.cost", total_cost)

            # Session linking
            current_span.set_attribute("langfuse.session.id", session_id)

            logger.info(f"📊 LLM Cost: ${total_cost:.6f} ({metrics.total_tokens} tokens)")
```

## Critical Configuration Requirements

### 1. Register Custom Models in Langfuse

Navigate to Langfuse Project Settings and add custom model definitions:

#### Cartesia-3 (TTS)
- **Model Name**: `Cartesia-3`
- **Match Pattern**: `(?i)^cartesia[-_]3$`
- **Unit**: `CHARACTERS`
- **Input Price**: `0.00000006` (per character)
- **Tokenizer**: `None` or `Custom`

#### deepgram-nova-2 (STT)
- **Model Name**: `deepgram-nova-2`
- **Match Pattern**: `(?i)^deepgram[-_]nova[-_]2$`
- **Unit**: `TOKENS` (we normalize seconds to tokens)
- **Input Price**: `0.00000072` (per token, where 1 second = 100 tokens)
- **Tokenizer**: `None` or `Custom`

### 2. OpenTelemetry Attribute Standards

Langfuse Model Usage specifically looks for these attributes:

```python
# Required for Model Usage visibility
"gen_ai.request.model"      # Model identifier
"gen_ai.usage.input_tokens"  # Input usage
"gen_ai.usage.output_tokens" # Output usage (0 for STT)

# Optional but recommended
"gen_ai.usage.cost"          # Total cost in USD
"langfuse.session.id"        # For session grouping
"langfuse.user.id"           # For user attribution
"langfuse.observation.type"  # Set to "generation"
```

## Enhanced Observability Features

### 1. Custom Dashboard Spans

Create additional spans for better debugging:

```python
# Create debug span for cost breakdown
with tracer.start_as_current_span("cost_breakdown") as span:
    span.set_attribute("session.total_cost", agent.session_costs["total_estimated_cost"])
    span.set_attribute("session.llm_cost", agent.session_costs["llm_cost"])
    span.set_attribute("session.tts_cost", agent.session_costs["cartesia_cost"])
    span.set_attribute("session.stt_cost", agent.session_costs["deepgram_cost"])
    span.set_attribute("session.duration_seconds", time.time() - session_start_time)
```

### 2. Metrics Aggregation

Track cumulative metrics per session:

```python
# Initialize in agent setup
agent.session_metrics = {
    "tts_characters_total": 0,
    "stt_seconds_total": 0,
    "llm_tokens_total": 0,
    "turns_count": 0,
    "errors_count": 0
}

# Update in metrics handler
if isinstance(metrics, TTSMetrics):
    agent.session_metrics["tts_characters_total"] += metrics.characters_count
    agent.session_metrics["turns_count"] += 1
```

### 3. Error Tracking

Add error spans for failed operations:

```python
try:
    # TTS/STT operation
    pass
except Exception as e:
    with tracer.start_as_current_span("error") as span:
        span.set_attribute("error.type", type(e).__name__)
        span.set_attribute("error.message", str(e))
        span.set_attribute("error.component", "tts" if is_tts else "stt")
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
```

## Testing & Verification

### 1. Test Generation Span Creation

```python
# Test script - test_langfuse_spans.py
import asyncio
from livekit.agents import metrics

async def test_span_creation():
    # Simulate TTS metrics
    tts_metrics = metrics.TTSMetrics(
        ttfb=0.5,
        duration=2.0,
        characters_count=100,
        audio_duration=3.0,
        cancelled=False,
        label="test_tts"
    )

    # Trigger metrics handler
    ev = metrics.MetricsCollectedEvent(metrics=tts_metrics)
    await _on_metrics_collected(ev)

    print("✅ Check Langfuse for 'tts_generation' span")

asyncio.run(test_span_creation())
```

### 2. Verify in Langfuse UI

1. Run a test session with your agent
2. Navigate to Langfuse → Traces
3. Look for new span types: `tts_generation`, `stt_generation`
4. Check Model Usage dashboard after 2-3 minutes
5. Verify `Cartesia-3` and `deepgram-nova-2` appear with costs

### 3. Debugging Commands

```bash
# Check if spans are being created
lk agent logs | grep -E "TTS Cost:|STT Cost:|LLM Cost:"

# Verify OpenTelemetry export
lk agent logs | grep -E "OTLP|otel|trace"

# Check for errors
lk agent logs | grep -E "ERROR|Failed|Exception" | tail -20
```

## Common Issues & Solutions

### Issue 1: Models Still Not Appearing

**Solution**: Check model registration in Langfuse:
1. Go to Project Settings → Models
2. Verify custom models are registered
3. Check match patterns are correct
4. Ensure pricing is set

### Issue 2: Costs Not Calculating

**Solution**: Verify pricing configuration:
```python
# Add debug logging
logger.info(f"Pricing config: {agent.provider_pricing}")
logger.info(f"TTS chars: {metrics.characters_count}, rate: {agent.provider_pricing.get('cartesia_sonic', 'MISSING')}")
```

### Issue 3: Spans Not Linking to Sessions

**Solution**: Ensure session ID is available:
```python
# Get session ID safely
session_id = None
if hasattr(ctx, 'room'):
    session_id = ctx.room.name
elif hasattr(agent, 'session_id'):
    session_id = agent.session_id
else:
    session_id = f"session_{int(time.time())}"

span.set_attribute("langfuse.session.id", session_id)
```

## Migration Path

### Step 1: Add Generation Span Creation (Priority)
1. Update `_on_metrics_collected` with the code above
2. Deploy and test with a single session
3. Verify spans appear in Langfuse

### Step 2: Register Models in Langfuse
1. Add Cartesia-3 and deepgram-nova-2 to Langfuse
2. Set correct pricing per unit
3. Test Model Usage dashboard

### Step 3: Remove Old Span Enrichment
1. Comment out old `current_span.set_attribute()` calls
2. Keep only the new generation span creation
3. Clean up `cost_tracking.py` if needed

### Step 4: Add Enhanced Observability
1. Implement session metrics aggregation
2. Add error tracking spans
3. Create custom dashboards in Langfuse

## Expected Outcome

After implementation, your Langfuse Model Usage dashboard will show:

```
Model Usage
├── gpt-4.1-mini     (LLM - already working)
├── Cartesia-3       (TTS - NEW)
└── deepgram-nova-2  (STT - NEW)

Each with:
- Token/character usage graphs
- Cost breakdowns
- Session attribution
- Time-series trends
```

## Files to Update

1. **Primary**: `/my-app/src/agent.py`
   - Replace `_on_metrics_collected` handler (lines 1358-1545)
   - Add generation span creation logic

2. **Optional**: `/my-app/src/utils/telemetry.py`
   - Already configured correctly for OpenTelemetry

3. **Optional**: `/my-app/src/utils/cost_tracking.py`
   - Can be simplified to just calculate costs (no span creation)

## Next Steps

1. **Immediate**: Update `agent.py` with generation span creation
2. **Today**: Register custom models in Langfuse UI
3. **Test**: Run agent and verify Model Usage dashboard
4. **Optimize**: Add session aggregation and error tracking
5. **Document**: Update team docs with new observability pattern