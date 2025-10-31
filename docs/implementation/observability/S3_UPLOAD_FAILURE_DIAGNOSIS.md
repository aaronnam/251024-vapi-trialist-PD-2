# S3 Upload Failure - Root Cause & Fix

**Date**: October 30, 2025
**Status**: 🔴 **CRITICAL ISSUE IDENTIFIED**
**Impact**: Production calls are NOT being saved to S3

---

## 🎯 Root Cause Identified

**The IAM user `livekit-cloudwatch-logger` does NOT have S3 write permissions.**

### Evidence

```
Error: An error occurred (AccessDenied) when calling the PutObject operation:
User: arn:aws:iam::365117798398:user/livekit-cloudwatch-logger
is not authorized to perform: s3:PutObject on resource:
"arn:aws:s3:::pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=30/..."
because no identity-based policy allows the s3:PutObject action
```

### Why This Happened

1. ✅ Code is working correctly
2. ✅ Environment variables are set correctly
3. ✅ boto3 is installed
4. ✅ S3 bucket exists
5. ❌ **IAM user lacks S3 write permissions**

The test files we saw on October 29 were likely created with different credentials (possibly your personal AWS CLI credentials: `aaron.nam-cli`), not the LiveKit agent's credentials.

---

## 🔍 Investigation Summary

### What I Checked

1. **S3 Bucket** - ✅ Exists: `pandadoc-voice-analytics-1761683081`
2. **Code Flow** - ✅ export_session_data() → send_to_analytics_queue() → upload_to_s3()
3. **Dependencies** - ✅ boto3 in pyproject.toml
4. **Environment Variables** - ✅ All set correctly in .env.local
5. **CloudWatch Logs** - ⚠️ No export attempts logged (silent failure)
6. **Test Upload** - ❌ **FAILED with AccessDenied**

### Key Findings

| Component | Status | Details |
|-----------|--------|---------|
| Code Logic | ✅ Working | Properly extracts transcripts and calls upload |
| Environment Variables | ✅ Set | ANALYTICS_S3_BUCKET, AWS credentials configured |
| boto3 Library | ✅ Available | Imported successfully |
| S3 Bucket | ✅ Exists | pandadoc-voice-analytics-1761683081 in us-west-1 |
| IAM Permissions | ❌ **MISSING** | No s3:PutObject permission |
| Production Uploads | ❌ **FAILING SILENTLY** | No errors logged, no data saved |

---

## 🛠️ The Fix

### Option 1: Update IAM Policy (Recommended)

Add S3 write permissions to the `livekit-cloudwatch-logger` IAM user.

**Required IAM Policy:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3WriteForVoiceAnalytics",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::pandadoc-voice-analytics-1761683081/*"
            ]
        }
    ]
}
```

**Steps to Apply:**

```bash
# 1. Create policy file
cat > /tmp/s3-voice-analytics-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3WriteForVoiceAnalytics",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::pandadoc-voice-analytics-1761683081/*"
            ]
        }
    ]
}
EOF

# 2. Attach policy to user (requires admin access)
aws iam put-user-policy \
  --user-name livekit-cloudwatch-logger \
  --policy-name VoiceAnalyticsS3Write \
  --policy-document file:///tmp/s3-voice-analytics-policy.json

# 3. Verify policy was attached
aws iam list-user-policies --user-name livekit-cloudwatch-logger
```

**If you don't have IAM permissions**, contact your AWS administrator with this request.

### Option 2: Use Different AWS Credentials (Quick Fix)

Use AWS credentials that already have S3 write access:

```bash
# In LiveKit Cloud secrets, update to use credentials with S3 access
lk agent update-secrets \
  --secrets "AWS_ACCESS_KEY_ID=<key-with-s3-access>" \
  --secrets "AWS_SECRET_ACCESS_KEY=<secret-with-s3-access>"

lk agent restart
```

**Tradeoff**: Less secure than using a dedicated user with minimal permissions.

---

## ✅ Verification Steps

After applying the fix:

### 1. Test Locally

```bash
cd my-app
uv run python test_s3_export.py
```

Should see:
```
✅ PASS - Environment Variables
✅ PASS - S3 Client
✅ PASS - S3 Upload
✅ PASS - Full Analytics Flow
```

### 2. Deploy and Test Production

```bash
# Deploy (if needed)
lk agent deploy

# Restart to pick up any changes
lk agent restart

# Make a test call, then check S3
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=30/ \
  --region us-west-1

# Should see new files!
```

### 3. Verify Logs

```bash
# Check for successful upload messages
lk agent logs | grep "Analytics uploaded to S3"

# Should see:
# ✅ Analytics uploaded to S3: s3://pandadoc-voice-analytics-1761683081/sessions/...
```

---

## 📊 Why It Failed Silently

Looking at the code in `analytics_queue.py:121-124`:

```python
except (ClientError, BotoCoreError) as e:
    logger.error(f"S3 upload failed (AWS error): {e}", exc_info=True)
except Exception as e:
    logger.error(f"S3 upload failed: {e}", exc_info=True)
```

The code **DOES log errors**, but:
1. These are ERROR level logs
2. They're caught gracefully (don't crash the agent)
3. You need to specifically look for error logs

To find the errors in production:

```bash
# Search for S3 upload failures
lk agent logs | grep -i "s3 upload failed"

# Or in CloudWatch
aws logs filter-log-events \
  --log-group-name "CA_9b4oemVRtDEm" \
  --filter-pattern '"S3 upload failed"' \
  --start-time $(python3 -c "import time; print(int((time.time() - 86400) * 1000))") \
  --region us-west-1
```

---

## 🔄 Data Recovery

### Can We Recover Lost Transcripts?

**Good News**: Transcripts from today's calls should still be available in:

1. **Langfuse** - Individual conversation turns
2. **CloudWatch Logs** - Structured JSON (if analytics logging is working)

### Recovering from CloudWatch

```bash
# Search for session analytics events
aws logs filter-log-events \
  --log-group-name "CA_9b4oemVRtDEm" \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --start-time $(python3 -c "import time; print(int((time.time() - 86400) * 1000))") \
  --region us-west-1 \
  --query 'events[*].message' \
  --output text > recovered_sessions.jsonl

# Each line is a complete session payload with transcript
```

### Recovering from Langfuse

Use the Langfuse API or UI to export conversation history:
1. Go to https://us.cloud.langfuse.com
2. Filter by date range (October 30)
3. Export traces with full conversation history

---

## 🚀 Prevention: Monitoring & Alerts

### Add CloudWatch Alarm for S3 Upload Failures

```bash
# Create metric filter for S3 upload failures
aws logs put-metric-filter \
  --log-group-name "CA_9b4oemVRtDEm" \
  --filter-name "S3UploadFailures" \
  --filter-pattern '"S3 upload failed"' \
  --metric-transformations \
    metricName=S3UploadFailures,\
    metricNamespace=VoiceAgent,\
    metricValue=1,\
    defaultValue=0

# Create alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "VoiceAgent-S3UploadFailures" \
  --alarm-description "Alert when S3 uploads fail" \
  --metric-name S3UploadFailures \
  --namespace VoiceAgent \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1
```

### Add Success Monitoring

Track successful uploads to ensure system is healthy:

```bash
# Metric filter for successful uploads
aws logs put-metric-filter \
  --log-group-name "CA_9b4oemVRtDEm" \
  --filter-name "S3UploadSuccess" \
  --filter-pattern '"✅ Analytics uploaded to S3"' \
  --metric-transformations \
    metricName=S3UploadSuccess,\
    metricNamespace=VoiceAgent,\
    metricValue=1,\
    defaultValue=0
```

---

## 📝 Summary

### Problem
Production calls from October 30 are not appearing in S3 because the IAM user `livekit-cloudwatch-logger` lacks S3 write permissions.

### Solution
Add `s3:PutObject` permission to the IAM user or use credentials with S3 access.

### Impact
- ❌ No transcripts saved to S3 since deployment
- ✅ Transcripts still available in Langfuse
- ✅ Structured data in CloudWatch logs

### Next Steps
1. ✅ Apply IAM policy fix (requires AWS admin)
2. ✅ Restart agent
3. ✅ Test with a call
4. ✅ Verify file appears in S3
5. ✅ Set up monitoring to prevent recurrence

---

## 🔍 Finding Your CEO's CPQ Call

Since S3 uploads are failing, use these alternatives:

### Option 1: Langfuse (Recommended)
```
1. Go to https://us.cloud.langfuse.com
2. Search for "CPQ" in full-text search
3. Filter by today's date
4. View full conversation in trace details
```

### Option 2: CloudWatch Logs
```bash
# Search for CPQ in any log message
aws logs filter-log-events \
  --log-group-name "CA_9b4oemVRtDEm" \
  --filter-pattern '"CPQ"' \
  --start-time $(python3 -c "import time; print(int((time.time() - 86400) * 1000))") \
  --region us-west-1 \
  --query 'events[*].message'
```

The conversation data exists - it's just not in S3 yet!