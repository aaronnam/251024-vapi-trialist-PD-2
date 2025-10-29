# Quick Observability Implementation Guide

**Time Required**: 45 minutes for required setup (tracing + metrics)

**IMPORTANT**: Tracing is MANDATORY for production debugging. Start here.

**Official Integration**: This guide follows the official [Langfuse + LiveKit Agents integration](https://langfuse.com/integrations/frameworks/livekit) pattern using OpenTelemetry for distributed tracing.

---

## Step 1: Set Up Tracing (30 minutes) - **REQUIRED**

You cannot effectively debug production issues without tracing. When something goes wrong, traces show you exactly what happened.

### 1.1: Get LangFuse Account

1. Sign up at https://cloud.langfuse.com (free tier)
2. Create new project
3. Go to Settings → API Keys
4. Copy your Public Key and Secret Key

### 1.2: Add Dependencies

```bash
cd my-app
uv add langfuse opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

### 1.3: Create Telemetry Module

**Note**: This file has already been created for you at `my-app/src/utils/telemetry.py`

If it doesn't exist, create it with this content:

```python
import base64
import os
from livekit.agents.telemetry import set_tracer_provider

def setup_observability():
    """Set up LangFuse tracing if configured."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        return False  # Tracing not configured

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Configure LangFuse
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://cloud.langfuse.com/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth}"

    # Set up tracing
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    set_tracer_provider(provider)
    return True
```

### 1.4: Integrate into Agent

Add to the top of `entrypoint` function in `my-app/src/agent.py` (around line 1099):

```python
from utils.telemetry import setup_observability

async def entrypoint(ctx: JobContext):
    # Initialize tracing with session metadata
    trace_provider = setup_observability(
        metadata={"langfuse.session.id": ctx.room.name}
    )

    if trace_provider:
        logger.info(f"✅ Tracing enabled for session {ctx.room.name}")
        # Register shutdown callback to flush traces
        ctx.add_shutdown_callback(lambda: trace_provider.force_flush())
    else:
        logger.warning("⚠️ Tracing DISABLED - Add LangFuse keys for production debugging!")

    # ... rest of function
```

### 1.5: Configure Secrets

```bash
# Using the keys from step 1.1
lk agent update-secrets \
  --secrets "LANGFUSE_PUBLIC_KEY=<your-public-key>" \
  --secrets "LANGFUSE_SECRET_KEY=<your-secret-key>"

# Verify they were added
lk agent secrets
```

### 1.6: Deploy and Verify

```bash
# Deploy the changes
lk agent deploy

# Restart to pick up new secrets
lk agent restart

# Test with a conversation
lk agent proxy console

# Have a brief conversation, then check LangFuse dashboard
# You should see traces appearing in real-time
```

**✅ Tracing Setup Complete!** You can now debug any production issue by viewing the exact sequence of events in LangFuse.

### 1.7: (Optional) Enhanced Metadata

For better trace organization, you can add additional metadata:

```python
# In entrypoint function
trace_provider = setup_observability(
    metadata={
        "langfuse.session.id": ctx.room.name,
        "langfuse.metadata.environment": "production",
        "langfuse.metadata.agent_version": "1.0.0",
    }
)
```

This enables advanced filtering in Langfuse like "show all production traces" or "show all traces from v1.0.0".

---

## Step 2: Add Real-Time Metrics (15 minutes)

Now add metrics to track performance in real-time.

### 2.1: Add Metrics Handler

In `my-app/src/agent.py`, after the AgentSession is created (around line 1150), add:

```python
from livekit.agents import metrics, MetricsCollectedEvent

@session.on("metrics_collected")
def _on_metrics_collected(ev: MetricsCollectedEvent):
    """Capture real-time performance metrics."""
    # Log metrics to console
    metrics.log_metrics(ev.metrics)

    # Calculate and alert on high latency
    if ev.metrics and ev.metrics.eou and ev.metrics.llm and ev.metrics.tts:
        total_latency = (
            ev.metrics.eou.end_of_utterance_delay +
            ev.metrics.llm.ttft +
            ev.metrics.tts.ttfb
        )

        if total_latency > 1.5:
            logger.warning(
                f"⚠️ High latency: {total_latency:.2f}s "
                f"(EOU: {ev.metrics.eou.end_of_utterance_delay:.2f}s, "
                f"LLM: {ev.metrics.llm.ttft:.2f}s, "
                f"TTS: {ev.metrics.tts.ttfb:.2f}s)"
            )

        # Log to CloudWatch for queries
        from utils.analytics_queue import analytics_logger
        analytics_logger.info(
            "Voice metrics",
            extra={
                "analytics_data": {
                    "_event_type": "voice_metrics",
                    "_session_id": ctx.room.name,
                    "total_latency": total_latency,
                }
            }
        )
```

### 2.2: Deploy

```bash
lk agent deploy
```

### 2.3: Verify Metrics

```bash
# Watch for metrics and latency warnings
lk agent logs --tail | grep -E "metrics|latency"
```

---

## Step 3: Save CloudWatch Queries (5 minutes)

Save these queries in CloudWatch Insights for quick debugging:

### Find Slow Sessions
```sql
fields @timestamp, _session_id, total_latency
| filter _event_type = "voice_metrics" and total_latency > 1.5
| sort @timestamp desc
| limit 20
```

### Daily P95 Latency
```sql
fields @timestamp, total_latency
| filter _event_type = "voice_metrics"
| stats percentile(total_latency, 95) as p95,
       avg(total_latency) as avg
by bin(1d)
```

### Qualified Leads Today
```sql
fields _session_id, discovered_signals
| filter _event_type = "session_analytics"
| filter discovered_signals.team_size >= 5 or discovered_signals.monthly_volume >= 100
| filter @timestamp > ago(24h)
```

---

## Debugging Production Issues

When a user reports a problem:

```
1. Get session ID from user or logs
    ↓
2. Check LangFuse traces FIRST
   → See exact sequence of events
   → Identify slow operations
   → Find failures
    ↓
3. Query CloudWatch for context
   → Check metrics around that time
   → Look for patterns
    ↓
4. Fix the issue with confidence
```

---

## Quick Setup Script

We've provided a helper script: `my-app/setup_tracing.sh`

```bash
cd my-app
chmod +x setup_tracing.sh
./setup_tracing.sh

# Follow the prompts to enter your LangFuse keys
```

---

## Verification Checklist

- [ ] LangFuse account created and keys obtained
- [ ] Dependencies added (`langfuse` in `pyproject.toml`)
- [ ] `utils/telemetry.py` created
- [ ] Tracing initialized in `entrypoint`
- [ ] Secrets configured in LiveKit Cloud
- [ ] Agent deployed and restarted
- [ ] Traces appearing in LangFuse dashboard
- [ ] Metrics handler added
- [ ] High latency warnings working
- [ ] CloudWatch queries saved

---

## Summary

**You now have production-ready observability**:
1. **Tracing** - Debug any issue with full visibility
2. **Metrics** - Track performance in real-time
3. **Queries** - Analyze patterns and trends

**Remember**: When something goes wrong, check traces first. They show you exactly what happened, not just that something happened.