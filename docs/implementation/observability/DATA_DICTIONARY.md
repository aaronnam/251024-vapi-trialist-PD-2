# Voice Agent Data Dictionary

**Complete reference** for all data fields available in S3 session files and CloudWatch logs.

**Last Updated**: October 31, 2025
**Agent Version**: v20251031051456

---

## Table of Contents

1. [S3 Session Data](#s3-session-data)
2. [CloudWatch Log Fields](#cloudwatch-log-fields)
3. [Field Relationships](#field-relationships)
4. [Data Types Reference](#data-types-reference)
5. [Usage Examples](#usage-examples)

---

## S3 Session Data

All session files are stored in S3 with gzip compression:
- **Path**: `s3://pandadoc-voice-analytics-1761683081/sessions/year=YYYY/month=MM/day=DD/session_id.json.gz`
- **Format**: JSON (gzip compressed)
- **Encoding**: UTF-8
- **Max Size**: ~2-5 KB compressed, ~10-20 KB uncompressed

### Complete Field Listing

| Field | Type | Always Present | Example | Source | Description |
|-------|------|----------------|---------|--------|-------------|
| **session_id** | string | ✅ Yes | `"pandadoc_trial_1761887896468_rdc63e"` | LiveKit room name | Unique session identifier |
| **user_email** | string | ⚠️ Conditional | `"aaron.nam@pandadoc.com"` | Agent extraction from conversation | User's email address (only if provided during call) |
| **user_metadata** | object | ✅ Yes | `{"user_email": "...", "session_start": "..."}` | Agent session data | Metadata passed from frontend/caller |
| **start_time** | string (ISO 8601) | ✅ Yes | `"2025-10-31T05:18:16.953621"` | Agent initialization | Session start timestamp (UTC with microseconds) |
| **end_time** | string (ISO 8601) | ✅ Yes | `"2025-10-31T05:19:32.504569"` | Session shutdown | Session end timestamp (UTC with microseconds) |
| **duration_seconds** | number | ✅ Yes | `75.550956` | Calculated: end_time - start_time | Total session duration in seconds (float) |
| **discovered_signals** | object | ✅ Yes | See [Discovered Signals](#discovered-signals) | Agent conversation analysis | Business qualification data extracted during call |
| **tool_calls** | array | ✅ Yes | `[{"tool": "search_docs", "timestamp": "...", ...}]` | Agent tool execution tracking | All tool/function calls made during session |
| **metrics_summary** | object | ✅ Yes | `{"total_metrics": 0, "metrics": {}}` | LiveKit UsageSummary | Performance metrics from LiveKit SDK |
| **cost_summary** | object | ✅ Yes | See [Cost Summary](#cost-summary) | Agent cost tracking | Token usage and estimated costs by provider |
| **conversation_notes** | array | ✅ Yes | `["User mentioned integration with Salesforce"]` | Agent note-taking | Important points captured during conversation |
| **conversation_state** | string | ✅ Yes | `"GREETING"` / `"QUALIFYING"` / `"HELPING"` | Agent state machine | Current conversation phase |
| **transcript** | array | ✅ Yes | See [Transcript Array](#transcript-array) | Extracted from ChatContext | Structured conversation transcript |
| **transcript_text** | string | ✅ Yes | `"ASSISTANT: Hi...\nUSER: Yes.\n..."` | Formatted from transcript array | Plain text formatted transcript |
| **consent_obtained** | boolean | ✅ Yes | `true` / `false` | Agent consent tracking | Whether user gave recording consent |
| **consent_timestamp** | string (ISO 8601) | ⚠️ If consent given | `"2025-10-31T05:18:25.123Z"` | Agent consent tracking | When consent was obtained |

---

### Discovered Signals

Business intelligence extracted during the conversation.

**Type**: Object with the following fields:

| Field | Type | Default | Example | Description |
|-------|------|---------|---------|-------------|
| **team_size** | number | `0` | `5` | Number of team members mentioned |
| **monthly_volume** | number | `0` | `100` | Monthly document volume mentioned |
| **integration_needs** | array[string] | `[]` | `["salesforce", "hubspot"]` | Integrations user mentioned needing |
| **urgency** | string\|null | `null` | `"high"` / `"medium"` / `"low"` | Urgency level detected |
| **qualification_tier** | string\|null | `null` | `"high_value"` / `"medium"` / `"low"` | Qualification assessment |
| **industry** | string\|null | `null` | `"Healthcare"` | Industry sector mentioned |
| **location** | string\|null | `null` | `"San Francisco"` | Geographic location |
| **use_case** | string\|null | `null` | `"Sales proposals"` | Primary use case |
| **current_tool** | string\|null | `null` | `"DocuSign"` | Current solution being replaced |
| **pain_points** | array[string] | `[]` | `["Manual workflows", "No templates"]` | Pain points mentioned |
| **decision_timeline** | string\|null | `null` | `"This quarter"` | Decision-making timeline |
| **budget_authority** | string\|null | `null` | `"decision_maker"` / `"influencer"` | Budget authority level |
| **team_structure** | string\|null | `null` | `"Sales team of 10"` | Team structure description |

**Note**: These fields are populated during conversation via agent analysis and tool calls. They start with default values and are updated as the conversation progresses.

---

### Cost Summary

Token usage and cost estimates by provider.

**Type**: Object with the following fields:

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| **openai_tokens** | number | `6382` | Total tokens used by OpenAI LLM (input + output) |
| **openai_cost** | number | `0.00098115` | Estimated cost for OpenAI usage ($) |
| **deepgram_minutes** | number | `0.831666666666665` | Audio minutes processed by Deepgram STT |
| **deepgram_cost** | number | `0.00005960277777777767` | Estimated cost for Deepgram usage ($) |
| **cartesia_characters** | number | `412` | Characters synthesized by Cartesia TTS |
| **cartesia_cost** | number | `0.00002472` | Estimated cost for Cartesia usage ($) |
| **unleash_searches** | number | `0` | Number of Unleash knowledge base searches |
| **total_estimated_cost** | number | `0.0010654727777777775` | Total estimated cost for session ($) |

**Pricing (as of Oct 2025)**:
- OpenAI GPT-4o-mini: ~$0.15/1M input tokens, ~$0.60/1M output tokens
- Deepgram STT: ~$0.0043/minute
- Cartesia TTS: ~$0.06/1M characters
- Unleash: Variable (knowledge base searches)

---

### Transcript Array

Structured conversation history with role attribution.

**Type**: Array of objects with the following structure:

```json
[
  {
    "role": "assistant",
    "content": "Hi! I'm your AI PandaDoc Trial Success Specialist..."
  },
  {
    "role": "user",
    "content": "Yes."
  }
]
```

**Fields per message**:

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| **role** | string | ✅ Yes | `"assistant"` or `"user"` |
| **content** | string | ✅ Yes | Message text content |

**Possible roles**:
- `"assistant"` - AI agent responses
- `"user"` - User speech transcriptions
- `"system"` - System messages (rare)

**Important Notes**:
- Messages are in chronological order
- Empty or whitespace-only content is filtered out
- Truncated messages indicate user hung up mid-response
- Array can be empty if transcript capture failed (pre-fix sessions)

---

### Tool Calls Array

Tracking of all tool/function executions during the session.

**Type**: Array of objects

**Structure** (example):
```json
[
  {
    "tool": "search_docs",
    "timestamp": "2025-10-31T05:18:30.123Z",
    "arguments": {"query": "salesforce integration"},
    "result": "...",
    "duration_ms": 234,
    "success": true
  }
]
```

**Fields per tool call**:

| Field | Type | Description |
|-------|------|-------------|
| **tool** | string | Tool/function name |
| **timestamp** | string (ISO 8601) | When tool was called |
| **arguments** | object | Tool input parameters |
| **result** | any | Tool return value (if successful) |
| **duration_ms** | number | Execution time in milliseconds |
| **success** | boolean | Whether tool succeeded |
| **error** | string (optional) | Error message if failed |

**Common tool names**:
- `search_docs` - Unleash knowledge base search
- `search_intercom` - Intercom article search
- `qualify_lead` - Lead qualification assessment
- `update_salesforce` - Salesforce CRM update
- `book_meeting` - Calendar booking

---

### User Metadata Object

Metadata passed from the frontend or calling application.

**Type**: Object with dynamic fields

**Common fields**:

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| **user_email** | string | `"user@example.com"` | Email from frontend |
| **session_start** | string (ISO 8601) | `"2025-10-31T05:18:16.468Z"` | Frontend session start time |
| **utm_source** | string (optional) | `"google"` | Marketing attribution |
| **utm_campaign** | string (optional) | `"trial_outreach"` | Campaign identifier |
| **trial_start_date** | string (optional) | `"2025-10-15"` | When trial began |
| **plan_tier** | string (optional) | `"business"` | Trial plan level |

**Note**: This object is flexible and can contain any metadata passed from the calling application. Fields vary based on frontend implementation.

---

## CloudWatch Log Fields

All agent runtime logs are sent to CloudWatch Logs with structured JSON format.

**Log Group**: `CA_9b4oemVRtDEm`
**Region**: `us-west-1`
**Format**: JSON (one object per log line)
**Retention**: 30 days (configurable)

### Standard Log Fields

Every log message includes these standard fields:

| Field | Type | Always Present | Example | Description |
|-------|------|----------------|---------|-------------|
| **message** | string | ✅ Yes | `"✅ Session started for email: user@example.com"` | Log message text |
| **level** | string | ✅ Yes | `"INFO"` / `"WARNING"` / `"ERROR"` / `"DEBUG"` | Log severity level |
| **name** | string | ✅ Yes | `"agent"` / `"utils.telemetry"` / `"analytics_queue"` | Logger name (module) |
| **room** | string | ✅ Yes | `"pandadoc_trial_1761886092749_q7z684"` | Session/room identifier |
| **pid** | number | ✅ Yes | `196` | Process ID of agent worker |
| **job_id** | string | ✅ Yes | `"AJ_ferSJQoXVGiY"` | LiveKit job identifier |
| **timestamp** | string (ISO 8601) | ✅ Yes | `"2025-10-31T04:48:13.296258+00:00"` | Log timestamp (UTC) |

---

### Log Level Meanings

| Level | Purpose | Example Use Cases |
|-------|---------|-------------------|
| **DEBUG** | Detailed diagnostic information | `"🔍 Processing ChatMessage 0: role=assistant"` |
| **INFO** | General informational messages | `"✅ Session started for email: user@example.com"` |
| **WARNING** | Warning messages (non-critical) | `"⚠️ High latency: 2.42s (EOU: 0.62s, LLM: 1.57s, TTS: 0.23s)"` |
| **ERROR** | Error messages (failures) | `"❌ Transcript extraction failed: 'ChatContext' object is not iterable"` |

---

### Common Log Message Patterns

#### Session Lifecycle

| Pattern | Level | Example | When |
|---------|-------|---------|------|
| Tracing enabled | INFO | `"✅ Tracing enabled with LangFuse at https://us.cloud.langfuse.com"` | Session start |
| Session started | INFO | `"✅ Session started for email: aaron.nam@pandadoc.com"` | After user email extracted |
| User ID updated | INFO | `"✅ Langfuse updated with user ID: aaron.nam@pandadoc.com"` | After email extraction |
| Analytics uploaded | INFO | `"✅ Analytics uploaded to S3: s3://bucket/..."` | Session end |
| Session complete | INFO | `"Analytics data collection complete for session {id}"` | Session end |

#### Performance Warnings

| Pattern | Level | Fields in Message | Example |
|---------|-------|-------------------|---------|
| High latency | WARNING | EOU, LLM, TTS times | `"⚠️ High latency: 2.42s (EOU: 0.62s, LLM: 1.57s, TTS: 0.23s)"` |

**Latency breakdown components**:
- **EOU**: End-of-utterance detection time
- **LLM**: Language model response time
- **TTS**: Text-to-speech synthesis time

#### Error Messages

| Pattern | Level | Example | Indicates |
|---------|-------|---------|-----------|
| Transcript extraction failed | ERROR | `"❌ Transcript extraction failed: 'ChatContext' object is not iterable"` | Bug in transcript code (fixed in v20251031051456) |
| Tool call failed | ERROR | `"❌ Tool call failed: search_docs - timeout after 5s"` | External service timeout |
| S3 upload failed | ERROR | `"Failed to upload to S3: AccessDenied"` | IAM permissions issue |

#### Diagnostic Messages

| Pattern | Level | Example | Purpose |
|---------|-------|---------|---------|
| Transcript extraction | INFO | `"🔍 Transcript extraction: 6 items in session.history"` | Debugging transcript capture |
| Content item type | DEBUG | `"🔍   Content item 0: type=str"` | Debugging content extraction |
| ChatMessage processing | DEBUG | `"🔍 Processing ChatMessage 0: role=assistant"` | Debugging message iteration |
| Captured message | INFO | `"✅ Captured user message: Yes."` | Confirming transcript capture |

---

## Field Relationships

### How Fields Connect

```
┌─────────────────────────────────────────────────────────────┐
│                     S3 Session Data                          │
│                                                               │
│  session_id ─────────────────────────────────────────────┐  │
│       │                                                    │  │
│       │  Matches "room" field in CloudWatch logs          │  │
│       │                                                    │  │
│       └──> room: "pandadoc_trial_1761887896468_rdc63e"    │  │
│                                                               │
│  user_email ─────────────────────────────────────────────┐  │
│       │                                                    │  │
│       │  Extracted during conversation, appears in logs   │  │
│       │                                                    │  │
│       └──> "✅ Session started for email: user@..."       │  │
│                                                               │
│  transcript[] ───────────────────────────────────────────┐  │
│       │                                                    │  │
│       │  Built from ChatContext in shutdown callback      │  │
│       │                                                    │  │
│       └──> "✅ Transcript extraction complete: 5 msgs"    │  │
│                                                               │
│  cost_summary.total_estimated_cost ──────────────────────┐  │
│       │                                                    │  │
│       │  Appears in session summary log                   │  │
│       │                                                    │  │
│       └──> "Total cost: $0.0011"                          │  │
└───────────────────────────────────────────────────────────┘
```

### Joining S3 and CloudWatch Data

**By session_id / room**:
```sql
-- Conceptual join (not actual SQL)
SELECT
  s3.session_id,
  s3.user_email,
  s3.transcript,
  s3.total_estimated_cost,
  cw.logs
FROM s3_sessions s3
JOIN cloudwatch_logs cw ON s3.session_id = cw.room
WHERE s3.session_id = 'pandadoc_trial_1761887896468_rdc63e'
```

**Practical approach**:
1. Get session_id from S3 file name or content
2. Query CloudWatch logs filtering by `room` field
3. Correlate using timestamps if needed

---

## Data Types Reference

### String Formats

| Type | Format | Example | Notes |
|------|--------|---------|-------|
| **ISO 8601 Timestamp** | `YYYY-MM-DDTHH:MM:SS.ssssss` | `"2025-10-31T05:18:16.953621"` | Always UTC, microsecond precision |
| **ISO 8601 with TZ** | `YYYY-MM-DDTHH:MM:SS.ssssss+00:00` | `"2025-10-31T04:48:13.296258+00:00"` | CloudWatch logs include timezone |
| **Session ID** | `pandadoc_trial_{timestamp}_{random}` | `"pandadoc_trial_1761887896468_rdc63e"` | Unique per session |
| **Email** | Standard email format | `"aaron.nam@pandadoc.com"` | Validated during extraction |

### Number Formats

| Type | Format | Example | Precision |
|------|--------|---------|-----------|
| **Duration** | Float (seconds) | `75.550956` | 6 decimal places |
| **Cost** | Float (USD) | `0.0010654727777777775` | 16+ decimal places |
| **Token Count** | Integer | `6382` | Whole number |
| **Timestamp (Unix)** | Integer (milliseconds) | `1761887896468` | Milliseconds since epoch |

### Enum Values

#### Log Levels
- `"DEBUG"` - Detailed diagnostic information
- `"INFO"` - General informational messages
- `"WARNING"` - Warning messages
- `"ERROR"` - Error messages

#### Conversation States
- `"GREETING"` - Initial greeting phase
- `"CONSENT"` - Obtaining recording consent
- `"QUALIFYING"` - Asking qualification questions
- `"HELPING"` - Answering questions / providing help
- `"BOOKING"` - Scheduling a meeting
- `"CLOSING"` - Wrapping up conversation

#### Message Roles
- `"assistant"` - AI agent
- `"user"` - Human user
- `"system"` - System messages

#### Qualification Tiers
- `"high_value"` - High-priority lead
- `"medium"` - Medium-priority lead
- `"low"` - Low-priority lead
- `null` - Not yet qualified

---

## Usage Examples

### Query: Get All Sessions with Transcripts

```bash
# Download all sessions from a specific date
aws s3 sync \
  s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=31/ \
  ./sessions/ \
  --region us-west-1

# Extract sessions with non-empty transcripts
for file in ./sessions/*.json.gz; do
  transcript_length=$(gunzip -c "$file" | jq '.transcript | length')
  if [ "$transcript_length" -gt 0 ]; then
    session_id=$(gunzip -c "$file" | jq -r '.session_id')
    user_email=$(gunzip -c "$file" | jq -r '.user_email')
    echo "$session_id,$user_email,$transcript_length"
  fi
done
```

---

### Query: Find Sessions Mentioning Specific Topics

```bash
# Find all sessions mentioning "Salesforce"
aws s3 sync \
  s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=31/ \
  ./sessions/ \
  --region us-west-1

# Search transcript text
for file in ./sessions/*.json.gz; do
  if gunzip -c "$file" | jq -r '.transcript_text' | grep -qi "salesforce"; then
    session_id=$(gunzip -c "$file" | jq -r '.session_id')
    user_email=$(gunzip -c "$file" | jq -r '.user_email')
    echo "Found: $session_id ($user_email)"
    gunzip -c "$file" | jq '.transcript'
  fi
done
```

---

### Query: Calculate Average Session Cost by Day

```bash
# Get all sessions and calculate average cost
aws s3 sync \
  s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=31/ \
  ./sessions/ \
  --region us-west-1

# Calculate average
total_cost=0
count=0

for file in ./sessions/*.json.gz; do
  cost=$(gunzip -c "$file" | jq -r '.cost_summary.total_estimated_cost')
  total_cost=$(echo "$total_cost + $cost" | bc)
  count=$((count + 1))
done

avg_cost=$(echo "scale=6; $total_cost / $count" | bc)
echo "Average cost per session: \$$avg_cost"
echo "Total sessions: $count"
echo "Total cost: \$$total_cost"
```

---

### Query: Find High-Value Qualified Leads

```bash
# Find sessions with high_value qualification
for file in ./sessions/*.json.gz; do
  qual=$(gunzip -c "$file" | jq -r '.discovered_signals.qualification_tier')
  if [ "$qual" = "high_value" ]; then
    session_id=$(gunzip -c "$file" | jq -r '.session_id')
    user_email=$(gunzip -c "$file" | jq -r '.user_email')
    team_size=$(gunzip -c "$file" | jq -r '.discovered_signals.team_size')
    monthly_volume=$(gunzip -c "$file" | jq -r '.discovered_signals.monthly_volume')

    echo "High-value lead: $user_email"
    echo "  Team size: $team_size"
    echo "  Monthly volume: $monthly_volume"
    echo "  Session: $session_id"
    echo ""
  fi
done
```

---

### Query: Get CloudWatch Logs for Specific Session

```bash
# Get all logs for a session
SESSION_ID="pandadoc_trial_1761887896468_rdc63e"

aws logs filter-log-events \
  --log-group-name CA_9b4oemVRtDEm \
  --filter-pattern "\"$SESSION_ID\"" \
  --region us-west-1 \
  --query 'events[*].message' \
  --output text | while read line; do
    echo "$line" | jq '.'
  done
```

---

### Query: Analyze Latency Patterns

```bash
# Extract latency warnings from CloudWatch
aws logs filter-log-events \
  --log-group-name CA_9b4oemVRtDEm \
  --filter-pattern '"High latency"' \
  --region us-west-1 \
  --start-time $(($(date -d "1 day ago" +%s) * 1000)) \
  --query 'events[*].message' \
  --output text | while read line; do
    echo "$line" | jq -r '.message'
  done | grep -oP '\d+\.\d+s' | sort -n
```

---

### Query: Export Session Data for Salesforce Sync

```bash
# Get yesterday's sessions with emails for Salesforce sync
YESTERDAY=$(date -d yesterday +%Y-%m-%d)
YEAR=$(date -d yesterday +%Y)
MONTH=$(date -d yesterday +%m)
DAY=$(date -d yesterday +%d)

aws s3 sync \
  s3://pandadoc-voice-analytics-1761683081/sessions/year=$YEAR/month=$MONTH/day=$DAY/ \
  ./sessions/ \
  --region us-west-1

# Extract fields needed for Salesforce
for file in ./sessions/*.json.gz; do
  email=$(gunzip -c "$file" | jq -r '.user_email')

  if [ "$email" != "null" ] && [ -n "$email" ]; then
    session_id=$(gunzip -c "$file" | jq -r '.session_id')
    start_time=$(gunzip -c "$file" | jq -r '.start_time')
    duration=$(gunzip -c "$file" | jq -r '.duration_seconds')
    transcript=$(gunzip -c "$file" | jq -r '.transcript_text')

    echo "Session: $session_id"
    echo "Email: $email"
    echo "Start: $start_time"
    echo "Duration: ${duration}s"
    echo "Transcript length: ${#transcript} chars"
    echo "---"
  fi
done
```

---

## Notes and Best Practices

### S3 Data

1. **Always decompress before reading**: Files are gzip compressed
2. **Check for empty transcripts**: Pre-fix sessions (before Oct 31) have empty transcript arrays
3. **Handle missing emails**: Not all sessions have email addresses
4. **Use jq for JSON parsing**: More reliable than grep/awk for structured data
5. **Timestamp precision**: Start/end times have microsecond precision for accurate duration

### CloudWatch Logs

1. **Filter by room/session_id**: Most efficient way to find session-specific logs
2. **Use structured JSON parsing**: All logs are valid JSON
3. **Mind the retention period**: Logs expire after 30 days (configurable)
4. **Combine with S3 data**: Logs provide debugging context, S3 has complete session data
5. **Watch for emoji markers**: `✅` `❌` `⚠️` `🔍` help filter log types

### Data Analysis

1. **Join on session_id**: Primary key for correlating S3 and CloudWatch data
2. **Calculate costs**: Use cost_summary for accurate per-session costs
3. **Transcript quality**: Check transcript length before using for analysis
4. **Qualification data**: May be incomplete if conversation was short
5. **Tool calls**: Empty array if no tools were invoked during session

---

## Changelog

| Date | Change | Impact |
|------|--------|--------|
| 2025-10-31 | Added transcript capture | `transcript` and `transcript_text` now populated |
| 2025-10-30 | Fixed S3 IAM permissions | Session files now upload correctly |
| 2025-10-31 | Fixed string content handling | Transcript extraction works reliably |

---

**Document Version**: 1.0
**Last Updated**: October 31, 2025
**Maintained By**: Engineering Team
