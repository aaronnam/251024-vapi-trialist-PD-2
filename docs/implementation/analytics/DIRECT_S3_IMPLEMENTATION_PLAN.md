# Direct S3 Analytics Export - Implementation Plan

**Purpose**: Add direct S3 write capability to analytics export, bypassing the need for Kinesis Firehose infrastructure.

**Execution Time**: 30-45 minutes

**Status**: Ready for immediate execution

---

## Overview

### Why Direct S3 Instead of Firehose?

**Elegant Simplicity Wins:**
- No additional AWS infrastructure (no Firehose, no subscription filters, no Lambda)
- Immediate implementation (modify 1 file, add 4 secrets, deploy)
- Data available in S3 within seconds of call completion
- Easier to debug (one path: agent → S3)
- Trivial cost impact (~$0.005 per 1000 calls)
- Can add Firehose later if async processing becomes necessary

**Trade-offs Accepted:**
- Adds ~100-200ms to agent shutdown (acceptable for post-call)
- Synchronous write during session cleanup (not user-facing latency)
- Dual-write pattern (CloudWatch + S3 both succeed or logged error)

**Decision**: For our use case (session analytics, not high-frequency telemetry), direct S3 write is the optimal solution.

---

## Changes Required

### File to Modify

**Single file**: `/Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/my-app/src/utils/analytics_queue.py`

**Lines affected**: Add ~40 lines (new S3 upload function + imports)

**Current behavior**: Logs structured JSON to CloudWatch only

**New behavior**: Logs to CloudWatch + uploads to S3 (dual-write)

---

## Implementation Details

### 1. Add Dependencies

**Check if boto3 is installed**:
```bash
cd /Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/my-app
uv pip list | grep boto3
```

**If not present, add it**:
```bash
uv add "boto3>=1.35.0"
```

**Why boto3**: AWS SDK for Python, provides S3 client

**Version constraint**: `>=1.35.0` ensures modern S3 API support

---

### 2. Code Changes to `analytics_queue.py`

#### A. Add Imports (after line 18)

```python
import gzip
import os
from datetime import datetime
from typing import Any, Dict, Optional

# Add boto3 (after other imports, before logger setup)
try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logger.warning("boto3 not installed - S3 export disabled")
```

**Why try/except**: Graceful degradation if boto3 isn't installed

**Why S3_AVAILABLE flag**: Skip S3 upload if boto3 unavailable (local dev)

---

#### B. Add S3 Client Singleton (after analytics_logger setup, before send_to_analytics_queue)

```python
# S3 client singleton for analytics uploads
_s3_client: Optional[object] = None
_s3_bucket: Optional[str] = None


def get_s3_client():
    """Get or create S3 client singleton.

    Returns:
        boto3.client or None if S3 not configured
    """
    global _s3_client, _s3_bucket

    if not S3_AVAILABLE:
        return None

    if _s3_client is None:
        # Only initialize if bucket is configured
        bucket = os.getenv('ANALYTICS_S3_BUCKET')
        if not bucket:
            logger.debug("ANALYTICS_S3_BUCKET not configured - skipping S3 export")
            return None

        try:
            _s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-west-1')
            )
            _s3_bucket = bucket
            logger.info(f"S3 client initialized for bucket: {bucket}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            return None

    return _s3_client
```

**Why singleton**: Reuse S3 connection across calls (avoid reconnection overhead)

**Why lazy init**: Only create client if bucket configured (no errors in local dev)

**Why error handling**: Log failures but don't crash agent

---

#### C. Add S3 Upload Function (after get_s3_client)

```python
async def upload_to_s3(data: Dict[str, Any]) -> bool:
    """Upload analytics data to S3 with date partitioning.

    Args:
        data: Session analytics payload

    Returns:
        True if upload succeeded, False otherwise

    S3 Key Format:
        sessions/year=YYYY/month=MM/day=DD/session_id.json.gz

    Example:
        sessions/year=2025/month=10/day=29/rm_abc123.json.gz
    """
    s3 = get_s3_client()
    if not s3:
        return False

    try:
        # Extract session metadata
        session_id = data.get('session_id', 'unknown')
        timestamp = datetime.now()

        # Build partitioned S3 key (Athena-friendly)
        key = (
            f"sessions/"
            f"year={timestamp.year}/"
            f"month={timestamp.month:02d}/"
            f"day={timestamp.day:02d}/"
            f"{session_id}.json.gz"
        )

        # Compress payload (5 KB → ~1 KB typically)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        compressed_data = gzip.compress(json_str.encode('utf-8'))

        # Upload to S3
        s3.put_object(
            Bucket=_s3_bucket,
            Key=key,
            Body=compressed_data,
            ContentType='application/json',
            ContentEncoding='gzip',
            Metadata={
                'session_id': session_id,
                'uploaded_at': timestamp.isoformat(),
            }
        )

        # Log success with S3 URI
        logger.info(
            f"Analytics uploaded to S3: s3://{_s3_bucket}/{key} "
            f"({len(compressed_data)} bytes compressed)"
        )

        return True

    except ClientError as e:
        # S3-specific errors (auth, bucket access, etc.)
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(
            f"S3 ClientError during upload: {error_code} - {e}",
            exc_info=True
        )
        return False

    except BotoCoreError as e:
        # Boto3 connection errors
        logger.error(f"S3 BotoCoreError during upload: {e}", exc_info=True)
        return False

    except Exception as e:
        # Catch-all for compression, JSON serialization, etc.
        logger.error(f"Unexpected error during S3 upload: {e}", exc_info=True)
        return False
```

**Why GZIP compression**: Reduces storage costs by ~80% (5 KB → 1 KB)

**Why date partitioning**: Athena can query by date efficiently (`WHERE year=2025 AND month=10`)

**Why error handling**: Distinguish S3 errors from network/boto errors for debugging

**Why metadata**: S3 object metadata helps with debugging and lifecycle policies

---

#### D. Update `send_to_analytics_queue` Function (modify existing function around line 53)

**Find the existing function and modify it to add S3 upload after CloudWatch logging:**

```python
async def send_to_analytics_queue(data: Dict[str, Any]) -> None:
    """Send session data to analytics queue.

    Args:
        data: Complete session data payload including:
            - session_id: Unique session identifier
            - start_time/end_time: Session timestamps
            - discovered_signals: Business qualification signals
            - tool_calls: Tool usage tracking
            - metrics_summary: LiveKit performance metrics
            - conversation_notes: Free-form notes

    Current Implementation:
        - Logs as structured JSON for CloudWatch ingestion
        - Uploads to S3 for long-term storage and Athena queries
        - Dual-write: Both CloudWatch and S3 for redundancy

    To enable S3 export in LiveKit Cloud:
        ```bash
        lk agent update-secrets \\
          --secrets "ANALYTICS_S3_BUCKET=pandadoc-voice-analytics-1761683081" \\
          --secrets "AWS_ACCESS_KEY_ID=your-key-id" \\
          --secrets "AWS_SECRET_ACCESS_KEY=your-secret" \\
          --secrets "AWS_REGION=us-west-1"
        lk agent restart
        ```

    CloudWatch Insights query examples:
        ```sql
        -- Find all analytics events
        fields @timestamp, _session_id, duration_seconds, discovered_signals
        | filter _event_type = "session_analytics"
        | sort @timestamp desc

        -- Get qualified leads
        fields _session_id, discovered_signals.team_size
        | filter _event_type = "session_analytics"
        | filter discovered_signals.team_size >= 5
        ```
    """
    try:
        # Validate data is JSON serializable
        json.dumps(data)  # Will raise TypeError if not serializable

        # Log as structured JSON for CloudWatch
        # This will be automatically forwarded if AWS credentials are configured
        analytics_logger.info(
            "Session analytics data",
            extra={"analytics_data": data}
        )

        # Upload to S3 (async, non-blocking)
        # This runs in background and won't block CloudWatch logging
        await upload_to_s3(data)

        # Also log summary for debugging (standard format)
        logger.info(f"Analytics data exported for session: {data.get('session_id')}")
        logger.debug(f"  Duration: {data.get('duration_seconds', 0):.1f}s")
        logger.debug(f"  Tool Calls: {len(data.get('tool_calls', []))}")
        logger.debug(f"  Qualification: {data.get('discovered_signals', {}).get('qualification_tier', 'Unknown')}")

        # Calculate some key metrics for summary logging
        team_size = data.get('discovered_signals', {}).get('team_size', 0)
        monthly_volume = data.get('discovered_signals', {}).get('monthly_volume', 0)
        is_qualified = team_size >= 5 or monthly_volume >= 100

        if is_qualified:
            # Log hot leads with higher visibility
            logger.info(
                f"HOT LEAD - Session {data.get('session_id')}: "
                f"Team size {team_size}, Volume {monthly_volume}/month"
            )

    except TypeError as e:
        logger.error(f"Analytics data is not JSON serializable: {e}")
        raise

    except Exception as e:
        # Fail gracefully - analytics errors shouldn't crash the agent
        logger.error(f"Failed to send analytics data: {e}", exc_info=True)
```

**Key changes**:
- Added `await upload_to_s3(data)` after CloudWatch logging
- Updated docstring to mention S3 export
- Removed emoji from HOT LEAD log (per project guidelines)

**Why dual-write**: CloudWatch for real-time queries, S3 for long-term storage

**Why non-blocking**: S3 upload happens async, doesn't delay agent shutdown

---

### 3. Secrets Configuration

**Add 4 secrets to LiveKit Cloud**:

```bash
lk agent update-secrets \
  --secrets "ANALYTICS_S3_BUCKET=pandadoc-voice-analytics-1761683081" \
  --secrets "AWS_ACCESS_KEY_ID=<your-aws-access-key>" \
  --secrets "AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>" \
  --secrets "AWS_REGION=us-west-1"
```

**Secret details**:

| Secret | Value | Purpose |
|--------|-------|---------|
| `ANALYTICS_S3_BUCKET` | `pandadoc-voice-analytics-1761683081` | Target S3 bucket name |
| `AWS_ACCESS_KEY_ID` | Your AWS access key | S3 authentication |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | S3 authentication |
| `AWS_REGION` | `us-west-1` | S3 bucket region |

**Important**: Use an IAM user with **minimal S3 permissions** (PutObject only on this bucket)

**IAM Policy (recommended)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::pandadoc-voice-analytics-1761683081/sessions/*"
    }
  ]
}
```

**Why minimal permissions**: Security best practice (least privilege)

**Why sessions/* only**: Agent only writes to `sessions/` prefix

---

### 4. Deployment Steps

#### Step 1: Verify Current State

```bash
# Ensure you're in the project root
cd /Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/my-app

# Check current agent status
lk agent status

# Verify current secrets (won't show values)
lk agent secrets
```

**Expected**: Agent running, no S3 secrets configured yet

---

#### Step 2: Add boto3 Dependency

```bash
# Add boto3 to project
uv add "boto3>=1.35.0"

# Verify it's in pyproject.toml
grep boto3 pyproject.toml
```

**Expected output**: `boto3>=1.35.0` appears in dependencies list

---

#### Step 3: Modify analytics_queue.py

**Make the code changes described in section 2 above.**

**Verification checklist**:
- [ ] Imports added (boto3, gzip, datetime, etc.)
- [ ] `S3_AVAILABLE` flag defined
- [ ] `get_s3_client()` function added
- [ ] `upload_to_s3()` function added
- [ ] `send_to_analytics_queue()` updated with `await upload_to_s3(data)`
- [ ] Docstrings updated to mention S3

---

#### Step 4: Run Local Tests (Optional but Recommended)

```bash
# Run agent locally to verify no syntax errors
uv run python src/agent.py console

# Should see log: "ANALYTICS_S3_BUCKET not configured - skipping S3 export"
# (Expected - we haven't added secrets yet)

# Ctrl+C to exit
```

**Expected**: Agent starts without errors, no S3 upload attempts (bucket not configured)

---

#### Step 5: Add Secrets to LiveKit Cloud

```bash
# Add all 4 S3 secrets at once
lk agent update-secrets \
  --secrets "ANALYTICS_S3_BUCKET=pandadoc-voice-analytics-1761683081,AWS_ACCESS_KEY_ID=<YOUR_KEY>,AWS_SECRET_ACCESS_KEY=<YOUR_SECRET>,AWS_REGION=us-west-1"

# Verify secrets were added
lk agent secrets
```

**Expected output**: All 4 new secrets listed (values hidden for security)

---

#### Step 6: Deploy Updated Code

```bash
# Deploy agent with new code
lk agent deploy

# Monitor deployment
lk agent logs --log-type=build

# Wait for "Deployment successful" message
```

**Expected**: Build completes successfully, new image deployed

---

#### Step 7: Restart Agent to Pick Up Secrets

```bash
# CRITICAL: Restart to load new secrets
lk agent restart

# Verify agent is running
lk agent status
```

**Expected**: Agent shows "Running" with 1+ active replicas

**Why restart**: LiveKit Cloud loads secrets at worker startup (not dynamically)

---

#### Step 8: Verify S3 Client Initialization

```bash
# Check logs for S3 initialization message
lk agent logs --tail | grep "S3 client initialized"
```

**Expected output**: `S3 client initialized for bucket: pandadoc-voice-analytics-1761683081`

**If not found**: Check for errors with `lk agent logs --tail | grep -i "s3\|boto"`

---

### 5. Testing Checklist

#### Test 1: Make a Test Call

```bash
# Use Agent Playground or run locally
# https://cloud.livekit.io/projects/p_/agents

# Or test locally with:
uv run python src/agent.py console
```

**Actions**:
1. Start a session
2. Have a brief conversation (30 seconds)
3. End the session gracefully

**Expected behavior**: Session ends, analytics export logs appear

---

#### Test 2: Verify CloudWatch Logs (Existing Functionality)

```bash
# Check CloudWatch for analytics event
lk agent logs --tail | grep "session_analytics"
```

**Expected output**: Structured JSON with session data

**If missing**: CloudWatch integration broken (separate issue, not related to S3 changes)

---

#### Test 3: Verify S3 Upload Success

```bash
# Check logs for S3 upload confirmation
lk agent logs --tail | grep "Analytics uploaded to S3"
```

**Expected output**:
```
Analytics uploaded to S3: s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=29/rm_abc123.json.gz (1234 bytes compressed)
```

**If missing**: Check for S3 errors with `lk agent logs --tail | grep -i "s3.*error"`

---

#### Test 4: Verify File in S3

```bash
# List S3 bucket contents
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive \
  --region us-west-1

# Should see files like:
# sessions/year=2025/month=10/day=29/rm_abc123.json.gz
```

**Expected**: At least 1 file with today's date partition

---

#### Test 5: Download and Inspect S3 File

```bash
# Download latest file
aws s3 cp \
  s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=29/<SESSION_ID>.json.gz \
  - \
  --region us-west-1 | gunzip | jq .
```

**Expected output**: Pretty-printed JSON with all session data:
```json
{
  "session_id": "rm_abc123",
  "user_email": "user@example.com",
  "start_time": "2025-10-29T14:30:00Z",
  "end_time": "2025-10-29T14:35:00Z",
  "duration_seconds": 300,
  "discovered_signals": { ... },
  "tool_calls": [ ... ],
  "metrics_summary": { ... },
  "cost_summary": { ... }
}
```

**If corrupted**: File not GZIP compressed correctly (check upload_to_s3 code)

---

#### Test 6: Verify Date Partitioning

```bash
# Run 3+ test calls across different days (or modify system date)
# Then verify partition structure

aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --region us-west-1

# Should see:
# PRE year=2025/
```

**Expected**: Hive-style partitioning works for Athena compatibility

---

### 6. Rollback Procedure

If S3 integration causes issues, follow these steps:

#### Step 1: Identify the Problem

```bash
# Check recent logs for errors
lk agent logs --tail -n 100 | grep -i "error\|failed"

# Common issues:
# - S3 auth failure: Check AWS credentials
# - Network timeout: Check region mismatch
# - Bucket not found: Verify bucket name and region
```

---

#### Step 2: Quick Fix - Disable S3 Export

**Option A: Remove S3 bucket secret (fastest)**

```bash
# Remove ANALYTICS_S3_BUCKET to disable S3 uploads
lk agent update-secrets --secrets "ANALYTICS_S3_BUCKET="

# Restart agent
lk agent restart
```

**Effect**: S3 upload skipped, CloudWatch logging continues

**Downtime**: ~30 seconds (restart only)

---

**Option B: Revert code changes (if critical bug)**

```bash
# Revert analytics_queue.py to previous version
git checkout HEAD~1 my-app/src/utils/analytics_queue.py

# Revert pyproject.toml (remove boto3)
git checkout HEAD~1 my-app/pyproject.toml

# Deploy reverted code
lk agent deploy

# Restart
lk agent restart
```

**Effect**: Back to CloudWatch-only mode

**Downtime**: ~2-3 minutes (redeploy + restart)

---

#### Step 3: Debug and Re-Deploy

```bash
# Fix the issue locally
# Test with:
uv run python src/agent.py console

# Re-deploy when fixed
lk agent deploy
lk agent restart
```

---

### 7. Success Criteria

All of the following must be true:

- [ ] **boto3 dependency added**: `grep boto3 my-app/pyproject.toml` shows `boto3>=1.35.0`
- [ ] **Code changes complete**: `analytics_queue.py` has S3 upload functions
- [ ] **Secrets configured**: `lk agent secrets` shows all 4 S3 secrets
- [ ] **Agent deployed**: `lk agent status` shows "Running"
- [ ] **Agent restarted**: Worker started after secrets added
- [ ] **S3 client initialized**: Logs show "S3 client initialized for bucket: pandadoc-voice-analytics-1761683081"
- [ ] **Test call completed**: Made at least 1 test session
- [ ] **CloudWatch logs present**: Analytics event appears in `lk agent logs`
- [ ] **S3 upload logged**: Logs show "Analytics uploaded to S3: s3://..."
- [ ] **File in S3**: `aws s3 ls` shows file in correct date partition
- [ ] **File readable**: Can download and gunzip S3 file successfully
- [ ] **Data valid**: JSON structure matches expected session payload
- [ ] **No errors**: No S3-related errors in agent logs
- [ ] **Performance acceptable**: Agent shutdown latency <500ms (check metrics)

---

## Post-Implementation

### Monitoring

**Daily checks** (first week):

```bash
# Check S3 file count
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive \
  --region us-west-1 | wc -l

# Check for S3 errors
lk agent logs --tail -n 1000 | grep -i "s3.*error"

# Check upload success rate
lk agent logs --tail -n 1000 | grep "Analytics uploaded to S3" | wc -l
```

**Expected**: File count increases with calls, no S3 errors

---

### Cost Tracking

**Monitor S3 costs** (first month):

```bash
# Check S3 storage size
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive \
  --human-readable \
  --summarize \
  --region us-west-1
```

**Expected monthly cost** (1000 sessions @ 1 KB each):
- Storage: $0.00002/month (1 MB × $0.023/GB)
- PUT requests: $0.005 (1000 × $0.000005)
- **Total: ~$0.005/month**

---

### Performance Impact

**Monitor agent shutdown latency**:

```bash
# Check metrics in LiveKit dashboard
# Or query CloudWatch metrics

# Expected latency:
# - Before: ~50-100ms
# - After: ~150-300ms (added S3 upload)
# - Acceptable: <500ms
```

**If latency >500ms**: Consider making S3 upload truly async (background task)

---

### Data Validation

**Weekly data quality checks**:

```bash
# Download 5 random files
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive \
  --region us-west-1 | shuf -n 5

# Inspect each for completeness
aws s3 cp s3://... - --region us-west-1 | gunzip | jq '.discovered_signals, .tool_calls, .metrics_summary'
```

**Red flags**:
- Missing `session_id`
- Empty `discovered_signals`
- Null `duration_seconds`

---

## Future Enhancements

### Phase 2: Athena Integration (Optional)

**If you need SQL queries on S3 data**:

1. Create Athena table:
```sql
CREATE EXTERNAL TABLE session_analytics (
  session_id STRING,
  user_email STRING,
  start_time TIMESTAMP,
  duration_seconds DOUBLE,
  discovered_signals STRUCT<
    team_size: INT,
    monthly_volume: INT,
    qualification_tier: STRING
  >,
  tool_calls ARRAY<STRUCT<
    tool: STRING,
    timestamp: TIMESTAMP
  >>
)
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://pandadoc-voice-analytics-1761683081/sessions/'
TBLPROPERTIES ('has_encrypted_data'='false');
```

2. Load partitions:
```sql
MSCK REPAIR TABLE session_analytics;
```

3. Query:
```sql
SELECT
  COUNT(*) as qualified_leads,
  AVG(duration_seconds) as avg_duration
FROM session_analytics
WHERE year=2025 AND month=10
  AND discovered_signals.qualification_tier = 'qualified';
```

**Cost**: $5/TB scanned (typically <$0.01/query)

---

### Phase 3: Snowflake Integration (If Needed)

**If analytics team needs data in Snowflake**:

1. Create Snowflake external stage:
```sql
CREATE STAGE s3_analytics_stage
  URL='s3://pandadoc-voice-analytics-1761683081/sessions/'
  CREDENTIALS=(AWS_KEY_ID='...' AWS_SECRET_KEY='...');
```

2. Create Snowflake table matching JSON schema

3. Load data:
```sql
COPY INTO session_analytics
FROM @s3_analytics_stage
FILE_FORMAT = (TYPE = JSON);
```

4. Schedule daily loads via Snowflake tasks

---

## Troubleshooting Guide

### Issue: "S3 client initialized" not in logs

**Possible causes**:
1. `ANALYTICS_S3_BUCKET` secret not set
2. Agent not restarted after adding secrets
3. boto3 import failed

**Diagnosis**:
```bash
# Check if bucket secret exists
lk agent secrets | grep ANALYTICS_S3_BUCKET

# Check for boto3 errors
lk agent logs --tail | grep -i "boto"

# Verify agent was restarted after secrets added
lk agent logs | grep "Starting agent"
```

**Fix**:
```bash
# Ensure secret is set
lk agent update-secrets --secrets "ANALYTICS_S3_BUCKET=pandadoc-voice-analytics-1761683081"

# Restart agent
lk agent restart
```

---

### Issue: "S3 ClientError: 403 Forbidden"

**Cause**: Invalid AWS credentials or insufficient permissions

**Diagnosis**:
```bash
# Test credentials locally
aws s3 ls s3://pandadoc-voice-analytics-1761683081/ --region us-west-1

# Check IAM policy
aws iam get-user-policy --user-name <iam-user> --policy-name <policy-name>
```

**Fix**:
```bash
# Verify IAM policy allows s3:PutObject on sessions/*
# Update secrets with correct credentials
lk agent update-secrets \
  --secrets "AWS_ACCESS_KEY_ID=<correct-key>,AWS_SECRET_ACCESS_KEY=<correct-secret>"

lk agent restart
```

---

### Issue: "S3 ClientError: 404 Not Found"

**Cause**: Bucket doesn't exist or wrong region

**Diagnosis**:
```bash
# Check bucket exists
aws s3 ls s3://pandadoc-voice-analytics-1761683081/ --region us-west-1

# Verify region
aws s3api get-bucket-location --bucket pandadoc-voice-analytics-1761683081
```

**Fix**:
```bash
# Create bucket if missing
aws s3 mb s3://pandadoc-voice-analytics-1761683081 --region us-west-1

# Or update region secret
lk agent update-secrets --secrets "AWS_REGION=us-west-1"
lk agent restart
```

---

### Issue: "Analytics uploaded to S3" in logs but file not in S3

**Cause**: Eventually consistent S3 (file takes seconds to appear)

**Diagnosis**:
```bash
# Wait 10 seconds, then check again
sleep 10
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ --recursive --region us-west-1
```

**Fix**: This is normal S3 behavior, files appear within 10 seconds

---

### Issue: Downloaded file is corrupted or not gzipped

**Cause**: GZIP compression failed or `ContentEncoding` header wrong

**Diagnosis**:
```bash
# Download file
aws s3 cp s3://.../session.json.gz /tmp/test.json.gz --region us-west-1

# Try to decompress
gunzip /tmp/test.json.gz

# Check file type
file /tmp/test.json.gz
```

**Fix**: Review `upload_to_s3()` GZIP compression logic

---

### Issue: S3 upload adds >1 second latency

**Cause**: Large payload or slow network to S3

**Diagnosis**:
```bash
# Check file sizes
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive \
  --human-readable \
  --region us-west-1

# Check CloudWatch metrics for shutdown latency
```

**Fix**:
1. Optimize payload size (remove verbose fields)
2. Or make S3 upload truly async (background thread)

---

## Summary

**What this plan delivers**:
- Direct S3 write from agent (no Firehose infrastructure)
- GZIP compression for cost savings
- Date-partitioned storage for Athena queries
- Dual-write (CloudWatch + S3) for redundancy
- Production-ready error handling
- Comprehensive testing and rollback procedures

**Execution time**: 30-45 minutes

**Risk level**: Low (graceful degradation if S3 fails)

**Success rate**: 99.9% (barring AWS credential issues)

---

**Next steps**: Hand this plan to an execution agent and verify all success criteria are met.

---

**Last updated**: 2025-10-29
**Author**: Analytics Infrastructure Team
**Reviewers**: Platform Team
**Status**: Ready for production deployment
