# Analytics Deployment Reference

**Last Updated**: 2025-01-28
**Status**: Reference for Future Implementation
**Deployment**: LiveKit Cloud (pd-voice-trialist-4)

---

## IMPORTANT: Implementation Status

**ACTUAL IMPLEMENTATION (as of 2025-10-29):**
- ✅ Agent code with analytics collection (complete)
- ✅ Direct S3 upload via boto3 (implemented 2025-10-29)
- ✅ Session data export on shutdown (complete)

**THIS DOCUMENT DESCRIBES:**
- ❌ Kinesis Data Firehose architecture (NOT implemented - future enhancement)
- ❌ CloudWatch → Firehose → S3 pipeline (NOT implemented - future enhancement)
- ❌ Lambda processing (NOT implemented - future enhancement)

**Current Architecture**: The agent exports session data directly to S3 using boto3 in the shutdown callback. This is simpler, has lower latency, and avoids CloudWatch/Firehose costs.

**This Document's Purpose**: Serves as reference documentation for a future Firehose-based architecture if streaming analytics or real-time processing is needed. The current direct S3 implementation meets all immediate requirements.

---

## Overview

This document provides complete reference documentation for a **Firehose-based analytics architecture** that is NOT currently implemented but may be useful for future enhancements requiring real-time streaming or complex event processing.

**For the current implementation**, see the agent code in `my-app/src/agent.py` which writes directly to S3.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Data Flow](#data-flow)
- [Components](#components)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Monitoring & Debugging](#monitoring--debugging)
- [Cost Analysis](#cost-analysis)
- [Future Enhancements](#future-enhancements)

---

## Architecture Overview

**NOTE**: This section describes a **future Firehose-based architecture** that is NOT currently implemented. The current implementation uses direct S3 upload.

The Firehose analytics architecture would follow a **separated architecture pattern** designed for zero-latency impact on voice conversations:

```
┌─────────────────────────────────────────────────────────────────┐
│                        VOICE AGENT                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Lightweight Collection (0ms latency impact)            │   │
│  │  - Session metadata                                      │   │
│  │  - Signal discovery (regex, keywords)                   │   │
│  │  - Tool usage tracking                                   │   │
│  │  - LiveKit metrics aggregation                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│                  Shutdown Callback                               │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Structured JSON Logging                                 │   │
│  │  (analytics_queue.py)                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AWS CLOUDWATCH LOGS                          │
│  - Ingestion point for all agent logs                           │
│  - Structured JSON parsing                                      │
│  - Real-time queries via CloudWatch Insights                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                  KINESIS DATA FIREHOSE                          │
│  - Automatic log streaming                                      │
│  - 60-second buffer                                             │
│  - GZIP compression (~80% reduction)                            │
│  - Date-based partitioning                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                         AMAZON S3                               │
│  - Long-term storage                                            │
│  - Date-partitioned structure                                   │
│  - SQL-queryable via Athena                                     │
│  - Cost-effective archival                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Zero Latency Impact**: All heavy processing happens after conversation ends
2. **Separated Concerns**: Collection (agent) vs. Analysis (pipeline)
3. **LiveKit Native**: Uses built-in patterns and metrics
4. **Cloud Native**: Leverages AWS managed services
5. **Cost Optimized**: ~$1/month for 1000 sessions/day

---

## Data Flow

**Current Implementation**: Phases 1 and 2 are implemented. Session data goes directly to S3 via boto3 after conversation ends. Phases 3-5 below are NOT implemented.

**Future Firehose Architecture**: Would add Phases 3-5 for streaming analytics.

### Phase 1: Collection (During Conversation) ✅ IMPLEMENTED

**Location**: `my-app/src/agent.py`

```python
# Session start (lines 168-174)
self.session_data = {
    "start_time": datetime.now().isoformat(),
    "tool_calls": [],
}
self.usage_collector = metrics.UsageCollector()
```

**What happens**:
- Session metadata captured on agent initialization
- Tool calls tracked in real-time (append to list)
- Signal discovery runs on each user message via `_detect_signals()`
- LiveKit metrics automatically collected via `UsageCollector`

**Performance**: <1ms per message, 0ms conversation latency impact

### Phase 2: Export (After Conversation) ✅ IMPLEMENTED (Direct S3)

**Location**: `my-app/src/agent.py` (lines 837-890)

**Current Implementation**: Data is written directly to S3 using boto3 in the shutdown callback.

```python
async def export_session_data():
    """Export session data to analytics queue on shutdown."""
    session_payload = {
        "session_id": agent_instance.room_name,
        "start_time": agent_instance.session_data["start_time"],
        "end_time": datetime.now().isoformat(),
        "duration_seconds": duration,
        "discovered_signals": agent_instance.discovered_signals,
        "tool_calls": agent_instance.session_data["tool_calls"],
        "metrics_summary": metrics_summary,
    }
    await send_to_analytics_queue(session_payload)

ctx.add_shutdown_callback(export_session_data)
```

**What happens**:
- Triggered when session ends (user disconnects)
- Compiles all collected data into single payload
- Calls analytics queue utility
- Runs asynchronously (doesn't block cleanup)

**Performance**: <100ms, runs after conversation ends

### Phase 3: Structured Logging ❌ NOT IMPLEMENTED (Future)

**Location**: `my-app/src/utils/analytics_queue.py`

**Status**: This phase is NOT currently used. With direct S3 upload, structured logging to CloudWatch is bypassed.

```python
class StructuredAnalyticsFormatter(logging.Formatter):
    """Formats analytics data as structured JSON for CloudWatch."""
    def format(self, record):
        if hasattr(record, 'analytics_data'):
            analytics_json = {
                "_event_type": "session_analytics",
                "_timestamp": record.created,
                "_session_id": record.analytics_data.get('session_id'),
                **record.analytics_data
            }
            return json.dumps(analytics_json)
```

**What happens**:
- Validates JSON serializability
- Formats as structured JSON with metadata fields
- Logs via dedicated `livekit.analytics` logger
- Automatically forwarded to CloudWatch by LiveKit Cloud

**Output format**:
```json
{
  "_event_type": "session_analytics",
  "_timestamp": 1738000000.123,
  "_session_id": "room_abc123",
  "duration_seconds": 330.5,
  "discovered_signals": {...},
  "tool_calls": [...],
  "metrics_summary": {...}
}
```

### Phase 4: CloudWatch Ingestion ❌ NOT IMPLEMENTED (Future)

**Service**: AWS CloudWatch Logs
**Region**: us-west-1
**Log Group**: Automatically created by LiveKit Cloud

**Status**: This phase is NOT implemented. Data goes directly to S3, bypassing CloudWatch Logs entirely.

**Future Use Case**: Would enable real-time queries via CloudWatch Insights if needed.

**What would happen**:
- LiveKit Cloud forwards all agent logs to CloudWatch
- JSON logs are parsed and indexed
- Available for real-time queries via CloudWatch Insights
- Retention: 7 days (configurable)

**Configuration**: Set via LiveKit secrets:
```bash
AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
AWS_REGION=us-west-1
```

### Phase 5: S3 Export ❌ NOT IMPLEMENTED via Firehose (Future)

**Service**: Kinesis Data Firehose
**Stream Name**: `voice-analytics-to-s3`
**Destination**: `s3://pandadoc-voice-analytics-1761683081/`

**Status**: This Firehose-based approach is NOT implemented. Data is written directly to S3 from the agent using boto3.

**Current Approach**: Direct S3 upload via `boto3.client('s3').put_object()` in the shutdown callback.

**Future Use Case**: Firehose would enable buffering, transformation, and streaming to multiple destinations if needed.

**What would happen** (if implemented):
- CloudWatch subscription filter streams analytics events to Firehose
- Firehose buffers data (60 seconds or 1 MB)
- Compresses with GZIP (~80% size reduction)
- Writes to S3 with date partitioning

**S3 Structure**:
```
s3://pandadoc-voice-analytics-1761683081/
├── sessions/
│   ├── year=2025/
│   │   ├── month=01/
│   │   │   ├── day=28/
│   │   │   │   ├── voice-analytics-to-s3-1-2025-01-28-19-30-00-abc123.gz
│   │   │   │   └── voice-analytics-to-s3-1-2025-01-28-19-31-00-def456.gz
│   │   │   ├── day=29/
│   ├── month=02/
└── errors/  (Firehose delivery errors)
```

---

## Components

**Implementation Status:**
- ✅ Agent Collection Layer (implemented)
- ❌ Analytics Queue Utility (NOT used - structured logging bypassed)
- ❌ CloudWatch Logs (NOT used - data goes directly to S3)
- ❌ Kinesis Data Firehose (NOT implemented - future enhancement)
- ✅ Amazon S3 (implemented via direct upload)

### 1. Agent Collection Layer ✅ IMPLEMENTED

**File**: `my-app/src/agent.py`

#### Session Data Tracking (Lines 168-174)
```python
self.session_data = {
    "start_time": datetime.now().isoformat(),
    "tool_calls": [],
}
```
- Initialized in `PandaDocVoiceAgent.__init__()`
- Lightweight dictionary, ~50 bytes
- Cleared automatically on agent destruction

#### Signal Discovery (Lines 274-335)
```python
def _detect_signals(self, message: str) -> None:
    """Lightweight pattern matching for qualification signals."""
```
- Runs on every user message
- Uses regex and keyword matching
- No external API calls
- Updates `self.discovered_signals` dict
- Detects: team_size, monthly_volume, integrations, urgency, industry

**Patterns**:
```python
# Team size
r'\b(?:team|company|organization) (?:of |with )(\d+)\b'
r'\b(\d+)[- ](?:person|people|member|employee|user)s?\b'

# Document volume
r'(\d+)[\s-](?:documents?|contracts?|agreements?)(?:\s+(?:per|a|each))?\s+(?:month|year|week)'

# Urgency
r'\b(urgent|asap|immediately|right away|time[- ]sensitive)\b'
```

#### Tool Usage Tracking (Lines 451-459, 628-639)
```python
# In unleash_search_knowledge
self.session_data["tool_calls"].append({
    "tool": "unleash_search_knowledge",
    "query": query,
    "category": category,
    "timestamp": datetime.now().isoformat(),
    "results_found": bool(results),
    "total_results": total_results,
})

# In book_sales_meeting
self.session_data["tool_calls"].append({
    "tool": "book_sales_meeting",
    "customer_name": customer_name,
    "customer_email": customer_email,
    "timestamp": datetime.now().isoformat(),
    "success": True,
})
```
- Tracks all tool invocations
- Includes parameters, timestamps, success/failure
- Appends to list (no deduplication)

#### Metrics Collection (Lines 168-174)
```python
self.usage_collector = metrics.UsageCollector()
```
- LiveKit built-in metrics aggregation
- Automatically captures:
  - STT: audio duration, processing time
  - LLM: TTFT, tokens, completion latency
  - TTS: TTFB, audio duration, characters
  - EOU: end-of-utterance delay
- Accessed via `usage_collector.get_summary()`

#### Shutdown Callback (Lines 837-890)
```python
async def export_session_data():
    try:
        # Compile session payload
        session_payload = {...}

        # Export to analytics queue
        await send_to_analytics_queue(session_payload)

    except Exception as e:
        logger.error(f"Failed to export analytics: {e}")

ctx.add_shutdown_callback(export_session_data)
```
- Registered with LiveKit context
- Runs after session ends
- Non-blocking (async)
- Error handling prevents agent crashes

### 2. Analytics Queue Utility ❌ NOT USED (Future)

**File**: `my-app/src/utils/analytics_queue.py`

**Status**: This utility is NOT currently used. With direct S3 upload, structured logging to CloudWatch is bypassed. This would be useful for the future Firehose architecture.

#### Structured JSON Formatter (Lines 25-42)
```python
class StructuredAnalyticsFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'analytics_data'):
            analytics_json = {
                "_event_type": "session_analytics",
                "_timestamp": record.created,
                "_log_level": record.levelname,
                **record.analytics_data
            }
            if 'session_id' in record.analytics_data:
                analytics_json['_session_id'] = record.analytics_data['session_id']
            return json.dumps(analytics_json)
        return super().format(record)
```
- Custom logging formatter
- Adds metadata fields (`_event_type`, `_timestamp`, `_session_id`)
- Preserves all analytics data fields
- Falls back to standard format for non-analytics logs

#### Analytics Logger (Lines 45-50)
```python
analytics_logger = logging.getLogger("livekit.analytics")
analytics_handler = logging.StreamHandler()
analytics_handler.setFormatter(StructuredAnalyticsFormatter())
analytics_logger.addHandler(analytics_handler)
analytics_logger.setLevel(logging.INFO)
```
- Dedicated logger for analytics events
- Namespace: `livekit.analytics`
- Writes to stdout (captured by LiveKit Cloud)
- Level: INFO (filters out debug noise)

#### Export Function (Lines 53-127)
```python
async def send_to_analytics_queue(data: Dict[str, Any]) -> None:
    try:
        # Validate JSON serializable
        json.dumps(data)

        # Log structured JSON
        analytics_logger.info(
            "Session analytics data",
            extra={"analytics_data": data}
        )

        # Debug logging
        logger.info(f"Analytics data exported for session: {data.get('session_id')}")

        # Hot lead detection
        team_size = data.get('discovered_signals', {}).get('team_size', 0)
        monthly_volume = data.get('discovered_signals', {}).get('monthly_volume', 0)
        is_qualified = team_size >= 5 or monthly_volume >= 100

        if is_qualified:
            logger.info(
                f"🔥 HOT LEAD - Session {data.get('session_id')}: "
                f"Team size {team_size}, Volume {monthly_volume}/month"
            )

    except TypeError as e:
        logger.error(f"Analytics data is not JSON serializable: {e}")
        raise

    except Exception as e:
        logger.error(f"Failed to send analytics data: {e}", exc_info=True)
```
- Validates data before logging
- Logs structured JSON for CloudWatch
- Adds debug logs for visibility
- Hot lead detection (🔥 emoji for qualified leads)
- Graceful error handling

### 3. CloudWatch Logs ❌ NOT USED (Future)

**Service**: AWS CloudWatch Logs
**Region**: us-west-1
**Pricing**: $0.50/GB ingested, $0.03/GB/month stored

**Status**: NOT used for analytics data. Agent writes directly to S3. CloudWatch is only used for general application logs, not analytics events.

#### Configuration
- **AWS Credentials**: Stored as LiveKit Cloud secrets
- **Automatic Forwarding**: Enabled by LiveKit Cloud when credentials present
- **Log Group**: Auto-created by LiveKit (name includes agent ID)
- **Retention**: 7 days default (configurable)

#### Log Format
```json
{
  "@timestamp": "2025-01-28T19:30:00.000Z",
  "@message": "{\"_event_type\":\"session_analytics\",\"_timestamp\":1738093800.0,\"_session_id\":\"room_abc123\",...}",
  "@logStream": "agent/CA_9b4oemVRtDEm/2025/01/28/[$LATEST]abc123",
  "@logGroup": "/aws/livekit/pd-voice-trialist-4"
}
```

#### CloudWatch Insights Queries

**Find qualified leads**:
```sql
fields _session_id, discovered_signals.team_size as team_size,
       discovered_signals.monthly_volume as volume
| filter _event_type = "session_analytics"
| filter team_size >= 5 or volume >= 100
| sort _timestamp desc
| limit 20
```

**Daily session stats**:
```sql
stats count() as sessions,
      avg(duration_seconds) as avg_duration,
      sum(metrics_summary.llm_tokens) as total_tokens
by bin(1d) as day
| filter _event_type = "session_analytics"
| sort day desc
```

**Tool usage report**:
```sql
fields _session_id, tool_calls
| filter _event_type = "session_analytics"
| filter ispresent(tool_calls)
| stats count() by tool_calls.0.tool
```

### 4. Kinesis Data Firehose ❌ NOT IMPLEMENTED (Future)

**Service**: Kinesis Data Firehose
**Stream Name**: `voice-analytics-to-s3`
**Region**: us-west-1
**Pricing**: $0.029/GB ingested

**Status**: NOT implemented. This section describes a future architecture for streaming analytics. Current implementation uses direct S3 upload.

#### Configuration
- **Source**: CloudWatch Logs (via subscription filter)
- **Destination**: S3 bucket `pandadoc-voice-analytics-1761683081`
- **Buffer Size**: 1 MB
- **Buffer Interval**: 60 seconds
- **Compression**: GZIP
- **Prefix**: `sessions/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/`
- **Error Prefix**: `errors/`

#### Subscription Filter
- **Filter Pattern**: `{ $._event_type = "session_analytics" }`
- **Effect**: Only analytics events forwarded to Firehose
- **Benefit**: Reduces S3 storage costs by filtering out debug logs

#### IAM Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "logs.amazonaws.com"
      },
      "Action": "firehose:PutRecord",
      "Resource": "arn:aws:firehose:us-west-1:*:deliverystream/voice-analytics-to-s3"
    }
  ]
}
```

### 5. Amazon S3 ✅ IMPLEMENTED (Direct Upload)

**Bucket**: `pandadoc-voice-analytics-1761683081`
**Region**: us-west-1
**Pricing**: $0.023/GB/month

**Status**: S3 storage is IMPLEMENTED. Data is written directly from the agent using boto3, not via Firehose.

#### Structure
```
s3://pandadoc-voice-analytics-1761683081/
├── sessions/                      # All session data
│   ├── year=2025/                # Partitioned by year
│   │   ├── month=01/             # Partitioned by month
│   │   │   ├── day=28/           # Partitioned by day
│   │   │   │   ├── *.gz          # GZIP compressed files
│   │   │   ├── day=29/
│   │   ├── month=02/
└── errors/                        # Firehose delivery errors
```

#### File Format
- **Compression**: GZIP (~80% size reduction)
- **Content**: Newline-delimited JSON
- **Naming**: `voice-analytics-to-s3-1-YYYY-MM-DD-HH-mm-ss-{random}.gz`

#### Accessing Data
```bash
# List files
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ --recursive --region us-west-1

# Download and view
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=01/day=28/file.gz - | gunzip

# Sync to local
aws s3 sync s3://pandadoc-voice-analytics-1761683081/sessions/ ./local-data/ --region us-west-1
```

---

## Configuration

**NOTE**: Most configuration in this section relates to the future Firehose architecture. For the current direct S3 implementation, only AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET_NAME) are needed.

### Environment Variables

**LiveKit Cloud Secrets** (set via `lk agent update-secrets`):

| Variable | Value | Purpose |
|----------|-------|---------|
| `AWS_ACCESS_KEY_ID` | `<your-aws-access-key-id>` | AWS IAM credentials |
| `AWS_SECRET_ACCESS_KEY` | `<your-aws-secret-access-key>` | AWS IAM secret |
| `AWS_REGION` | `us-west-1` | CloudWatch region |

**Setting secrets**:
```bash
lk agent update-secrets \
  --secrets "AWS_ACCESS_KEY_ID=<your-aws-access-key-id>" \
  --secrets "AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>" \
  --secrets "AWS_REGION=us-west-1"
```

**Viewing secrets**:
```bash
lk agent secrets
```

### IAM Permissions

**User**: `livekit-cloudwatch-logger`
**Policy**: `CloudWatchLogsFullAccess` (or custom minimal policy)

**Minimal Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-west-1:*:*"
    }
  ]
}
```

### Agent Configuration

**Deployment**: LiveKit Cloud
**Project**: pd-voice-trialist-4
**Agent ID**: CA_9b4oemVRtDEm
**Region**: us-east

**Check status**:
```bash
lk agent status
```

**View logs**:
```bash
lk agent logs --tail
lk agent logs --log-type=build
```

### CloudWatch Configuration

**Log Group**: Auto-created by LiveKit
**Retention**: 7 days (configurable)
**Subscription Filter**: `S3Export`
**Filter Pattern**: `{ $._event_type = "session_analytics" }`

**Update retention**:
```bash
aws logs put-retention-policy \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --retention-in-days 7 \
  --region us-west-1
```

### Firehose Configuration

**Stream Name**: `voice-analytics-to-s3`
**Source**: CloudWatch Logs
**Destination**: S3
**Buffer**: 1 MB or 60 seconds
**Compression**: GZIP

**Check status**:
```bash
aws firehose describe-delivery-stream \
  --delivery-stream-name voice-analytics-to-s3 \
  --region us-west-1
```

---

## Deployment

**NOTE**: Steps 4-5 below (Firehose and CloudWatch Subscription Filter) are NOT implemented and represent future architecture. Current deployment only requires steps 1-3.

### Prerequisites

1. **LiveKit Cloud Account**
   - Project created: `pd-voice-trialist-4`
   - Agent deployed: `CA_9b4oemVRtDEm`

2. **AWS Account**
   - IAM user with CloudWatch permissions
   - Access keys generated

3. **Local Tools**
   - LiveKit CLI (`lk`) installed
   - AWS CLI configured

### Deployment Steps

**Current Implementation**: Only steps 1-3 are needed. Steps 4-5 are for future Firehose architecture.

#### 1. Deploy Agent Code ✅ IMPLEMENTED

```bash
# From repo root
cd my-app

# Deploy to LiveKit Cloud
lk agent deploy
```

**What this does**:
- Builds Docker image with analytics code
- Pushes to LiveKit Cloud registry
- Starts new agent version
- Takes ~2-3 minutes

**Verify**:
```bash
lk agent status
# Should show "Running"
```

#### 2. Configure AWS Credentials ✅ IMPLEMENTED

```bash
# Add secrets to LiveKit Cloud
lk agent update-secrets \
  --secrets "AWS_ACCESS_KEY_ID=<your-aws-access-key-id>" \
  --secrets "AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>" \
  --secrets "AWS_REGION=us-west-1"
```

**What this does**:
- Encrypts and stores secrets in LiveKit Cloud
- Makes secrets available as environment variables
- Enables CloudWatch log forwarding

**Verify**:
```bash
lk agent secrets
# Should show AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
```

#### 3. Create S3 Bucket ✅ IMPLEMENTED

```bash
# Create bucket (name must be globally unique)
aws s3 mb s3://pandadoc-voice-analytics-1761683081 --region us-west-1

# Enable versioning (optional)
aws s3api put-bucket-versioning \
  --bucket pandadoc-voice-analytics-1761683081 \
  --versioning-configuration Status=Enabled
```

#### 4. Create Kinesis Firehose Stream ❌ NOT IMPLEMENTED (Future)

**Status**: This step is NOT needed for current implementation. Only relevant for future Firehose architecture.

**Via AWS Console** (recommended for future implementation):
1. Go to: https://console.aws.amazon.com/kinesis/home?region=us-west-1
2. Click "Create Firehose stream"
3. Select "Direct PUT" source
4. Select "Amazon S3" destination
5. Configure:
   - Name: `voice-analytics-to-s3`
   - S3 bucket: `pandadoc-voice-analytics-1761683081`
   - Prefix: `sessions/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/`
   - Error prefix: `errors/`
   - Buffer: 1 MB or 60 seconds
   - Compression: GZIP
6. Create IAM role (auto-generated)
7. Click "Create"

**Via AWS CLI**:
```bash
aws firehose create-delivery-stream \
  --delivery-stream-name voice-analytics-to-s3 \
  --s3-destination-configuration \
    BucketARN=arn:aws:s3:::pandadoc-voice-analytics-1761683081,\
    Prefix=sessions/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/,\
    ErrorOutputPrefix=errors/,\
    BufferingHints={SizeInMBs=1,IntervalInSeconds=60},\
    CompressionFormat=GZIP \
  --region us-west-1
```

#### 5. Create CloudWatch Subscription Filter ❌ NOT IMPLEMENTED (Future)

**Status**: This step is NOT needed for current implementation. Only relevant for future Firehose architecture.

**Via AWS Console** (for future implementation):
1. Go to: https://console.aws.amazon.com/cloudwatch/home?region=us-west-1#logsV2:log-groups
2. Find and click your log group
3. Go to "Subscription filters" tab
4. Click "Create" → "Create Kinesis Firehose subscription filter"
5. Configure:
   - Firehose stream: `voice-analytics-to-s3`
   - Filter pattern: `{ $._event_type = "session_analytics" }`
   - Filter name: `S3Export`
6. Grant permissions when prompted
7. Click "Start streaming"

**Via AWS CLI**:
```bash
# First, find your log group name
aws logs describe-log-groups --region us-west-1 | grep logGroupName

# Create subscription filter (replace LOG_GROUP_NAME)
aws logs put-subscription-filter \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --filter-name "S3Export" \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --destination-arn "arn:aws:firehose:us-west-1:YOUR_ACCOUNT_ID:deliverystream/voice-analytics-to-s3" \
  --region us-west-1
```

#### 6. Test End-to-End

```bash
# Run test session
lk agent proxy --agent-id CA_9b4oemVRtDEm console

# Have test conversation with qualification signals
# Example: "We're a team of 10 people processing 500 documents per month"

# Exit session (triggers analytics export)

# Wait 2-3 minutes for buffers to flush

# Check CloudWatch
aws logs tail /aws/livekit/pd-voice-trialist-4 \
  --since 5m \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --region us-west-1

# Check S3
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive --region us-west-1
```

### Rollback Procedure

If issues occur, rollback to previous version:

```bash
# List versions
lk agent versions

# Rollback to previous version
lk agent rollback

# Verify
lk agent status
lk agent logs --tail
```

Analytics will stop flowing but agent will continue functioning normally.

---

## Monitoring & Debugging

### Health Checks

#### 1. Agent Health

```bash
# Check agent status
lk agent status

# Should show:
# - Status: Running
# - Replicas: 1/1
# - CPU/Memory: Normal utilization

# View recent logs
lk agent logs --tail --since 10m

# Look for:
# - "Session analytics data" (analytics exports)
# - "🔥 HOT LEAD" (qualified leads detected)
# - No error stack traces
```

#### 2. CloudWatch Health

```bash
# Check log group exists
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/livekit" \
  --region us-west-1

# Check recent analytics events
aws logs tail /aws/livekit/pd-voice-trialist-4 \
  --since 10m \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --region us-west-1 \
  --format short

# Check subscription filter
aws logs describe-subscription-filters \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --region us-west-1
```

#### 3. Firehose Health

```bash
# Check stream status
aws firehose describe-delivery-stream \
  --delivery-stream-name voice-analytics-to-s3 \
  --region us-west-1 \
  --query 'DeliveryStreamDescription.DeliveryStreamStatus'

# Should return: "ACTIVE"

# Check metrics (last hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=voice-analytics-to-s3 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region us-west-1
```

#### 4. S3 Health

```bash
# Check recent files
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive --region us-west-1 | tail -10

# Check file count by day
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=01/day=28/ \
  --region us-west-1 | wc -l

# Download and verify recent file
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=01/day=28/file.gz - \
  --region us-west-1 | gunzip | jq
```

### Common Issues

#### Issue: No analytics events in CloudWatch

**Symptoms**:
- No "Session analytics data" in agent logs
- CloudWatch Insights returns 0 results for `_event_type = "session_analytics"`

**Diagnosis**:
```bash
# 1. Check agent logs for errors
lk agent logs --tail --since 30m | grep -i error

# 2. Check if sessions are ending properly
lk agent logs --tail --since 30m | grep -i "shutdown"

# 3. Check if analytics_queue is being called
lk agent logs --tail --since 30m | grep -i "analytics"
```

**Possible Causes**:
1. **Sessions not ending properly** → Agent crashes before shutdown callback
2. **Import error** → `analytics_queue.py` not found
3. **JSON serialization error** → Data contains non-serializable objects
4. **AWS credentials not set** → CloudWatch forwarding disabled

**Solutions**:
```bash
# Verify AWS secrets are set
lk agent secrets

# If missing, add them
lk agent update-secrets \
  --secrets "AWS_ACCESS_KEY_ID=..." \
  --secrets "AWS_SECRET_ACCESS_KEY=..." \
  --secrets "AWS_REGION=us-west-1"

# Redeploy agent
lk agent deploy

# Test with short session
lk agent proxy --agent-id CA_9b4oemVRtDEm console
# Say "exit" immediately to trigger shutdown
```

#### Issue: Analytics events in CloudWatch but not in S3

**Symptoms**:
- CloudWatch Insights shows `_event_type = "session_analytics"` events
- S3 bucket is empty or not updating

**Diagnosis**:
```bash
# 1. Check Firehose status
aws firehose describe-delivery-stream \
  --delivery-stream-name voice-analytics-to-s3 \
  --region us-west-1 \
  --query 'DeliveryStreamDescription.DeliveryStreamStatus'

# 2. Check Firehose metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=voice-analytics-to-s3 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region us-west-1

# 3. Check subscription filter
aws logs describe-subscription-filters \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --region us-west-1
```

**Possible Causes**:
1. **Subscription filter not created** → CloudWatch not sending to Firehose
2. **Filter pattern incorrect** → Events not matching filter
3. **IAM permissions missing** → CloudWatch can't write to Firehose
4. **Buffer not full** → Wait 60 seconds for buffer to flush

**Solutions**:
```bash
# Check if subscription filter exists
aws logs describe-subscription-filters \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --region us-west-1

# If missing, create it (via console or CLI)
# See Deployment section above

# Test filter pattern in CloudWatch Insights
fields @timestamp, @message
| filter _event_type = "session_analytics"
| limit 10

# Wait 60 seconds for buffer, then check S3
sleep 60
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ --recursive
```

#### Issue: S3 files empty or corrupted

**Symptoms**:
- Files exist in S3 but contain 0 bytes
- GZIP decompression fails
- JSON parsing fails

**Diagnosis**:
```bash
# Download and inspect file
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=01/day=28/file.gz \
  ./test.gz --region us-west-1

# Check file size
ls -lh test.gz

# Try decompression
gunzip test.gz

# Try parsing JSON
cat test | jq
```

**Possible Causes**:
1. **Firehose delivery errors** → Check errors/ prefix in S3
2. **Data format issues** → Non-JSON data in CloudWatch
3. **Compression issues** → Firehose compression misconfigured

**Solutions**:
```bash
# Check Firehose errors
aws s3 ls s3://pandadoc-voice-analytics-1761683081/errors/ --recursive

# Download and inspect error
aws s3 cp s3://pandadoc-voice-analytics-1761683081/errors/latest.gz - | gunzip

# Check Firehose configuration
aws firehose describe-delivery-stream \
  --delivery-stream-name voice-analytics-to-s3 \
  --region us-west-1 \
  --query 'DeliveryStreamDescription.Destinations[0].S3DestinationDescription'
```

#### Issue: High costs

**Symptoms**:
- AWS bill higher than expected
- CloudWatch or Firehose charges excessive

**Diagnosis**:
```bash
# Check CloudWatch data ingestion
aws cloudwatch get-metric-statistics \
  --namespace AWS/Logs \
  --metric-name IncomingBytes \
  --dimensions Name=LogGroupName,Value=/aws/livekit/pd-voice-trialist-4 \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --region us-west-1

# Check Firehose data delivery
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name DataReadFromKinesisDataStreams \
  --dimensions Name=DeliveryStreamName,Value=voice-analytics-to-s3 \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --region us-west-1

# Check S3 storage
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive --summarize --human-readable
```

**Possible Causes**:
1. **Too many debug logs** → Filter pattern not working
2. **Excessive session volume** → More traffic than expected
3. **Retention too long** → CloudWatch storing logs too long
4. **Missing compression** → S3 files not compressed

**Solutions**:
```bash
# Verify filter pattern is active
aws logs describe-subscription-filters \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --region us-west-1

# Reduce CloudWatch retention
aws logs put-retention-policy \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --retention-in-days 3 \
  --region us-west-1

# Verify GZIP compression enabled
aws firehose describe-delivery-stream \
  --delivery-stream-name voice-analytics-to-s3 \
  --region us-west-1 \
  --query 'DeliveryStreamDescription.Destinations[0].S3DestinationDescription.CompressionFormat'

# Should return: "GZIP"
```

#### Issue: Missing qualification signals

**Symptoms**:
- Sessions exported but `discovered_signals` empty
- Known qualified leads not detected

**Diagnosis**:
```bash
# Check recent analytics events
aws logs tail /aws/livekit/pd-voice-trialist-4 \
  --since 30m \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --region us-west-1 \
  --format short | jq '.discovered_signals'

# Check agent logs for signal detection
lk agent logs --tail --since 30m | grep -i "detected"
```

**Possible Causes**:
1. **Pattern matching failing** → User language doesn't match regex
2. **Signal detection not running** → `_detect_signals()` not called
3. **Signals cleared** → `discovered_signals` reset somewhere

**Solutions**:
```python
# Test pattern matching locally
# In my-app/src/agent.py, add debug logging:

def _detect_signals(self, message: str) -> None:
    logger.debug(f"Analyzing message for signals: {message}")

    # ... existing code ...

    if team_size:
        logger.info(f"Detected team_size: {team_size}")
```

**Alternative**: Review conversation transcripts to verify users are providing signals:
```bash
# Find sessions with conversations but no signals
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/... - | \
  gunzip | \
  jq 'select(.discovered_signals | length == 0)'
```

### Logging and Observability

#### Agent Logs

**Standard output**:
```bash
# Real-time tail
lk agent logs --tail

# Last 30 minutes
lk agent logs --since 30m

# Build logs
lk agent logs --log-type=build

# Filter for analytics
lk agent logs --tail | grep "analytics"

# Filter for errors
lk agent logs --tail | grep -i error
```

**Log levels**:
- `INFO`: Normal operations, analytics exports
- `DEBUG`: Detailed signal detection, tool calls
- `ERROR`: Failures, exceptions

#### CloudWatch Logs

**Via Console**:
- https://console.aws.amazon.com/cloudwatch/home?region=us-west-1#logsV2:log-groups

**Via CLI**:
```bash
# Tail recent logs
aws logs tail /aws/livekit/pd-voice-trialist-4 \
  --since 10m \
  --region us-west-1

# Filter for analytics events
aws logs tail /aws/livekit/pd-voice-trialist-4 \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --region us-west-1

# Query with CloudWatch Insights
aws logs start-query \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, _session_id, discovered_signals | filter _event_type = "session_analytics"' \
  --region us-west-1
```

#### Firehose Monitoring

**Via Console**:
- https://console.aws.amazon.com/firehose/home?region=us-west-1#/details/voice-analytics-to-s3/monitoring

**Key Metrics**:
- `IncomingRecords`: Events received from CloudWatch
- `DeliveryToS3.Success`: Successful writes to S3
- `DeliveryToS3.DataFreshness`: Latency to S3 (should be ~60s)
- `IncomingBytes`: Data volume

**Via CLI**:
```bash
# Get recent metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=voice-analytics-to-s3 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-1
```

#### S3 Monitoring

```bash
# Count files by day
for day in {26..31}; do
  count=$(aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=01/day=$day/ 2>/dev/null | wc -l)
  echo "Day $day: $count files"
done

# Total storage used
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive --summarize --human-readable

# Recent files
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive | tail -10
```

### Alerts

**Recommended CloudWatch Alarms**:

1. **No Analytics Events** (indicates broken pipeline):
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name no-analytics-events \
  --alarm-description "No analytics events in last 2 hours" \
  --metric-name IncomingRecords \
  --namespace AWS/Firehose \
  --statistic Sum \
  --period 7200 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=DeliveryStreamName,Value=voice-analytics-to-s3 \
  --evaluation-periods 1 \
  --region us-west-1
```

2. **Firehose Delivery Failures**:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name firehose-delivery-failed \
  --alarm-description "Firehose failing to deliver to S3" \
  --metric-name DeliveryToS3.DataFreshness \
  --namespace AWS/Firehose \
  --statistic Maximum \
  --period 300 \
  --threshold 3600 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=DeliveryStreamName,Value=voice-analytics-to-s3 \
  --evaluation-periods 2 \
  --region us-west-1
```

3. **Hot Lead Alert** (optional, requires SNS):
```python
# In analytics_queue.py, add SNS notification:
if is_qualified:
    # Send SNS notification
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-west-1:ACCOUNT:hot-leads',
        Subject=f'Hot Lead: {session_id}',
        Message=json.dumps(data, indent=2)
    )
```

---

## Cost Analysis

**NOTE**: This section describes costs for the future Firehose architecture. The current direct S3 implementation has much lower costs (only S3 storage and PUT requests, approximately $0.02-0.05/month at 1000 sessions/day).

### Future Firehose Configuration Costs

Based on **1000 sessions/day**, average **5 minutes/session**, **~5KB data/session** (for future reference):

| Service | Usage | Cost/Month | Notes |
|---------|-------|------------|-------|
| **CloudWatch Logs** | | | |
| Ingestion | ~150 GB/month | $75.00 | $0.50/GB |
| Storage (7 days) | ~35 GB | $1.05 | $0.03/GB/month |
| Insights queries | 10 GB scanned | $0.05 | $0.005/GB |
| **Kinesis Firehose** | | | |
| Data delivery | ~5 GB/month | $0.15 | $0.029/GB (analytics only) |
| **S3** | | | |
| Storage (GZIP) | ~1 GB | $0.02 | $0.023/GB/month (~80% compressed) |
| PUT requests | ~1,500/month | $0.01 | $0.005/1000 |
| GET requests | ~100/month | $0.00 | $0.0004/1000 |
| **Data Transfer** | | | |
| Out to internet | Minimal | $0.00 | Only for downloads |
| **Total** | | **~$76.28/month** | At 1000 sessions/day |

### Cost Optimization Opportunities

#### 1. Reduce CloudWatch Retention (Save ~$0.70/month)
```bash
# Reduce from 7 days to 3 days
aws logs put-retention-policy \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --retention-in-days 3 \
  --region us-west-1
```

#### 2. Filter Non-Analytics Logs (Save ~50% CloudWatch costs)
The subscription filter already does this, but ensure it's active:
```bash
# Verify filter
aws logs describe-subscription-filters \
  --log-group-name "/aws/livekit/pd-voice-trialist-4" \
  --region us-west-1
```

#### 3. Increase Firehose Buffer (Save ~10% Firehose costs)
Fewer, larger files reduce overhead:
```bash
# Update to 5 MB buffer
aws firehose update-destination \
  --delivery-stream-name voice-analytics-to-s3 \
  --current-delivery-stream-version-id $(aws firehose describe-delivery-stream --delivery-stream-name voice-analytics-to-s3 --query 'DeliveryStreamDescription.VersionId' --output text) \
  --s3-destination-update BufferingHints={SizeInMBs=5,IntervalInSeconds=300} \
  --region us-west-1
```

#### 4. Lifecycle Policy for S3 (Save ~$0.01/month after 1 year)
Archive old data to Glacier:
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket pandadoc-voice-analytics-1761683081 \
  --lifecycle-configuration file://lifecycle.json
```

`lifecycle.json`:
```json
{
  "Rules": [
    {
      "Id": "ArchiveOldSessions",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

### Scaling Projections

| Sessions/Day | CloudWatch | Firehose | S3 | Total/Month |
|--------------|------------|----------|-----|-------------|
| 100 | $7.50 | $0.02 | $0.00 | **$7.60** |
| 1,000 | $75.00 | $0.15 | $0.02 | **$76.28** |
| 10,000 | $750.00 | $1.50 | $0.20 | **$762.75** |
| 100,000 | $7,500.00 | $15.00 | $2.00 | **$7,627.50** |

**Note**: At 10K+ sessions/day, consider alternative architectures (direct S3 write, streaming analytics).

---

## Future Enhancements

### Phase 2: Advanced Analytics (Planned)

#### 1. Real-time Lead Scoring
- **Goal**: Score leads in real-time using LLM
- **Approach**: Lambda function triggered by Firehose transform
- **Benefit**: Instant qualification, automated routing

**Implementation**:
```python
# Lambda function
def lambda_handler(event, context):
    for record in event['records']:
        data = json.loads(base64.b64decode(record['data']))

        # Score with LLM
        score = score_lead_with_llm(data)
        data['lead_score'] = score

        # Update record
        record['data'] = base64.b64encode(
            json.dumps(data).encode()
        )

    return {'records': event['records']}
```

#### 2. Salesforce Integration
- **Goal**: Auto-create leads for qualified sessions
- **Approach**: EventBridge rule triggering Lambda → Salesforce API
- **Benefit**: Automatic CRM population

**Implementation**:
```python
# Lambda triggered by EventBridge
def create_salesforce_lead(session_data):
    sf = Salesforce(
        username=os.getenv('SF_USERNAME'),
        password=os.getenv('SF_PASSWORD'),
        security_token=os.getenv('SF_TOKEN')
    )

    lead = sf.Lead.create({
        'FirstName': session_data.get('first_name'),
        'LastName': session_data.get('last_name'),
        'Email': session_data.get('email'),
        'Company': session_data.get('company'),
        'LeadSource': 'Voice Agent',
        'Description': f"Qualified via voice: Team size {session_data['team_size']}"
    })
```

#### 3. Amplitude Events
- **Goal**: Send session events to Amplitude for product analytics
- **Approach**: Lambda function reading from S3 → Amplitude API
- **Benefit**: Unified analytics across web and voice

#### 4. Athena for SQL Analytics
- **Goal**: Query S3 data with SQL
- **Approach**: Create Athena table pointing to S3
- **Benefit**: Ad-hoc analysis, BI tool integration

**Setup**:
```sql
CREATE EXTERNAL TABLE voice_sessions (
  _event_type string,
  _timestamp double,
  _session_id string,
  duration_seconds double,
  discovered_signals struct<
    team_size: int,
    monthly_volume: int,
    urgency: string
  >,
  tool_calls array<struct<
    tool: string,
    success: boolean
  >>
)
STORED AS JSON
LOCATION 's3://pandadoc-voice-analytics-1761683081/sessions/'
PARTITIONED BY (year int, month int, day int);
```

#### 5. Real-time Dashboards
- **Goal**: Live visualization of agent performance
- **Approach**: CloudWatch Dashboard or Grafana
- **Benefit**: Real-time monitoring, alerts

### Phase 3: AI-Powered Insights (Future)

- **Sentiment Analysis**: Analyze conversation tone
- **Topic Extraction**: Identify common questions/issues
- **Churn Prediction**: Flag at-risk conversations
- **Coaching Insights**: Suggest agent improvements

---

## Summary

**Current Implementation (as of 2025-10-29):**

✅ **Implemented Features:**
- Agent-side data collection (zero latency impact)
- Direct S3 upload via boto3
- Session metrics, signals, tool usage tracking
- Cost-effective storage (~$0.02-0.05/month for 1000 sessions/day)

**This Document Describes (Future Firehose Architecture):**

This document primarily describes a **future Firehose-based analytics architecture** that would provide:

❌ **Zero Latency Impact**: All processing after conversation ends (future)
❌ **Comprehensive Data**: Session metrics, signals, tool usage, LiveKit stats (future)
❌ **Real-time Insights**: CloudWatch Insights for instant queries (not implemented)
❌ **Streaming Pipeline**: Firehose buffering and transformation (not implemented)
❌ **Cost Effective**: ~$76/month for 1000 sessions/day (future Firehose cost)
❌ **Scalable**: AWS managed services, auto-scaling (future)
❌ **Multiple Consumers**: Easy extension with Salesforce, Amplitude, Athena (future)

**When to Migrate to Firehose:**
- Need real-time analytics queries via CloudWatch Insights
- Want to stream to multiple destinations simultaneously
- Require data transformation before storage
- Need buffering and retry logic for reliability

### Key Files and Resources

**Currently Used:**
- `my-app/src/agent.py`: Agent with analytics collection and direct S3 upload
- S3 Bucket: `pandadoc-voice-analytics-1761683081`
- Agent ID: `CA_9b4oemVRtDEm`

**For Future Firehose Architecture:**
- `my-app/src/utils/analytics_queue.py`: Structured logging utility (not currently used)
- Firehose Stream: `voice-analytics-to-s3` (not created)
- CloudWatch Log Group: `/aws/livekit/pd-voice-trialist-4` (used for app logs, not analytics)

### Key Commands

**Current Implementation:**
```bash
# Deployment
lk agent deploy
lk agent update-secrets --secrets "AWS_ACCESS_KEY_ID=..." --secrets "AWS_S3_BUCKET_NAME=pandadoc-voice-analytics-1761683081"

# Monitoring
lk agent status
lk agent logs --tail
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ --recursive --region us-west-1

# Download and view analytics data
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=29/session-xyz.json - --region us-west-1 | jq
```

**Future Firehose Architecture (NOT implemented):**
```bash
# CloudWatch queries
aws logs tail /aws/livekit/pd-voice-trialist-4 --filter-pattern '{ $._event_type = "session_analytics" }'

# Firehose status
aws firehose describe-delivery-stream --delivery-stream-name voice-analytics-to-s3
```

---

## Document Status Reminder

**CURRENT IMPLEMENTATION (2025-10-29):**
- Agent collects session data during conversation
- Direct S3 upload via boto3 on session end
- Simple, low-cost, low-latency solution

**THIS DOCUMENT:**
- Describes comprehensive Firehose-based streaming architecture
- Most components (CloudWatch, Firehose, subscription filters) are NOT implemented
- Use as reference for future migration to streaming analytics if needed

**For current implementation details**, see the agent code in `my-app/src/agent.py` which handles direct S3 upload.

---

**For questions or issues, refer to the [Monitoring & Debugging](#monitoring--debugging) section or contact the platform team.**