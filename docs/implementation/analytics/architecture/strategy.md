# PandaDoc Voice Agent Analytics & Metrics Strategy

## Executive Summary
This document outlines a **separated analytics architecture** for the PandaDoc Trial Success Voice Agent, where the LiveKit agent focuses solely on data collection while a dedicated analytics pipeline handles all analysis. This separation ensures optimal voice performance while enabling sophisticated business intelligence.

## 🏗️ Architecture Philosophy: Separation of Concerns

### ✅ What the LiveKit Agent Does (Simple & Fast)
- Collect raw conversation data
- Track basic session metrics
- Store discovered signals
- Push data to storage/queue
- **That's it.**

### 🧠 What the Analytics Pipeline Does (Complex & Async)
- Process transcripts with LLMs
- Calculate lead scores
- Extract sales intelligence
- Generate reports
- Sync with CRM/BI tools
- Send alerts and notifications

## 🔄 Data Flow Architecture

```
┌─────────────────────┐
│   LiveKit Agent     │
│  (Data Collection)  │
│                     │
│ • Session metadata  │
│ • Raw transcripts   │
│ • Basic metrics     │
│ • Discovered signals│
└──────────┬──────────┘
           │
           ▼ JSON/Events
┌─────────────────────┐
│   Message Queue     │
│  (SQS/Pub/Sub)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Analytics Agent    │
│  (Heavy Processing) │
│                     │
│ • LLM Analysis      │
│ • Lead Scoring      │
│ • Pattern Detection │
│ • Report Generation │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────┬───────────┐
    ▼             ▼          ▼           ▼
[Salesforce] [Amplitude] [Dashboard] [Alerts]
```

---

## 🎯 Analytics Buckets Overview

### 1. **Call Performance & Technical Health**
→ Engineering, DevOps, Product Teams

### 2. **Sales Intelligence & Qualification**
→ Revenue Operations, Sales Leadership, BDRs

### 3. **User Experience & Engagement**
→ Product, Customer Success, Trial Experience Teams

### 4. **Business Impact & ROI**
→ Executive Team, Finance, Strategy

### 5. **Knowledge Base & Tool Effectiveness**
→ Content Team, Product Marketing, Support

---

## 📊 Bucket 1: Call Performance & Technical Health

### Core Performance Metrics

| Metric | Source | Collection Method | Alert Threshold | Purpose |
|--------|--------|-------------------|-----------------|---------|
| **End-to-End Latency** | `MetricsCollectedEvent` | `eou.delay + llm.ttft + tts.ttfb` | >1500ms | User experience quality |
| **STT Processing Time** | `STTMetrics.duration` | Event listener | >500ms | Speech recognition speed |
| **LLM Response Time (TTFT)** | `LLMMetrics.ttft` | Event listener | >700ms | Thinking speed perception |
| **TTS First Byte (TTFB)** | `TTSMetrics.ttfb` | Event listener | >300ms | Speaking start latency |
| **Token Generation Rate** | `LLMMetrics.tokens_per_second` | Usage collector | <50 tokens/s | LLM throughput |
| **Audio Quality Score** | LiveKit Cloud Analytics | API polling | <3.5/5 | Connection quality |
| **Error Rate** | Exception tracking | Try/catch logging | >5% | System reliability |
| **Interruption Frequency** | `conversation_item.interrupted` | Session history | >3 per call | Turn-taking quality |

### Data Collection vs Analysis

```python
# IN LIVEKIT AGENT (Simple Collection Only)
class LightweightAgent(Agent):
    def __init__(self):
        super().__init__(instructions="...")
        self.metrics_buffer = []

    @session.on("metrics_collected")
    async def collect_metrics(self, ev: MetricsCollectedEvent):
        # Just collect, don't analyze
        self.metrics_buffer.append({
            "timestamp": datetime.now().isoformat(),
            "eou_delay": ev.metrics.eou.end_of_utterance_delay if ev.metrics.eou else None,
            "llm_ttft": ev.metrics.llm.ttft if ev.metrics.llm else None,
            "tts_ttfb": ev.metrics.tts.ttfb if ev.metrics.tts else None,
            "total_tokens": ev.metrics.llm.total_tokens if ev.metrics.llm else None,
        })

    async def on_session_end(self):
        # Push raw metrics to queue
        await self.push_to_queue({
            "session_id": ctx.room.name,
            "metrics": self.metrics_buffer
        })

# IN ANALYTICS PIPELINE (Complex Analysis)
class PerformanceAnalyzer:
    async def analyze_performance(self, session_data):
        metrics = session_data["metrics"]

        # Calculate statistics
        latencies = [
            m["eou_delay"] + m["llm_ttft"] + m["tts_ttfb"]
            for m in metrics
            if all(m.get(k) for k in ["eou_delay", "llm_ttft", "tts_ttfb"])
        ]

        analysis = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": np.percentile(latencies, 95),
            "max_latency": max(latencies),
            "performance_score": self.calculate_score(latencies),
            "alerts": self.check_thresholds(latencies)
        }

        # Send alerts if needed
        if analysis["max_latency"] > 1500:
            await self.send_ops_alert("high_latency", analysis)

        return analysis
```

### Network & Connection Metrics

| Metric | Source | Collection Method | Purpose |
|--------|--------|-------------------|---------|
| **Bandwidth Usage** | Analytics API: `bandwidthIn/Out` | API polling | Cost optimization |
| **Connection Success Rate** | `connectionCounts` | Webhooks | Reliability tracking |
| **Packet Loss** | WebRTC stats | Room quality events | Audio quality |
| **Jitter** | WebRTC stats | Room quality events | Call stability |
| **Region Distribution** | Participant metadata | Session details | Infrastructure planning |

---

## 💰 Bucket 2: Sales Intelligence & Qualification

### Lead Qualification Signals

| Metric | Source | Collection Method | RevOps Value |
|--------|--------|-------------------|--------------|
| **Team Size Mentioned** | `discovered_signals['team_size']` | Conversation parsing | Lead scoring +10 pts if ≥5 |
| **Monthly Volume** | `discovered_signals['monthly_volume']` | NLP extraction | Enterprise indicator if ≥100 |
| **CRM Integration Need** | `discovered_signals['integration_needs']` | Keyword detection | High-value signal for ACV |
| **Current Tool Mentioned** | `discovered_signals['current_tool']` | Competitor analysis | Battlecard activation |
| **Budget Authority** | `discovered_signals['budget_authority']` | Role extraction | BANT qualification |
| **Urgency Timeline** | `discovered_signals['decision_timeline']` | Date parsing | Pipeline velocity |
| **Industry Vertical** | `discovered_signals['industry']` | Entity recognition | Segment targeting |
| **Pain Points** | `discovered_signals['pain_points']` | Sentiment analysis | Solution mapping |

### Conversation Intelligence (Separated Architecture)

```python
# IN LIVEKIT AGENT (Simple Signal Collection)
class LightweightAgent(Agent):
    def __init__(self):
        super().__init__(instructions="...")
        # Only track basic signals during conversation
        self.discovered_signals = {
            "team_size": None,
            "monthly_volume": None,
            "integration_needs": [],
        }

    async def on_session_end(self, session):
        # Just dump raw data - NO analysis
        raw_data = {
            "session_id": ctx.room.name,
            "transcript": session.history.to_dict(),
            "discovered_signals": self.discovered_signals,
            "timestamp": datetime.now().isoformat()
        }
        await self.push_to_queue(raw_data)

# IN ANALYTICS PIPELINE (Heavy LLM Analysis)
class SalesIntelligenceAnalyzer:
    def __init__(self):
        # Can use more powerful models here without latency concerns
        self.llm = Anthropic(model="claude-3.5-sonnet")  # Or GPT-4

    async def analyze_transcript(self, raw_data):
        transcript = raw_data["transcript"]

        # Complex multi-pass analysis with powerful LLM
        insights = await self.llm.analyze(
            prompt="""Analyze this sales call transcript for:
            1. Team size and structure
            2. Document volume and frequency
            3. Integration requirements
            4. Current tools and competitors
            5. Budget authority signals
            6. Urgency and timeline
            7. Objections and concerns
            8. Feature requests
            9. Buying signals
            10. Key stakeholders mentioned

            Return structured JSON with confidence scores.""",
            transcript=transcript
        )

        # Lead scoring with ML model
        lead_score = self.ml_model.predict(insights)

        # Enrich with external data
        company_data = await self.enrich_from_clearbit(raw_data["email"])

        # Generate sales intelligence report
        report = {
            **insights,
            "lead_score": lead_score,
            "company_data": company_data,
            "recommended_next_action": self.determine_next_step(insights),
            "battlecard_triggers": self.identify_competitive_situations(insights),
        }

        # Push to multiple systems
        await asyncio.gather(
            self.sync_to_salesforce(report),
            self.update_amplitude(report),
            self.notify_sales_team(report) if lead_score > 80 else None
        )

        return report
```

### Sales Meeting Analytics

| Metric | Source | Collection Method | Purpose |
|--------|--------|-------------------|---------|
| **Meeting Book Rate** | `book_sales_meeting` calls | Tool tracking | Conversion funnel |
| **Qualification Accuracy** | Post-call CRM validation | Salesforce sync | Model training |
| **Time to Qualification** | Session duration until tier assigned | Timer | Efficiency |
| **Discovery Completion %** | Signals populated / total signals | State tracking | Thoroughness |
| **Objection Patterns** | Transcript analysis | NLP clustering | Sales enablement |

### Lead Scoring Inputs

```python
# Automated Lead Scoring
SCORING_WEIGHTS = {
    "team_size": {
        "1-2": 0,
        "3-4": 5,
        "5-10": 15,
        "10+": 25
    },
    "monthly_volume": {
        "<10": 0,
        "10-50": 5,
        "50-100": 10,
        "100+": 20
    },
    "integration_needs": {
        "salesforce": 20,
        "hubspot": 15,
        "api": 10,
        "none": 0
    },
    "urgency": {
        "this_week": 15,
        "this_month": 10,
        "this_quarter": 5,
        "evaluating": 0
    },
    "budget_authority": {
        "decision_maker": 15,
        "influencer": 10,
        "needs_approval": 5,
        "unknown": 0
    }
}
```

---

## 🎭 Bucket 3: User Experience & Engagement

### Conversation Quality Metrics

| Metric | Source | Collection Method | Target |
|--------|--------|-------------------|--------|
| **Call Duration** | Session end timestamp | Webhooks | 3-7 minutes optimal |
| **Turn Count** | `conversation_item_added` events | Counter | 8-15 turns |
| **Interruption Rate** | `item.interrupted` count | History analysis | <10% |
| **Dead Air Time** | Gap analysis between turns | Audio processing | <5% of call |
| **Speaking Pace** | Words per minute from TTS | Character count / duration | 140-160 WPM |
| **User Engagement Score** | Composite metric | Multiple signals | >7/10 |
| **Sentiment Progression** | Sentiment over time | NLP on transcript | Positive trend |
| **Question Resolution Rate** | Questions answered / asked | Conversation analysis | >90% |

### User Behavior Patterns

```python
class UserExperienceAnalyzer:
    def calculate_engagement_score(self, session_data):
        score_components = {
            "active_participation": self.measure_turn_balance(session_data),  # 0-10
            "question_engagement": self.count_questions_asked(session_data),   # 0-10
            "feature_exploration": self.track_topics_discussed(session_data),  # 0-10
            "positive_signals": self.count_affirmations(session_data),        # 0-10
            "completion_rate": self.check_natural_ending(session_data),       # 0-10
        }

        weights = {
            "active_participation": 0.25,
            "question_engagement": 0.20,
            "feature_exploration": 0.25,
            "positive_signals": 0.15,
            "completion_rate": 0.15
        }

        engagement_score = sum(
            score * weights[component]
            for component, score in score_components.items()
        )

        return {
            "overall_score": engagement_score,
            "components": score_components,
            "recommendations": self.generate_improvement_tips(score_components)
        }
```

### Voice Interaction Quality

| Metric | Source | Collection Method | Purpose |
|--------|--------|-------------------|---------|
| **STT Confidence** | STT provider metrics | Event data | Accuracy tracking |
| **User Speaking Rate** | Audio analysis | Duration / word count | Adaptation needs |
| **Clarification Requests** | "Could you repeat" detection | Pattern matching | Comprehension issues |
| **Natural Endings** | Proper goodbye detection | Conversation analysis | Satisfaction proxy |

---

## 📈 Bucket 4: Business Impact & ROI

### Conversion & Revenue Metrics

| Metric | Source | Calculation | Business Value |
|--------|--------|-------------|----------------|
| **Trial → Paid Conversion** | CRM + Agent logs | Engaged trials / Total trials | Primary KPI |
| **Assisted Revenue** | Salesforce opportunity | Sum of influenced deals | ROI calculation |
| **Cost per Qualified Lead** | Usage costs / SQLs | API costs / qualified count | Efficiency |
| **Agent ROI** | Revenue - Costs | Assisted revenue / Total spend | Investment validation |
| **Time to Value** | First feature adoption | Session → First document sent | Activation metric |
| **Deflection Rate** | Support ticket reduction | Tickets with agent / without | Cost savings |

### Operational Efficiency

```python
class BusinessImpactCalculator:
    def calculate_agent_roi(self, period_days=30):
        # Cost components
        costs = {
            "livekit_usage": self.get_livekit_costs(period_days),
            "llm_tokens": self.get_openai_costs(period_days),
            "stt_minutes": self.get_deepgram_costs(period_days),
            "tts_characters": self.get_elevenlabs_costs(period_days),
        }

        # Value components
        value = {
            "qualified_leads": self.count_qualified_leads(period_days) * AVG_SQL_VALUE,
            "meetings_booked": self.count_meetings_booked(period_days) * AVG_MEETING_VALUE,
            "support_deflection": self.calculate_ticket_savings(period_days),
            "sales_acceleration": self.measure_pipeline_velocity_impact(period_days),
        }

        roi = {
            "total_cost": sum(costs.values()),
            "total_value": sum(value.values()),
            "roi_percentage": ((sum(value.values()) - sum(costs.values())) / sum(costs.values())) * 100,
            "cost_breakdown": costs,
            "value_breakdown": value,
            "recommendations": self.generate_optimization_recommendations(costs, value)
        }

        return roi
```

### Trial Success Metrics

| Metric | Source | Collection | Impact |
|--------|--------|-----------|--------|
| **Trial Activation Rate** | Product usage data | API integration | Conversion predictor |
| **Feature Adoption** | Unleash search patterns | Tool call analysis | Value realization |
| **Return User Rate** | Multiple sessions | User ID tracking | Engagement |
| **Escalation to Human** | Unresolved issues | Fallback tracking | Experience gaps |

---

## 🔍 Bucket 5: Knowledge Base & Tool Effectiveness

### Unleash Knowledge Base Analytics

| Metric | Source | Collection Method | Purpose |
|--------|--------|-------------------|---------|
| **Search Success Rate** | `unleash_search_knowledge` results | Response tracking | Content gaps |
| **Top Search Queries** | Query parameters | Aggregation | Content priorities |
| **No Results Rate** | Empty results | Counter | Missing content |
| **Category Distribution** | Category parameter | Histogram | Usage patterns |
| **Result Click-through** | Follow-up questions | Conversation flow | Relevance |
| **Intercom Source Coverage** | Result source analysis | API filtering | Source effectiveness |

### Tool Usage Analytics

```python
class ToolEffectivenessTracker:
    def __init__(self):
        self.tool_metrics = {
            "unleash_search_knowledge": {
                "total_calls": 0,
                "successful_calls": 0,
                "avg_results": 0,
                "empty_results": 0,
                "categories_used": {},
                "common_queries": {},
                "error_rate": 0
            },
            "book_sales_meeting": {
                "total_attempts": 0,
                "successful_bookings": 0,
                "qualification_accuracy": 0,
                "false_positives": 0,
                "booking_errors": 0
            }
        }

    async def track_knowledge_base_effectiveness(self, query, results):
        metrics = self.tool_metrics["unleash_search_knowledge"]
        metrics["total_calls"] += 1

        if results.get("found"):
            metrics["successful_calls"] += 1
            metrics["avg_results"] = (
                (metrics["avg_results"] * (metrics["total_calls"] - 1) +
                results.get("total_results", 0)) / metrics["total_calls"]
            )
        else:
            metrics["empty_results"] += 1
            await self.log_content_gap(query)

        # Track query patterns
        query_pattern = self.extract_query_pattern(query)
        metrics["common_queries"][query_pattern] = (
            metrics["common_queries"].get(query_pattern, 0) + 1
        )
```

### Content Gap Analysis

| Metric | Source | Analysis Method | Action |
|--------|--------|-----------------|--------|
| **Unanswered Questions** | Failed searches | Query clustering | Content creation |
| **Repeat Questions** | Query frequency | Pattern detection | FAQ updates |
| **Fallback Triggers** | Error responses | Exception tracking | Training data |
| **Source Distribution** | Result metadata | Source analysis | Integration review |

---

## 🔧 Implementation Roadmap (Separated Architecture)

### Phase 1: Simplify LiveKit Agent (Week 1)
```python
# STEP 1: Strip out all analysis from agent.py
class SimplifiedPandaDocAgent(Agent):
    def __init__(self):
        super().__init__(instructions="...")
        self.session_data = {
            "discovered_signals": {},
            "tool_calls": [],
            "metrics": []
        }

    async def on_session_end(self, session):
        # Just collect and store - no analysis
        payload = {
            "session_id": ctx.room.name,
            "timestamp": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).seconds,
            "transcript": session.history.to_dict(),
            **self.session_data
        }

        # Fire and forget to queue
        await self.send_to_sqs(payload)
        logger.info(f"Session data queued: {ctx.room.name}")
```

### Phase 2: Build Analytics Pipeline (Week 2)
```python
# STEP 2: Create separate analytics service
# analytics_service.py (runs as separate Lambda/Cloud Function)
class AnalyticsProcessor:
    def __init__(self):
        self.llm = Anthropic(model="claude-3.5-sonnet")
        self.salesforce = SalesforceClient()

    async def process_session(self, raw_data):
        # All heavy processing happens here
        analysis = await asyncio.gather(
            self.extract_sales_intelligence(raw_data),
            self.calculate_performance_metrics(raw_data),
            self.analyze_conversation_quality(raw_data),
            self.generate_executive_summary(raw_data)
        )

        # Store and distribute results
        await self.store_to_warehouse(analysis)
        await self.sync_to_crm(analysis)
        await self.send_notifications(analysis)
```

### Phase 3: Set Up Infrastructure (Week 3)
- **Message Queue**: AWS SQS or Google Pub/Sub
- **Storage**: S3/GCS for raw transcripts
- **Processing**: Lambda/Cloud Functions for analytics
- **Database**: BigQuery/Snowflake for analysis results
- **Monitoring**: DataDog/CloudWatch for pipeline health

### Phase 4: Advanced Analytics (Week 4-5)
- Implement batch processing for cost optimization
- Add ML models for lead scoring
- Create feedback loops for model improvement
- Build real-time alerting for hot leads

---

## 📊 Dashboard Requirements

### Engineering Dashboard
- Real-time latency monitoring
- Error rate tracking
- Resource utilization
- Geographic performance distribution

### Revenue Operations Dashboard
- Lead qualification funnel
- Meeting booking conversion
- Sales intelligence insights
- Pipeline influence tracking

### Executive Dashboard
- ROI metrics
- Trial conversion impact
- Cost per acquisition
- Agent utilization rates

---

## 🎯 Success Metrics & Targets

### Month 1 Targets
- Average latency: <1000ms
- Qualification accuracy: >80%
- Search success rate: >85%
- User engagement score: >7/10

### Quarter 1 Goals
- Trial conversion lift: +15%
- Cost per SQL: <$50
- Agent-influenced pipeline: $500K
- Support deflection: 30%

### Year 1 Vision
- Full sales intelligence automation
- Predictive trial scoring
- Personalized trial journeys
- $5M influenced revenue

---

## 🔐 Data Governance & Privacy

### PII Handling
```python
class PIIRedactor:
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    }

    def redact_transcript(self, text):
        for pattern_name, pattern in self.PATTERNS.items():
            text = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", text)
        return text
```

### Compliance Requirements
- GDPR: User consent for recording
- CCPA: Data deletion requests
- SOC 2: Audit logging
- HIPAA: Healthcare data handling (if applicable)

---

## 🎯 Benefits of Separated Architecture

### Performance Benefits
| Aspect | Monolithic Agent | Separated Architecture | Improvement |
|--------|-----------------|----------------------|-------------|
| **Latency** | +500ms for analysis | 0ms impact | 100% faster |
| **Memory** | 2GB+ with ML models | <500MB | 75% reduction |
| **Reliability** | Analysis failures break calls | Isolated failures | 100% call uptime |
| **Scalability** | Scale everything | Independent scaling | 10x more efficient |

### Development Benefits
- **Faster iteration**: Update analytics without touching voice agent
- **Better testing**: Test collection and analysis separately
- **Team autonomy**: Voice team and analytics team work independently
- **Technology flexibility**: Use best tools for each job (Python for voice, Go for pipeline, etc.)

### Business Benefits
- **Cost optimization**: Run expensive analysis in batch during off-peak
- **Historical reprocessing**: Re-analyze old calls with improved models
- **A/B testing**: Test different analysis approaches without affecting calls
- **Compliance**: Easier to manage PII and data retention separately

---

## 📝 Appendix: Implementation Templates

### LiveKit Agent (Simplified for Collection Only)
```python
# agent.py - Focus on conversation and data collection
from livekit.agents import Agent, AgentSession, JobContext, metrics
import json
import asyncio
import boto3
from datetime import datetime

class PandaDocTrialistAgent(Agent):
    def __init__(self):
        super().__init__(instructions="[YOUR EXISTING INSTRUCTIONS]")
        self.session_start = datetime.now()
        self.discovered_signals = {}
        self.metrics_buffer = []
        self.tool_calls = []

    async def on_session_start(self, session: AgentSession):
        self.usage_collector = metrics.UsageCollector()

        # Just collect metrics, no analysis
        session.on("metrics_collected", self.buffer_metrics)
        session.on("function_tools_executed", self.track_tools)

    async def buffer_metrics(self, ev):
        # Lightweight collection only
        self.usage_collector.collect(ev.metrics)
        self.metrics_buffer.append({
            "timestamp": datetime.now().isoformat(),
            "metrics": str(ev.metrics)  # Just serialize, don't analyze
        })

    async def track_tools(self, ev):
        self.tool_calls.append({
            "timestamp": datetime.now().isoformat(),
            "tools": [call.name for call in ev.function_calls]
        })

    async def on_session_end(self, session):
        # Collect all raw data
        session_data = {
            "session_id": ctx.room.name,
            "start_time": self.session_start.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "transcript": session.history.to_dict(),
            "discovered_signals": self.discovered_signals,
            "metrics": self.metrics_buffer,
            "tool_calls": self.tool_calls,
            "usage_summary": self.usage_collector.get_summary(),
        }

        # Push to queue and forget
        try:
            await self.push_to_queue(session_data)
            logger.info(f"Session data queued: {ctx.room.name}")
        except Exception as e:
            # Don't let analytics failure affect the voice call
            logger.error(f"Failed to queue session data: {e}")

    async def push_to_queue(self, data):
        # Option 1: SQS
        sqs = boto3.client('sqs')
        sqs.send_message(
            QueueUrl=os.getenv("ANALYTICS_QUEUE_URL"),
            MessageBody=json.dumps(data)
        )

        # Option 2: Direct S3 (simpler)
        # s3 = boto3.client('s3')
        # key = f"sessions/{datetime.now().strftime('%Y/%m/%d')}/{data['session_id']}.json"
        # s3.put_object(
        #     Bucket=os.getenv("RAW_DATA_BUCKET"),
        #     Key=key,
        #     Body=json.dumps(data)
        # )

### Analytics Service (Separate Process/Lambda)
```python
# analytics_processor.py - Heavy lifting happens here
import json
from anthropic import Anthropic
import asyncio
from simple_salesforce import Salesforce

class SessionAnalyzer:
    def __init__(self):
        self.llm = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.sf = Salesforce(
            username=os.getenv("SF_USERNAME"),
            password=os.getenv("SF_PASSWORD"),
            security_token=os.getenv("SF_TOKEN")
        )

    async def process_queue_message(self, message):
        """Process a session from the queue"""
        session_data = json.loads(message['Body'])

        try:
            # Run all analysis in parallel
            analysis = await asyncio.gather(
                self.analyze_sales_intelligence(session_data),
                self.calculate_performance_metrics(session_data),
                self.score_conversation_quality(session_data),
                self.extract_action_items(session_data),
                return_exceptions=True  # Don't fail if one analysis fails
            )

            # Combine results
            report = self.generate_report(analysis)

            # Distribute results
            await asyncio.gather(
                self.store_to_warehouse(report),
                self.sync_to_salesforce(report),
                self.send_alerts(report),
                return_exceptions=True
            )

            logger.info(f"Analysis complete for session {session_data['session_id']}")

        except Exception as e:
            logger.error(f"Analysis failed for {session_data['session_id']}: {e}")
            # Could retry or send to DLQ

    async def analyze_sales_intelligence(self, data):
        """Use powerful LLM for deep analysis"""
        response = await self.llm.messages.create(
            model="claude-3.5-sonnet",
            messages=[{
                "role": "user",
                "content": f"""
                Analyze this sales call transcript and extract:
                - Team size and structure
                - Budget indicators
                - Decision timeline
                - Objections raised
                - Competitors mentioned
                - Feature requests
                - Buying signals

                Transcript: {json.dumps(data['transcript'])}

                Return as structured JSON with confidence scores.
                """
            }]
        )

        return json.loads(response.content[0].text)

# Lambda handler for AWS
def lambda_handler(event, context):
    analyzer = SessionAnalyzer()

    for record in event['Records']:
        asyncio.run(analyzer.process_queue_message(record))

    return {'statusCode': 200}
```

---

## 📊 Comprehensive Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LiveKit Agent                               │
│                      (Data Collection Only)                         │
│                                                                     │
│  Session Metadata:                                                  │
│    • session_id (room name)                                         │
│    • start_time (ISO timestamp)                                     │
│    • end_time (ISO timestamp)                                       │
│    • duration_seconds                                               │
│    • participant_id                                                 │
│    • user_email (from metadata)                                     │
│    • user_name (from metadata)                                      │
│                                                                     │
│  Raw Transcript:                                                    │
│    • Complete conversation history                                  │
│    • User utterances with timestamps                                │
│    • Agent responses with timestamps                                │
│    • Interruption markers                                           │
│    • Turn-taking data                                               │
│                                                                     │
│  Performance Metrics:                                               │
│    • eou_delay (end-of-utterance delay, ms)                         │
│    • llm_ttft (time to first token, ms)                             │
│    • tts_ttfb (time to first byte, ms)                              │
│    • stt_duration (transcription time, ms)                          │
│    • total_latency (calculated sum, ms)                             │
│    • prompt_tokens (LLM input tokens)                               │
│    • completion_tokens (LLM output tokens)                          │
│    • total_tokens (sum)                                             │
│    • stt_audio_duration (seconds)                                   │
│    • tts_characters_count                                           │
│    • tts_audio_duration (seconds)                                   │
│                                                                     │
│  Discovered Signals (from conversation):                            │
│    • team_size (integer or null)                                    │
│    • monthly_volume (integer or null)                               │
│    • integration_needs (array: salesforce, hubspot, etc.)           │
│    • industry (string: healthcare, legal, etc.)                     │
│    • location (string)                                              │
│    • use_case (string: proposals, contracts, etc.)                  │
│    • current_tool (string: manual, DocuSign, etc.)                  │
│    • pain_points (array of strings)                                 │
│    • decision_timeline (string: this_week, etc.)                    │
│    • budget_authority (string: decision_maker, etc.)                │
│    • urgency (string: high, medium, low)                            │
│    • qualification_tier (Tier 1 or Tier 2)                          │
│                                                                     │
│  Tool Usage:                                                        │
│    • unleash_search_knowledge calls:                                │
│      - query (string)                                               │
│      - category (optional)                                          │
│      - results_found (boolean)                                      │
│      - total_results (integer)                                      │
│      - timestamp                                                    │
│    • book_sales_meeting calls:                                      │
│      - customer_name                                                │
│      - customer_email                                               │
│      - preferred_date/time                                          │
│      - success (boolean)                                            │
│      - meeting_link                                                 │
│      - timestamp                                                    │
│                                                                     │
│  Connection Quality:                                                │
│    • bandwidth_in (bytes)                                           │
│    • bandwidth_out (bytes)                                          │
│    • packet_loss (percentage)                                       │
│    • jitter (ms)                                                    │
│    • device_info (browser, OS, location)                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ JSON Payload via HTTP POST
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Message Queue                               │
│                     (AWS SQS / Google Pub/Sub)                      │
│                                                                     │
│  Raw Session Data (JSON):                                           │
│    • All metadata above (no transformation)                         │
│    • Message attributes:                                            │
│      - session_id (for deduplication)                               │
│      - priority (hot_lead vs standard)                              │
│      - timestamp                                                    │
│    • Retry policy: 3 attempts with exponential backoff              │
│    • Dead letter queue for failed messages                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Lambda/Cloud Function trigger
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Analytics Agent                              │
│                     (Heavy Processing Pipeline)                     │
│                                                                     │
│  PROCESSING MODULES:                                                │
│                                                                     │
│  1. Sales Intelligence Analyzer:                                    │
│     • Team size extraction & validation                             │
│     • Document volume estimation                                    │
│     • CRM integration detection                                     │
│     • Budget authority inference                                    │
│     • Decision timeline parsing                                     │
│     • Competitor mention detection                                  │
│     • Objection classification                                      │
│     • Feature request extraction                                    │
│     • Buying signal detection                                       │
│     • Stakeholder identification                                    │
│     • Use case categorization                                       │
│     • Pain point analysis                                           │
│     • BANT qualification scoring                                    │
│     → Output: Sales Intelligence Report                             │
│                                                                     │
│  2. Lead Scoring Engine:                                            │
│     • Demographic score (company size, industry)                    │
│     • Behavioral score (engagement, questions)                      │
│     • Firmographic score (revenue, employees)                       │
│     • Intent score (urgency, timeline)                              │
│     • Fit score (ICP matching)                                      │
│     • Weighted total score (0-100)                                  │
│     • Confidence level (high/medium/low)                            │
│     → Output: Lead Score + Breakdown                                │
│                                                                     │
│  3. Conversation Quality Analyzer:                                  │
│     • Turn balance ratio                                            │
│     • Question engagement count                                     │
│     • Active listening indicators                                   │
│     • Interruption frequency                                        │
│     • Dead air percentage                                           │
│     • Natural ending detection                                      │
│     • Sentiment progression (start → end)                           │
│     • User satisfaction proxy                                       │
│     • Agent effectiveness score                                     │
│     → Output: Quality Score (0-10) + Components                     │
│                                                                     │
│  4. Sentiment Analyzer:                                             │
│     • Overall sentiment (positive/neutral/negative)                 │
│     • Sentiment by conversation segment                             │
│     • Emotional tone detection                                      │
│     • Frustration indicators                                        │
│     • Enthusiasm markers                                            │
│     • Confidence level                                              │
│     → Output: Sentiment Report                                      │
│                                                                     │
│  5. Objection & Competitor Detector:                                │
│     • Pricing objections                                            │
│     • Feature gap objections                                        │
│     • Timing objections                                             │
│     • Competitor mentions (DocuSign, Adobe, etc.)                   │
│     • Competitor comparison requests                                │
│     • Switching barriers identified                                 │
│     → Output: Objection List + Competitor Analysis                  │
│                                                                     │
│  6. Performance Metrics Calculator:                                 │
│     • Average latency                                               │
│     • p50, p95, p99 latency percentiles                             │
│     • Token usage statistics                                        │
│     • Cost calculation (per provider)                               │
│     • Performance score vs targets                                  │
│     • Anomaly detection                                             │
│     → Output: Performance Report                                    │
│                                                                     │
│  7. Content Gap Analyzer:                                           │
│     • Failed knowledge base searches                                │
│     • Unanswered questions                                          │
│     • Repeat question patterns                                      │
│     • Missing documentation areas                                   │
│     • Source effectiveness (Intercom coverage)                      │
│     → Output: Content Gap Report                                    │
│                                                                     │
│  8. Action Item Extractor:                                          │
│     • Commitments made by user                                      │
│     • Follow-up tasks for sales                                     │
│     • Feature demo requests                                         │
│     • Document sharing needs                                        │
│     • Next steps timeline                                           │
│     → Output: Action Items List                                     │
│                                                                     │
│  9. Executive Summary Generator:                                    │
│     • Call outcome (qualified/unqualified)                          │
│     • Key takeaways (3-5 bullets)                                   │
│     • Risk factors                                                  │
│     • Opportunity summary                                           │
│     • Recommended next action                                       │
│     → Output: Executive Summary                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┬─────────────┐
                    ▼             ▼             ▼             ▼
         ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐
         │  Salesforce  │ │  Amplitude   │ │Dashboard │ │  Alerts  │
         └──────────────┘ └──────────────┘ └──────────┘ └──────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          Salesforce CRM                             │
│                   (Sales Intelligence Destination)                  │
│                                                                     │
│  Lead/Contact Record Updates:                                       │
│    • Lead Score (custom field, 0-100)                               │
│    • Lead Score Breakdown (JSON field)                              │
│    • Qualification Tier (Tier 1 / Tier 2)                           │
│    • Last Call Date (timestamp)                                     │
│    • Call Duration (minutes)                                        │
│    • Engagement Score (0-10)                                        │
│                                                                     │
│  Discovered Signals (custom fields):                                │
│    • Team_Size__c (number)                                          │
│    • Monthly_Document_Volume__c (number)                            │
│    • Integration_Needs__c (multi-select: SF, HubSpot, etc.)        │
│    • Industry_Vertical__c (picklist)                                │
│    • Decision_Timeline__c (picklist: this week, month, etc.)        │
│    • Budget_Authority__c (picklist)                                 │
│    • Current_Tool__c (text)                                         │
│    • Urgency_Level__c (picklist: high/medium/low)                   │
│                                                                     │
│  Pain Points & Needs:                                               │
│    • Pain_Points__c (long text area, comma-separated)               │
│    • Use_Cases__c (multi-select picklist)                           │
│    • Feature_Requests__c (long text area)                           │
│                                                                     │
│  Competitive Intelligence:                                          │
│    • Competitor_Mentioned__c (picklist: DocuSign, Adobe, etc.)      │
│    • Current_Solution__c (text)                                     │
│    • Switching_Barriers__c (long text)                              │
│                                                                     │
│  Call Intelligence:                                                 │
│    • Objections_Raised__c (long text area)                          │
│    • Buying_Signals__c (long text area)                             │
│    • Stakeholders_Mentioned__c (text)                               │
│    • Key_Quotes__c (long text area)                                 │
│    • Call_Sentiment__c (positive/neutral/negative)                  │
│                                                                     │
│  Action Items:                                                      │
│    • Next_Best_Action__c (text)                                     │
│    • Follow_Up_Priority__c (high/medium/low)                        │
│    • Recommended_Owner__c (lookup to User)                          │
│                                                                     │
│  Task Creation (if qualified):                                      │
│    • Subject: "Follow up on voice trial call"                       │
│    • Description: Executive summary + action items                  │
│    • Due Date: Based on urgency                                     │
│    • Assigned To: Account Executive (based on territory)            │
│                                                                     │
│  Call Record Object (custom):                                       │
│    • Voice_Call__c:                                                 │
│      - Session_Id__c (text, external ID)                            │
│      - Transcript__c (long text area, rich text)                    │
│      - Call_Summary__c (long text)                                  │
│      - Transcript_URL__c (URL to S3/GCS)                            │
│      - Quality_Score__c (number)                                    │
│      - Related_To__c (lookup to Lead/Contact)                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          Amplitude Analytics                        │
│                    (Product Analytics Destination)                  │
│                                                                     │
│  Session Event:                                                     │
│    • Event: "voice_trial_session_completed"                         │
│    • Properties:                                                    │
│      - session_id                                                   │
│      - duration_seconds                                             │
│      - turn_count                                                   │
│      - qualification_tier                                           │
│      - engagement_score (0-10)                                      │
│      - sentiment (positive/neutral/negative)                        │
│      - meeting_booked (boolean)                                     │
│      - tool_calls_count                                             │
│                                                                     │
│  User Identification:                                               │
│    • User ID: email or participant_id                               │
│    • User Properties:                                               │
│      - team_size                                                    │
│      - monthly_volume                                               │
│      - industry                                                     │
│      - location                                                     │
│      - qualification_tier                                           │
│      - lead_score                                                   │
│                                                                     │
│  Engagement Events:                                                 │
│    • "knowledge_base_searched"                                      │
│      - query                                                        │
│      - results_found (boolean)                                      │
│      - category                                                     │
│    • "sales_meeting_booked"                                         │
│      - meeting_time                                                 │
│      - preferred_date                                               │
│    • "feature_discussed"                                            │
│      - feature_name                                                 │
│      - interest_level                                               │
│                                                                     │
│  Quality Metrics:                                                   │
│    • "conversation_quality_measured"                                │
│      - quality_score                                                │
│      - interruption_count                                           │
│      - natural_ending (boolean)                                     │
│                                                                     │
│  Performance Events:                                                │
│    • "latency_measured"                                             │
│      - avg_latency_ms                                               │
│      - p95_latency_ms                                               │
│      - total_tokens                                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      Real-Time Dashboard                            │
│                   (Looker / Tableau / Metabase)                     │
│                                                                     │
│  PERFORMANCE MONITORING:                                            │
│    • Current calls active (count)                                   │
│    • Average latency (last hour, real-time)                         │
│    • P95 latency trend (line chart)                                 │
│    • Error rate (percentage)                                        │
│    • Token usage rate (tokens/minute)                               │
│    • Cost burn rate ($/hour)                                        │
│    • Connection quality distribution                                │
│                                                                     │
│  BUSINESS METRICS:                                                  │
│    • Today's calls (count)                                          │
│    • Qualified leads (Tier 1 count)                                 │
│    • Meetings booked (count)                                        │
│    • Average engagement score (0-10)                                │
│    • Conversion rate (qualified / total)                            │
│    • Revenue pipeline influenced ($)                                │
│                                                                     │
│  CALL QUALITY:                                                      │
│    • Average call duration (minutes)                                │
│    • Average turn count                                             │
│    • Interruption rate (percentage)                                 │
│    • Sentiment distribution (pie chart)                             │
│    • Natural ending rate (percentage)                               │
│    • User satisfaction proxy                                        │
│                                                                     │
│  KNOWLEDGE BASE EFFECTIVENESS:                                      │
│    • Search success rate (percentage)                               │
│    • Top searched queries (table)                                   │
│    • Content gaps identified (count)                                │
│    • Average results per query                                      │
│    • Tool usage breakdown (pie chart)                               │
│                                                                     │
│  SALES INTELLIGENCE:                                                │
│    • Lead score distribution (histogram)                            │
│    • Top industries (bar chart)                                     │
│    • Team size distribution                                         │
│    • Integration needs breakdown                                    │
│    • Competitor mentions (word cloud)                               │
│    • Common objections (table)                                      │
│                                                                     │
│  TRENDING INSIGHTS:                                                 │
│    • Calls trend (last 7/30 days)                                   │
│    • Qualification rate trend                                       │
│    • Meeting booking trend                                          │
│    • Performance degradation alerts                                 │
│    • Hot leads today (top 10 list)                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      Alert & Notification System                    │
│                  (PagerDuty / Slack / Email / SMS)                  │
│                                                                     │
│  CRITICAL ALERTS (Immediate - PagerDuty):                           │
│    • Agent down (no sessions in 10 minutes)                         │
│    • Error rate >10% (5 minute window)                              │
│    • Average latency >2000ms (5 minute window)                      │
│    • Queue backlog >100 messages                                    │
│    • API failures (Unleash, Salesforce, etc.)                       │
│                                                                     │
│  HIGH PRIORITY ALERTS (5 min - Slack #ops):                         │
│    • Latency >1500ms sustained                                      │
│    • Error rate >5%                                                 │
│    • Token usage spike (>2x normal)                                 │
│    • Cost burn rate exceeds budget                                  │
│    • Connection quality degraded                                    │
│                                                                     │
│  BUSINESS ALERTS (Real-time - Slack #sales):                        │
│    • Hot lead detected (score >80):                                 │
│      - Lead name, company, score                                    │
│      - Key signals (team size, urgency, etc.)                       │
│      - Salesforce link                                              │
│      - Recommended action                                           │
│    • Meeting booked:                                                │
│      - Customer name, email                                         │
│      - Meeting time                                                 │
│      - Calendar link                                                │
│      - Qualification summary                                        │
│    • Competitor mentioned:                                          │
│      - Competitor name                                              │
│      - Context from conversation                                    │
│      - Battlecard recommendation                                    │
│                                                                     │
│  QUALITY ALERTS (Hourly digest - Slack #product):                   │
│    • Content gaps identified:                                       │
│      - Failed search queries                                        │
│      - Missing documentation areas                                  │
│      - User confusion points                                        │
│    • Low engagement sessions:                                       │
│      - Session IDs with score <5                                    │
│      - Patterns in poor calls                                       │
│    • Feature requests:                                              │
│      - New feature mentions                                         │
│      - Frequency and urgency                                        │
│                                                                     │
│  EXECUTIVE ALERTS (Daily digest - Email):                           │
│    • Daily summary:                                                 │
│      - Total calls, qualified leads, meetings                       │
│      - Performance averages                                         │
│      - Top opportunities                                            │
│      - Key insights                                                 │
│    • Weekly rollup:                                                 │
│      - Week-over-week trends                                        │
│      - Pipeline impact                                              │
│      - ROI metrics                                                  │
│      - Recommendations                                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    Data Warehouse (Historical)                      │
│                  (Snowflake / BigQuery / Redshift)                  │
│                                                                     │
│  Tables:                                                            │
│    • sessions (fact table)                                          │
│    • transcripts (text data)                                        │
│    • metrics (time-series)                                          │
│    • leads (dimension table)                                        │
│    • analysis_results (processed intelligence)                      │
│    • alerts_history (audit log)                                     │
│                                                                     │
│  Retention:                                                         │
│    • Raw transcripts: 90 days (then archive to cold storage)        │
│    • Metrics: 1 year (then aggregate)                               │
│    • Analysis results: Indefinite                                   │
│    • PII: Redacted after 30 days (GDPR/CCPA)                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Document Version: 2.0 - Separated Architecture*
*Last Updated: 2025-01-28*
*Major Change: Shifted from monolithic to separated collection/analysis architecture*
*Next Review: Q2 2025*