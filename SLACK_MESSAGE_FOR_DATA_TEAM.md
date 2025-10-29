# Slack Message (Copy-Paste Ready)

---

Hi @Phil Warner (TX) / @hannah.burak - Quick correction on the technical details I shared earlier:

## Corrected Information

**Update Frequency**: ~~Continuous (60-second buffer via Kinesis Firehose)~~
→ **Per-session (direct S3 write when call ends)** - No Firehose currently implemented

**Data Schema** - Each JSON record contains:
- ✅ Session metadata (ID, timestamps, duration, user info)
- ✅ Qualification signals (team size, document volume, integrations, urgency)
- ✅ Voice performance metrics (latency, tokens, audio durations)
- ✅ Tool usage tracking (knowledge searches, meeting bookings)
- ❌ ~~Complete conversation transcripts~~ **NOT INCLUDED** (only structured signals extracted via regex)

## AWS Account Info (Unchanged)
- **Account**: PandaDoc_AI_Operations
- **Account ID**: 365117798398
- **Region**: us-west-1
- **Bucket**: `pandadoc-voice-analytics-1761683081`
- **Path**: `s3://pandadoc-voice-analytics-1761683081/sessions/`
- **Structure**: Date-partitioned (`year=YYYY/month=MM/day=DD/`)
- **Format**: GZIP-compressed JSON (`.gz` files)

## How It Works (Actual)
```
Voice Call Ends → Agent exports session data → Direct S3 Write (boto3)
                                             → CloudWatch Logs (parallel)
```

Files are written directly to S3 when each session completes, not streamed via Firehose.

## For Snowflake Integration
Happy to create IAM policies/roles for cross-account access. Just need:
1. Your Snowflake account ID
2. Snowflake external ID (for assume role trust)
3. Read-only sufficient, or need write access?

Full technical details in the attached document. Let me know what you need for the Snowflake ingestion setup!

---

**Attached**: Full technical spec with sample queries, schema recommendations, and IAM policy guidance
