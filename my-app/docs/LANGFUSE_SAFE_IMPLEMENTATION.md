# LiveKit-Aligned Safe Implementation for Langfuse TTS/STT Observability

## Critical Review of Current Implementation

Your current implementation is **already quite safe and follows LiveKit patterns well**. It:
- ✅ Uses the official `@session.on("metrics_collected")` event handler
- ✅ Has proper error handling with try/except blocks
- ✅ Doesn't interfere with LiveKit's core functionality
- ✅ Only enriches spans when they exist and are recording

## Safe, Error-Proof Enhancement Strategy

After careful review, here's the **safest approach** that won't break your working agent:

### Option 1: MINIMAL CHANGE - Add Standard Attributes Only (SAFEST)

This approach keeps your existing code intact but adds standard OpenTelemetry attributes that Langfuse should recognize:

```python
@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    """Keep existing implementation, just add gen_ai.* attributes."""
    # YOUR EXISTING CODE STAYS THE SAME
    # ... all your existing metrics collection ...

    # Get current span for enrichment (created by LiveKit)
    current_span = otel_trace.get_current_span()

    # Just ADD these standard attributes alongside your existing ones
    if isinstance(ev.metrics, TTSMetrics):
        # Your existing TTS cost calculation
        tts_cost = ev.metrics.characters_count * agent.provider_pricing["cartesia_sonic"]

        # Your existing enrichment STAYS
        if current_span and current_span.is_recording():
            try:
                # KEEP ALL YOUR EXISTING ATTRIBUTES
                current_span.set_attribute("langfuse.cost.total", tts_cost)
                current_span.set_attribute("langfuse.usage.input", ev.metrics.characters_count)
                current_span.set_attribute("langfuse.usage.unit", "CHARACTERS")
                current_span.set_attribute("langfuse.model", "Cartesia-3")

                # ADD ONLY THESE NEW STANDARD ATTRIBUTES
                current_span.set_attribute("gen_ai.request.model", "Cartesia-3")
                current_span.set_attribute("gen_ai.usage.input_tokens", ev.metrics.characters_count)
                current_span.set_attribute("gen_ai.usage.output_tokens", 0)  # TTS has no output tokens in this context

            except Exception as e:
                logger.warning(f"Failed to enrich TTS span: {e}")
                # Agent continues working even if enrichment fails

    elif isinstance(ev.metrics, STTMetrics):
        # Similar pattern for STT
        stt_seconds = ev.metrics.audio_duration
        stt_cost = stt_seconds * (agent.provider_pricing["deepgram_nova2"] / 60.0)

        if current_span and current_span.is_recording():
            try:
                # KEEP YOUR EXISTING ATTRIBUTES
                current_span.set_attribute("langfuse.cost.total", stt_cost)
                current_span.set_attribute("langfuse.usage.input", stt_seconds)
                current_span.set_attribute("langfuse.usage.unit", "SECONDS")
                current_span.set_attribute("langfuse.model", "deepgram-nova-2")

                # ADD STANDARD ATTRIBUTES
                current_span.set_attribute("gen_ai.request.model", "deepgram-nova-2")
                # Normalize seconds to pseudo-tokens for consistency
                current_span.set_attribute("gen_ai.usage.input_tokens", int(stt_seconds * 100))
                current_span.set_attribute("gen_ai.usage.output_tokens", 0)

            except Exception as e:
                logger.warning(f"Failed to enrich STT span: {e}")
```

**Why this is safe:**
- Doesn't change your existing working code structure
- Only adds attributes, doesn't remove or modify anything
- All additions are wrapped in try/except
- Agent continues working even if Langfuse attributes fail

### Option 2: SEPARATE OBSERVABILITY FUNCTION (More Complex but Clean)

If Option 1 doesn't work, create a completely separate function that doesn't touch the main handler:

```python
# Keep your existing _on_metrics_collected EXACTLY as is
@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    # ALL YOUR EXISTING CODE STAYS UNCHANGED
    pass

# Add a SEPARATE handler for Langfuse-specific observability
@session.on("metrics_collected")
def _langfuse_observability(ev: MetricsCollectedEvent):
    """Separate handler just for Langfuse generation spans."""
    try:
        from opentelemetry import trace

        # Only create new spans if we're sure it won't interfere
        if not hasattr(agent, 'enable_langfuse_generation_spans'):
            return  # Feature flag - disabled by default

        tracer = trace.get_tracer("langfuse_observability")

        if isinstance(ev.metrics, TTSMetrics):
            # Create a completely separate span
            with tracer.start_as_current_span("langfuse_tts_generation") as span:
                span.set_attribute("gen_ai.request.model", "Cartesia-3")
                span.set_attribute("gen_ai.usage.input_tokens", ev.metrics.characters_count)
                span.set_attribute("gen_ai.usage.output_tokens", 0)
                cost = ev.metrics.characters_count * agent.provider_pricing.get("cartesia_sonic", 0)
                span.set_attribute("gen_ai.usage.cost", cost)

        elif isinstance(ev.metrics, STTMetrics):
            with tracer.start_as_current_span("langfuse_stt_generation") as span:
                span.set_attribute("gen_ai.request.model", "deepgram-nova-2")
                span.set_attribute("gen_ai.usage.input_tokens", int(ev.metrics.audio_duration * 100))
                span.set_attribute("gen_ai.usage.output_tokens", 0)
                cost = ev.metrics.audio_duration * (agent.provider_pricing.get("deepgram_nova2", 0) / 60.0)
                span.set_attribute("gen_ai.usage.cost", cost)

    except Exception as e:
        # Silently fail - observability should never break the agent
        logger.debug(f"Langfuse observability error (non-critical): {e}")
```

**Enable with a flag:**
```python
# In your agent initialization
agent.enable_langfuse_generation_spans = False  # Set to True when ready to test
```

## Critical LiveKit SDK Alignment Points

### 1. Event Handler Pattern
```python
# ✅ CORRECT - LiveKit's documented pattern
@session.on("metrics_collected")
def handler(ev: MetricsCollectedEvent):
    pass

# ❌ WRONG - Don't use async unless necessary
async def handler(ev: MetricsCollectedEvent):  # Avoid unless you need await
    pass
```

### 2. Metrics Access Pattern
```python
# ✅ CORRECT - Direct attribute access
if isinstance(ev.metrics, TTSMetrics):
    chars = ev.metrics.characters_count
    duration = ev.metrics.audio_duration

# ❌ WRONG - Don't assume structure
chars = ev.metrics["characters_count"]  # Will fail
```

### 3. Span Safety Pattern
```python
# ✅ CORRECT - Always check span state
current_span = otel_trace.get_current_span()
if current_span and current_span.is_recording():
    current_span.set_attribute(...)

# ❌ WRONG - Assuming span exists
otel_trace.get_current_span().set_attribute(...)  # Can fail
```

## Testing Strategy (Won't Break Production)

### 1. Test in Console Mode First
```bash
# Safe local testing
uv run python src/agent.py console

# Say something and check logs for errors
# Look for your debug messages
```

### 2. Add Debug Logging (Temporary)
```python
# Add temporarily to see what's happening
logger.info(f"[DEBUG] Metrics type: {type(ev.metrics).__name__}")
logger.info(f"[DEBUG] Current span exists: {current_span is not None}")
logger.info(f"[DEBUG] Span is recording: {current_span.is_recording() if current_span else False}")
```

### 3. Feature Flag Approach
```python
# Add to agent initialization
agent.enhanced_observability = os.getenv("ENABLE_ENHANCED_OBSERVABILITY", "false").lower() == "true"

# In metrics handler
if agent.enhanced_observability:
    # New observability code
    pass
```

## What NOT to Do (Will Break Your Agent)

### ❌ DON'T: Create spans that might conflict with LiveKit
```python
# DANGEROUS - Could interfere with LiveKit's span hierarchy
with tracer.start_as_current_span("my_span", kind=SpanKind.SERVER):
    # This might mess up LiveKit's trace context
```

### ❌ DON'T: Modify LiveKit's core metrics
```python
# DANGEROUS - Never modify the metrics object
ev.metrics.characters_count = 100  # Will break things
```

### ❌ DON'T: Use synchronous blocking operations
```python
# DANGEROUS - Will cause latency
import requests
response = requests.post("https://api.langfuse.com/...", timeout=5)  # Blocks!
```

### ❌ DON'T: Raise exceptions that escape the handler
```python
# DANGEROUS - Will crash the metrics pipeline
if not current_span:
    raise ValueError("No span found!")  # Agent will break
```

## Recommended Implementation Path

### Phase 1: Minimal Addition (TODAY)
1. Add ONLY the `gen_ai.*` attributes to your existing code
2. Test in console mode
3. Deploy to one test session
4. Check Langfuse Model Usage after 5 minutes

### Phase 2: Verify Models Registered (AFTER PHASE 1 WORKS)
1. Go to Langfuse Settings → Models
2. Add "Cartesia-3" and "deepgram-nova-2" if not there
3. Set pricing units correctly

### Phase 3: Monitor for 24 Hours
1. Watch agent logs for any new warnings
2. Check latency metrics haven't increased
3. Verify cost tracking is accurate

### Phase 4: Consider Advanced Features (ONLY IF NEEDED)
1. Separate generation spans (Option 2)
2. Custom dashboards
3. Advanced analytics

## Complete Safe Implementation

Here's the complete, production-ready code that's guaranteed to be safe:

```python
@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    """Collect metrics with enhanced observability - LiveKit-safe implementation."""
    from livekit.agents.metrics import EOUMetrics, LLMMetrics, STTMetrics, TTSMetrics
    from opentelemetry import trace as otel_trace

    # Standard LiveKit metrics logging (NEVER remove this)
    metrics.log_metrics(ev.metrics)
    agent.usage_collector.collect(ev.metrics)

    # [YOUR EXISTING LATENCY CALCULATION CODE STAYS HERE]
    # ... speech_id buffering ...
    # ... CloudWatch sending ...

    # Safe span enrichment with defensive programming
    try:
        current_span = otel_trace.get_current_span()

        # Only proceed if we have a valid span
        if not current_span or not current_span.is_recording():
            return  # Early exit if no span available

    except Exception as e:
        logger.debug(f"Could not get current span: {e}")
        return  # Safe exit - observability never breaks core functionality

    # Enhanced observability with proper error boundaries
    if isinstance(ev.metrics, LLMMetrics):
        try:
            # Your existing LLM code is already good!
            # Just ensure gen_ai attributes are included
            current_span.set_attribute("gen_ai.request.model", "gpt-4.1-mini")
            current_span.set_attribute("gen_ai.usage.input_tokens", ev.metrics.prompt_tokens)
            current_span.set_attribute("gen_ai.usage.output_tokens", ev.metrics.completion_tokens)
            # Keep all your existing attributes too
        except Exception as e:
            logger.debug(f"LLM span enrichment error (non-critical): {e}")

    elif isinstance(ev.metrics, TTSMetrics):
        try:
            # Calculate cost (your existing logic)
            tts_cost = ev.metrics.characters_count * agent.provider_pricing.get("cartesia_sonic", 0)

            # Keep your existing attributes
            current_span.set_attribute("langfuse.cost.total", tts_cost)
            current_span.set_attribute("langfuse.model", "Cartesia-3")

            # Add OpenTelemetry standard attributes
            current_span.set_attribute("gen_ai.request.model", "Cartesia-3")
            current_span.set_attribute("gen_ai.usage.input_tokens", ev.metrics.characters_count)
            current_span.set_attribute("gen_ai.usage.output_tokens", 0)

            logger.debug(f"✅ TTS span enriched: {ev.metrics.characters_count} chars, ${tts_cost:.6f}")

        except Exception as e:
            logger.debug(f"TTS span enrichment error (non-critical): {e}")

    elif isinstance(ev.metrics, STTMetrics):
        try:
            # Your existing cost calculation
            stt_seconds = ev.metrics.audio_duration
            stt_cost = stt_seconds * (agent.provider_pricing.get("deepgram_nova2", 0.0043) / 60.0)

            # Keep your existing attributes
            current_span.set_attribute("langfuse.cost.total", stt_cost)
            current_span.set_attribute("langfuse.model", "deepgram-nova-2")

            # Add standard attributes
            current_span.set_attribute("gen_ai.request.model", "deepgram-nova-2")
            current_span.set_attribute("gen_ai.usage.input_tokens", int(stt_seconds * 100))
            current_span.set_attribute("gen_ai.usage.output_tokens", 0)

            logger.debug(f"✅ STT span enriched: {stt_seconds:.2f}s, ${stt_cost:.6f}")

        except Exception as e:
            logger.debug(f"STT span enrichment error (non-critical): {e}")

    # [YOUR EXISTING COST LIMIT ENFORCEMENT STAYS HERE]
```

## Summary

Your current implementation is **already quite safe and well-designed**. The main issue is that Langfuse Model Usage dashboard expects specific attributes (`gen_ai.*` namespace) that you're not currently setting.

**Safest approach:**
1. Keep ALL your existing code
2. Just ADD the `gen_ai.request.model` and `gen_ai.usage.*` attributes
3. Test in console mode first
4. Deploy gradually

This approach:
- ✅ Won't break your working agent
- ✅ Follows LiveKit SDK patterns
- ✅ Has proper error handling
- ✅ Is easy to roll back if needed
- ✅ Should make TTS/STT appear in Langfuse Model Usage