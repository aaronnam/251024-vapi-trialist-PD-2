# Corrected S3 Bucket Information for Data Team

**To**: Phil Warner, Hannah Burak
**Re**: Voice Agent S3 Analytics - Corrected Technical Details

---

## S3 Bucket Details

**Bucket**: `pandadoc-voice-analytics-1761683081`

**Path**: `s3://pandadoc-voice-analytics-1761683081/sessions/`

**Structure**: Date-partitioned (`year=YYYY/month=MM/day=DD/`)

**Format**: GZIP-compressed newline-delimited JSON (`.gz` files)

**Update Frequency**: ~~Continuous (60-second buffer via Kinesis Firehose)~~ **Per-session (direct S3 write when call ends)**

---

## AWS Account Details

**AWS Account ID**: `365117798398`

**Account Name**: `PandaDoc_AI_Operations`

**Region**: `us-west-1`

**Bucket ARN**: `arn:aws:s3:::pandadoc-voice-analytics-1761683081`

---

## Data Schema

Each JSON record contains:

- ✅ Session metadata (ID, timestamps, duration, user info)
- ❌ ~~Complete conversation transcripts~~ **NOT INCLUDED** (lightweight regex-based signals only)
- ✅ Qualification signals (team size, document volume, integrations, urgency)
- ✅ Voice performance metrics (latency, tokens, audio durations)
- ✅ Tool usage tracking (knowledge searches, meeting bookings)
- ✅ Cost breakdown (OpenAI, Deepgram, ElevenLabs costs per session)

---

## Important Corrections

### ❌ What I Said Originally (INCORRECT)

1. **Update Frequency**: "Continuous (60-second buffer via Kinesis Firehose)"
2. **Transcripts**: "Complete conversation transcripts"

### ✅ What's Actually Implemented

1. **Update Frequency**: Direct S3 write when each call session ends (not streaming, no Firehose)
2. **Transcripts**: NOT included in exports (only structured qualification signals extracted via regex)

---

## Technical Architecture (Actual Implementation)

```
Voice Call Ends
     ↓
Agent: export_session_data()
     ↓
analytics_queue.py: send_to_analytics_queue()
     ↓
     ├─→ CloudWatch Logs (structured JSON)
     └─→ S3 Direct Write (GZIP compressed, date partitioned)
```

**No Firehose** - Files are written directly to S3 using boto3 when each session completes.

---

## S3 File Structure

```
s3://pandadoc-voice-analytics-1761683081/
└── sessions/
    └── year=2025/
        └── month=10/
            └── day=29/
                ├── rm_abc123.json.gz
                ├── rm_def456.json.gz
                └── rm_xyz789.json.gz
```

Each file is named by `session_id` (LiveKit room name format: `rm_*`).

---

## Sample Data Access

```bash
# List all sessions for a specific date
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=29/ \
  --region us-west-1

# Download and view a specific session
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=29/[SESSION_ID].json.gz - \
  --region us-west-1 | gunzip | jq .

# Copy all sessions for a date range to local
aws s3 sync s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/ ./local_data/ \
  --region us-west-1
```

---

## Snowflake Integration Notes

For Snowflake ingestion, you'll need:

1. **External Stage** pointing to this S3 bucket
2. **IAM Role/Policy** for cross-account access from Snowflake
3. **File Format** definition for GZIP JSON with date partitioning
4. **Table Schema** matching the session data structure

### Recommended Table Structure

```sql
CREATE TABLE voice_agent_sessions (
  session_id VARCHAR(100),
  user_email VARCHAR(255),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  duration_seconds NUMBER,
  discovered_signals VARIANT,  -- JSON object
  tool_calls ARRAY,
  metrics_summary VARIANT,     -- JSON object
  cost_summary VARIANT,        -- JSON object
  conversation_state VARCHAR(50),
  -- Partition columns
  year NUMBER,
  month NUMBER,
  day NUMBER
);
```

### IAM Policy Needed

I can create an IAM policy/role for Snowflake cross-account access if needed. Let me know:
- Your Snowflake account ID
- Snowflake external ID (for assume role trust policy)
- Read-only access sufficient, or need write access too?

---

## Current Status

- ✅ S3 bucket created and configured
- ✅ Direct S3 write implemented (deployed 2025-10-29)
- ✅ Date partitioning enabled (Hive-style for Athena/Snowflake compatibility)
- ✅ GZIP compression enabled (~80% storage savings)
- ✅ Tested and verified working
- ❌ No Firehose (future enhancement if streaming needed)
- ❌ No transcripts (can add if needed for analysis)

---

## Questions?

Let me know if you need:
1. IAM policies/roles for Snowflake access
2. Sample session JSON for schema design
3. Transcripts added to the export payload
4. Different partitioning scheme
5. Additional fields in the data schema
