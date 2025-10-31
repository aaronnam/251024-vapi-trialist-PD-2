# Fix: Add S3 Permissions to livekit-cloudwatch-logger

## Problem Confirmed

The IAM user `livekit-cloudwatch-logger` has the `CloudWatchLogsFullAccess` policy, which **only grants CloudWatch Logs permissions**, NOT S3 permissions.

```json
{
  "Action": [
    "logs:*",
    "cloudwatch:GenerateQuery",
    "cloudwatch:GenerateQueryResultsSummary"
  ]
}
```

❌ No `s3:*` actions = No S3 write access

## Quick Fix: Add Inline Policy via AWS Console

Since you're already in the AWS Console:

### Step 1: Click "Add permissions" → "Create inline policy"

### Step 2: Switch to JSON tab and paste this:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VoiceAnalyticsS3Write",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::pandadoc-voice-analytics-1761683081/*"
        }
    ]
}
```

### Step 3: Name the policy

Policy name: `VoiceAnalyticsS3Write`

### Step 4: Create policy

Click "Create policy"

## Verify the Fix

After adding the policy:

1. **The policy should appear** in the "Permissions policies" section alongside `CloudWatchLogsFullAccess`

2. **Test locally:**
   ```bash
   cd my-app
   uv run python test_s3_export.py
   ```
   Should now show all green ✅

3. **Restart the agent:**
   ```bash
   lk agent restart
   ```

4. **Make a test call** and check S3:
   ```bash
   aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=30/ --region us-west-1
   ```

## Why This Minimal Policy is Secure

This policy:
- ✅ Only grants write access (not read or delete)
- ✅ Only to one specific bucket
- ✅ Only to objects within the bucket (not bucket configuration)
- ✅ Follows principle of least privilege

## Alternative: CLI Command

If you prefer CLI:

```bash
aws iam put-user-policy \
  --user-name livekit-cloudwatch-logger \
  --policy-name VoiceAnalyticsS3Write \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["s3:PutObject", "s3:PutObjectAcl"],
        "Resource": "arn:aws:s3:::pandadoc-voice-analytics-1761683081/*"
    }]
}'
```

## After the Fix

Once applied, every production call will automatically:
1. ✅ Extract full conversation transcript
2. ✅ Compress it with gzip
3. ✅ Upload to S3 with date partitioning
4. ✅ Be queryable and searchable

You'll be able to find your CEO's future CPQ conversations (and all others) in S3!