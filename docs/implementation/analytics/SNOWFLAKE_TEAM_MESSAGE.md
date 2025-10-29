# Message for Snowflake Integration Team

---

Hi team,

We have voice agent analytics data ready for ingestion into Snowflake. Here's everything you need to get started:

## S3 Bucket Details

**AWS Account ID**: `365117798398`
**Bucket**: `pandadoc-voice-analytics-1761683081`
**Region**: `us-west-1`
**Path**: `s3://pandadoc-voice-analytics-1761683081/sessions/`
**Bucket ARN**: `arn:aws:s3:::pandadoc-voice-analytics-1761683081`
**Structure**: Date-partitioned (`year=YYYY/month=MM/day=DD/`)
**Format**: GZIP-compressed newline-delimited JSON (`.gz` files)
**Update Frequency**: Continuous (60-second buffer via Kinesis Firehose)

## Data Schema

Each JSON record contains:
- Session metadata (ID, timestamps, duration, user info)
- Complete conversation transcripts
- Qualification signals (team size, document volume, integrations, urgency)
- Voice performance metrics (latency, tokens, audio durations)
- Tool usage tracking (knowledge searches, meeting bookings)

**Full data schema**: See `docs/implementation/analytics/S3_DATA_SUMMARY.md` in this repo

## Integration Guide

We've prepared a complete integration guide with three setup options:

**Recommended**: Snowflake Storage Integration (most secure, no access keys)
**Guide**: `docs/implementation/analytics/guides/snowflake-integration.md`

The guide includes:
- Step-by-step setup instructions
- IAM policy templates
- Sample Snowflake SQL for table creation and incremental loading
- Testing and verification procedures
- Troubleshooting tips

## Next Steps

1. Review the integration guide and choose your preferred setup approach (we recommend Storage Integration)
2. Let us know which option you'd like to use, and we'll create the necessary IAM policies/roles on our end
3. We'll coordinate the exchange of ARNs/credentials as outlined in the guide

## Quick Access Commands

```bash
# List available files
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive --region us-west-1

# Download and preview a sample file
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=01/day=28/[FILE].gz - \
  --region us-west-1 | gunzip | jq
```

Let me know if you need any additional information or have questions about the data structure!

---

**Documentation Links**:
- Integration guide: `docs/implementation/analytics/guides/snowflake-integration.md`
- Data schema: `docs/implementation/analytics/S3_DATA_SUMMARY.md`
- Complete system reference: `docs/implementation/analytics/01-DEPLOYMENT_REFERENCE.md`
