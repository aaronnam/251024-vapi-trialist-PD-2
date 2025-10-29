# Snowflake Integration Guide

**Goal**: Enable cross-functional partners to ingest analytics data from S3 into Snowflake securely and efficiently.

**Recommended Approach**: Snowflake Storage Integration with IAM role (no access keys, automatic credential rotation)

---

## Table of Contents

1. [Option 1: Snowflake Storage Integration (Recommended)](#option-1-snowflake-storage-integration-recommended)
2. [Option 2: IAM User with Access Keys (Simple)](#option-2-iam-user-with-access-keys-simple)
3. [Option 3: Cross-Account IAM Role (Enterprise)](#option-3-cross-account-iam-role-enterprise)
4. [Testing and Verification](#testing-and-verification)
5. [Ongoing Maintenance](#ongoing-maintenance)

---

## Option 1: Snowflake Storage Integration (Recommended)

**Best for**: Production use, long-term partnerships, security-conscious orgs

**Advantages**:
- ✅ No access keys to manage or rotate
- ✅ Automatic credential management by Snowflake
- ✅ Native Snowflake integration
- ✅ Easy to audit and revoke
- ✅ Follows AWS and Snowflake best practices

**Disadvantages**:
- Requires Snowflake ACCOUNTADMIN privileges (partner needs this)
- Slightly more initial setup (but easier long-term)

### Step 1: Create IAM Policy for Snowflake

This policy grants read-only access to your analytics S3 bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::pandadoc-voice-analytics-1761683081/sessions/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::pandadoc-voice-analytics-1761683081",
      "Condition": {
        "StringLike": {
          "s3:prefix": ["sessions/*"]
        }
      }
    }
  ]
}
```

**Create the policy**:

```bash
# Save policy as snowflake-s3-policy.json
cat > snowflake-s3-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::pandadoc-voice-analytics-1761683081/sessions/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::pandadoc-voice-analytics-1761683081",
      "Condition": {
        "StringLike": {
          "s3:prefix": ["sessions/*"]
        }
      }
    }
  ]
}
EOF

# Create IAM policy
aws iam create-policy \
  --policy-name SnowflakeVoiceAnalyticsReadOnly \
  --policy-document file://snowflake-s3-policy.json \
  --description "Read-only access to voice analytics S3 bucket for Snowflake"

# Note the policy ARN returned - you'll need it in Step 2
```

### Step 2: Share Policy ARN with Partner

Send your partner:
1. **Policy ARN** (from step 1, looks like: `arn:aws:iam::YOUR_ACCOUNT_ID:policy/SnowflakeVoiceAnalyticsReadOnly`)
2. **S3 bucket name**: `pandadoc-voice-analytics-1761683081`
3. **S3 prefix**: `sessions/`
4. **Region**: `us-west-1`

### Step 3: Partner Creates Storage Integration in Snowflake

**Your partner runs these commands in Snowflake**:

```sql
-- Create storage integration
CREATE STORAGE INTEGRATION voice_analytics_s3
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_ACCOUNT_ID:role/snowflake-voice-analytics-role'  -- Will create this role
  STORAGE_ALLOWED_LOCATIONS = ('s3://pandadoc-voice-analytics-1761683081/sessions/');

-- Get Snowflake IAM user ARN and External ID (partner sends these to you)
DESC STORAGE INTEGRATION voice_analytics_s3;
```

**Partner sends you**:
- `STORAGE_AWS_IAM_USER_ARN` (looks like: `arn:aws:iam::123456789012:user/abc`)
- `STORAGE_AWS_EXTERNAL_ID` (looks like: `ABC123_SFCRole=1_AbCdEfGhIjK=`)

### Step 4: Create IAM Role with Trust Relationship

**You create IAM role** that Snowflake can assume:

```bash
# Create trust policy document
cat > snowflake-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "STORAGE_AWS_IAM_USER_ARN_FROM_PARTNER"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "STORAGE_AWS_EXTERNAL_ID_FROM_PARTNER"
        }
      }
    }
  ]
}
EOF

# Replace placeholders with actual values from partner
sed -i '' 's|STORAGE_AWS_IAM_USER_ARN_FROM_PARTNER|arn:aws:iam::123456789012:user/abc|g' snowflake-trust-policy.json
sed -i '' 's|STORAGE_AWS_EXTERNAL_ID_FROM_PARTNER|ABC123_SFCRole=1_AbCdEfGhIjK=|g' snowflake-trust-policy.json

# Create IAM role
aws iam create-role \
  --role-name snowflake-voice-analytics-role \
  --assume-role-policy-document file://snowflake-trust-policy.json \
  --description "Role for Snowflake to access voice analytics S3 bucket"

# Attach the policy created in Step 1
aws iam attach-role-policy \
  --role-name snowflake-voice-analytics-role \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/SnowflakeVoiceAnalyticsReadOnly

# Get the role ARN (send this to partner)
aws iam get-role \
  --role-name snowflake-voice-analytics-role \
  --query 'Role.Arn' \
  --output text
```

### Step 5: Partner Updates Storage Integration

**Partner updates Snowflake with the role ARN**:

```sql
ALTER STORAGE INTEGRATION voice_analytics_s3
SET STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_ACCOUNT_ID:role/snowflake-voice-analytics-role';
```

### Step 6: Partner Creates External Stage

**Partner creates stage to access your S3 data**:

```sql
-- Create external stage
CREATE STAGE voice_analytics_stage
  STORAGE_INTEGRATION = voice_analytics_s3
  URL = 's3://pandadoc-voice-analytics-1761683081/sessions/'
  FILE_FORMAT = (
    TYPE = JSON
    COMPRESSION = GZIP
  );

-- Test listing files
LIST @voice_analytics_stage;
```

### Step 7: Partner Creates Table and Loads Data

**Partner sets up table and ingestion**:

```sql
-- Create database and schema
CREATE DATABASE IF NOT EXISTS ANALYTICS;
CREATE SCHEMA IF NOT EXISTS ANALYTICS.VOICE;

-- Create table for voice sessions
CREATE TABLE ANALYTICS.VOICE.SESSIONS (
  raw_data VARIANT,
  _event_type STRING,
  _timestamp TIMESTAMP,
  _session_id STRING,
  duration_seconds NUMBER,
  discovered_signals VARIANT,
  tool_calls VARIANT,
  metrics_summary VARIANT,
  load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Load data from S3
COPY INTO ANALYTICS.VOICE.SESSIONS (
  raw_data,
  _event_type,
  _timestamp,
  _session_id,
  duration_seconds,
  discovered_signals,
  tool_calls,
  metrics_summary
)
FROM (
  SELECT
    $1 as raw_data,
    $1:_event_type::STRING,
    TO_TIMESTAMP($1:_timestamp::NUMBER),
    $1:_session_id::STRING,
    $1:duration_seconds::NUMBER,
    $1:discovered_signals,
    $1:tool_calls,
    $1:metrics_summary
  FROM @voice_analytics_stage
)
FILE_FORMAT = (TYPE = JSON COMPRESSION = GZIP)
PATTERN = '.*year=.*/month=.*/day=.*/.*\\.gz';

-- Set up automated incremental loads
CREATE TASK voice_analytics_incremental_load
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = '60 MINUTE'
AS
  COPY INTO ANALYTICS.VOICE.SESSIONS (
    raw_data,
    _event_type,
    _timestamp,
    _session_id,
    duration_seconds,
    discovered_signals,
    tool_calls,
    metrics_summary
  )
  FROM (
    SELECT
      $1 as raw_data,
      $1:_event_type::STRING,
      TO_TIMESTAMP($1:_timestamp::NUMBER),
      $1:_session_id::STRING,
      $1:duration_seconds::NUMBER,
      $1:discovered_signals,
      $1:tool_calls,
      $1:metrics_summary
    FROM @voice_analytics_stage
  )
  FILE_FORMAT = (TYPE = JSON COMPRESSION = GZIP)
  PATTERN = '.*year=.*/month=.*/day=.*/.*\\.gz';

-- Enable task
ALTER TASK voice_analytics_incremental_load RESUME;
```

### Complete Setup Summary

**What you did**:
1. Created IAM policy with read-only S3 access
2. Created IAM role that Snowflake can assume
3. Shared bucket name, prefix, region with partner

**What partner did**:
1. Created Snowflake storage integration
2. Created external stage pointing to your S3
3. Set up table and automated ingestion

**Result**: Partner can now query your analytics data in Snowflake with automatic updates every hour.

---

## Option 2: IAM User with Access Keys (Simple)

**Best for**: Quick setup, temporary access, simple use cases

**Advantages**:
- ✅ Fast setup (5 minutes)
- ✅ No Snowflake admin privileges required
- ✅ Works with any tool (not just Snowflake)

**Disadvantages**:
- ⚠️ Access keys need manual rotation
- ⚠️ Credentials can be compromised if leaked
- ⚠️ Harder to audit

### Setup Steps

#### Step 1: Create IAM User

```bash
# Create user
aws iam create-user \
  --user-name snowflake-voice-analytics-reader

# Create and attach policy (same as Option 1)
aws iam create-policy \
  --policy-name SnowflakeVoiceAnalyticsReadOnly \
  --policy-document file://snowflake-s3-policy.json

# Attach policy to user
aws iam attach-user-policy \
  --user-name snowflake-voice-analytics-reader \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/SnowflakeVoiceAnalyticsReadOnly

# Create access keys
aws iam create-access-key \
  --user-name snowflake-voice-analytics-reader
```

#### Step 2: Share Credentials with Partner

**Send via secure channel** (1Password, LastPass, etc.):
- `AWS_ACCESS_KEY_ID`: (from previous command)
- `AWS_SECRET_ACCESS_KEY`: (from previous command)
- `S3_BUCKET`: `pandadoc-voice-analytics-1761683081`
- `S3_PREFIX`: `sessions/`
- `AWS_REGION`: `us-west-1`

#### Step 3: Partner Creates Snowflake Stage

```sql
-- Create stage with credentials
CREATE STAGE voice_analytics_stage
  URL = 's3://pandadoc-voice-analytics-1761683081/sessions/'
  CREDENTIALS = (
    AWS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'
    AWS_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
  )
  FILE_FORMAT = (
    TYPE = JSON
    COMPRESSION = GZIP
  );

-- Test
LIST @voice_analytics_stage;
```

Partner then follows Step 7 from Option 1 to create table and load data.

### Security Best Practices for Option 2

1. **Rotate keys every 90 days**:
```bash
# Deactivate old key
aws iam update-access-key \
  --user-name snowflake-voice-analytics-reader \
  --access-key-id OLD_KEY_ID \
  --status Inactive

# Create new key
aws iam create-access-key \
  --user-name snowflake-voice-analytics-reader

# After partner updates Snowflake, delete old key
aws iam delete-access-key \
  --user-name snowflake-voice-analytics-reader \
  --access-key-id OLD_KEY_ID
```

2. **Monitor access**:
```bash
# Check last used
aws iam get-access-key-last-used \
  --access-key-id ACCESS_KEY_ID
```

---

## Option 3: Cross-Account IAM Role (Enterprise)

**Best for**: Partner has their own AWS account, enterprise-grade security

**Advantages**:
- ✅ No credentials to share
- ✅ Partner uses their own AWS account
- ✅ Easy to audit and revoke
- ✅ Supports multiple partners easily

**Disadvantages**:
- Requires partner to have AWS account
- More complex setup

### Setup Steps

#### Step 1: Get Partner's AWS Account ID

Partner provides their AWS account ID (12-digit number).

#### Step 2: Create IAM Role with Cross-Account Trust

```bash
# Create trust policy
cat > cross-account-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::PARTNER_AWS_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "voice-analytics-2025-01-28"
        }
      }
    }
  ]
}
EOF

# Replace PARTNER_AWS_ACCOUNT_ID
sed -i '' 's|PARTNER_AWS_ACCOUNT_ID|123456789012|g' cross-account-trust-policy.json

# Create role
aws iam create-role \
  --role-name CrossAccountVoiceAnalyticsReader \
  --assume-role-policy-document file://cross-account-trust-policy.json \
  --description "Cross-account access to voice analytics for partner"

# Attach S3 read policy
aws iam attach-role-policy \
  --role-name CrossAccountVoiceAnalyticsReader \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/SnowflakeVoiceAnalyticsReadOnly

# Get role ARN
aws iam get-role \
  --role-name CrossAccountVoiceAnalyticsReader \
  --query 'Role.Arn' \
  --output text
```

#### Step 3: Share with Partner

Send partner:
- **Role ARN**: `arn:aws:iam::YOUR_ACCOUNT_ID:role/CrossAccountVoiceAnalyticsReader`
- **External ID**: `voice-analytics-2025-01-28`
- **S3 Bucket**: `pandadoc-voice-analytics-1761683081`
- **S3 Prefix**: `sessions/`
- **Region**: `us-west-1`

#### Step 4: Partner Assumes Role

**Partner creates IAM role in their account**:

```bash
# Partner creates policy to assume your role
cat > assume-role-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::YOUR_ACCOUNT_ID:role/CrossAccountVoiceAnalyticsReader"
    }
  ]
}
EOF

# Partner creates role for Snowflake
aws iam create-policy \
  --policy-name AssumeVoiceAnalyticsRole \
  --policy-document file://assume-role-policy.json

# Partner then follows Snowflake Storage Integration setup
# using this policy to assume your cross-account role
```

---

## Testing and Verification

### Test 1: Partner Can List Files

**Partner runs**:
```sql
LIST @voice_analytics_stage;
```

**Expected**: Should see `.gz` files organized by date partition.

### Test 2: Partner Can Read File Content

**Partner runs**:
```sql
SELECT $1
FROM @voice_analytics_stage/year=2025/month=01/day=28/
LIMIT 1;
```

**Expected**: Should see JSON content with session data.

### Test 3: Full Data Load

**Partner runs**:
```sql
-- Load sample
COPY INTO ANALYTICS.VOICE.SESSIONS
FROM @voice_analytics_stage
FILE_FORMAT = (TYPE = JSON COMPRESSION = GZIP)
FILES = ('year=2025/month=01/day=28/voice-analytics-to-s3-1-2025-01-28-19-30-00-abc123.gz');

-- Verify
SELECT COUNT(*), MIN(_timestamp), MAX(_timestamp)
FROM ANALYTICS.VOICE.SESSIONS;
```

**Expected**: Rows loaded, timestamps within expected range.

### Test 4: Query Analytics

**Partner tests queries**:
```sql
-- Find qualified leads
SELECT
  _session_id,
  _timestamp,
  discovered_signals:team_size::INT as team_size,
  discovered_signals:monthly_volume::INT as monthly_volume,
  duration_seconds
FROM ANALYTICS.VOICE.SESSIONS
WHERE discovered_signals:team_size::INT >= 5
   OR discovered_signals:monthly_volume::INT >= 100
ORDER BY _timestamp DESC;
```

---

## Ongoing Maintenance

### For You (Data Owner)

#### Monitor Access

```bash
# Check who's accessing your bucket
aws s3api get-bucket-logging \
  --bucket pandadoc-voice-analytics-1761683081

# Enable CloudTrail for detailed access logs (optional)
aws cloudtrail create-trail \
  --name voice-analytics-access \
  --s3-bucket-name your-cloudtrail-bucket
```

#### Audit Permissions

```bash
# List all policies attached to the role
aws iam list-attached-role-policies \
  --role-name snowflake-voice-analytics-role

# Review policy
aws iam get-policy-version \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/SnowflakeVoiceAnalyticsReadOnly \
  --version-id v1
```

#### Revoke Access (if needed)

```bash
# For Storage Integration approach
aws iam delete-role \
  --role-name snowflake-voice-analytics-role

# For IAM user approach
aws iam delete-access-key \
  --user-name snowflake-voice-analytics-reader \
  --access-key-id ACCESS_KEY_ID

aws iam delete-user \
  --user-name snowflake-voice-analytics-reader

# For cross-account approach
aws iam delete-role \
  --role-name CrossAccountVoiceAnalyticsReader
```

### For Partner (Data Consumer)

#### Schedule Regular Loads

```sql
-- Snowflake task runs every hour
CREATE TASK voice_analytics_incremental_load
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = '60 MINUTE'
AS
  COPY INTO ANALYTICS.VOICE.SESSIONS
  FROM @voice_analytics_stage
  FILE_FORMAT = (TYPE = JSON COMPRESSION = GZIP)
  PATTERN = '.*year=.*/month=.*/day=.*/.*\\.gz';

ALTER TASK voice_analytics_incremental_load RESUME;
```

#### Monitor Load Status

```sql
-- Check task history
SELECT *
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
  TASK_NAME => 'voice_analytics_incremental_load'
))
ORDER BY SCHEDULED_TIME DESC
LIMIT 10;

-- Check for load errors
SELECT *
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'SESSIONS',
  START_TIME => DATEADD(day, -1, CURRENT_TIMESTAMP())
))
WHERE STATUS = 'LOAD_FAILED';
```

#### Create Views for Analysis

```sql
-- Flattened view for easier querying
CREATE VIEW ANALYTICS.VOICE.SESSIONS_FLATTENED AS
SELECT
  _session_id,
  _timestamp as session_timestamp,
  duration_seconds,
  discovered_signals:team_size::INT as team_size,
  discovered_signals:monthly_volume::INT as monthly_volume,
  discovered_signals:urgency::STRING as urgency,
  discovered_signals:industry::STRING as industry,
  metrics_summary:llm_tokens::INT as llm_tokens,
  metrics_summary:stt_audio_seconds::FLOAT as stt_audio_seconds,
  tool_calls,
  load_timestamp
FROM ANALYTICS.VOICE.SESSIONS;

-- Qualified leads view
CREATE VIEW ANALYTICS.VOICE.QUALIFIED_LEADS AS
SELECT *
FROM ANALYTICS.VOICE.SESSIONS_FLATTENED
WHERE team_size >= 5 OR monthly_volume >= 100;
```

---

## Recommendation Matrix

| Scenario | Recommended Option | Why |
|----------|-------------------|-----|
| **Long-term production partnership** | Option 1: Storage Integration | Most secure, no credentials, Snowflake best practice |
| **Quick proof-of-concept** | Option 2: IAM User | Fastest setup, minimal complexity |
| **Enterprise with AWS account** | Option 3: Cross-Account Role | Best security, audit trail, scalable |
| **Multiple partners** | Option 1 or 3 | Easy to create multiple roles |
| **Partner lacks ACCOUNTADMIN** | Option 2: IAM User | Doesn't require admin privileges |
| **High security requirements** | Option 1 or 3 | No long-term credentials |
| **Temporary access (< 1 month)** | Option 2: IAM User | Easy to create and delete |

---

## Quick Start: Storage Integration (Most Common)

If you're unsure, use **Option 1 (Storage Integration)**. Here's the condensed version:

### You Do (5 minutes):
1. Create IAM policy with read-only S3 access
2. Share policy ARN + bucket info with partner

### Partner Does (10 minutes):
1. Create storage integration in Snowflake
2. Send you IAM user ARN + external ID

### You Do (5 minutes):
3. Create IAM role with trust policy
4. Send role ARN to partner

### Partner Does (5 minutes):
5. Update storage integration with role ARN
6. Create stage and load data

**Total time**: 25 minutes
**Long-term maintenance**: Minimal (automatic credential rotation)

---

## Support and Troubleshooting

### Common Issues

**Partner can't list files**:
- Check IAM policy allows `s3:ListBucket`
- Verify bucket name and prefix are correct
- Check trust policy has correct Snowflake user ARN

**Partner can list but can't read files**:
- Check IAM policy allows `s3:GetObject`
- Verify file format matches (GZIP compression)

**Access denied errors**:
- Verify IAM role trust relationship
- Check external ID matches
- Confirm policy is attached to role

### Debug Commands

```bash
# Test IAM policy simulator
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/snowflake-voice-analytics-role \
  --action-names s3:ListBucket s3:GetObject \
  --resource-arns arn:aws:s3:::pandadoc-voice-analytics-1761683081/sessions/*
```

---

## Summary

**Recommended**: Use **Option 1 (Snowflake Storage Integration)** for production partnerships.

**Key Benefits**:
- No access keys to manage
- Automatic credential rotation
- Snowflake native integration
- Easy to audit and revoke

**Total Setup Time**: 25 minutes
**Ongoing Maintenance**: Minimal

**Result**: Partner has secure, automated access to your analytics data in Snowflake with hourly updates.