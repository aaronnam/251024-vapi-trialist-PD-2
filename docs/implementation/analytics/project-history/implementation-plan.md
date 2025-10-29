# PandaDoc Voice Agent - Analytics Implementation Plan

## Philosophy: Elegant Simplicity

This implementation plan follows the principle of **elegant simplicity**: leverage LiveKit's built-in patterns, minimize code in the voice agent, and defer heavy processing to asynchronous systems. The voice agent should do the absolute minimum required for data collection.

---

## Phase 1: Lightweight Data Collection (Week 1)

### 1.1 Leverage LiveKit's Built-in Metrics

LiveKit already provides comprehensive metrics through `MetricsCollectedEvent`. We'll use these directly without reinventing the wheel.

```python
# In agent.py - Add to PandaDocTrialistAgent.__init__
from livekit.agents import metrics

# Initialize collectors
self.usage_collector = metrics.UsageCollector()
self.session_data = {
    "session_id": ctx.room.name,
    "start_time": datetime.now().isoformat(),
    "user_metadata": {},  # Populated from participant metadata
    "discovered_signals": {},  # Populated during conversation
    "tool_calls": [],  # Track tool usage
}

# In start() method
@self.session.on("metrics_collected")
def on_metrics_collected(ev: MetricsCollectedEvent):
    # Aggregate metrics using LiveKit's built-in collector
    self.usage_collector.collect(ev.metrics)

    # Log for debugging (optional, can be removed in production)
    metrics.log_metrics(ev.metrics)
```

### 1.2 Minimal Signal Discovery

Instead of complex NLP during the conversation, use simple pattern matching and defer analysis to the analytics pipeline.

```python
# In agent.py - Add simple signal detection
def _detect_signals(self, message: str) -> None:
    """Lightweight signal detection - no heavy processing."""
    # Team size detection (simple regex)
    if match := re.search(r'\b(\d+)\s*(?:people|users|team|employees)\b', message, re.I):
        self.session_data["discovered_signals"]["team_size"] = int(match.group(1))

    # Integration mentions (keyword matching)
    integrations = ["salesforce", "hubspot", "zapier", "api"]
    mentioned = [i for i in integrations if i in message.lower()]
    if mentioned:
        self.session_data["discovered_signals"]["integrations"] = mentioned

    # Timeline detection (simple keywords)
    if any(word in message.lower() for word in ["this week", "urgent", "asap"]):
        self.session_data["discovered_signals"]["urgency"] = "high"
```

### 1.3 Track Tool Usage

Already implemented in your agent - just ensure we're capturing the data:

```python
# In unleash_search_knowledge function
self.session_data["tool_calls"].append({
    "tool": "unleash_search",
    "query": query,
    "category": category,
    "timestamp": datetime.now().isoformat(),
    "results_found": bool(results)
})

# In book_sales_meeting function
self.session_data["tool_calls"].append({
    "tool": "book_meeting",
    "customer_email": customer_email,
    "timestamp": datetime.now().isoformat(),
    "success": success
})
```

### 1.4 Use Shutdown Callback for Data Export

This is the LiveKit-approved pattern for post-processing. The agent collects data during the session, then sends it all at once when shutting down.

```python
# In agent.py - In entrypoint function
async def entrypoint(ctx: JobContext):
    async def export_session_data():
        """Export session data to analytics queue on shutdown."""
        try:
            # Add final metrics summary
            usage_summary = agent.usage_collector.get_summary()

            # Compile complete session data
            session_payload = {
                **agent.session_data,
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "metrics_summary": usage_summary,
                "transcript": ctx.room.chat_context.messages if hasattr(ctx.room, 'chat_context') else [],
            }

            # Send to queue (SQS or Pub/Sub)
            await send_to_analytics_queue(session_payload)
            logger.info(f"Session data exported: {ctx.room.name}")

        except Exception as e:
            logger.error(f"Failed to export session data: {e}")

    # Register shutdown callback
    ctx.add_shutdown_callback(export_session_data)

    # Start the agent
    await agent.start(ctx.room)
```

---

## Phase 2: Message Queue Setup (Week 1)

### 2.1 Choose Queue Service

**Recommendation: Google Cloud Pub/Sub** (if using Google Cloud) or **AWS SQS** (if using AWS)

Both are simple, reliable, and have Python SDKs. Choose based on your existing infrastructure.

### 2.2 Simple Queue Publisher

```python
# utils/analytics_queue.py
import json
import os
from google.cloud import pubsub_v1  # or boto3 for AWS

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(
    os.getenv("GCP_PROJECT_ID"),
    os.getenv("ANALYTICS_TOPIC", "voice-sessions")
)

async def send_to_analytics_queue(data: dict) -> None:
    """Send session data to analytics queue."""
    try:
        # Serialize data
        message = json.dumps(data).encode('utf-8')

        # Publish to queue
        future = publisher.publish(topic_path, message)
        future.result(timeout=5)  # Non-blocking with timeout

    except Exception as e:
        # Log error but don't crash the agent
        logger.error(f"Analytics queue error: {e}")
```

### 2.3 Environment Configuration

Add to `.env.local`:
```bash
# Analytics Queue (Google Pub/Sub)
GCP_PROJECT_ID=your-project-id
ANALYTICS_TOPIC=voice-sessions
ANALYTICS_SUBSCRIPTION=voice-sessions-analytics

# OR for AWS SQS
AWS_REGION=us-east-1
ANALYTICS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/voice-sessions
```

---

## Phase 3: Analytics Processing Service (Week 2)

### 3.1 Separate Python Service

Create a new service (`analytics-processor/`) that runs independently from the voice agent.

```
analytics-processor/
├── pyproject.toml
├── src/
│   ├── main.py           # Queue consumer
│   ├── analyzers/        # Analysis modules
│   │   ├── lead_scorer.py
│   │   ├── sentiment.py
│   │   └── sales_intelligence.py
│   └── destinations/     # Output adapters
│       ├── salesforce.py
│       ├── amplitude.py
│       └── data_warehouse.py
```

### 3.2 Queue Consumer Pattern

```python
# analytics-processor/src/main.py
from google.cloud import pubsub_v1
import json
import asyncio

async def process_session(data: dict):
    """Process a single session through all analyzers."""
    try:
        # Run analyzers
        lead_score = await analyze_lead_score(data)
        sentiment = await analyze_sentiment(data)
        sales_intel = await analyze_sales_intelligence(data)

        # Distribute to destinations
        await update_salesforce(data, lead_score, sales_intel)
        await send_to_amplitude(data, sentiment)
        await store_in_warehouse(data)

    except Exception as e:
        logger.error(f"Processing error: {e}")
        # Could send to DLQ here

def message_callback(message):
    """Handle incoming queue messages."""
    try:
        data = json.loads(message.data.decode('utf-8'))
        asyncio.create_task(process_session(data))
        message.ack()
    except Exception as e:
        logger.error(f"Message processing failed: {e}")
        message.nack()  # Retry later

# Subscribe to queue
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    os.getenv("GCP_PROJECT_ID"),
    os.getenv("ANALYTICS_SUBSCRIPTION")
)

streaming_pull_future = subscriber.subscribe(
    subscription_path,
    callback=message_callback
)

# Keep running
with subscriber:
    streaming_pull_future.result()
```

### 3.3 Use Powerful LLMs for Analysis

Since this runs asynchronously, we can use more powerful models without impacting voice latency:

```python
# analytics-processor/src/analyzers/sales_intelligence.py
from openai import OpenAI

client = OpenAI()

async def analyze_sales_intelligence(data: dict) -> dict:
    """Extract sales intelligence using GPT-4."""

    # Construct transcript text
    transcript = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in data.get('transcript', [])
    ])

    # Use GPT-4 for comprehensive analysis
    response = await client.chat.completions.create(
        model="gpt-4",  # Use powerful model here
        messages=[
            {"role": "system", "content": SALES_ANALYSIS_PROMPT},
            {"role": "user", "content": transcript}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
```

---

## Phase 4: Minimal Dashboard (Week 2)

### 4.1 Use Existing Tools

Don't build a custom dashboard initially. Use:
- **Google Cloud Monitoring** or **AWS CloudWatch** for metrics
- **Salesforce Reports** for sales insights
- **Amplitude Dashboards** for product analytics

### 4.2 Simple Alert System

Start with basic Slack notifications:

```python
# analytics-processor/src/alerts.py
import httpx

async def send_slack_alert(webhook_url: str, message: dict):
    """Send alert to Slack."""
    await httpx.post(webhook_url, json=message)

# In processing pipeline
if lead_score > 80:
    await send_slack_alert(SALES_WEBHOOK, {
        "text": f"🔥 Hot Lead: {data['user_email']} (Score: {lead_score})"
    })
```

---

## Implementation Timeline

### Week 1: Agent-Side Changes
- **Day 1-2**: Add metrics collection to agent.py
- **Day 3**: Implement shutdown callback with data export
- **Day 4**: Set up message queue (Pub/Sub or SQS)
- **Day 5**: Test end-to-end data flow

### Week 2: Analytics Service
- **Day 6-7**: Create analytics-processor service structure
- **Day 8**: Implement queue consumer
- **Day 9**: Add basic analyzers (lead scoring, sentiment)
- **Day 10**: Connect to Salesforce and Amplitude

### Week 3: Polish & Deploy
- **Day 11-12**: Add error handling and retries
- **Day 13**: Deploy to production
- **Day 14**: Monitor and tune
- **Day 15**: Documentation and handoff

---

## Key Design Decisions

### Why This Approach is Elegant

1. **Leverages LiveKit Patterns**: Uses built-in metrics, shutdown callbacks, and event handlers
2. **Minimal Agent Code**: ~50 lines added to existing agent
3. **Zero Voice Latency Impact**: All processing happens after the call
4. **Standard Tools**: Uses industry-standard queues, no custom infrastructure
5. **Gradual Enhancement**: Can start simple and add analyzers incrementally

### What We're NOT Doing

- ❌ Building custom metrics collection (use LiveKit's)
- ❌ Real-time streaming analytics (batch at session end)
- ❌ Heavy NLP in the agent (defer to analytics service)
- ❌ Custom dashboard initially (use existing tools)
- ❌ Complex orchestration (simple queue → processor pattern)

---

## Code Changes Summary

### Changes to `agent.py`

```python
# 1. Add imports
from livekit.agents import metrics, MetricsCollectedEvent
import re
from datetime import datetime

# 2. In __init__, add:
self.usage_collector = metrics.UsageCollector()
self.session_data = {
    "session_id": ctx.room.name,
    "start_time": datetime.now().isoformat(),
    "discovered_signals": {},
    "tool_calls": []
}

# 3. In start(), add:
@self.session.on("metrics_collected")
def on_metrics_collected(ev: MetricsCollectedEvent):
    self.usage_collector.collect(ev.metrics)

# 4. In tool functions, add tracking:
self.session_data["tool_calls"].append({...})

# 5. Add signal detection in message processing:
self._detect_signals(message)
```

### New file: `utils/analytics_queue.py`

```python
# ~30 lines for queue publisher
```

### In `entrypoint` function:

```python
# Add shutdown callback
ctx.add_shutdown_callback(export_session_data)
```

**Total new code in agent: ~50-75 lines**

---

## Testing Strategy

### 1. Unit Tests
```python
# tests/test_analytics.py
def test_signal_detection():
    agent = PandaDocTrialistAgent()
    agent._detect_signals("We have 5 people on our team")
    assert agent.session_data["discovered_signals"]["team_size"] == 5
```

### 2. Integration Tests
```python
# tests/test_queue_export.py
async def test_session_export():
    # Mock queue
    with patch('utils.analytics_queue.send_to_analytics_queue') as mock:
        # Run session
        await run_test_session()
        # Verify data was sent
        assert mock.called
        assert "metrics_summary" in mock.call_args[0][0]
```

### 3. End-to-End Test
- Run agent in console mode
- Complete a full conversation
- Verify message appears in queue
- Verify processing completes
- Check Salesforce/Amplitude for data

---

## Deployment Considerations

### 1. Agent Deployment
No changes needed - just deploy updated agent code to LiveKit Cloud as usual.

### 2. Analytics Service Deployment
```yaml
# Cloud Run service (or equivalent)
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: analytics-processor
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project/analytics-processor
        env:
        - name: GCP_PROJECT_ID
          value: "your-project"
        resources:
          limits:
            memory: "2Gi"
            cpu: "1"
```

### 3. Monitoring
- Queue depth (should stay near 0)
- Processing latency (should be <30s)
- Error rate (should be <1%)
- Cost per session (track LLM usage)

---

## Cost Optimization

### Estimated Costs per 1000 Sessions
- **Queue**: ~$1 (Pub/Sub or SQS)
- **Analytics Processing**: ~$50 (GPT-4 analysis)
- **Storage**: ~$5 (data warehouse)
- **Compute**: ~$10 (Cloud Run or Lambda)

**Total: ~$66 per 1000 sessions ($0.066 per session)**

### Optimization Opportunities
1. Use GPT-3.5 for initial analysis, GPT-4 only for hot leads
2. Batch process during off-peak hours
3. Cache common patterns (competitor mentions, objections)
4. Use local models for simple tasks (sentiment, word counts)

---

## Success Criteria

### Week 1 Success
✅ Agent successfully exports data on every session end
✅ Data appears in message queue
✅ No impact on voice latency

### Week 2 Success
✅ Analytics service processes 100% of sessions
✅ Salesforce records updated within 1 minute
✅ Hot lead alerts sent to Slack

### Week 3 Success
✅ Running in production with <1% error rate
✅ Processing cost <$0.10 per session
✅ Sales team actively using the data

---

## Next Steps After MVP

Once the basic system is working, consider:

1. **Real-time streaming** for hot leads (WebSocket to dashboard)
2. **Custom dashboard** if existing tools insufficient
3. **ML models** for better lead scoring
4. **A/B testing** framework for agent improvements
5. **Historical analysis** for trend detection

But remember: **Start simple, prove value, then enhance.**

---

## Appendix: Environment Variables

Complete list of new environment variables needed:

```bash
# Analytics Queue (choose one)
# Option A: Google Pub/Sub
GCP_PROJECT_ID=your-project-id
ANALYTICS_TOPIC=voice-sessions
ANALYTICS_SUBSCRIPTION=voice-sessions-analytics
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Option B: AWS SQS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
ANALYTICS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123/voice-sessions

# Analytics Processing
OPENAI_API_KEY=sk-...  # For GPT-4 analysis
SALESFORCE_URL=https://your-instance.salesforce.com
SALESFORCE_USERNAME=integration@company.com
SALESFORCE_PASSWORD=password
SALESFORCE_TOKEN=token
AMPLITUDE_API_KEY=your-amplitude-key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Data Warehouse (optional)
BIGQUERY_DATASET=voice_analytics
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
```

---

*This plan prioritizes simplicity and leverages existing tools wherever possible. The total implementation should be achievable in 2-3 weeks with one developer.*