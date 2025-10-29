# Voice Agent Observability Strategy

**Last Updated**: 2025-01-29
**Status**: Required Implementation
**Effort**: 1-2 hours
**Philosophy**: Build on existing infrastructure, tracing-first approach for production debugging

---

## Executive Summary

This document outlines a **tracing-first observability strategy** that extends your existing CloudWatch/S3 analytics pipeline with OpenTelemetry distributed tracing and real-time metrics. Tracing is **mandatory** for production debugging - without it, you're flying blind when issues occur.

**Core Requirements**:
1. **OpenTelemetry tracing** (30 minutes) - **MANDATORY** - LangFuse integration for debugging
2. **Real-time metrics collection** (15 minutes) - LiveKit's built-in metrics events
3. **Enhanced CloudWatch queries** (15 minutes) - Pre-built queries for common issues
4. **Cost tracking** (already done) - Your existing UsageCollector

**Why Tracing is Non-Negotiable**: When a user reports "the agent was slow" or "it didn't understand me", tracing shows you exactly what happened - which API calls were made, how long each step took, and where failures occurred. Without tracing, you're guessing.

---

## Official Integration Pattern

This implementation follows the **official Langfuse + LiveKit Agents integration** as documented at:
- **Langfuse Docs**: https://langfuse.com/integrations/frameworks/livekit
- **LiveKit Example**: https://github.com/livekit/agents/blob/main/examples/voice_agents/langfuse_trace.py

**Key Design Principles**:
1. **OpenTelemetry Standard** - Uses OpenTelemetry Protocol (OTLP) for distributed tracing
2. **Native LiveKit Support** - Leverages LiveKit's built-in `set_tracer_provider()` integration
3. **Session Metadata** - Tags traces with session ID for easy filtering in Langfuse UI
4. **Graceful Trace Flushing** - Ensures all traces are exported before agent shutdown
5. **Zero-dependency Fallback** - Gracefully handles missing configuration without breaking the agent

**Why OpenTelemetry Instead of Langfuse SDK?**
- LiveKit Agents framework has **native OpenTelemetry integration** built-in
- Automatic tracing of all agent operations (STT, LLM, TTS, tools)
- Uses industry-standard OTLP protocol supported by all major observability platforms
- Langfuse provides OTLP endpoint specifically for this use case

---

## Current State Analysis

### What You Already Have ✅

From reviewing your implementation in `/my-app/src/agent.py`:

1. **CloudWatch Logging** - All logs forwarded automatically
2. **S3 Data Lake** - Session data via Kinesis Firehose
3. **UsageCollector** - Aggregated metrics at session end
4. **Session Analytics** - Tool usage, discovered signals, duration
5. **Structured JSON** - `analytics_queue.py` for formatted logging

### What You're Missing ❌

1. **Trace-based debugging** ⚠️ **CRITICAL** - No OpenTelemetry for following request flow
2. **Real-time metrics events** - No `@session.on("metrics_collected")` handler
3. **Detailed latency breakdown** - Not tracking EOU, STT, LLM TTFT, TTS TTFB separately
4. **Pre-built queries** - No saved CloudWatch Insights queries for common patterns

**The #1 Gap**: Without tracing, you cannot debug production issues effectively. When something goes wrong, you need to see the exact sequence of events, timings, and failures. Logs alone won't tell you why a specific user had a bad experience.

---

## Required Implementation

### Phase 1: OpenTelemetry Tracing with LangFuse (30 minutes) - **MANDATORY**

**This must be implemented first**. Tracing is your primary debugging tool in production. Without it, you cannot effectively troubleshoot issues.

#### Step 1: Install Dependencies

```bash
cd my-app
uv add langfuse opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

#### Step 2: Set up LangFuse Integration

Create `my-app/src/utils/telemetry.py`:

```python
import base64
import os
from livekit.agents.telemetry import set_tracer_provider


def setup_observability():
    """Set up LangFuse for OpenTelemetry tracing."""
    # Skip if not configured
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        return  # Tracing not configured

    # Set up LangFuse authentication
    langfuse_auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{host.rstrip('/')}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"

    # Configure tracer provider
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    set_tracer_provider(trace_provider)
```

#### Step 3: Initialize in Agent

Add to `my-app/src/agent.py` at the top of the `entrypoint` function (around line 1075):

```python
from utils.telemetry import setup_observability

async def entrypoint(ctx: JobContext):
    # Set up observability with session metadata (gracefully skips if not configured)
    trace_provider = setup_observability(
        metadata={"langfuse.session.id": ctx.room.name}
    )

    if trace_provider:
        logger.info(f"✅ Tracing enabled for session {ctx.room.name}")
        # Register shutdown callback to flush traces before agent stops
        ctx.add_shutdown_callback(lambda: trace_provider.force_flush())
    else:
        logger.warning("⚠️ Tracing not configured - running without observability")

    # ... rest of entrypoint
```

#### Step 4: Configure LangFuse (Optional)

Add to LiveKit Cloud secrets:
```bash
lk agent update-secrets \
  --secrets "LANGFUSE_PUBLIC_KEY=<your-key>" \
  --secrets "LANGFUSE_SECRET_KEY=<your-secret>"
```

Or use the free cloud tier at https://cloud.langfuse.com

**What this gives you**:
- Full request tracing through your agent
- Visual timeline of each conversation turn
- Bottleneck identification
- Tool execution timing
- Essential debugging capability for production issues
- **Session-level filtering** - Traces are tagged with `langfuse.session.id` for easy filtering in Langfuse UI
- **Guaranteed trace delivery** - `force_flush()` ensures traces are exported even if agent terminates abruptly

**Optional Metadata Enhancements**:
You can add additional metadata to all traces for better organization:

```python
trace_provider = setup_observability(
    metadata={
        "langfuse.session.id": ctx.room.name,
        "langfuse.user.id": user_email,  # If you have user identity
        "langfuse.metadata.environment": "production",
        "langfuse.metadata.agent_version": "1.0.0",
    }
)
```

This metadata appears in Langfuse UI and enables filtering like "show me all traces from production" or "show me sessions for user@example.com".

---

### Phase 2: Real-Time Metrics Collection (15 minutes)

Add a metrics handler to capture detailed performance data in real-time:

```python
# In my-app/src/agent.py, after session creation

from livekit.agents import metrics, MetricsCollectedEvent

@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    """Capture real-time performance metrics."""
    # Log for immediate visibility
    metrics.log_metrics(ev.metrics)

    # Also push to CloudWatch as structured JSON
    if ev.metrics:
        metric_data = {
            "_event_type": "voice_metrics",
            "_timestamp": datetime.now().isoformat(),
            "_session_id": ctx.room.name,
        }

        # Calculate total latency when all components present
        if ev.metrics.eou and ev.metrics.llm and ev.metrics.tts:
            total_latency = (
                ev.metrics.eou.end_of_utterance_delay +
                ev.metrics.llm.ttft +
                ev.metrics.tts.ttfb
            )
            metric_data["total_latency"] = total_latency

            # Alert on high latency
            if total_latency > 1.5:
                logger.warning(f"⚠️ High latency: {total_latency:.2f}s")

        # Log to CloudWatch
        from utils.analytics_queue import analytics_logger
        analytics_logger.info("Voice metrics", extra={"analytics_data": metric_data})
```

**What this gives you**:
- Real-time latency tracking
- Detailed performance breakdown
- Automatic CloudWatch ingestion
- Latency alerts

---

### Phase 3: CloudWatch Insights Queries (15 minutes)

Save these queries in CloudWatch Insights for quick debugging:

#### 1. Latency P95 Dashboard
```sql
fields @timestamp, total_latency
| filter _event_type = "voice_metrics"
| stats percentile(total_latency, 95) as p95_latency,
       percentile(total_latency, 99) as p99_latency,
       avg(total_latency) as avg_latency
by bin(5m)
```

#### 2. Slow Response Investigation
```sql
fields @timestamp, _session_id, total_latency, llm.ttft, tts.ttfb, eou.delay
| filter _event_type = "voice_metrics" and total_latency > 1.5
| sort @timestamp desc
| limit 20
```

#### 3. Qualified Leads Monitor
```sql
fields @timestamp, _session_id, discovered_signals.team_size as team_size,
       discovered_signals.monthly_volume as volume
| filter _event_type = "session_analytics"
| filter team_size >= 5 or volume >= 100
| sort @timestamp desc
| limit 50
```

#### 4. Tool Failure Tracking
```sql
fields @timestamp, _session_id, tool_calls
| filter _event_type = "session_analytics"
| filter tool_calls like /success.*false/
| stats count() by tool_calls.0.tool
```

#### 5. Cost Analysis
```sql
fields @timestamp,
       metrics_summary.llm_tokens as tokens,
       metrics_summary.stt_audio_seconds as stt_seconds,
       metrics_summary.tts_audio_seconds as tts_seconds
| filter _event_type = "session_analytics"
| stats sum(tokens) as total_tokens,
       sum(stt_seconds) as total_stt,
       sum(tts_seconds) as total_tts
by bin(1d)
```

**Save these in CloudWatch**:
1. Go to CloudWatch Insights
2. Select your log group (`/aws/livekit/pd-voice-trialist-4`)
3. Paste query
4. Click "Save query"
5. Name it descriptively

---

## Implementation Checklist

### Required Setup (1 hour total)

- [x] **Phase 1: OpenTelemetry Tracing** (30 min) - **MANDATORY**
  - [x] Sign up for LangFuse Cloud (free tier)
  - [x] Add dependencies: `uv add langfuse opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp`
  - [x] Create `utils/telemetry.py`
  - [x] Add secrets to LiveKit Cloud
  - [x] Deploy and verify traces appear in LangFuse

- [x] **Phase 2: Real-time metrics** (15 min)
  - [x] Add `@session.on("metrics_collected")` handler with latency tracking
  - [x] Deploy: `lk agent deploy` (v20251029184411)
  - [x] Verify: Check CloudWatch for `_event_type = "voice_metrics"`

- [ ] **Phase 3: CloudWatch queries** (15 min) - **OPTIONAL**
  - [ ] Save 5 queries in CloudWatch Insights (queries provided below)
  - [ ] Create CloudWatch Dashboard with key metrics
  - [ ] Set up latency alarm (>1.5s P95)

**Status**: ✅ Phases 1-2 Complete | Agent: pd-voice-trialist-4 | Deployed: 2025-10-29

---

## Monitoring Playbook

### Daily Health Check (2 minutes)
1. CloudWatch Dashboard - Check P95 latency trend
2. Qualified leads query - Any hot leads from yesterday?
3. Error rate - Any spikes in tool failures?

### Debugging Slow Sessions
1. User reports slow response
2. Get session ID from complaint
3. **FIRST**: Check LangFuse traces for that session ID - see exact timings and sequence
4. Run "Slow Response Investigation" query in CloudWatch for additional context
5. Identify bottleneck from traces: LLM, TTS, network, or tool execution?

### Cost Optimization
1. Run "Cost Analysis" query weekly
2. If token usage high: Check for verbose system prompts
3. If audio usage high: Check for long sessions, consider timeouts

---

## Why This Approach?

### What We're NOT Doing (Over-engineering)
- ❌ Building custom metrics servers
- ❌ Running Prometheus/Grafana
- ❌ Complex ETL pipelines
- ❌ Custom dashboarding solutions
- ❌ Multiple observability tools

### What We ARE Doing (Elegant & Essential)
- ✅ **OpenTelemetry tracing as the foundation** - Non-negotiable for production
- ✅ Using LiveKit's built-in metrics for performance monitoring
- ✅ Leveraging existing CloudWatch pipeline for aggregation
- ✅ Pre-built queries you can copy/paste
- ✅ Single tracing provider (LangFuse) for simplicity

### Cost Impact
- **CloudWatch**: Already paying for it, no change
- **LangFuse**: Free tier covers 50k traces/month
- **S3**: Negligible increase (~1KB per session)
- **Total additional cost**: ~$0/month

---

## Advanced Options (Future)

Once the basics are working, consider:

1. **Athena SQL on S3** - Complex analytics on historical data
2. **Amplitude Integration** - Business metrics alongside product analytics
3. **PagerDuty Alerts** - Wake someone up if P95 > 2 seconds
4. **Snowflake Integration** - Already documented, cross-reference with other data

But start simple. Get the basics working first.

---

## Quick Reference

### Files to Modify
1. `my-app/src/agent.py` - Add metrics handler
2. `my-app/src/utils/telemetry.py` - New file for OpenTelemetry
3. `my-app/pyproject.toml` - Add langfuse dependency

### Commands
```bash
# Deploy changes
lk agent deploy

# Check metrics are flowing
aws logs tail /aws/livekit/pd-voice-trialist-4 \
  --filter-pattern '{ $._event_type = "voice_metrics" }' \
  --region us-west-1

# Update secrets for tracing
lk agent update-secrets \
  --secrets "LANGFUSE_PUBLIC_KEY=..." \
  --secrets "LANGFUSE_SECRET_KEY=..."
```

### Key Metrics to Track
- **Total Latency** - Should be <1.5s P95
- **LLM TTFT** - Should be <700ms
- **TTS TTFB** - Should be <300ms
- **Qualified Lead Rate** - Track week-over-week
- **Tool Success Rate** - Should be >95%

---

## Summary

This observability strategy gives you:
1. **Essential debugging capability** through OpenTelemetry traces (MANDATORY) ✅
2. **Real-time performance visibility** through CloudWatch metrics ✅
3. **Business insights** through your existing analytics pipeline ✅
4. **Zero additional infrastructure** to maintain ✅

**Implementation Status**:
- ✅ **Phase 1**: Tracing with Langfuse (MANDATORY) - Complete
- ✅ **Phase 2**: Real-time metrics with latency tracking - Complete
- ⚪ **Phase 3**: CloudWatch query setup (OPTIONAL) - Queries documented, ready to save

**Current Deployment**:
- **Agent**: pd-voice-trialist-4 (CA_9b4oemVRtDEm)
- **Version**: v20251029184411
- **Langfuse**: https://us.cloud.langfuse.com
- **Region**: US East

**Key Files Modified**:
- `my-app/src/agent.py:1134-1144` - Tracing initialization
- `my-app/src/agent.py:1198-1239` - Enhanced metrics handler
- `my-app/.env.local` - Langfuse secrets configured

**Remember**: Tracing is not optional. When production issues occur, traces are the difference between guessing and knowing what went wrong.