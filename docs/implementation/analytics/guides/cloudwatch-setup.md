# CloudWatch Analytics Deployment Guide for LiveKit Cloud

## Quick Start (5 Minutes)

### Step 1: Configure AWS Credentials in LiveKit Cloud

```bash
# From your project directory
lk agent update-secrets \
  --secrets "AWS_ACCESS_KEY_ID=your-key-id" \
  --secrets "AWS_SECRET_ACCESS_KEY=your-secret" \
  --secrets "AWS_REGION=us-east-1"
```

### Step 2: Deploy Your Agent

```bash
# Deploy with the updated analytics code
lk agent deploy
```

### Step 3: Verify CloudWatch Log Streaming

1. Navigate to AWS CloudWatch Console
2. Go to **Log Groups**
3. Look for a log group named after your LiveKit agent
4. You should see structured JSON logs appearing within 1-2 minutes

## What's Already Implemented ✅

Your agent is already configured to output structured JSON logs that CloudWatch can parse:

```json
{
  "_event_type": "session_analytics",
  "_timestamp": 1738000000.123,
  "_session_id": "room_abc123",
  "_log_level": "INFO",
  "duration_seconds": 330.5,
  "discovered_signals": {
    "team_size": 8,
    "monthly_volume": 200,
    "integration_needs": ["salesforce"],
    "urgency": "high"
  },
  "tool_calls": [...],
  "metrics_summary": {...}
}
```

## CloudWatch Insights Queries

Once logs are flowing, use these queries in CloudWatch Insights:

### 1. Find Today's Qualified Leads
```sql
fields _session_id, discovered_signals.team_size as team_size,
       discovered_signals.monthly_volume as volume
| filter _event_type = "session_analytics"
| filter team_size >= 5 or volume >= 100
| sort _timestamp desc
| limit 20
```

### 2. Daily Session Analytics
```sql
stats count() as total_sessions,
      avg(duration_seconds) as avg_duration_seconds,
      sum(metrics_summary.llm_tokens) as total_tokens
by bin(1d) as day
| filter _event_type = "session_analytics"
| sort day desc
```

### 3. Tool Usage Report
```sql
fields _session_id, tool_calls
| filter _event_type = "session_analytics"
| filter ispresent(tool_calls)
| stats count() by tool_calls.0.tool
```

### 4. Conversation Success Rate
```sql
stats count() as total,
      sum(case when tool_calls.1.tool = "book_sales_meeting"
          and tool_calls.1.success = true then 1 else 0 end) as bookings
| filter _event_type = "session_analytics"
| fields total, bookings, (bookings * 100.0 / total) as booking_rate
```

## AWS IAM Policy Required

Create an IAM user with this minimal policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:*"
    }
  ]
}
```

## Testing Your Setup

### 1. Run a Test Session
```bash
# Start a console session to generate test data
uv run python src/agent.py console
```

### 2. Have a Test Conversation
```
You: "We're a team of 10 people looking for document automation"
Agent: [responds and detects team_size signal]
You: "We process about 500 documents per month"
Agent: [detects monthly_volume signal]
You: "Can you show me how to create templates?"
Agent: [calls unleash_search_knowledge tool]
You: "exit"
[Session ends, analytics exported]
```

### 3. Check CloudWatch (1-2 minutes later)
- Log should appear with all collected data
- Use CloudWatch Insights to query

## Optional: Set Up CloudWatch Dashboard

Create a dashboard with these widgets:

1. **Qualified Leads Counter** - Shows leads with team_size >= 5
2. **Session Volume Graph** - Daily session count
3. **Tool Usage Pie Chart** - Distribution of tool calls
4. **Average Session Duration** - Trend over time
5. **Hot Leads Table** - Real-time qualified lead details

## Troubleshooting

### Logs Not Appearing in CloudWatch?

1. **Check Credentials**:
```bash
lk agent secrets list
# Verify AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION are set
```

2. **Check Agent Logs**:
```bash
lk agent logs --tail
# Look for "Session analytics data" messages
```

3. **Verify IAM Permissions**:
- Ensure IAM user has CloudWatch write permissions
- Check AWS_REGION matches your CloudWatch region

### Structured Logs Appearing as Plain Text?

This is normal! CloudWatch stores them as JSON strings but parses them for Insights queries. The queries will work correctly.

## Cost Optimization

### Current Implementation (Phase 1)
- **CloudWatch Logs**: ~$0.50/GB ingested
- **Estimated**: $3/month for 1000 sessions/day

### Future Optimization (Phase 2+)
- Set up S3 export for logs older than 7 days
- Use CloudWatch Logs Insights for recent data
- Use Athena on S3 for historical analysis
- Reduces cost by ~80% for historical data

## Next Steps

### Week 1
- [x] Enable CloudWatch forwarding (this guide)
- [ ] Create CloudWatch dashboard
- [ ] Set up CloudWatch alarms for hot leads

### Week 2
- [ ] Configure S3 export for long-term storage
- [ ] Set up Athena for SQL analytics
- [ ] Create weekly analytics reports

### Month 1
- [ ] Build analytics service consuming from S3
- [ ] Integrate with Salesforce/Amplitude
- [ ] Add real-time processing if needed

---

**Status**: Ready for CloudWatch deployment
**Time to Deploy**: 5 minutes
**Time to First Analytics**: 10 minutes