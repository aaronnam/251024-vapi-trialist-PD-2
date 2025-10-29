PandaDoc Voice Agent - Complete Data Flow Specification (Simplified)

Overview
This document provides an exhaustive breakdown of all data, metrics, and analytics flowing through the separated architecture system. Each section details exactly what data is collected, processed, and distributed to various systems.

---

1. LiveKit Agent (Data Collection Layer)

The LiveKit agent focuses solely on collecting raw data during voice sessions without performing any analysis.

1.1 Session Metadata
- session_id
- start_time
- end_time
- duration_seconds
- participant_id
- user_email
- user_name

1.2 Raw Transcript Data
- Complete conversation history
- User utterances
- Agent responses
- Interruption markers
- Turn-taking data

1.3 Performance Metrics (LiveKit Built-in)
- eou_delay
- llm_ttft
- tts_ttfb
- stt_duration
- total_latency
- prompt_tokens
- completion_tokens
- total_tokens
- stt_audio_duration
- tts_characters_count
- tts_audio_duration

1.4 Discovered Signals (Business Context)
- team_size
- monthly_volume
- integration_needs
- industry
- location
- use_case
- current_tool
- pain_points
- decision_timeline
- budget_authority
- urgency
- qualification_tier

1.5 Tool Usage Tracking

unleash_search_knowledge calls
- query
- category
- results_found
- total_results
- timestamp

book_sales_meeting calls
- customer_name
- customer_email
- preferred_date
- preferred_time
- success
- meeting_link
- calendar_event_id
- timestamp

1.6 Connection Quality Metrics
- bandwidth_in
- bandwidth_out
- packet_loss
- jitter
- device_info

---

2. Message Queue (Data Transport)

2.1 Queue Configuration
- Platform: AWS SQS or Google Pub/Sub
- Message Format: JSON
- Message Size: Up to 256KB (SQS) or 10MB (Pub/Sub)

2.2 Message Structure
- Body: Complete raw session data (all sections above)
- Message Attributes

2.3 Reliability Configuration
- Retry Policy: 3 attempts with exponential backoff (1s, 2s, 4s)
- Visibility Timeout: 5 minutes (processing time limit)
- Dead Letter Queue: Failed messages after 3 retries
- Message Retention: 14 days
- Deduplication: 5-minute deduplication window (for SQS FIFO)

---

3. Analytics Agent (Processing Pipeline)

The analytics agent processes raw session data through multiple specialized modules.

3.1 Sales Intelligence Analyzer

Extractions Performed:
- Team size extraction & validation
- Document volume estimation
- CRM integration detection
- Budget authority inference
- Decision timeline parsing
- Competitor mention detection
- Objection classification
- Feature request extraction
- Buying signal detection
- Stakeholder identification
- Use case categorization
- Pain point analysis
- BANT qualification scoring

Output: Sales Intelligence Report

3.2 Lead Scoring Engine

Score Components:
- Demographic score (0-20 points)
- Behavioral score (0-25 points)
- Firmographic score (0-20 points)
- Intent score (0-20 points)
- Fit score (0-15 points)
- Weighted total score (0-100)
- Confidence level

Output: Lead Score Report

3.3 Conversation Quality Analyzer

Quality Metrics:
- Turn balance ratio
- Question engagement count
- Active listening indicators
- Interruption frequency
- Dead air percentage
- Natural ending detection
- Sentiment progression (start to end)
- User satisfaction proxy
- Agent effectiveness score

Output: Quality Score Report

3.4 Sentiment Analyzer

Sentiment Dimensions:
- Overall sentiment
- Sentiment by conversation segment
- Emotional tone detection
- Frustration indicators
- Enthusiasm markers
- Confidence level

Output: Sentiment Report

3.5 Objection & Competitor Detector

Objection Types:
- Pricing objections
- Feature gap objections
- Timing objections
- Competitor mentions
- Competitor comparison requests
- Switching barriers identified

Output: Objection & Competitor Report

3.6 Performance Metrics Calculator

Calculations:
- Average latency
- p50, p95, p99 latency percentiles
- Token usage statistics
- Cost calculation (per provider)
- Performance score vs targets
- Anomaly detection

Output: Performance Report

3.7 Content Gap Analyzer

Gap Identification:
- Failed knowledge base searches
- Unanswered questions
- Repeat question patterns
- Missing documentation areas
- Source effectiveness (Intercom coverage)

Output: Content Gap Report

3.8 Action Item Extractor

Action Items:
- Commitments made by user
- Follow-up tasks for sales
- Feature demo requests
- Document sharing needs
- Next steps timeline

Output: Action Items List

3.9 Executive Summary Generator

Summary Components:
- Call outcome
- Key takeaways (3-5 bullets)
- Risk factors
- Opportunity summary
- Recommended next action

Output: Executive Summary

---

4. Salesforce CRM (Sales Intelligence Destination)

All analyzed data is synced to Salesforce for sales team use.

4.1 Lead/Contact Record Updates (Standard Fields)
- Lead Score
- Lead Score Breakdown
- Qualification Tier
- Last Call Date
- Call Duration
- Engagement Score

4.2 Discovered Signals (Custom Fields)
- Team_Size__c
- Monthly_Document_Volume__c
- Integration_Needs__c
- Industry_Vertical__c
- Decision_Timeline__c
- Budget_Authority__c
- Current_Tool__c
- Urgency_Level__c

4.3 Pain Points & Needs
- Pain_Points__c
- Use_Cases__c
- Feature_Requests__c

4.4 Competitive Intelligence
- Competitor_Mentioned__c
- Current_Solution__c
- Switching_Barriers__c

4.5 Call Intelligence
- Objections_Raised__c
- Buying_Signals__c
- Stakeholders_Mentioned__c
- Key_Quotes__c
- Call_Sentiment__c

4.6 Action Items & Next Steps
- Next_Best_Action__c
- Follow_Up_Priority__c
- Recommended_Owner__c

4.7 Automated Task Creation
- Subject: "Follow up on voice trial call - [Lead Name]"
- Description
- Due Date
- Priority
- Status
- Assigned To

4.8 Custom Object: Voice_Call__c
- Session_Id__c
- Transcript__c
- Call_Summary__c
- Transcript_URL__c
- Quality_Score__c
- Call_Date__c
- Duration_Minutes__c
- Related_To__c
- Metrics_JSON__c

---

5. Amplitude Analytics (Product Analytics)

5.1 Session Completion Event
Event Name: voice_trial_session_completed

Event Properties:
- session_id
- duration_seconds
- turn_count
- qualification_tier
- engagement_score
- sentiment
- meeting_booked
- tool_calls_count

5.2 User Identification
User Properties:
- team_size
- monthly_volume
- industry
- location
- qualification_tier
- lead_score
- last_call_date
- total_calls

5.3 Engagement Events

Event: knowledge_base_searched
Properties:
- query
- results_found
- total_results
- category
- session_id

Event: sales_meeting_booked
Properties:
- meeting_time
- preferred_date
- preferred_time
- success
- qualification_tier
- session_id

Event: feature_discussed
Properties:
- feature_name
- interest_level
- context
- session_id

5.4 Quality Metrics Event

Event: conversation_quality_measured
Properties:
- quality_score
- turn_balance
- interruption_count
- dead_air_percentage
- natural_ending
- session_id

5.5 Performance Metrics Event

Event: latency_measured
Properties:
- avg_latency_ms
- p95_latency_ms
- max_latency_ms
- avg_llm_ttft_ms
- avg_tts_ttfb_ms
- total_tokens
- session_id

---

6. Real-Time Dashboard (Looker/Tableau/Metabase)

6.1 Performance Monitoring Panel
Widgets:
- Current calls active
- Average latency (last hour)
- P95 latency trend
- Error rate
- Token usage rate
- Cost burn rate
- Connection quality distribution

6.2 Business Metrics Panel
Widgets:
- Today's calls
- Qualified leads (Tier 1)
- Meetings booked
- Average engagement score
- Conversion rate
- Revenue pipeline influenced

6.3 Call Quality Panel
Widgets:
- Average call duration
- Average turn count
- Interruption rate
- Sentiment distribution
- Natural ending rate
- User satisfaction proxy

6.4 Knowledge Base Effectiveness Panel
Widgets:
- Search success rate
- Top searched queries
- Content gaps identified
- Average results per query
- Tool usage breakdown

6.5 Sales Intelligence Panel
Widgets:
- Lead score distribution
- Top industries
- Team size distribution
- Integration needs breakdown
- Competitor mentions
- Common objections

6.6 Trending Insights Panel
Widgets:
- Calls trend (last 7/30 days)
- Qualification rate trend
- Meeting booking trend
- Performance degradation alerts
- Hot leads today

6.7 Dashboard Filters (Global)
- Date range
- Qualification tier
- Sentiment
- Industry
- Agent version

---

7. Alert & Notification System

7.1 Critical Alerts (Immediate - PagerDuty)
Severity: P1 (Critical)
- Agent Down
- Error Rate >10%
- Average Latency >2000ms
- Queue Backlog >100
- API Failures

7.2 High Priority Alerts (5 min - Slack #ops)
Severity: P2 (High)
- Latency >1500ms Sustained
- Error Rate >5%
- Token Usage Spike
- Cost Burn Rate Exceeds Budget
- Connection Quality Degraded

7.3 Business Alerts (Real-time - Slack #sales)
Severity: Business Critical
- Hot Lead Detected (Score >80)
- Meeting Booked
- Competitor Mentioned

7.4 Quality Alerts (Hourly digest - Slack #product)
Severity: P3 (Normal)
- Content Gaps Identified
- Low Engagement Sessions
- Feature Requests

7.5 Executive Alerts (Daily/Weekly - Email)
- Daily Executive Summary
- Weekly Executive Rollup

---

8. Data Warehouse (Historical Storage)

8.1 Table Schemas

sessions (Fact Table)
Columns:
- session_id
- start_time
- end_time
- duration_seconds
- participant_id
- user_email
- user_name
- turn_count
- interruption_count
- qualification_tier
- lead_score
- engagement_score
- sentiment
- meeting_booked
- created_at

transcripts (Text Data)
Columns:
- session_id
- transcript_json
- transcript_text
- word_count
- created_at

metrics (Time-Series)
Columns:
- id
- session_id
- timestamp
- metric_type
- eou_delay_ms
- llm_ttft_ms
- tts_ttfb_ms
- total_latency_ms
- prompt_tokens
- completion_tokens
- total_tokens
- stt_duration_ms
- created_at

leads (Dimension Table)
Columns:
- email
- name
- latest_session_id
- team_size
- monthly_volume
- integration_needs
- industry
- location
- use_case
- current_tool
- pain_points
- decision_timeline
- budget_authority
- urgency
- qualification_tier
- lead_score
- first_call_date
- last_call_date
- total_calls
- updated_at

analysis_results (Processed Intelligence)
Columns:
- session_id
- sales_intelligence
- lead_score_breakdown
- quality_analysis
- sentiment_analysis
- objections
- competitors
- performance_analysis
- content_gaps
- action_items
- executive_summary
- analyzed_at
- analyzer_version

alerts_history (Audit Log)
Columns:
- id
- alert_type
- alert_name
- severity
- message
- context
- session_id
- triggered_at
- sent_to
- acknowledged_at
- acknowledged_by
- resolved_at

8.2 Data Retention Policies

Raw Transcripts
- Retention: 90 days in hot storage
- Archive: After 90 days, move to cold storage
- Deletion: After 2 years
- PII Redaction: Applied after 30 days for non-qualified leads
- Access: Restricted to authorized personnel only

Metrics
- Retention: 1 year at full granularity
- Aggregation: After 1 year, aggregate to hourly summaries
- Archive: Aggregated data retained for 5 years
- Deletion: After 5 years unless required for compliance

Analysis Results
- Retention: Indefinite
- Reason: Business intelligence, model training, trend analysis
- PII: Redacted or anonymized per privacy policy

Alerts History
- Retention: 1 year in active database
- Archive: After 1 year, move to cold storage
- Deletion: After 3 years

PII Data Handling (GDPR/CCPA Compliance)
- Redaction Policy
- Redacted Fields
- Exceptions

8.3 Data Access Patterns

Real-Time Queries (Dashboard)
- Target: Last 24 hours of data
- Latency: <1 second
- Cache: 5-minute cache for aggregate metrics
- Optimization: Materialized views for common queries

Analytical Queries (Reports)
- Target: Last 90 days typically
- Latency: <30 seconds acceptable
- Schedule: Run overnight for large reports
- Optimization: Columnar storage, partitioning by date

Historical Analysis (Trends)
- Target: Up to 1 year of data
- Latency: <2 minutes acceptable
- Access: Typically scheduled jobs
- Optimization: Pre-aggregated rollups

---

Summary: Complete Data Lineage

Data Flow Summary
1. LiveKit Agent collects 70+ raw data points during conversation
2. Message Queue reliably transports data to analytics
3. Analytics Agent processes data through 9 specialized modules
4. Salesforce receives 40+ enriched fields for sales action
5. Amplitude tracks 15+ events and properties for product analytics
6. Dashboard displays 35+ metrics across 6 panels in real-time
7. Alerts notify 4 teams with 20+ alert types across 5 severity levels
8. Data Warehouse stores 6 table schemas with full retention policies

Total Data Points Tracked
- Collection: 70+ metrics and signals
- Analysis: 50+ derived insights
- Distribution: 100+ fields across systems
- Visualization: 35+ dashboard metrics
- Alerting: 20+ alert types
