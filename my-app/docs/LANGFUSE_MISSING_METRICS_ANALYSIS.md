# Langfuse Missing Metrics Analysis

## Executive Summary

Based on review of:
- LiveKit Agents documentation (https://docs.livekit.io/agents/build/metrics/)
- LiveKit Events documentation (https://docs.livekit.io/agents/build/events/)
- Langfuse OpenTelemetry integration (https://langfuse.com/integrations/native/opentelemetry)
- Current implementation in `my-app/src/agent.py` and `my-app/src/utils/cost_tracking.py`

**Status**: You have basic cost tracking but are missing **critical performance and latency metrics** in Langfuse.

---

## What You Currently Track

### ✅ Implemented Features

**1. OpenTelemetry Setup** (`utils/telemetry.py`)
- TracerProvider with LangFuse OTLP exporter
- Session-level metadata
- Batch span processing
- Resource attributes

**2. Cost Tracking** (`utils/cost_tracking.py`)
- LLM: prompt_tokens, completion_tokens, cost
- STT: audio_duration, cost
- TTS: character_count, cost
- Session aggregation

**3. Metrics Collection** (`agent.py:1358-1545`)
- `metrics_collected` event handler
- Speech-ID buffering
- Total latency calculation
- CloudWatch export

**4. Conversation Tracking**
- User transcription capture
- Conversation item logging
- LLM span enrichment with history

---

## Critical Missing Metrics

### P0: Latency Metrics (CRITICAL)

**Problem**: You calculate latency but **don't send it to Langfuse spans**.

```python
# Current: You calculate this...
total_latency = (
    turn_metrics["eou"].end_of_utterance_delay
    + (turn_metrics["llm"].ttft or 0)
    + (turn_metrics["tts"].ttfb or 0)
)

# But only send to CloudWatch, NOT to Langfuse spans!
```

**Missing in Langfuse**:
- `llm.ttft` - Time-to-first-token (how fast LLM starts responding)
- `tts.ttfb` - Time-to-first-byte (how fast TTS starts generating)
- `eou.end_of_utterance_delay` - VAD processing delay
- `eou.transcription_delay` - STT transcription delay
- `eou.on_user_turn_completed_delay` - Callback processing time

**Impact**:
- ❌ Can't filter slow conversations in Langfuse
- ❌ Can't identify latency bottlenecks per component
- ❌ Can't track latency trends over time
- ❌ Can't debug "why was this response slow?"

**Fix**: Add these to Langfuse spans in `_on_metrics_collected`:

```python
# When tracking LLM costs, also add latency
if isinstance(ev.metrics, LLMMetrics):
    current_span.set_attribute("llm.ttft", ev.metrics.ttft)
    current_span.set_attribute("llm.duration", ev.metrics.duration)
    current_span.set_attribute("llm.tokens_per_second", ev.metrics.tokens_per_second)
    current_span.set_attribute("llm.prompt_cached_tokens", ev.metrics.prompt_cached_tokens)

# When tracking TTS costs, also add latency
if isinstance(ev.metrics, TTSMetrics):
    current_span.set_attribute("tts.ttfb", ev.metrics.ttfb)
    current_span.set_attribute("tts.duration", ev.metrics.duration)
    current_span.set_attribute("tts.audio_duration", ev.metrics.audio_duration)

# When tracking EOUMetrics, add delays
if isinstance(ev.metrics, EOUMetrics):
    current_span.set_attribute("eou.end_of_utterance_delay", ev.metrics.end_of_utterance_delay)
    current_span.set_attribute("eou.transcription_delay", ev.metrics.transcription_delay)
```

---

### P0: OpenTelemetry Standard Attributes

**Problem**: Using only `langfuse.*` namespace, missing standard `gen_ai.*` attributes.

**Missing**:
- `gen_ai.usage.input_tokens`
- `gen_ai.usage.output_tokens`
- `gen_ai.usage.cost`
- `gen_ai.request.model`
- `gen_ai.request.temperature`
- `gen_ai.request.max_tokens`

**Impact**:
- ❌ Less compatible with other observability tools
- ❌ Harder to correlate with industry standards
- ❌ Missing automatic Langfuse parsing of standard attributes

**Fix**: Add both namespaces in `cost_tracking.py`:

```python
# In track_llm_cost()
span.set_attribute("langfuse.usage.prompt_tokens", prompt_tokens)
span.set_attribute("gen_ai.usage.input_tokens", prompt_tokens)  # ADD THIS

span.set_attribute("langfuse.usage.completion_tokens", completion_tokens)
span.set_attribute("gen_ai.usage.output_tokens", completion_tokens)  # ADD THIS

span.set_attribute("langfuse.cost.total", total_cost)
span.set_attribute("gen_ai.usage.cost", total_cost)  # ADD THIS

span.set_attribute("langfuse.model", model)
span.set_attribute("gen_ai.request.model", model)  # ADD THIS
```

---

### P1: LLM Performance Metrics

**Problem**: Tracking costs but not performance.

**Missing**:
- `llm.tokens_per_second` - generation speed
- `llm.duration` - total processing time
- `llm.prompt_cached_tokens` - cache hit rate

**Impact**:
- ❌ Can't identify slow LLM responses
- ❌ Can't measure cache effectiveness
- ❌ Can't track generation speed trends

**Location**: Add in `agent.py:1441-1497` when handling `LLMMetrics`.

---

### P1: Component Duration Metrics

**Problem**: Tracking usage but not duration.

**Missing**:
- `stt.duration` - STT processing time (0 for streaming)
- `tts.duration` - TTS generation time
- `tts.audio_duration` - duration of generated audio

**Impact**:
- ❌ Can't pinpoint slow components
- ❌ Can't differentiate streaming vs batch performance

**Location**: Add in `agent.py:1498-1534` when handling `STTMetrics` and `TTSMetrics`.

---

### P1: Trace-Level Context

**Problem**: Missing user and session context at trace level.

**Current**:
```python
setup_observability(
    metadata={"langfuse.session.id": ctx.room.name}
)
```

**Missing**:
- `langfuse.trace.userId` - user identifier
- `langfuse.trace.name` - conversation name/title
- `langfuse.trace.metadata.*` - custom filterable metadata
- `langfuse.trace.tags` - tags for grouping/filtering

**Impact**:
- ❌ Hard to filter traces by user
- ❌ Can't add custom tags for organization
- ❌ Limited searchability in Langfuse UI

**Fix**: Enhance `setup_observability` call in `agent.py:1274-1276`:

```python
trace_provider = setup_observability(
    metadata={
        "langfuse.session.id": ctx.room.name,
        "langfuse.trace.userId": user_email or "anonymous",  # ADD
        "langfuse.trace.name": f"Voice Call - {ctx.room.name[:8]}",  # ADD
        "langfuse.trace.tags": ["voice_agent", "production"],  # ADD
        "langfuse.trace.metadata.room_name": ctx.room.name,  # ADD
        "langfuse.trace.metadata.deployment_env": os.getenv("DEPLOYMENT_ENV", "production"),  # ADD
    }
)
```

---

### P2: Span Hierarchy

**Problem**: Flat span structure, not nested.

**Current Structure**:
```
llm_usage (standalone span)
stt_usage (standalone span)
tts_usage (standalone span)
conversation_turn (standalone span)
```

**Desired Structure**:
```
conversation_turn (root span)
├── stt_processing (child span)
│   ├── duration, audio_duration
│   └── cost
├── llm_generation (child span)
│   ├── ttft, duration, tokens_per_second
│   └── cost
└── tts_synthesis (child span)
    ├── ttfb, duration, audio_duration
    └── cost
```

**Impact**:
- ❌ Harder to view complete turn context
- ❌ Can't see parent-child relationships
- ❌ Less organized trace view in UI

**Fix**: Refactor `cost_tracking.py` to accept parent span context:

```python
def track_llm_cost(
    self,
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gpt-4.1-mini",
    speech_id: Optional[str] = None,
    parent_span = None  # ADD THIS
) -> float:
    # ...
    with self.tracer.start_as_current_span("llm_generation", context=parent_span) as span:
        # ... set attributes
```

---

### P2: Error Tracking

**Problem**: No error event tracking in Langfuse.

**Missing**:
- Error events from `@session.on("close")` with error details
- Recoverable vs unrecoverable error distinction
- Function tool execution errors
- LLM/STT/TTS provider errors

**Impact**:
- ❌ Can't analyze failure patterns
- ❌ Can't track error rates per component
- ❌ No visibility into production errors in Langfuse

**Fix**: Add error event handler:

```python
@session.on("close")
def on_session_close(ev):
    """Capture session close events and errors."""
    if ev.error:
        try:
            from opentelemetry import trace as otel_trace
            current_span = otel_trace.get_current_span()

            if current_span and current_span.is_recording():
                current_span.set_attribute("error", True)
                current_span.set_attribute("error.type", type(ev.error).__name__)
                current_span.set_attribute("error.message", str(ev.error))
                current_span.set_attribute("error.recoverable", getattr(ev.error, "recoverable", False))
        except Exception as e:
            logger.warning(f"Failed to track session error: {e}")
```

---

### P2: User State Metrics

**Problem**: Not tracking user engagement metrics.

**Missing**:
- User state transitions (speaking → listening → away)
- Time spent in each state
- Interruption rate (`conversation_item_added.interrupted` flag)

**Impact**:
- ❌ Can't measure user engagement
- ❌ Can't identify high-interruption conversations
- ❌ Can't track "away" time (user disengagement)

**Fix**: Already have `@session.on("user_state_changed")` handler, just need to add Langfuse tracking:

```python
@session.on("user_state_changed")
def on_user_state(ev):
    """Track user state changes in Langfuse."""
    try:
        from opentelemetry import trace as otel_trace
        current_span = otel_trace.get_current_span()

        if current_span and current_span.is_recording():
            current_span.set_attribute("user.state.previous", ev.old_state)
            current_span.set_attribute("user.state.current", ev.new_state)
            current_span.set_attribute("user.state.timestamp", datetime.now().isoformat())
    except Exception as e:
        logger.warning(f"Failed to track user state: {e}")

    asyncio.create_task(handle_user_state_changed(ev))
```

---

## Implementation Priority

### Phase 1: Critical Latency Metrics (Do First)
1. Add `llm.ttft`, `tts.ttfb`, `eou.*_delay` to Langfuse spans
2. Add OpenTelemetry standard `gen_ai.*` attributes
3. Add trace-level `userId` and metadata

**Estimated effort**: 2-3 hours
**Impact**: Immediate visibility into latency bottlenecks

### Phase 2: Performance Metrics
1. Add `llm.tokens_per_second`, `llm.duration`, `llm.prompt_cached_tokens`
2. Add `stt.duration`, `tts.duration`, `tts.audio_duration`
3. Add streaming indicators

**Estimated effort**: 1-2 hours
**Impact**: Better performance analysis

### Phase 3: Error & Engagement Tracking
1. Add error event tracking
2. Add user state tracking
3. Add interruption rate tracking

**Estimated effort**: 2-3 hours
**Impact**: Better reliability insights

### Phase 4: Span Hierarchy Refactor
1. Refactor to nested span structure
2. Update all span creation to use parent context

**Estimated effort**: 3-4 hours
**Impact**: Better trace organization in UI

---

## Code Changes Required

### File: `my-app/src/agent.py`

**Lines 1441-1497** (LLM metrics handler):
```python
# ADD after line 1463:
current_span = otel_trace.get_current_span()
if current_span and current_span.is_recording():
    # Latency metrics
    current_span.set_attribute("llm.ttft", ev.metrics.ttft or 0)
    current_span.set_attribute("llm.duration", ev.metrics.duration or 0)
    current_span.set_attribute("llm.tokens_per_second", ev.metrics.tokens_per_second or 0)
    current_span.set_attribute("llm.prompt_cached_tokens", ev.metrics.prompt_cached_tokens or 0)

    # OpenTelemetry standard attributes
    current_span.set_attribute("gen_ai.usage.input_tokens", ev.metrics.prompt_tokens)
    current_span.set_attribute("gen_ai.usage.output_tokens", ev.metrics.completion_tokens)
    current_span.set_attribute("gen_ai.usage.cost", llm_cost)
    current_span.set_attribute("gen_ai.request.model", "gpt-4.1-mini")
```

**Lines 1498-1515** (STT metrics handler):
```python
# ADD after line 1515:
try:
    from opentelemetry import trace as otel_trace
    current_span = otel_trace.get_current_span()

    if current_span and current_span.is_recording():
        current_span.set_attribute("stt.duration", ev.metrics.duration or 0)
        current_span.set_attribute("stt.audio_duration", ev.metrics.audio_duration)
        current_span.set_attribute("stt.streamed", ev.metrics.streamed)
except Exception as e:
    logger.warning(f"Failed to enrich STT span: {e}")
```

**Lines 1517-1534** (TTS metrics handler):
```python
# ADD after line 1534:
try:
    from opentelemetry import trace as otel_trace
    current_span = otel_trace.get_current_span()

    if current_span and current_span.is_recording():
        current_span.set_attribute("tts.ttfb", ev.metrics.ttfb or 0)
        current_span.set_attribute("tts.duration", ev.metrics.duration or 0)
        current_span.set_attribute("tts.audio_duration", ev.metrics.audio_duration or 0)
        current_span.set_attribute("tts.streamed", ev.metrics.streamed)
except Exception as e:
    logger.warning(f"Failed to enrich TTS span: {e}")
```

**Lines 1274-1276** (Trace setup):
```python
# REPLACE with:
trace_provider = setup_observability(
    metadata={
        "langfuse.session.id": ctx.room.name,
        "langfuse.trace.userId": user_email or "anonymous",
        "langfuse.trace.name": f"Voice Call - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "langfuse.trace.tags": ["voice_agent", "production", "pandadoc"],
        "langfuse.trace.metadata.room_name": ctx.room.name,
        "langfuse.trace.metadata.deployment_env": os.getenv("DEPLOYMENT_ENV", "production"),
    }
)
```

---

## Testing Verification

After implementing changes, verify in Langfuse:

1. **Check for new attributes in traces**:
   - Filter for recent traces
   - Expand a trace to see spans
   - Look for `llm.ttft`, `tts.ttfb`, etc. in span attributes

2. **Verify trace-level metadata**:
   - Check trace has `userId` field
   - Check trace has tags
   - Verify you can filter by user

3. **Check latency filtering**:
   - Try filtering traces by `llm.ttft > 1.0`
   - Try filtering by `total_latency > 2.0`

4. **Verify span hierarchy** (Phase 4 only):
   - Check spans are nested under `conversation_turn`
   - Verify parent-child relationships visible in UI

---

## Expected Langfuse Dashboard After Implementation

### Current View:
```
Trace: session-abc123
├── llm_usage (flat)
├── stt_usage (flat)
├── tts_usage (flat)
└── conversation_turn (flat)
```

### After Phase 1-2:
```
Trace: session-abc123 (userId: user@example.com, tags: [voice_agent, production])
├── llm_usage
│   ├── cost: $0.0015
│   ├── llm.ttft: 0.45s  ← NEW
│   ├── llm.duration: 1.2s  ← NEW
│   ├── llm.tokens_per_second: 45  ← NEW
│   └── gen_ai.usage.input_tokens: 150  ← NEW
├── stt_usage
│   ├── cost: $0.0002
│   ├── stt.duration: 0.1s  ← NEW
│   └── stt.audio_duration: 3.5s  ← NEW
├── tts_usage
│   ├── cost: $0.0001
│   ├── tts.ttfb: 0.35s  ← NEW
│   ├── tts.duration: 0.8s  ← NEW
│   └── tts.audio_duration: 2.1s  ← NEW
└── conversation_turn
    └── total_latency: 1.8s
```

### After Phase 4 (Nested):
```
Trace: session-abc123
└── conversation_turn (root span, total_latency: 1.8s)
    ├── stt_processing (child)
    │   └── ...
    ├── llm_generation (child)
    │   └── ...
    └── tts_synthesis (child)
        └── ...
```

---

## References

- LiveKit Metrics: https://docs.livekit.io/agents/build/metrics/
- LiveKit Events: https://docs.livekit.io/agents/build/events/
- Langfuse OpenTelemetry: https://langfuse.com/integrations/native/opentelemetry
- OpenTelemetry Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/

---

## Next Steps

1. Review this analysis
2. Decide on implementation priority (recommend Phase 1 first)
3. Implement Phase 1 changes
4. Test in console mode: `uv run python src/agent.py console`
5. Deploy and verify in Langfuse dashboard
6. Iterate to Phase 2, 3, 4 as needed
