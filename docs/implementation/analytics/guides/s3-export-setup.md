# Setting Up S3 Export for Analytics Data

## Option 1: Kinesis Firehose (Real-time, Automated) - RECOMMENDED

This continuously streams your CloudWatch logs to S3 in near real-time.

### Step 1: Create S3 Bucket

```bash
# Create bucket for analytics
aws s3 mb s3://pandadoc-voice-analytics --region us-west-1

# Enable versioning (optional but recommended)
aws s3api put-bucket-versioning \
  --bucket pandadoc-voice-analytics \
  --versioning-configuration Status=Enabled
```

### Step 2: Create Kinesis Firehose Delivery Stream

1. Go to AWS Kinesis console: https://console.aws.amazon.com/kinesis
2. Click "Create delivery stream"
3. Configure:
   - **Source**: Direct PUT
   - **Destination**: Amazon S3
   - **Delivery stream name**: `voice-analytics-to-s3`
   - **S3 bucket**: `pandadoc-voice-analytics`
   - **S3 prefix**: `sessions/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/`
   - **S3 error prefix**: `errors/`
   - **Buffer interval**: 60 seconds (or 300 for cost savings)
   - **Buffer size**: 5 MB
   - **Compression**: GZIP (reduces storage costs by ~80%)

### Step 3: Create CloudWatch Subscription Filter

```bash
# Get your log group name first
aws logs describe-log-groups --region us-west-1 | grep logGroupName

# Create subscription filter (replace LOG_GROUP_NAME)
aws logs put-subscription-filter \
  --log-group-name "/aws/lambda/your-agent-log-group" \
  --filter-name "S3Export" \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --destination-arn "arn:aws:firehose:us-west-1:YOUR_ACCOUNT_ID:deliverystream/voice-analytics-to-s3" \
  --region us-west-1
```

### Step 4: Grant Permissions

Create IAM role for CloudWatch to write to Firehose:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "logs.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Attach policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "firehose:PutRecord",
        "firehose:PutRecordBatch"
      ],
      "Resource": "arn:aws:firehose:us-west-1:*:deliverystream/voice-analytics-to-s3"
    }
  ]
}
```

## Option 2: Lambda Function (More Control)

If you want to process/transform data before storing:

### Lambda Function Code

```python
import json
import boto3
import base64
import gzip
from datetime import datetime

s3 = boto3.client('s3')
BUCKET = 'pandadoc-voice-analytics'

def lambda_handler(event, context):
    # Decompress CloudWatch Logs data
    cw_data = event['awslogs']['data']
    compressed_payload = base64.b64decode(cw_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    log_data = json.loads(uncompressed_payload)

    for log_event in log_data['logEvents']:
        try:
            # Parse the analytics event
            message = json.loads(log_event['message'])

            # Only process analytics events
            if message.get('_event_type') != 'session_analytics':
                continue

            # Extract session info
            session_id = message.get('_session_id', 'unknown')
            timestamp = datetime.fromtimestamp(message.get('_timestamp', 0))

            # Determine if this is a qualified lead
            team_size = message.get('discovered_signals', {}).get('team_size', 0)
            monthly_volume = message.get('discovered_signals', {}).get('monthly_volume', 0)
            is_qualified = team_size >= 5 or monthly_volume >= 100

            # Create S3 key with partitioning
            folder = 'qualified' if is_qualified else 'all'
            key = f"sessions/{folder}/year={timestamp.year}/month={timestamp.month:02d}/day={timestamp.day:02d}/{session_id}.json"

            # Store in S3
            s3.put_object(
                Bucket=BUCKET,
                Key=key,
                Body=json.dumps(message, indent=2),
                ContentType='application/json',
                Metadata={
                    'session-id': session_id,
                    'qualified': str(is_qualified),
                    'team-size': str(team_size)
                }
            )

            print(f"Stored session {session_id} to S3")

        except Exception as e:
            print(f"Error processing log event: {e}")

    return {'statusCode': 200}
```

### Deploy Lambda

```bash
# Package and deploy
zip function.zip lambda_function.py
aws lambda create-function \
  --function-name voice-analytics-to-s3 \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-s3-writer \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 60 \
  --memory-size 256
```

### Create CloudWatch Subscription

```bash
aws logs put-subscription-filter \
  --log-group-name "/aws/your-log-group" \
  --filter-name "S3Export" \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --destination-arn "arn:aws:lambda:us-west-1:YOUR_ACCOUNT:function:voice-analytics-to-s3"
```

## Option 3: Direct S3 Write from Agent (Immediate)

Modify your `analytics_queue.py` to also write to S3:

```python
# In analytics_queue.py, add S3 upload
import boto3
from botocore.exceptions import ClientError

s3_client = None
S3_BUCKET = os.getenv('ANALYTICS_S3_BUCKET')

def get_s3_client():
    global s3_client
    if not s3_client and S3_BUCKET:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-west-1')
        )
    return s3_client

async def send_to_analytics_queue(data: Dict[str, Any]) -> None:
    """Send session data to analytics queue."""
    try:
        # Existing CloudWatch logging
        analytics_logger.info(
            "Session analytics data",
            extra={"analytics_data": data}
        )

        # Also upload to S3 if configured
        s3 = get_s3_client()
        if s3 and S3_BUCKET:
            session_id = data.get('session_id', 'unknown')
            timestamp = datetime.now()

            # Create S3 key with date partitioning
            key = f"sessions/year={timestamp.year}/month={timestamp.month:02d}/day={timestamp.day:02d}/{session_id}.json"

            # Upload to S3
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )

            logger.info(f"Analytics data uploaded to S3: s3://{S3_BUCKET}/{key}")

    except Exception as e:
        logger.error(f"Failed to send analytics data: {e}", exc_info=True)
```

Then add the S3 bucket to your LiveKit secrets:

```bash
lk agent update-secrets \
  --secrets "ANALYTICS_S3_BUCKET=pandadoc-voice-analytics"
```

## Querying S3 Data with Athena

Once data is in S3, set up Athena for SQL queries:

### 1. Create Athena Table

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS voice_sessions (
  `_event_type` string,
  `_timestamp` double,
  `_session_id` string,
  `duration_seconds` double,
  `discovered_signals` struct<
    team_size: int,
    monthly_volume: int,
    integration_needs: array<string>,
    urgency: string,
    industry: string
  >,
  `tool_calls` array<struct<
    tool: string,
    timestamp: string,
    success: boolean
  >>,
  `metrics_summary` struct<
    llm_tokens: int,
    stt_audio_seconds: double,
    tts_characters: int
  >
)
STORED AS JSON
LOCATION 's3://pandadoc-voice-analytics/sessions/'
PARTITIONED BY (
  year int,
  month int,
  day int
);

-- Update partitions
MSCK REPAIR TABLE voice_sessions;
```

### 2. Example Athena Queries

```sql
-- Find qualified leads this week
SELECT
  _session_id,
  discovered_signals.team_size,
  discovered_signals.monthly_volume,
  duration_seconds
FROM voice_sessions
WHERE year = 2025
  AND (discovered_signals.team_size >= 5
       OR discovered_signals.monthly_volume >= 100)
ORDER BY _timestamp DESC;

-- Average session duration by day
SELECT
  year, month, day,
  COUNT(*) as session_count,
  AVG(duration_seconds) as avg_duration,
  SUM(metrics_summary.llm_tokens) as total_tokens
FROM voice_sessions
GROUP BY year, month, day
ORDER BY year DESC, month DESC, day DESC;
```

## Cost Estimates

- **S3 Storage**: $0.023/GB/month (~$0.12/month for 5GB)
- **Kinesis Firehose**: $0.029/GB ingested (~$0.15/month for 5GB)
- **Lambda**: Free tier covers most usage
- **Athena**: $5/TB scanned (~$0.025/month for typical queries)

**Total: ~$0.50/month for 1000 sessions/day**

## Which Option to Choose?

1. **Kinesis Firehose** (Option 1): Best for production, automatic, real-time
2. **Lambda Function** (Option 2): Best if you need custom processing
3. **Direct S3** (Option 3): Simplest to implement, immediate availability

Start with Option 1 (Kinesis Firehose) for the most robust solution!