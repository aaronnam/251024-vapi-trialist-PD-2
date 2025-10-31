# Transcription Recording & Persistence Guide

## Current State Analysis

### ✅ What You Have Working

Your agent **DOES capture and export transcriptions**, but only at session end:

1. **In-Memory Collection**: During the conversation, transcripts are held in `session.history`
2. **Session Export**: At shutdown, transcripts are exported via `export_session_data()` function
3. **S3 Storage**: If configured, full transcripts are saved to S3 as compressed JSON
4. **Langfuse Tracing**: Conversation turns are visible in Langfuse traces (but not full transcript text)

### ⚠️ Current Limitations

1. **Only at Session End**: Transcripts are only persisted when the session ends normally
2. **Lost on Crashes**: If the agent crashes, transcript is lost
3. **No Real-time Access**: Can't query transcripts while conversation is ongoing
4. **S3 Optional**: Requires `ANALYTICS_S3_BUCKET` environment variable to be set

## Your Current Implementation

Located in `/my-app/src/agent.py`:

```python
# Lines 1680-1710: Transcript extraction at session end
async def export_session_data():
    # Extract transcript from session history
    transcript = []
    transcript_text = ""

    if hasattr(session, 'history') and session.history:
        chat_messages = list(session.history)
        for msg in chat_messages:
            role = getattr(msg, 'role', 'unknown')
            # Extract text content...
            transcript.append({
                "role": role,
                "content": content_text,
            })
            transcript_text += f"{role.upper()}: {content_text}\n"

    # Compile into session_payload with transcript
    session_payload = {
        "transcript": transcript,
        "transcript_text": transcript_text,
        # ... other data
    }

    # Send to S3 if configured
    await send_to_analytics_queue(session_payload)
```

## Where Transcripts Currently Go

### 1. CloudWatch Logs (Structured JSON)
- **Location**: CloudWatch log group `CA_9b4oemVRtDEm`
- **Format**: JSON with `_event_type: "session_analytics"`
- **Query**: Use CloudWatch Insights to search

### 2. S3 Storage (If Configured)
- **Bucket**: Set via `ANALYTICS_S3_BUCKET` environment variable
- **Path**: `s3://your-bucket/sessions/year=2025/month=10/day=31/{session_id}.json.gz`
- **Format**: Compressed JSON with full transcript
- **Partitioned**: Hive-style for Athena queries

### 3. Langfuse Traces
- **What's Captured**: Individual conversation turns as "observations"
- **What's Missing**: Full transcript text not sent to Langfuse
- **Access**: Via Langfuse UI or API

## How to Enable S3 Transcript Storage

### Step 1: Set Environment Variables

```bash
# Add to your .env.local file
ANALYTICS_S3_BUCKET=pandadoc-voice-transcripts
AWS_REGION=us-west-1
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key

# Deploy to LiveKit Cloud
lk agent update-secrets --secrets-file .env.local
lk agent restart
```

### Step 2: Create S3 Bucket

```bash
# Create bucket with versioning for compliance
aws s3api create-bucket \
  --bucket pandadoc-voice-transcripts \
  --region us-west-1 \
  --create-bucket-configuration LocationConstraint=us-west-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket pandadoc-voice-transcripts \
  --versioning-configuration Status=Enabled
```

### Step 3: Verify It's Working

After a call ends, check S3:

```bash
# List today's transcripts
aws s3 ls s3://pandadoc-voice-transcripts/sessions/year=2025/month=10/day=31/

# Download and view a transcript
aws s3 cp s3://pandadoc-voice-transcripts/sessions/year=2025/month=10/day=31/CAW_abc123.json.gz .
gunzip CAW_abc123.json.gz
cat CAW_abc123.json | jq '.transcript_text'
```

## Recommended Improvements

### 1. Real-time Transcript Streaming (Immediate Access)

Add real-time transcript capture using events:

```python
# Add to your agent.py after session.start()

# Real-time transcript capture
@session.on("conversation_item_added")
def on_conversation_item(item):
    """Capture each conversation turn as it happens"""
    try:
        # Log to CloudWatch immediately
        logger.info(json.dumps({
            "_event_type": "transcript_turn",
            "session_id": ctx.room.name,
            "timestamp": datetime.now().isoformat(),
            "role": item.role,
            "content": item.content,
        }))

        # Optionally send to Langfuse as custom event
        if langfuse_context:
            langfuse_context.score(
                name="transcript_turn",
                value=1,
                comment=f"{item.role}: {item.content[:100]}..."
            )
    except Exception as e:
        logger.error(f"Failed to log transcript turn: {e}")

@session.on("user_input_transcribed")
def on_user_transcribed(text):
    """Capture user speech as soon as it's transcribed"""
    logger.info(f"User said (realtime): {text}")
```

### 2. Periodic Checkpoint Saves (Crash Protection)

Save transcript periodically during conversation:

```python
# Add to your agent.py
import asyncio

async def periodic_transcript_save():
    """Save transcript every 60 seconds as checkpoint"""
    while True:
        await asyncio.sleep(60)  # Save every minute
        try:
            if hasattr(session, 'history') and session.history:
                checkpoint_data = {
                    "session_id": ctx.room.name,
                    "checkpoint_time": datetime.now().isoformat(),
                    "transcript": list(session.history),
                    "is_checkpoint": True
                }

                # Save to S3 as checkpoint
                if os.getenv('ANALYTICS_S3_BUCKET'):
                    key = f"checkpoints/{ctx.room.name}/{datetime.now().isoformat()}.json"
                    # Upload checkpoint...

        except Exception as e:
            logger.error(f"Checkpoint save failed: {e}")

# Start checkpoint task after session.start()
checkpoint_task = asyncio.create_task(periodic_transcript_save())

# Cancel in shutdown callback
ctx.add_shutdown_callback(lambda: checkpoint_task.cancel())
```

### 3. Audio Recording with Egress (Full Compliance)

For complete compliance and quality review, record audio:

```python
from livekit import api

async def entrypoint(ctx: JobContext):
    # Start audio recording at beginning of session
    if os.getenv("ENABLE_AUDIO_RECORDING") == "true":
        req = api.RoomCompositeEgressRequest(
            room_name=ctx.room.name,
            audio_only=True,
            file_outputs=[api.EncodedFileOutput(
                file_type=api.EncodedFileType.OGG,
                filepath=f"recordings/{ctx.room.name}.ogg",
                s3=api.S3Upload(
                    bucket=os.getenv("RECORDINGS_BUCKET"),
                    region=os.getenv("AWS_REGION"),
                    access_key=os.getenv("AWS_ACCESS_KEY_ID"),
                    secret=os.getenv("AWS_SECRET_ACCESS_KEY"),
                ),
            )],
        )

        lkapi = api.LiveKitAPI()
        egress_info = await lkapi.egress.start_room_composite_egress(req)
        logger.info(f"Recording started: {egress_info.egress_id}")
        await lkapi.aclose()

    # Rest of your entrypoint...
```

### 4. Enhanced Langfuse Integration (Full Transcript in Traces)

Send full transcript to Langfuse for better searchability:

```python
# In your export_session_data function
if trace_provider and transcript_text:
    from opentelemetry import trace as otel_trace
    tracer = otel_trace.get_tracer(__name__)

    # Create a span with full transcript
    with tracer.start_as_current_span("session_transcript") as span:
        span.set_attribute("transcript.full_text", transcript_text[:8000])  # Langfuse limit
        span.set_attribute("transcript.turn_count", len(transcript))
        span.set_attribute("transcript.word_count", len(transcript_text.split()))

    # Also update trace metadata
    if langfuse_context:
        langfuse_context.update_current_trace(
            metadata={
                "transcript_available": True,
                "transcript_turns": len(transcript),
                "s3_location": f"s3://{bucket}/{key}" if bucket else None
            }
        )
```

## Finding Transcripts for Your CEO's Call

### Option 1: CloudWatch Logs

```bash
# Search for session with CPQ mention
aws logs filter-log-events \
  --log-group-name "CA_9b4oemVRtDEm" \
  --filter-pattern '{ $._event_type = "session_analytics" && $.transcript_text like /CPQ/ }' \
  --start-time $(date -u -d '24 hours ago' +%s)000 \
  --region us-west-1 \
  --query 'events[*].message' \
  --output text | jq -r '.session_id'
```

### Option 2: S3 Query with Athena

```sql
-- Create Athena table for transcripts
CREATE EXTERNAL TABLE voice_transcripts (
  session_id string,
  transcript_text string,
  transcript array<struct<
    role: string,
    content: string
  >>
)
STORED AS JSON
LOCATION 's3://pandadoc-voice-transcripts/sessions/'
PARTITIONED BY (year int, month int, day int);

-- Query for CPQ conversations
SELECT session_id, transcript_text
FROM voice_transcripts
WHERE transcript_text LIKE '%CPQ%'
  AND year = 2025 AND month = 10 AND day = 31;
```

### Option 3: Download Today's Transcripts

```bash
# Download all transcripts from today
aws s3 sync \
  s3://pandadoc-voice-transcripts/sessions/year=2025/month=10/day=31/ \
  ./transcripts/

# Search locally
grep -r "CPQ" ./transcripts/ | head -5
```

## Compliance Considerations

### Required for Compliance

1. **Consent Tracking**: ✅ Already implemented
   - Your agent asks for consent
   - Tracks consent in `consent_given` field
   - Exports consent timestamp

2. **Data Retention**: ⚠️ Need to implement
   - Add S3 lifecycle policies
   - Delete after retention period
   - Archive to Glacier for long-term

3. **Access Control**: ⚠️ Need to implement
   - Encrypt S3 bucket
   - Restrict IAM permissions
   - Audit trail with CloudTrail

### S3 Lifecycle Policy Example

```json
{
  "Rules": [{
    "Id": "TranscriptRetention",
    "Status": "Enabled",
    "Transitions": [{
      "Days": 30,
      "StorageClass": "GLACIER"
    }],
    "Expiration": {
      "Days": 365
    }
  }]
}
```

## Quick Setup Checklist

To enable full transcript recording right now:

- [ ] Set `ANALYTICS_S3_BUCKET` environment variable
- [ ] Create S3 bucket with versioning
- [ ] Deploy with `lk agent deploy` and `lk agent restart`
- [ ] Make test call and verify S3 upload
- [ ] Optional: Set up Athena for SQL queries
- [ ] Optional: Enable audio recording with Egress
- [ ] Optional: Add real-time streaming for immediate access

## Summary

**You DO have transcript recording**, but it needs these improvements:

1. **Enable S3**: Set `ANALYTICS_S3_BUCKET` to persist transcripts
2. **Add Real-time**: Use events for immediate transcript access
3. **Add Checkpoints**: Periodic saves to prevent loss on crashes
4. **Consider Audio**: Use Egress for full compliance recording
5. **Query Setup**: Use Athena or CloudWatch Insights for searching

Your transcripts are currently:
- ✅ Captured in memory during calls
- ✅ Exported at session end
- ⚠️ Only saved to S3 if configured
- ⚠️ Lost if agent crashes mid-call
- ❌ Not searchable in Langfuse (only turns visible)

**Action Required**: Set `ANALYTICS_S3_BUCKET` to start persisting transcripts immediately.