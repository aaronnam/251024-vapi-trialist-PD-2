# Fix: Making TTS/STT Costs Visible in Langfuse Model Usage (LiveKit-Aligned)

## Problem Summary
Only `gpt-4.1-mini` costs appear in Langfuse Model Usage dashboard because:
- Langfuse only tracks costs for "generation" and "embedding" observation types
- LiveKit automatically creates spans via OpenTelemetry, but they lack cost attributes
- Langfuse doesn't have built-in model definitions for Deepgram, Cartesia, etc.

## Root Cause Analysis

**LiveKit already creates the spans automatically** via OpenTelemetry integration:
- ✅ `llm_request` spans (with `gen_ai.request.model` attributes)
- ✅ `tts_request` spans (visible in your traces)
- ✅ STT spans (may exist but not visible in trace list)

**The issue**: These spans are missing:
1. Cost calculation attributes (`langfuse.cost.total`)
2. Model names that match Langfuse definitions (`langfuse.model`)

**Your current `cost_tracking.py`** creates separate custom spans (`stt_usage`, `tts_usage`), which are redundant and don't appear in Model Usage because they're not "generation" type observations.

---

## Correct Solution (Aligned with LiveKit Architecture)

### Overview

**DON'T**: Create new spans with Langfuse SDK
**DO**: Enrich LiveKit's existing spans with cost attributes

This approach:
- ✅ Works with LiveKit's automatic OpenTelemetry integration
- ✅ No duplicate spans
- ✅ No conflicts with LiveKit's architecture
- ✅ Minimal code changes

---

## Step 1: Add Custom Model Definitions in Langfuse UI

### Cartesia Sonic-3 (TTS)

Configure in Langfuse UI:

```
Model Name: Cartesia-3
Match Pattern: (?i)^(cartesia[-_]3|cartesia[-_]sonic[-_]3)$
Usage type "input": 0.00000006    # $60 per 1M chars = $0.00000006 per char
Tokenizer: None
```

**Important notes:**
- ✅ Use only "input" usage type (TTS cost is based on input characters only)
- ✅ Match pattern uses `[-_]` not `[_-]` or `[3]` (Postgres regex syntax)
- ✅ Price should match your code: `0.06 / 1000000 = 0.00000006` per character
- ❌ Don't add "output" usage type - it's not used for TTS

### Deepgram Nova-2 (STT)

Configure in Langfuse UI:

```
Model Name: deepgram-nova-2
Match Pattern: (?i)^(deepgram[-_]nova[-_]2)$
Usage type "input": 0.00007167    # $0.0043 per minute ÷ 60 seconds = $0.00007167 per second
Tokenizer: None
```

**Important notes:**
- ✅ Use only "input" usage type (STT cost is based on input audio duration only)
- ✅ Match pattern uses `[-_]` not `[_-]` (Postgres regex syntax)
- ✅ Price should be per **second** not per minute, because LiveKit metrics report `audio_duration` in **seconds**
- ✅ Calculation: `$0.0043 / 60 = $0.00007167` per second
- ❌ Don't add "output" usage type - it's not used for STT

**Important**: Langfuse's "Prices" are **per unit**. For STT (seconds) and TTS (characters), you'll set the usage count in your code, and Langfuse multiplies by this price.

---

## Step 2: Update `agent.py` to Enrich LiveKit's Spans

### Current Code (Lines 1441-1534)

Your current implementation creates costs but doesn't add them to LiveKit's spans properly.

### Updated Code

Replace the metrics handler in `agent.py` (lines 1358-1545) with this enhanced version:

```python
@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    """Collect metrics, track costs, and enrich spans for Langfuse observability."""
    from livekit.agents.metrics import EOUMetrics, LLMMetrics, STTMetrics, TTSMetrics
    from opentelemetry import trace as otel_trace

    # Standard metrics logging
    metrics.log_metrics(ev.metrics)
    agent.usage_collector.collect(ev.metrics)

    # Get current span (created by LiveKit)
    current_span = otel_trace.get_current_span()

    # Get speech_id if available
    speech_id = getattr(ev.metrics, "speech_id", None)

    # Buffer metrics for latency calculation
    if speech_id:
        if speech_id not in metrics_buffer:
            metrics_buffer[speech_id] = {}

        if isinstance(ev.metrics, EOUMetrics):
            metrics_buffer[speech_id]["eou"] = ev.metrics
        elif isinstance(ev.metrics, LLMMetrics):
            metrics_buffer[speech_id]["llm"] = ev.metrics
        elif isinstance(ev.metrics, TTSMetrics):
            metrics_buffer[speech_id]["tts"] = ev.metrics

        # Calculate total latency when we have all three
        turn_metrics = metrics_buffer[speech_id]
        if "eou" in turn_metrics and "llm" in turn_metrics and "tts" in turn_metrics:
            total_latency = (
                turn_metrics["eou"].end_of_utterance_delay
                + (turn_metrics["llm"].ttft or 0)
                + (turn_metrics["tts"].ttfb or 0)
            )

            # Send to CloudWatch
            metric_data = {
                "_event_type": "voice_metrics",
                "_timestamp": datetime.now().isoformat(),
                "_session_id": ctx.room.name,
                "_speech_id": speech_id,
                "total_latency": total_latency,
                "eou_delay": turn_metrics["eou"].end_of_utterance_delay,
                "llm_ttft": turn_metrics["llm"].ttft,
                "tts_ttfb": turn_metrics["tts"].ttfb,
            }

            if total_latency > 1.5:
                logger.warning(
                    f"⚠️ High latency: {total_latency:.2f}s "
                    f"(EOU: {turn_metrics['eou'].end_of_utterance_delay:.2f}s, "
                    f"LLM: {turn_metrics['llm'].ttft:.2f}s, "
                    f"TTS: {turn_metrics['tts'].ttfb:.2f}s)"
                )

            try:
                send_to_analytics_queue(metric_data)
            except Exception as e:
                logger.error(f"Failed to send metrics to analytics queue: {e}")

            del metrics_buffer[speech_id]

    # ============================================================================
    # ENRICH LIVEKIT'S SPANS WITH COST ATTRIBUTES (for Langfuse Model Usage)
    # ============================================================================

    if isinstance(ev.metrics, LLMMetrics):
        # Calculate LLM costs
        input_cost = ev.metrics.prompt_tokens * agent.provider_pricing["openai_gpt4_mini_input"]
        output_cost = ev.metrics.completion_tokens * agent.provider_pricing["openai_gpt4_mini_output"]
        llm_cost = input_cost + output_cost

        # Update session costs
        agent.session_costs["openai_tokens"] += ev.metrics.total_tokens
        agent.session_costs["openai_cost"] += llm_cost
        agent.session_costs["total_estimated_cost"] += llm_cost

        # Enrich LiveKit's existing llm_request span
        if current_span and current_span.is_recording():
            try:
                # Cost attributes (Langfuse Model Usage uses these)
                current_span.set_attribute("langfuse.cost.total", llm_cost)
                current_span.set_attribute("langfuse.cost.input", input_cost)
                current_span.set_attribute("langfuse.cost.output", output_cost)

                # OpenTelemetry standard attributes (best practice)
                current_span.set_attribute("gen_ai.usage.cost", llm_cost)

                # Model name (should already be set by LiveKit, but ensure it's there)
                current_span.set_attribute("langfuse.model", "gpt-4.1-mini")

                # Performance metrics
                current_span.set_attribute("llm.ttft", ev.metrics.ttft or 0)
                current_span.set_attribute("llm.duration", ev.metrics.duration or 0)
                current_span.set_attribute("llm.tokens_per_second", ev.metrics.tokens_per_second or 0)
                current_span.set_attribute("llm.prompt_cached_tokens", ev.metrics.prompt_cached_tokens or 0)

                logger.debug(
                    f"✅ Enriched LLM span with cost: ${llm_cost:.6f} "
                    f"(prompt: {ev.metrics.prompt_tokens}, completion: {ev.metrics.completion_tokens})"
                )
            except Exception as e:
                logger.warning(f"Failed to enrich LLM span: {e}")

        # Enrich with conversation context (existing code)
        try:
            conversation_input = format_conversation_history(session.history)
            if current_span and current_span.is_recording():
                current_span.set_attribute("langfuse.input", conversation_input)
                message_count = len(session.history.items) if hasattr(session.history, 'items') else 0
                current_span.set_attribute("llm.messages.count", message_count)
        except Exception as e:
            logger.warning(f"Failed to enrich LLM span with conversation context: {e}")

    elif isinstance(ev.metrics, STTMetrics):
        # Calculate STT costs
        # Note: LiveKit reports audio_duration in SECONDS
        # Deepgram pricing is $0.0043 per minute = $0.00007167 per second
        stt_seconds = ev.metrics.audio_duration  # Already in seconds
        stt_cost = stt_seconds * (agent.provider_pricing["deepgram_nova2"] / 60.0)  # Convert $/min to $/sec

        # Update session costs (keep minutes for session tracking)
        stt_minutes = stt_seconds / 60.0
        agent.session_costs["deepgram_minutes"] += stt_minutes
        agent.session_costs["deepgram_cost"] += stt_cost
        agent.session_costs["total_estimated_cost"] += stt_cost

        # Enrich LiveKit's existing STT span
        if current_span and current_span.is_recording():
            try:
                # Cost attributes
                current_span.set_attribute("langfuse.cost.total", stt_cost)

                # Usage details - Langfuse needs "input" usage type IN SECONDS
                # Important: Use seconds, not minutes, to match Langfuse model definition
                current_span.set_attribute("langfuse.usage.input", stt_seconds)
                current_span.set_attribute("langfuse.usage.unit", "SECONDS")

                # Model name for Langfuse matching
                current_span.set_attribute("langfuse.model", "deepgram-nova-2")

                # Performance metrics
                current_span.set_attribute("stt.duration", ev.metrics.duration or 0)
                current_span.set_attribute("stt.audio_duration", ev.metrics.audio_duration)
                current_span.set_attribute("stt.streamed", ev.metrics.streamed)

                logger.debug(
                    f"✅ Enriched STT span with cost: ${stt_cost:.6f} ({stt_seconds:.2f} seconds, {stt_minutes:.2f} minutes)"
                )
            except Exception as e:
                logger.warning(f"Failed to enrich STT span: {e}")

    elif isinstance(ev.metrics, TTSMetrics):
        # Calculate TTS costs
        tts_cost = ev.metrics.characters_count * agent.provider_pricing["cartesia_sonic"]

        # Update session costs
        agent.session_costs["cartesia_characters"] += ev.metrics.characters_count
        agent.session_costs["cartesia_cost"] += tts_cost
        agent.session_costs["total_estimated_cost"] += tts_cost

        # Enrich LiveKit's existing tts_request span
        if current_span and current_span.is_recording():
            try:
                # Cost attributes
                current_span.set_attribute("langfuse.cost.total", tts_cost)

                # Usage details - Langfuse needs "input" usage type
                current_span.set_attribute("langfuse.usage.input", ev.metrics.characters_count)
                current_span.set_attribute("langfuse.usage.unit", "CHARACTERS")

                # Model name for Langfuse matching (match your custom model definition)
                current_span.set_attribute("langfuse.model", "Cartesia-3")  # Match your screenshot

                # Performance metrics
                current_span.set_attribute("tts.ttfb", ev.metrics.ttfb or 0)
                current_span.set_attribute("tts.duration", ev.metrics.duration or 0)
                current_span.set_attribute("tts.audio_duration", ev.metrics.audio_duration or 0)
                current_span.set_attribute("tts.streamed", ev.metrics.streamed)

                logger.debug(
                    f"✅ Enriched TTS span with cost: ${tts_cost:.6f} ({ev.metrics.characters_count} chars)"
                )
            except Exception as e:
                logger.warning(f"Failed to enrich TTS span: {e}")

    # Cost limit enforcement (existing code)
    if agent.session_costs["total_estimated_cost"] > agent.cost_limits["session_max"]:
        logger.warning(
            f"Session cost limit exceeded: ${agent.session_costs['total_estimated_cost']:.4f} "
            f"(limit: ${agent.cost_limits['session_max']})"
        )
```

---

## Step 3: Simplify or Remove `cost_tracking.py`

Your current `cost_tracking.py` module creates separate spans, which is now redundant. You have two options:

### Option A: Keep as Cost Calculator Only (Recommended)

Remove the span creation code, keep only cost calculation:

```python
class CostTracker:
    def __init__(self):
        """Initialize cost tracker with provider pricing."""
        self.provider_pricing = {
            "openai_gpt4_mini_input": 0.000150 / 1000,
            "openai_gpt4_mini_output": 0.000600 / 1000,
            "deepgram_nova2": 0.0043 / 60,
            "cartesia_sonic": 0.06 / 1000000,
        }

        self.session_costs = {
            "llm": {"tokens": 0, "cost": 0.0},
            "stt": {"minutes": 0.0, "cost": 0.0},
            "tts": {"characters": 0, "cost": 0.0},
            "total": 0.0
        }

    def calculate_llm_cost(self, prompt_tokens: int, completion_tokens: int) -> dict:
        """Calculate LLM cost breakdown."""
        input_cost = prompt_tokens * self.provider_pricing["openai_gpt4_mini_input"]
        output_cost = completion_tokens * self.provider_pricing["openai_gpt4_mini_output"]
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost
        }

    # Similar for STT and TTS...
```

### Option B: Remove Entirely

Since you're now calculating costs directly in `agent.py`, you could remove `cost_tracking.py` entirely and keep all cost logic in one place.

---

## Step 4: Verification Steps

After implementing:

### 1. Test in Console Mode

```bash
cd /Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/my-app
uv run python src/agent.py console
```

Look for debug logs:
```
✅ Enriched LLM span with cost: $0.001234 (prompt: 150, completion: 35)
✅ Enriched STT span with cost: $0.000215 (0.05 minutes)
✅ Enriched TTS span with cost: $0.000120 (120 chars)
```

### 2. Check Langfuse Traces

After a test call:
1. Go to Langfuse → Traces
2. Click on a recent trace
3. Expand `llm_request` span → Check for:
   - `langfuse.cost.total`
   - `langfuse.cost.input`
   - `langfuse.cost.output`
   - `gen_ai.usage.cost`

4. Expand `tts_request` span → Check for:
   - `langfuse.cost.total`
   - `langfuse.usage.input` (character count)
   - `langfuse.model = "Cartesia-3"`

### 3. Check Model Usage Dashboard

Go to Langfuse → Model Usage

You should now see:
- ✅ `gpt-4.1-mini` (already working)
- ✅ `Cartesia-3` (new!)
- ✅ `deepgram-nova-2` (new!)

---

## Common Issues & Troubleshooting

### Issue 1: Models Still Not Appearing

**Check**: Does the `langfuse.model` attribute match your model definition's "Match Pattern"?

Example:
- If you set `current_span.set_attribute("langfuse.model", "cartesia-sonic-3")`
- Your match pattern must be: `(?i)^(cartesia[-_]sonic[-_]3)$`

### Issue 2: Costs Are Wrong

**Check**: Langfuse prices are **per unit**:
- LLM: per token (e.g., $0.00015 per token)
- STT: per minute (e.g., $0.0043 per minute)
- TTS: per character (e.g., $0.00000006 per char)

Make sure:
- `langfuse.usage.input` = **count** (tokens, minutes, or characters)
- Model definition price = **price per unit**
- Langfuse calculates: `cost = usage.input × price`

### Issue 3: Spans Not Being Enriched

**Check**: Is `current_span` valid and recording?

Add debug logging:
```python
current_span = otel_trace.get_current_span()
logger.debug(f"Current span: {current_span}, Recording: {current_span.is_recording() if current_span else False}")
```

---

## Expected Results

### Before Implementation
- Langfuse Model Usage: Only `gpt-4.1-mini` ($0.294893)
- TTS/STT costs: Tracked in session totals, not visible per-model

### After Implementation
- Langfuse Model Usage:
  - `gpt-4.1-mini`: $0.25
  - `Cartesia-3`: $0.03
  - `deepgram-nova-2`: $0.015
- Per-span cost visibility in trace view
- Performance metrics (ttft, ttfb, duration) in spans

---

## Summary

### What Changed
1. ❌ **Old approach**: Create separate spans with `cost_tracking.py`
2. ✅ **New approach**: Enrich LiveKit's existing spans with cost attributes

### Why This Works
- Works with LiveKit's automatic OpenTelemetry integration
- No duplicate spans
- Costs appear in Langfuse Model Usage dashboard
- Follows LiveKit best practices

### Code Changes Required
- Update `agent.py` metrics handler (~100 lines modified)
- Simplify or remove `cost_tracking.py` (optional)
- Add model definitions in Langfuse UI (5 minutes)

### Testing
1. Console mode verification
2. Check span attributes in Langfuse
3. Verify Model Usage dashboard shows all three models

---

## References

- LiveKit Metrics Documentation: https://docs.livekit.io/agents/build/metrics/
- Langfuse Model Usage: https://langfuse.com/docs/model-usage-and-cost
- OpenTelemetry Attributes: https://opentelemetry.io/docs/specs/semconv/gen-ai/
