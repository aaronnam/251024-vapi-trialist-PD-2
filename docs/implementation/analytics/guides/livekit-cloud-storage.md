# LiveKit Cloud Storage Strategy for Analytics Data

## The Most Elegant Approach: Structured Logging + CloudWatch

When deploying to LiveKit Cloud, the most elegant solution leverages their built-in log forwarding capabilities without adding external infrastructure complexity.

## Architecture Overview

```
LiveKit Agent → Structured Logs → CloudWatch → S3/Analytics
      ↓                                ↓
Shutdown Callback              CloudWatch Insights
      ↓                                ↓
  JSON Logs                    Real-time Queries
```

## Implementation Plan

### Step 1: Convert Analytics to Structured Logging

Instead of sending to a queue, log structured JSON that CloudWatch can parse:

```python
# In src/utils/analytics_queue.py
import json
import logging

# Configure structured JSON logging
class StructuredLogFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'analytics_data'):
            # This is an analytics event
            return json.dumps({
                "_event_type": "analytics",
                "_timestamp": record.created,
                "_session_id": record.analytics_data.get('session_id'),
                **record.analytics_data
            })
        return super().format(record)

# Create dedicated analytics logger
analytics_logger = logging.getLogger("analytics")
handler = logging.StreamHandler()
handler.setFormatter(StructuredLogFormatter())
analytics_logger.addHandler(handler)
analytics_logger.setLevel(logging.INFO)

async def send_to_analytics_queue(data: Dict[str, Any]) -> None:
    """Log analytics data as structured JSON for CloudWatch ingestion."""
    # Log as structured JSON
    analytics_logger.info(
        "Session analytics",
        extra={"analytics_data": data}
    )
```

### Step 2: Enable CloudWatch Log Forwarding

Add AWS credentials as LiveKit secrets:

```bash
# Set up CloudWatch forwarding
lk agent update-secrets \
  --secrets "AWS_ACCESS_KEY_ID=your-key-id" \
  --secrets "AWS_SECRET_ACCESS_KEY=your-secret" \
  --secrets "AWS_REGION=us-east-1"
```

This automatically forwards ALL logs to CloudWatch Logs.

### Step 3: CloudWatch Log Insights Queries

Query your analytics data directly in CloudWatch:

```sql
-- Find all analytics events
fields @timestamp, session_id, duration_seconds, discovered_signals
| filter _event_type = "analytics"
| sort @timestamp desc

-- Get qualified leads
fields session_id, discovered_signals.team_size, discovered_signals.monthly_volume
| filter _event_type = "analytics"
| filter discovered_signals.team_size >= 5 OR discovered_signals.monthly_volume >= 100

-- Calculate average session duration
stats avg(duration_seconds) as avg_duration
| filter _event_type = "analytics"
```

### Step 4: Automated S3 Export (Optional)

Set up CloudWatch subscription filter to stream to S3:

```python
# AWS Lambda function to process logs and store in S3
import json
import boto3
import base64
import gzip

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Decompress CloudWatch logs
    log_data = json.loads(
        gzip.decompress(
            base64.b64decode(event['awslogs']['data'])
        )
    )

    for log_event in log_data['logEvents']:
        message = json.loads(log_event['message'])

        if message.get('_event_type') == 'analytics':
            # Store in S3 with partition by date
            key = f"sessions/{message['_session_id']}/{message['_timestamp']}.json"
            s3.put_object(
                Bucket='your-analytics-bucket',
                Key=key,
                Body=json.dumps(message)
            )
```

## Alternative Options

### Option 2: Direct HTTP POST to Your API

If you prefer more control, make direct HTTP calls from the shutdown callback:

```python
# In agent.py shutdown callback
async def export_session_data():
    try:
        # ... compile session_payload ...

        # Direct HTTP POST to your API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://your-api.com/analytics",
                json=session_payload,
                headers={"Authorization": f"Bearer {os.getenv('ANALYTICS_API_KEY')}"},
                timeout=5.0
            )
            response.raise_for_status()

    except Exception as e:
        logger.error(f"Analytics export failed: {e}")
```

### Option 3: Webhooks + External Service

Use LiveKit webhooks for room events + your own service:

```python
# External webhook handler (not in agent)
@app.post("/livekit-webhook")
async def handle_webhook(request):
    event = await request.json()

    if event["event"] == "room_finished":
        # Fetch transcript/data from your storage
        # Process analytics
        # Store results
```

## Why This Approach is Most Elegant

### ✅ Advantages

1. **Zero Additional Infrastructure**: Uses LiveKit's built-in log forwarding
2. **Cost Effective**: CloudWatch Logs pricing is ~$0.50/GB
3. **Queryable**: CloudWatch Insights provides SQL-like queries
4. **Reliable**: AWS manages retention, backups, availability
5. **Simple**: Just structured logging, no queues or databases
6. **Compliant**: AWS handles GDPR/HIPAA compliance
7. **Scalable**: Handles any volume automatically

### ✅ LiveKit Cloud Native

- Works perfectly with `lk agent logs` command
- Integrates with LiveKit's monitoring
- No custom infrastructure to maintain
- Follows LiveKit's recommended patterns

### ✅ Production Ready Features

- **Retention**: Configure 1-90 days in CloudWatch
- **Archival**: Auto-export to S3 for long-term storage
- **Alerting**: CloudWatch Alarms for patterns
- **Dashboards**: CloudWatch Dashboards for metrics
- **Analysis**: Athena queries on S3 data

## Implementation Checklist

### Immediate (10 minutes)
- [ ] Update `analytics_queue.py` to use structured logging
- [ ] Deploy agent with updated code
- [ ] Add AWS credentials via `lk agent update-secrets`

### Day 1
- [ ] Verify logs appearing in CloudWatch
- [ ] Create CloudWatch Insights queries
- [ ] Set up basic CloudWatch dashboard

### Week 1 (Optional)
- [ ] Configure S3 export for long-term storage
- [ ] Set up Athena for SQL queries on S3 data
- [ ] Create CloudWatch alarms for hot leads

## Cost Estimate

For 1000 sessions/day with ~5KB per session:
- **CloudWatch Logs Ingestion**: ~$0.08/day ($0.50/GB)
- **CloudWatch Logs Storage**: ~$0.01/day ($0.03/GB/month)
- **S3 Storage**: ~$0.0004/day ($0.023/GB/month)

**Total: ~$3/month for 1000 sessions/day**

## Example Structured Log Output

When a session completes, this JSON appears in CloudWatch:

```json
{
  "_event_type": "analytics",
  "_timestamp": 1738000000.123,
  "_session_id": "room_abc123",
  "duration_seconds": 330.5,
  "discovered_signals": {
    "team_size": 8,
    "monthly_volume": 200,
    "integration_needs": ["salesforce"],
    "urgency": "high"
  },
  "tool_calls": [
    {
      "tool": "unleash_search_knowledge",
      "query": "how to create templates",
      "results_found": true
    }
  ],
  "metrics_summary": {
    "llm_tokens": 2500,
    "avg_latency_ms": 450
  }
}
```

## Query Examples in CloudWatch Insights

### Find Hot Leads
```sql
fields session_id, discovered_signals.team_size as team,
       discovered_signals.monthly_volume as volume
| filter _event_type = "analytics"
| filter team >= 5 or volume >= 100
| sort _timestamp desc
| limit 20
```

### Daily Session Stats
```sql
stats count() as sessions,
      avg(duration_seconds) as avg_duration,
      sum(metrics_summary.llm_tokens) as total_tokens
by bin(5m)
| filter _event_type = "analytics"
```

### Failed Tool Calls
```sql
fields session_id, tool_calls
| filter _event_type = "analytics"
| filter tool_calls.0.results_found = false
```

## Migration Path

If you later need more sophisticated analytics:

1. **Phase 1**: Start with CloudWatch (immediate)
2. **Phase 2**: Add S3 export + Athena (week 1)
3. **Phase 3**: Build analytics service reading from S3 (month 1)
4. **Phase 4**: Add real-time processing with Kinesis (if needed)

This approach starts simple and can grow with your needs.

---

**This is the most elegant solution because it requires the least code changes, leverages LiveKit Cloud's native capabilities, and can scale from MVP to enterprise without architectural changes.**