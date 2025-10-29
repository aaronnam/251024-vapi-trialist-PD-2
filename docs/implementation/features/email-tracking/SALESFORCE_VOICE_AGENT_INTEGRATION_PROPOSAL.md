# Voice AI Agent → Salesforce Integration Proposal

**To**: PandaDoc Salesforce Administration Team
**From**: Voice AI Engineering Team
**Date**: 2025-10-29
**Subject**: Automated Salesforce Updates from Voice Agent Calls

---

## Executive Summary

Our new Voice AI Agent for trial success is now live and capturing valuable interaction data. This proposal outlines the recommended architecture for automatically updating Salesforce with call activity, enabling sales teams to track trial user engagement and follow up effectively.

**Recommended Approach**: Event-driven S3 → Lambda → Salesforce integration

**Key Benefits**:
- ✅ Near real-time Salesforce updates (< 2 minutes after call ends)
- ✅ Zero impact on agent performance
- ✅ Automatic contact/lead matching via email
- ✅ Simple architecture with minimal moving parts
- ✅ Easy to monitor, debug, and maintain
- ✅ Scales automatically with call volume

**Implementation Effort**: 2-3 days (AWS setup + Salesforce configuration)

---

## Current State

### What's Working Today

Our Voice AI Agent is fully operational with analytics export:

**Data Flow (Current)**:
```
User Call → Voice Agent → S3 Export
                          ↓
                    (stops here)
```

**S3 Bucket**: `pandadoc-voice-analytics-1761683081`
**Data Format**: Gzipped JSON files organized by date
**Partition Structure**: `s3://bucket/sessions/year=YYYY/month=MM/day=DD/session_ID.json.gz`

**Sample Data Captured**:
```json
{
  "session_id": "rm_abc123xyz",
  "user_email": "john.doe@acme.com",
  "start_time": "2025-10-29T14:30:00Z",
  "end_time": "2025-10-29T14:45:00Z",
  "duration_seconds": 900,
  "tool_calls": [
    {
      "tool": "book_sales_meeting",
      "customer_name": "John Doe",
      "customer_email": "john.doe@acme.com",
      "preferred_date": "2025-11-01",
      "meeting_booked": true
    }
  ],
  "discovered_signals": {
    "use_case": "sales_proposals",
    "team_size": "10-50",
    "pain_points": ["manual contract creation", "slow approval process"]
  }
}
```

### The Gap

Sales teams don't currently see voice agent activity in Salesforce, leading to:
- ❌ Missed follow-up opportunities
- ❌ Incomplete trial engagement picture
- ❌ Manual checking of separate analytics dashboards
- ❌ Inability to trigger automated workflows based on call activity

---

## Proposed Solution: Event-Driven Integration

### Architecture Overview

```
┌─────────────┐
│  Voice Call │
│   Ends      │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Agent Exports     │
│   Session Data      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐     S3 Event Notification
│  S3 Bucket          │────────────────────┐
│  (analytics)        │                    │
└─────────────────────┘                    │
                                           ▼
                                    ┌──────────────┐
                                    │   Lambda     │
                                    │  Function    │
                                    └──────┬───────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
            ┌───────────────┐      ┌─────────────┐      ┌──────────────┐
            │ Match Contact │      │ Create Task │      │ Update Lead  │
            │ by Email      │      │ or Activity │      │ Status       │
            └───────────────┘      └─────────────┘      └──────────────┘
                    │                      │                      │
                    └──────────────────────┼──────────────────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │  Salesforce  │
                                    │              │
                                    └──────────────┘
```

### How It Works

1. **Voice call ends** → Agent exports session data to S3
2. **S3 triggers Lambda** → New file arrival fires Lambda function
3. **Lambda processes data** → Extracts key information from JSON
4. **Match in Salesforce** → Finds Contact/Lead by email address
5. **Create Activity** → Logs call as Task or Activity record
6. **Update fields** → Enriches Contact/Lead with call insights

**Latency**: < 2 minutes from call end to Salesforce update

---

## Salesforce Data Model

### Recommended Objects to Update

#### 1. Task (Primary) - Log the Call Activity

**Object**: `Task`
**Purpose**: Create a record of each voice agent call

**Fields to Populate**:
```
Subject:          "Voice AI Call - [Date]"
WhoId:            Contact/Lead ID (matched by email)
WhatId:           Account ID (if applicable)
ActivityDate:     Call date
Status:           "Completed"
TaskSubtype:      "Call"
Type:             "Voice AI Call"
Description:      Call summary with key signals
CallDurationInSeconds: Duration of call
```

**Example Task Description**:
```
Voice AI Call Summary
Duration: 15 minutes
Topics Discussed: Sales proposals, contract automation
Use Case: Sales team (10-50 users)
Pain Points: Manual contract creation, slow approval process

Agent Actions:
✓ Booked sales meeting for Nov 1, 2025
✓ Sent product documentation
```

#### 2. Contact/Lead (Secondary) - Enrich with Insights

**Object**: `Contact` or `Lead`
**Purpose**: Update engagement tracking and qualification data

**Custom Fields Needed** (if don't exist):
```
Voice_Agent_Last_Call_Date__c:     Date
Voice_Agent_Total_Calls__c:        Number
Voice_Agent_Engagement_Score__c:   Number (0-100)
Voice_Agent_Identified_Use_Case__c: Text
Voice_Agent_Team_Size__c:          Picklist
Voice_Agent_Meeting_Booked__c:     Checkbox
```

**Update Logic**:
- Increment total calls counter
- Update last call date
- Set engagement score based on call quality/duration
- Capture identified use case
- Flag if meeting was booked

#### 3. Opportunity (Optional) - Update Trial Stage

**Object**: `Opportunity`
**Purpose**: Progress trial opportunities based on engagement

**Example Logic**:
- If meeting booked → Move to "Meeting Scheduled"
- If high engagement score → Add to "Hot Trials" campaign
- If pain points discovered → Update opportunity notes

---

## Lambda Function Design

### Function Overview

**Language**: Python 3.11
**Runtime**: 512 MB memory, 30 second timeout
**Trigger**: S3 PUT event on `sessions/` prefix

### Core Logic Flow

```python
def lambda_handler(event, context):
    """
    Process voice agent session data and update Salesforce.
    """

    # 1. Extract S3 file info from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # 2. Download and decompress session data
    session_data = download_and_parse_s3_file(bucket, key)

    # 3. Match Contact/Lead in Salesforce by email
    salesforce_record = find_salesforce_record(session_data['user_email'])

    if not salesforce_record:
        # No match - log to CloudWatch for review
        log_unmatched_email(session_data['user_email'])
        return

    # 4. Create Task for call activity
    task_id = create_salesforce_task(
        contact_id=salesforce_record['Id'],
        session_data=session_data
    )

    # 5. Update Contact/Lead with engagement data
    update_contact_fields(
        contact_id=salesforce_record['Id'],
        session_data=session_data
    )

    # 6. (Optional) Update related Opportunity
    if salesforce_record.get('OpportunityId'):
        update_opportunity(
            opportunity_id=salesforce_record['OpportunityId'],
            session_data=session_data
        )

    return {
        'statusCode': 200,
        'body': f'Updated Salesforce for {session_data["user_email"]}'
    }
```

### Key Functions

#### Match Contact/Lead by Email
```python
def find_salesforce_record(email):
    """
    Find Contact or Lead in Salesforce by email.
    Returns Contact if found, else Lead, else None.
    """
    # Try Contact first
    query = f"SELECT Id, AccountId FROM Contact WHERE Email = '{email}' LIMIT 1"
    result = sf.query(query)

    if result['totalSize'] > 0:
        return {'Id': result['records'][0]['Id'], 'Type': 'Contact'}

    # Try Lead if no Contact found
    query = f"SELECT Id FROM Lead WHERE Email = '{email}' AND IsConverted = false LIMIT 1"
    result = sf.query(query)

    if result['totalSize'] > 0:
        return {'Id': result['records'][0]['Id'], 'Type': 'Lead'}

    return None
```

#### Create Task
```python
def create_salesforce_task(contact_id, session_data):
    """
    Create a Task record for the voice call.
    """
    # Build description from session data
    description = build_call_summary(session_data)

    task = {
        'Subject': f"Voice AI Call - {session_data['start_time'][:10]}",
        'WhoId': contact_id,
        'ActivityDate': session_data['start_time'][:10],
        'Status': 'Completed',
        'TaskSubtype': 'Call',
        'Type': 'Voice AI Call',
        'Description': description,
        'CallDurationInSeconds': int(session_data['duration_seconds'])
    }

    result = sf.Task.create(task)
    return result['id']
```

#### Build Call Summary
```python
def build_call_summary(session_data):
    """
    Generate human-readable call summary for Task description.
    """
    summary_parts = [
        "Voice AI Call Summary",
        f"Duration: {int(session_data['duration_seconds'] / 60)} minutes",
        ""
    ]

    # Add discovered signals
    if session_data.get('discovered_signals'):
        signals = session_data['discovered_signals']
        summary_parts.append("Discovered Information:")
        if signals.get('use_case'):
            summary_parts.append(f"• Use Case: {signals['use_case']}")
        if signals.get('team_size'):
            summary_parts.append(f"• Team Size: {signals['team_size']}")
        if signals.get('pain_points'):
            summary_parts.append(f"• Pain Points: {', '.join(signals['pain_points'])}")
        summary_parts.append("")

    # Add tool usage
    if session_data.get('tool_calls'):
        summary_parts.append("Agent Actions:")
        for tool_call in session_data['tool_calls']:
            if tool_call['tool'] == 'book_sales_meeting':
                summary_parts.append(f"✓ Booked sales meeting for {tool_call.get('preferred_date', 'TBD')}")
            elif tool_call['tool'] == 'send_documentation':
                summary_parts.append(f"✓ Sent product documentation")
        summary_parts.append("")

    # Add session link
    summary_parts.append(f"Session ID: {session_data['session_id']}")

    return "\n".join(summary_parts)
```

---

## Implementation Plan

### Phase 1: AWS Infrastructure Setup (1 day)

**Tasks**:
1. Create Lambda function with Python 3.11 runtime
2. Configure S3 event trigger for `sessions/` prefix
3. Set up IAM role with permissions:
   - S3 read access to analytics bucket
   - CloudWatch Logs write access
   - Secrets Manager read access (for Salesforce credentials)
4. Store Salesforce credentials in AWS Secrets Manager
5. Install `simple-salesforce` Python package in Lambda layer

**Owner**: DevOps/Platform Engineering

### Phase 2: Salesforce Configuration (1 day)

**Tasks**:
1. Create custom fields on Contact/Lead objects:
   - `Voice_Agent_Last_Call_Date__c` (Date)
   - `Voice_Agent_Total_Calls__c` (Number)
   - `Voice_Agent_Engagement_Score__c` (Number)
   - `Voice_Agent_Identified_Use_Case__c` (Text)
   - `Voice_Agent_Team_Size__c` (Picklist)
   - `Voice_Agent_Meeting_Booked__c` (Checkbox)

2. Create Task record type (if needed):
   - Name: "Voice AI Call"
   - Available to relevant profiles

3. Create Salesforce connected app:
   - OAuth 2.0 authentication
   - Required scopes: `api`, `refresh_token`
   - Grant access to integration user

4. Set up integration user with appropriate permissions

**Owner**: Salesforce Admin Team

### Phase 3: Lambda Development & Testing (1 day)

**Tasks**:
1. Implement core Lambda function
2. Add error handling and logging
3. Test with sample S3 files
4. Verify Salesforce updates work correctly
5. Test edge cases:
   - Email not found in Salesforce
   - Invalid JSON data
   - Salesforce API errors
   - Duplicate prevention

**Owner**: Voice AI Engineering Team

### Phase 4: Monitoring & Rollout (Ongoing)

**Tasks**:
1. Set up CloudWatch alarms:
   - Lambda errors
   - Unmatched emails
   - Salesforce API failures
2. Create dashboard for monitoring
3. Enable Lambda for production traffic
4. Monitor for 1 week
5. Iterate based on feedback

**Owner**: Voice AI Engineering + Salesforce Admin

---

## Data Governance

### Email Matching Strategy

**Primary Strategy**: Exact email match
```
Contact.Email = session_data.user_email
OR
Lead.Email = session_data.user_email (where IsConverted = false)
```

**Match Priority**:
1. Contact (converted leads)
2. Lead (non-converted)
3. No match → Log to CloudWatch for manual review

### Handling Unmatched Emails

**Scenarios**:
- Email not in Salesforce (new user not yet synced)
- Typo in email address
- Personal email used instead of work email

**Solution**:
1. Log unmatched emails to CloudWatch
2. Create weekly report of unmatched emails
3. Manual review and reconciliation
4. Consider creating new Lead if email is valid

### Data Retention

**S3 Session Data**: Retained per existing analytics retention policy

**Salesforce Tasks**: Follow standard Salesforce retention

**Lambda Logs**: 30-day retention in CloudWatch

---

## Error Handling & Resilience

### Lambda Retry Logic

**Built-in S3 Event Retry**: If Lambda fails, S3 will retry up to 3 times

**Dead Letter Queue**: Failed events sent to SQS for manual review

**Error Scenarios Handled**:

| Error Type | Handling Strategy |
|------------|-------------------|
| S3 file not found | Log error, exit gracefully |
| Invalid JSON | Log error with file path, alert team |
| Email not in SF | Log to CloudWatch, continue (not a failure) |
| SF API error | Retry up to 3 times with exponential backoff |
| SF rate limit | Implement backoff, queue for later retry |
| Duplicate Task | Check for existing Task with same session_id, skip if exists |

### Monitoring & Alerts

**CloudWatch Metrics to Track**:
- Lambda invocations
- Lambda errors
- Emails matched vs. unmatched
- Salesforce API call count
- Processing latency

**Alerts to Configure**:
- Lambda error rate > 5%
- Unmatched email rate > 20%
- Salesforce API errors
- Processing latency > 5 minutes

---

## Alternative Approaches Considered

### Option B: Batch Processing (S3 → Glue → Snowflake → Salesforce)

**Architecture**:
```
S3 → AWS Glue → Snowflake → Salesforce (scheduled sync)
```

**Pros**:
- Integrates with existing data warehouse
- Better for complex analytics
- Handles high volume efficiently

**Cons**:
- ❌ Higher latency (hourly or daily sync)
- ❌ More complex architecture
- ❌ More expensive (Glue jobs + Snowflake compute)
- ❌ Overkill for simple call logging

**Recommendation**: Consider for future if we need complex analytics, but not for initial implementation.

---

### Option C: Direct API from Agent (Real-time)

**Architecture**:
```
Agent → Salesforce API (during call)
```

**Pros**:
- Instant updates
- No additional infrastructure

**Cons**:
- ❌ Couples agent to Salesforce (vendor lock-in)
- ❌ Adds latency to agent (impacts call quality)
- ❌ Salesforce outage breaks agent
- ❌ Harder to test and debug
- ❌ Not recommended by LiveKit SDK patterns

**Recommendation**: Not recommended. Violates separation of concerns.

---

### Option D: Salesforce Data Cloud

**Architecture**:
```
S3 → Salesforce Data Cloud → Salesforce
```

**Pros**:
- Native Salesforce solution
- Advanced analytics capabilities

**Cons**:
- ❌ Expensive (additional licensing)
- ❌ Overkill for this use case
- ❌ Longer setup time

**Recommendation**: Consider only if already using Data Cloud.

---

## Cost Estimate

### AWS Costs (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 10,000 calls/month @ 512MB, 5s avg | ~$1 |
| S3 Event Notifications | 10,000 events/month | Free |
| CloudWatch Logs | 5 GB/month | ~$2.50 |
| Secrets Manager | 1 secret | ~$0.40 |
| **Total** | | **~$4/month** |

### Salesforce Costs

**API Calls**: ~10,000/month (within standard API limits for most orgs)

**Storage**: Minimal (Task records are small)

**Total Additional Cost**: **$0** (within existing limits)

### Total Cost: **~$4/month**

---

## Security Considerations

### Salesforce Credentials

**Storage**: AWS Secrets Manager (encrypted at rest)
**Access**: Lambda execution role only
**Rotation**: 90-day rotation policy recommended

### Data in Transit

**S3 → Lambda**: Internal AWS network (encrypted)
**Lambda → Salesforce**: HTTPS with TLS 1.2+

### IAM Best Practices

- Least privilege access for Lambda role
- No hardcoded credentials in code
- Audit logging enabled via CloudTrail

### PII Handling

**Email Addresses**: Already stored in Salesforce
**Session Data**: Contains business context, no sensitive PII
**Compliance**: GDPR/CCPA compliant (data already in Salesforce)

---

## Success Metrics

### Technical Metrics

- **Processing Success Rate**: > 95%
- **Email Match Rate**: > 80%
- **Latency**: < 2 minutes from call end to Salesforce update
- **Error Rate**: < 5%

### Business Metrics

- **Sales Visibility**: 100% of voice calls visible in Salesforce
- **Follow-up Time**: Reduced time to follow up after call
- **Conversion Impact**: Track trial-to-paid conversion for users who used voice AI

### Monitoring Dashboard

Create Salesforce report showing:
- Voice AI calls this week
- Contacts with voice AI engagement
- Meetings booked via voice AI
- Top use cases discovered

---

## Timeline

| Week | Milestone |
|------|-----------|
| Week 1 | AWS infrastructure setup, Salesforce field creation |
| Week 2 | Lambda development, unit testing |
| Week 3 | Integration testing, monitoring setup |
| Week 4 | Production rollout, monitoring |

**Total Duration**: 4 weeks to production

**Minimum Viable Product**: Could launch basic version (just Task creation) in 1-2 weeks

---

## Next Steps

### Immediate Actions Required

1. **Salesforce Admin Team**:
   - [ ] Review proposed custom fields
   - [ ] Create connected app for API access
   - [ ] Set up integration user
   - [ ] Provide OAuth credentials

2. **Platform Engineering Team**:
   - [ ] Provision Lambda function
   - [ ] Configure S3 event trigger
   - [ ] Set up Secrets Manager

3. **Voice AI Engineering Team**:
   - [ ] Develop Lambda function
   - [ ] Test with sample data
   - [ ] Document error handling

4. **Joint Teams**:
   - [ ] Schedule kickoff meeting
   - [ ] Align on data model
   - [ ] Define success criteria

---

## Questions for Salesforce Team

1. **Field Naming**: Do we have a naming convention for custom fields? Should we use `Voice_Agent__c` or different prefix?

2. **Existing Fields**: Do we already track any phone/call engagement metrics we should align with?

3. **Task Assignment**: Should Tasks be assigned to a specific user (e.g., account owner) or left unassigned?

4. **Workflow Automation**: Should we trigger any workflows when these Tasks are created? (e.g., email to account owner)

5. **Reporting**: Do you need specific reports/dashboards built for voice AI activity?

6. **API Limits**: What's our current API usage? Do we have headroom for 10k additional calls/month?

7. **Opportunity Stage**: Should voice calls automatically progress Opportunity stage?

---

## Conclusion

The recommended **Event-Driven S3 → Lambda → Salesforce** integration provides the optimal balance of:

- ✅ Simplicity (minimal moving parts)
- ✅ Performance (near real-time updates)
- ✅ Reliability (built-in retries, error handling)
- ✅ Cost-effectiveness (~$4/month)
- ✅ Maintainability (standard AWS patterns)
- ✅ Scalability (handles growth automatically)

This architecture leverages existing infrastructure (S3 analytics export) and requires minimal ongoing maintenance. Sales teams will gain immediate visibility into trial user engagement through voice AI calls, enabling better follow-up and improved conversion rates.

We're ready to proceed with implementation pending Salesforce admin team approval and OAuth credentials.

---

**Contact for Questions**:
- Technical Implementation: Voice AI Engineering Team
- Salesforce Configuration: [Your Salesforce Admin Contact]
- Project Management: [Your PM Contact]

**Appendix**:
- [A] Sample Lambda Code (Full Implementation)
- [B] Sample S3 Session Data (JSON Schema)
- [C] Salesforce Field Definitions (Detailed Spec)
- [D] Monitoring Dashboard Configuration
