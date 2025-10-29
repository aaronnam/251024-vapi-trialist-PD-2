# PandaDoc Trial Success Voice Agent Specification
*Version 1.0 - Production Specification*

---

## Executive Summary

PandaDoc will deploy two AI voice agents designed to maximize trial-to-paid conversion by delivering proactive success enablement. These agents will proactively guide trialists to value, accelerating their path to paid adoption, while seamlessly routing larger opportunities to sales. The ultimate goal is to materially impact Q4 2025 revenue by increasing conversion rates and uncovering high-value prospects that would otherwise be missed.

**Why Now:** With Q4 2025 revenue tracking 20% below target, traditional approaches won't close the gap in time. Voice agents can deploy within days and immediately impact November/December trial cohorts.

**Expected Impact:** Meaningful improvement in trial-to-paid conversion, better qualification of enterprise opportunities, and scalable trial success that wasn't previously possible.
- Material Q4 2025 revenue contribution through:
  - Lift in trial-to-paid conversion
  - Uncovering hidden enterprise opportunities
  - Converting at-risk trials that would otherwise abandon  
- With a 2-month runway to year-end, voice agents can immediately impact November and December cohorts.

**Hypothesis:**
Trials can fail not only because of product inadequacy, but due to discovery friction—users often don't know what they need or how to achieve it.
- Voice conversations remove this friction by providing instant, personalized guidance exactly when needed.
- Helping trialists achieve their first success (e.g., sending a document that gets signed) creates momentum that naturally drives conversion.
- The 10+ seat outbound agent amplifies this effect by proactively rescuing high-value trials before they abandon.
- **Q4 2025 Revenue Path:** With ~1,000 trials per month and 20% current conversion, lifting to 30% captures 100 additional customers monthly. At $500 MRR average, that's $50K MRR or $100K in Q4 revenue recognition. Combined with 50 enterprise opportunities at $5K MRR, we can contribute $400K+ toward closing the 20% revenue gap.

---

## 1. Business Context & Problem Statement

### The Core Problem

**The Trial Experience Paradox**
B2B SaaS trials exist in a fundamental contradiction: they need to be self-serve to scale, yet complex enough products require guidance to realize value. PandaDoc, like most document automation platforms, has sophisticated capabilities that solve real business problems - but only if users discover and implement them correctly within their trial window.

**The Hidden Trial Journey**
Most trialists are not professional software evaluators. They're sales reps, operations managers, or business owners who squeezed "evaluate PandaDoc" between meetings. They arrive with a vague pain point ("our proposals take too long") but lack the mental model to translate PandaDoc's features into their specific solution. They don't know what they don't know.

**The Scaling Challenge**
Human touch dramatically improves trial outcomes, but economics make it impossible to provide human guidance to every trial. Sales teams focus on high-value prospects, leaving the majority to navigate alone. Support is reactive - users must recognize they need help and take initiative to seek it. By then, many have already formed their conclusion.

**The Qualification Blindness**
Without interaction, we can't distinguish a solo freelancer exploring options from a department head evaluating for their 50-person team. High-value trials fail silently while low-value trials consume support resources. We learn about enterprise needs only after they've chosen a competitor.

**The Revenue Gap Reality**
PandaDoc is tracking 20% below Q4 2025 revenue targets with only 2 months remaining. Traditional sales motions won't scale fast enough to close this gap. We need a force multiplier that can impact hundreds of trials simultaneously. Voice agents represent our fastest path to incremental revenue - they can be deployed within days, not quarters, and immediately begin converting trials that would otherwise abandon.

### The Opportunity

**Voice AI as Scalable Empathy**
Voice agents provide something previously impossible: authentic, helpful conversations at infinite scale. Unlike chatbots that feel like navigating a phone tree, voice creates genuine connection. Users can express confusion, ask "dumb questions," and think out loud - natural behaviors that accelerate learning.

**Success-First Revenue Generation**
When users succeed with the product, revenue follows naturally. By focusing agents on enablement rather than sales, we create positive brand experiences that drive both immediate conversion and long-term advocacy. Qualification happens organically through helpful discovery.

**Intelligence Through Interaction**
Every conversation generates insights about user needs, friction points, and decision criteria. This creates a compounding advantage - the system continuously improves its ability to guide users to success.

### Strategic Business Goals

Rather than specific metrics, success means:
- **Activation:** More trials experience meaningful value quickly
- **Conversion:** Higher percentage move from trial to paid
- **Expansion:** Better identification and nurturing of high-value accounts
- **Efficiency:** Lower cost per quality customer acquisition
- **Intelligence:** Deeper understanding of trial behavior and needs

---

## 2. Agent Definitions

### Agent 1: Inbound Trial Success Agent
**Purpose:** Reactive support that transforms friction into momentum

**Trigger:** Trialist clicks call button within product interface

**Primary Job:** Resolve immediate blockers and guide to value realization

**Unique Characteristics:**
- High intent users (they initiated contact)
- Specific problem context
- Immediate value delivery expected
- Trust already partially established

### Agent 2: Outbound Trial Success Agent
**Purpose:** Proactive enablement for high-potential trials

**Trigger:** System identifies trial with 10+ seat potential

**Primary Job:** Ensure trial success and natural path to conversion

**Unique Characteristics:**
- Pre-qualified audience (10+ seat potential known)
- Proactive value creation required
- Must earn attention quickly
- Qualification refinement needed

---

## 3. Core Design Principles

### 3.1 Success Over Sales
Every interaction prioritizes user success. Sales opportunities emerge naturally from successful users, never from pressure tactics.

### 3.2 Value in Every Interaction
Users should accomplish something tangible during each conversation - send a document, create a template, invite a teammate.

### 3.3 Natural Qualification
Discovery questions that help users also reveal qualification criteria. We never interrogate.

### 3.4 Contextual Intelligence
Agents understand where users are in their journey and adapt accordingly. Day 1 needs differ from Day 13 needs.

### 3.5 Graceful Escalation
Seamless handoff to humans when appropriate, with full context transfer.

---

## 4. User Personas & Journey Mapping

### Primary Personas

**The Explorer (Day 1-3)**
- Testing multiple solutions
- Needs quick wins to stay engaged
- Questions: "Can it do X?" "How does this work?"

**The Builder (Day 4-10)**
- Committed to testing
- Setting up for their use case
- Questions: "How do I..." "What's the best way to..."

**The Evaluator (Day 11-14)**
- Deciding whether to buy
- Comparing to alternatives
- Questions: "What plan do I need?" "How much for my team?"

### Critical Journey Moments

1. **First Document Send** - Must happen by Day 2
2. **Template Creation** - Indicates long-term thinking
3. **Team Invitation** - Shows organizational commitment
4. **Integration Attempt** - Reveals workflow integration intent
5. **Pricing Page Visit** - Buying consideration signal

---

## 5. Conversation Architecture

### 5.1 Conversation Layers

**Layer 1: Rapport (0-30 seconds)**
- Warm, human greeting
- Acknowledge their context
- Set helpful tone

**Layer 2: Discovery (30s-2min)**
- Understand their use case
- Identify immediate needs
- Surface qualification signals

**Layer 3: Value Delivery (2-5min)**
- Guide through specific actions
- Demonstrate ROI
- Create "aha moments"

**Layer 4: Next Steps (5-7min)**
- Ensure momentum continues
- Book sales meeting if qualified
- Schedule follow-up if needed

### 5.2 Conversation Intelligence

The agent maintains three parallel tracks:

1. **Support Track:** Solving immediate problems
2. **Success Track:** Driving valuable behaviors
3. **Qualification Track:** Identifying sales opportunities

### 5.3 Dynamic Scripting

Rather than rigid scripts, agents use contextual frameworks:

```
IF user_stuck_on_templates:
  ACKNOWLEDGE frustration
  GUIDE through creation
  DEMONSTRATE time savings
  CELEBRATE completion
  EXPLORE team needs

IF user_comparing_competitors:
  DISCOVER specific needs
  DEMONSTRATE differentiators
  GUIDE to experience difference
  CALCULATE specific ROI
  OFFER specialist consultation
```

---

## 6. User Experience & Product Integration

### 6.1 Entry Points & Discovery

**Target Segmentation:**
- **Voice Agent Path (1-10 CS):** Trialists with 1-10 seats 
- **Sales Demo Path (11+ CS):** Trialists with 11+ potential seats  

**In-Product Entry Points:**
1. **Discovery Page Card** - "Get instant help" CTA integrated with trial checklist
2. **Help Menu Option** - "Talk to our AI Assistant" for qualified segments
3. **Sticky Banner** - Contextual trigger after 5+ minutes on complex features

**Messaging & Positioning:**
- **1-10 Seats:** "Get instant help - no scheduling required"
- **11+ Seats:** "Book a personalized demo with our experts"

### 6.2 Conversation Initiation

**Web-Based Launch Flow:**
1. User clicks CTA → Opens new tab with voice agent interface
2. Simple consent screen: "I'll help you get the most from PandaDoc"
3. One-click to start conversation
4. Visual indicator shows when agent is listening/speaking

**Setting Expectations:**
- "Hi! I'm Sarah from PandaDoc. I can help you set up templates, send documents, or answer any questions. This 5-minute conversation is recorded for quality. How can I help you succeed today?"

### 6.3 During Conversation Experience

**User Controls:**
- Mute/unmute button prominently displayed
- End call button always accessible
- "Connect me to a human" option visible
- Visual transcript updating in real-time (optional toggle)

**Real-Time Indicators:**
- Speaking/listening status
- "Sarah is typing..." when agent processes
- Progress indicators for multi-step guidance

### 6.4 Post-Call Experience

**Email Follow-up (Within 5 minutes):**
- Personalized email with call summary
- Links to features discussed
- Step-by-step guides for tasks mentioned
- Calendar invite if meeting was booked

**Nurture Sequence (Based on outcome):**

*If Qualified (10+ seats):*
- Day 1: Meeting confirmation + prep materials
- Day 2: Sales rep intro email
- Day 7: Check-in if meeting was missed

*If Not Qualified (<10 seats):*
- Day 3: "How's your progress?" email with tips
- Day 7: Feature spotlight based on conversation
- Day 12: Conversion offer aligned to trial end

*If Unresolved Issues:*
- Immediate: Support ticket creation
- Day 1: Human support follow-up
- Resolution tracking and confirmation

### 6.5 Segment-Specific Experiences

**1-10 Seats (Self-Serve Focus):**
- Emphasis on immediate value creation
- Self-service resources prioritized
- Community and help center links
- Simplified pricing calculator
- Direct-to-purchase CTAs

**11+ Seats (Sales-Assisted Path):**
- Immediate sales qualification
- Calendar booking within conversation
- ROI calculation and business case
- Enterprise feature discussion
- Custom demo scheduling

**Dynamic Elevation:**
If a 1-10 seat trial reveals enterprise needs during conversation:
- Seamless transition to enterprise talking points
- Offer to connect with specialist
- Capture qualification signals
- Route to appropriate sales team

---

## 7. Capability Matrix

### Can Do (Autonomously)
- Answer product questions
- Guide through features
- Calculate ROI
- Share best practices
- Book sales meetings
- Send resources
- Schedule follow-ups
- Handle basic objections

### Cannot Do (Requires Human)
- Access account data
- Modify subscriptions
- Apply discounts
- Provide legal advice
- Handle technical bugs
- Process payments
- Make product commitments
- Handle angry escalations

### Smart Handoffs
- Enterprise pricing discussions → Sales
- Technical integration issues → Support
- Contract negotiations → Sales
- Bug reports → Support
- Feature requests → Product feedback loop

---

## 8. Qualification Framework

### Qualification Criteria (ALL agents discover)

**Tier 1: Sales-Ready (Book immediately)**
- 10+ seats AND any of:
  - 100+ documents/month
  - Salesforce/HubSpot integration need
  - API/embedded requirements
  - Whitelabeling needs
  - Enterprise security requirements

**Tier 2: Nurture (Agent continues support)**
- 10+ seats potential but no enterprise needs yet
- 5-9 seats with growth trajectory
- High engagement but small team

**Tier 3: Self-Serve (Pure enablement)**
- <10 seats
- Individual users
- Simple use cases

### Natural Discovery Questions

Instead of "How many users?" ask:
> "Walk me through your document workflow - who creates proposals, who needs to review them, and who sends them out?"

Instead of "What's your budget?" ask:
> "What are you using today and what made you look for something better?"

Instead of "Do you need integrations?" ask:
> "Once a document is signed, where does that information need to go?"

---

## 9. Agent Tools Architecture & External Integrations

### 9.1 Tool Design Philosophy

Each tool represents a specific external integration or API call. Tools are named clearly to indicate their service, consolidate related operations, and return only high-signal information the agent needs for conversation.

### 9.2 Knowledge Base Integration

**`unleash_search_knowledge`**
- **External Service:** Unleash API (Knowledge Base)
- **Endpoint:** `GET /api/v1/knowledge/search`
- **Purpose:** Search PandaDoc knowledge base for answers
- **Parameters:**
  ```json
  {
    "query": "string",  // Natural language question
    "category": "string",  // Optional: "features", "pricing", "integrations", "troubleshooting"
    "max_results": 3
  }
  ```
- **Returns:**
  ```json
  {
    "results": [
      {
        "title": "Creating Templates",
        "content": "Step-by-step guide...",
        "relevance_score": 0.95,
        "category": "features"
      }
    ],
    "suggested_followup": "Would you like me to walk you through this?"
  }
  ```
- **Error Handling:** Falls back to general guidance if API unavailable

**`unleash_get_competitor_comparison`**
- **External Service:** Unleash API (Competitive Intelligence)
- **Endpoint:** `GET /api/v1/knowledge/competitors/{competitor_name}`
- **Purpose:** Get specific competitive differentiation
- **Parameters:**
  ```json
  {
    "competitor": "docusign|hellosign|proposify|adobe_sign",
    "feature_focus": "string"  // Optional specific feature to compare
  }
  ```
- **Returns:** Structured comparison with PandaDoc advantages

### 9.3 Meeting Booking Integration

**`chilipiper_book_meeting`**
- **External Service:** Chili Piper API
- **Endpoint:** `POST /api/v1/meetings/book`
- **Purpose:** Schedule qualified meetings with sales team
- **MVP Behavior:** Books on single calendar (implementing user's) with email notification
- **V2 Behavior:** Intelligent routing to account owner or round-robin assignment
- **Parameters:**
  ```json
  {
    "lead": {
      "email": "string",
      "first_name": "string",
      "last_name": "string",
      "company": "string",
      "phone": "string"  // Optional
    },
    "meeting_type": "pandadoc_enterprise_demo",
    "qualification": {
      "team_size": "10+",
      "monthly_volume": "number",
      "integration_needs": ["salesforce", "hubspot"],
      "urgency": "high|medium|low"
    },
    "preferred_times": ["2024-01-15T10:00:00Z"],
    "notes": "string"  // Context for sales rep
  }
  ```
- **MVP Returns:**
  ```json
  {
    "success": true,
    "meeting": {
      "time": "2024-01-15T10:00:00Z",
      "calendar_event_id": "string",
      "meeting_link": "https://meet.pandadoc.com/...",
      "notification_sent": true
    }
  }
  ```
- **V2 Returns:**
  ```json
  {
    "success": true,
    "meeting": {
      "time": "2024-01-15T10:00:00Z",
      "rep_name": "John Smith",
      "rep_title": "Enterprise Account Executive",
      "meeting_link": "https://meet.pandadoc.com/...",
      "calendar_event_id": "string",
      "routing_method": "account_owner|round_robin"
    }
  }
  ```
- **Fallback:** Returns booking link if API fails

**`chilipiper_check_availability`**
- **External Service:** Chili Piper API
- **Endpoint:** `GET /api/v1/availability`
- **Purpose:** Check rep availability before offering times
- **Parameters:**
  ```json
  {
    "meeting_type": "pandadoc_enterprise_demo",
    "date_range": {
      "start": "2024-01-15",
      "end": "2024-01-22"
    }
  }
  ```
- **Returns:** Available time slots

### 9.4 Analytics & Tracking

**`webhook_send_conversation_event`**
- **External Service:** Internal Webhook (→ Snowflake/HubSpot)
- **Endpoint:** `POST /webhooks/voice-agent/event`
- **Purpose:** Track conversation events and qualification signals
- **Parameters:**
  ```json
  {
    "event_type": "qualification|objection|booking|support",
    "call_id": "uuid",
    "timestamp": "ISO-8601",
    "trialist": {
      "email": "string",
      "company": "string"
    },
    "data": {
      "qualification_score": 85,
      "intent_signals": ["pricing_inquiry", "demo_request"],
      "objections": ["too_expensive"],
      "topics_discussed": ["templates", "integrations"]
    }
  }
  ```
- **Async:** Fire-and-forget, doesn't block conversation
- **Used For:** MQL scoring, conversation analytics, sales alerts

### 9.5 ROI Calculation Service

**`calculate_pandadoc_roi`**
- **External Service:** Internal ROI Calculator API
- **Endpoint:** `POST /api/v1/roi/calculate`
- **Purpose:** Generate personalized ROI calculations
- **Parameters:**
  ```json
  {
    "team_size": 12,
    "documents_per_month": 200,
    "average_doc_value": 5000,
    "current_process": {
      "hours_per_doc": 2,
      "approval_days": 3,
      "error_rate": 0.05
    },
    "use_case": "sales|hr|legal|procurement"
  }
  ```
- **Returns:**
  ```json
  {
    "annual_savings": 47000,
    "hours_saved_weekly": 18,
    "roi_percentage": 340,
    "payback_months": 2.5,
    "key_benefits": [
      "Reduce proposal creation from 2 hours to 20 minutes",
      "Decrease approval time by 70%",
      "Eliminate 95% of manual errors"
    ]
  }
  ```

### 9.6 Resource Delivery

**`hubspot_send_resource`**
- **External Service:** hubspot API
- **Endpoint:** `POST /v3/mail/send`
- **Purpose:** Email relevant resources to trialist
- **Parameters:**
  ```json
  {
    "to": "trialist@company.com",
    "template_id": "case_study_template",
    "dynamic_data": {
      "first_name": "string",
      "resource_type": "case_study",
      "industry": "saas",
      "resource_url": "https://pandadoc.com/resources/..."
    }
  }
  ```
- **Templates Available:**
  - `case_study_template`
  - `integration_guide_template`
  - `pricing_overview_template`
  - more TBD

### 9.7 Trial Status Check (V2)

**`pandadoc_api_get_trial_status`**
- **External Service:** PandaDoc Internal API (V2 only)
- **Endpoint:** `GET /api/v1/trials/{email}`
- **Purpose:** Get actual trial usage data
- **Note:** Not available in MVP - agent asks user instead
- **Parameters:**
  ```json
  {
    "email": "trialist@company.com",
    "include_activity": true
  }
  ```
- **Returns:**
  ```json
  {
    "trial_day": 5,
    "documents_created": 3,
    "documents_sent": 2,
    "templates_created": 1,
    "team_members_invited": 0,
    "integrations_connected": [],
    "last_login": "2024-01-14T15:30:00Z"
  }
  ```

### 9.8 Tool Orchestration Patterns

**Qualification Flow:**
```
unleash_search_knowledge → webhook_send_conversation_event
                        ↘ chilipiper_check_availability → chilipiper_book_meeting
```

**Value Discovery Flow:**
```
unleash_search_knowledge → calculate_pandadoc_roi → sendgrid_send_resource
                        ↘ webhook_send_conversation_event
```

**Competitive Handling:**
```
unleash_get_competitor_comparison → calculate_pandadoc_roi
                                 ↘ chilipiper_book_meeting (if qualified)
```

### 9.9 Data Sources & Knowledge Context

#### Primary Knowledge Sources (Available at Launch)

**1. Unleash Knowledge Base**
- **Content:** 500+ articles covering features, pricing, troubleshooting
- **Structure:** Categorized by user journey stage
- **Access Method:** `unleash_search_knowledge` tool
- **Coverage:**
  - Feature documentation
  - Setup guides and tutorials
  - Pricing and plan comparisons
  - Common troubleshooting solutions
  - Integration guides

**2. Competitive Intelligence Database**
- **Content:** Detailed comparisons vs DocuSign, HelloSign, Adobe Sign, Proposify
- **Structure:** Feature-by-feature comparisons with talk tracks
- **Update Frequency:** Monthly
- **Access Method:** `unleash_get_competitor_comparison` tool

**3. ROI & Value Data**
- **Content:** Industry benchmarks, time savings data, cost calculations
- **Structure:** Parameterized by industry, company size, use case
- **Update Frequency:** Quarterly
- **Access Method:** `calculate_pandadoc_roi` tool

#### Conversation Context (Real-time)

**4. In-Call Discovery**
- **What:** Information gathered during current conversation
- **Includes:** Stated needs, team size, pain points, objectives
- **Storage:** In-memory during call, webhook to Snowflake after
- **Usage:** Informs qualification and next-best-action

**5. Trial Timing Context**
- **What:** Where trialist is in their journey (derived from conversation)
- **Day 1-3:** Focus on quick wins and setup
- **Day 4-10:** Focus on advanced features and team adoption
- **Day 11-14:** Focus on pricing and conversion

#### Future Data Sources (V2)

**6. Trial Behavior Data** (Not available in MVP)
- **Source:** PandaDoc internal API
- **Content:** Documents created/sent, features used, team activity
- **Access Method:** `pandadoc_api_get_trial_status` tool

**7. CRM Enrichment** (V2)
- **Source:** Salesforce API
- **Content:** Company info, previous interactions, industry data
- **Usage:** Pre-call context for outbound agent

**8. Historical Conversation Data** (V2)
- **Source:** Gong aggregated transcripts that are kept in Snowflake
- **Content:** Common questions, successful talk tracks, objection patterns
- **Usage:** Continuous improvement of responses

### 9.10 Knowledge Management Philosophy

**What the Agent Knows:**
- Product capabilities and limitations
- Pricing structure and value propositions
- Competitive advantages
- Common use cases and best practices
- Troubleshooting steps

**What the Agent Discovers:**
- User's specific needs and pain points
- Team structure and document workflow
- Current tools and processes
- Budget and timeline constraints
- Decision criteria

**What the Agent Doesn't Know (MVP):**
- User's actual trial activity
- Account configuration details
- Payment or billing information
- Internal company data
- Previous support ticket history

### 9.11 Lead Routing & Assignment Flow

#### MVP Approach (Simple Manual Process)

**Philosophy:** Prove value fast by avoiding complex routing logic. Manual assignment validates lead quality before automation investment.

**Flow:**
1. Agent qualifies lead during conversation
2. `chilipiper_book_meeting` books on single calendar (implementing user's)
3. Email notification sent with qualification details
4. User manually reviews lead context
5. User assigns to appropriate Salesforce owner
6. User moves meeting to assigned seller's calendar
7. User updates Salesforce opportunity owner

**Advantages:**
- Fast to implement and launch
- Human validation of lead quality
- Flexibility during learning phase
- No dependency on Salesforce API integration

**Notification Email Includes:**
- Lead contact information
- Qualification summary (team size, needs, urgency)
- Call transcript and key insights
- Meeting time and calendar link
- Suggested account owner (if known)

#### V2 Approach (Automated Intelligent Routing)

**Philosophy:** Eliminate manual work once routing rules are validated and proven effective.

**Flow:**
1. Agent qualifies lead during conversation
2. System queries Salesforce for existing account owner
3. If owner exists:
   - Check owner's calendar availability via Chili Piper
   - Book directly on owner's calendar
   - Notify owner with qualification brief
4. If no owner exists:
   - Use Chili Piper round-robin from defined pod/pool
   - Assign based on territory, segment, or availability
   - Create Salesforce opportunity with proper attribution
5. Fully automated with no manual intervention

**Routing Logic Priority:**
1. Existing Salesforce account owner
2. Territory-based assignment (if configured)
3. Segment-based routing (Enterprise vs SMB pod)
4. Round-robin within appropriate pod
5. Fallback to default calendar

**V2 Enhancements:**
- Automatic Salesforce opportunity creation
- Pre-meeting intelligence brief for assigned rep
- Calendar synchronization across systems
- Lead scoring and prioritization
- Routing analytics and optimization

### 9.12 Sales Team Enablement

#### Minimal Enablement Plan

**Slack Announcement (Week of Launch):**
```
🤖 New: AI Voice Agents Qualifying Trials Starting [Date]

What's happening:
- AI voice agents will start having conversations with trialists
- Qualified leads will book on account owners' calendars initially or go into a round robin 
- You'll receive email notifications with full context

What you need to know:
- These are PRE-QUALIFIED leads (10+ seats, enterprise needs)
- They've already had a 5-7 min discovery conversation
- Full transcript and qualification notes provided
- Treat like inbound demo requests - they're expecting your call

What's different:
- Higher intent - they've already discussed needs with "Sarah"
- Better context - you'll know their pain points before the call
- Reference the AI conversation: "Sarah mentioned you need X..."

Questions? Contact @aaronnam
```

**Enablement Materials (Delivered by Aaron):**
- Loom video showing sample conversation
- One-pager: "Handling Voice-Agent Qualified Leads"
- Voice Agent Spec 

**Success Handoff Protocol:**
Each qualified lead notification includes:
1. Conversation summary (3-5 bullets)
2. Qualification criteria met
3. Suggested talking points
4. Link to full transcript

---

## 10. Technical Architecture - Leveraging VAPI Platform

### 10.1 Architecture Philosophy

**Build on VAPI, Don't Rebuild VAPI**

VAPI provides enterprise-grade voice AI infrastructure out of the box. Our implementation focuses on three simple layers:
1. **Function definitions** (what the agent can do)
2. **Webhook handlers** (how actions execute)
3. **Data pipeline** (how we learn from conversations)

Everything else—voice quality, multi-agent orchestration, context preservation, conversation management—is handled by VAPI's platform.

### 10.2 VAPI Squads Architecture

**Single Agent (MVP) → VAPI Squads (V2)**

```
MVP (Single Agent):
┌─────────────────────────────────────┐
│     Trialist SDR Agent              │
│  • Handles all conversations        │
│  • All functions in one assistant   │
│  • Direct webhook calls             │
└─────────────────────────────────────┘
                 ↓
        8-10 Webhook Functions


V2 (VAPI Squads - Native Multi-Agent):
┌─────────────────────────────────────┐
│         Primary SDR Agent           │
│  "Hi, I'm Sarah from PandaDoc..."   │
└──────────────┬──────────────────────┘
               │
               ↓ (VAPI handles routing)
    ┌──────────┴──────────┐
    ↓                     ↓
┌─────────────┐    ┌──────────────┐
│ Technical   │    │ Enterprise   │
│ Specialist  │    │ Specialist   │
│ Agent       │    │ Agent        │
└─────────────┘    └──────────────┘
```

**What VAPI Squads Provides (No Code Needed):**
- Automatic agent handoffs with full context
- Preserved conversation history across transfers
- Natural "Let me connect you with..." transitions
- Return to primary agent after specialist consultation
- Unified call recording and transcript

**What We Build:**
- Agent personas and system prompts
- Function definitions for each specialist
- Transfer decision logic

### 10.3 Function Definitions (What the Agent Can Do)

**Design Philosophy: Elegant Operational Categories**

Rather than a flat list, functions are organized by operational purpose. MVP focuses on the essential 16 functions that VAPI can leverage effectively, with clear V2 expansion paths.

---

#### Category 1: Context & Intelligence (6 functions)

**Understanding who we're talking to and their journey**

```javascript
// 1. User Trial Context
{
  name: "get_user_trial_context",
  description: "Get trialist's current status and usage patterns",
  service: "Internal API → Amplitude aggregation",
  parameters: {
    email: "string",
    pandadoc_user_id: "string"
  },
  returns: {
    trial_day: "number",
    documents_created: "number",
    last_login: "timestamp",
    engagement_score: "number"
  },
  vapi_native: false,
  implementation: "Custom webhook → Amplitude MCP query → cached response"
}

// 2. Product Usage Intelligence
{
  name: "amplitude_get_feature_adoption",
  description: "Identify which features used/not used for tailored guidance",
  service: "Amplitude API (via MCP)",
  parameters: {
    user_id: "string",
    feature_list: ["templates", "integrations", "e-signature", "workflows"]
  },
  returns: {
    adoption_rates: "object",
    last_used_dates: "object",
    engagement_percentile: "number"
  },
  vapi_native: false,
  implementation: "Amplitude MCP tool - query behavioral data",
  use_case: "Agent: 'I see you haven't tried our template library yet - that's our #1 time-saver'"
}

// 3. Conversation History
{
  name: "hubspot_get_contact_history",
  description: "Retrieve past interactions to personalize conversation",
  service: "HubSpot API",
  parameters: {
    email: "string"
  },
  returns: {
    lifecycle_stage: "string",
    last_interaction_date: "timestamp",
    interaction_summary: "array",
    deal_stage: "string"
  },
  vapi_native: false,
  implementation: "HubSpot REST API via webhook",
  use_case: "Avoid re-asking questions; reference past pain points"
}

// 4. Account Ownership Check
{
  name: "salesforce_check_account_ownership",
  description: "Determine if company has assigned sales rep",
  service: "Salesforce API",
  parameters: {
    company_domain: "string"
  },
  returns: {
    account_id: "string",
    owner_name: "string",
    owner_email: "string",
    account_tier: "enterprise|smb|unassigned"
  },
  vapi_native: false,
  implementation: "SFDC API lookup via webhook",
  routing_logic: "If owned → route to owner; else → round robin"
}

// 5. ROI Calculator
{
  name: "calculate_roi",
  description: "Generate personalized ROI based on conversation data",
  service: "Internal ROI Service",
  parameters: {
    team_size: "number",
    monthly_doc_volume: "number",
    current_tool: "string",
    use_case: "sales|hr|legal|procurement"
  },
  returns: {
    annual_savings: "number",
    hours_saved_weekly: "number",
    payback_months: "number",
    key_benefits: "array"
  },
  vapi_native: false,
  implementation: "Custom calculation service with industry benchmarks"
}

// 6. Knowledge Base Search
{
  name: "search_knowledge_base",
  description: "Search Unleash KB for product answers",
  service: "Unleash API",
  parameters: {
    query: "string",
    category: "enum[product|pricing|integrations|troubleshooting]"
  },
  returns: {
    results: "array",
    relevance_scores: "array",
    suggested_followup: "string"
  },
  vapi_native: false,
  implementation: "Unleash search API via webhook"
}
```

---

#### Category 2: Lead Routing & Booking (4 functions)

**Getting qualified leads to the right rep at the right time**

```javascript
// 7. Check Rep Availability
{
  name: "chilipiper_check_availability",
  description: "Get available time slots before offering specific times",
  service: "ChiliPiper API",
  parameters: {
    routing_pool: "enterprise|smb",
    date_range: {start: "date", end: "date"},
    timezone: "string"
  },
  returns: {
    available_slots: "array",
    next_available: "timestamp"
  },
  vapi_native: true,  // ChiliPiper is VAPI-supported natively
  implementation: "VAPI native calendar integration",
  mvp_note: "Use VAPI's built-in calendar features - no custom code"
}

// 8. Round Robin Assignment
{
  name: "chilipiper_round_robin_assignment",
  description: "Assign lead to appropriate rep when no owner exists",
  service: "ChiliPiper Routing Logic",
  parameters: {
    company_size: "number",
    qualification_signals: "object",
    priority_level: "high|medium|low"
  },
  returns: {
    assigned_rep_email: "string",
    rep_name: "string",
    routing_reason: "string"
  },
  vapi_native: true,
  implementation: "ChiliPiper native routing rules (configured in CP dashboard)",
  mvp_approach: "Simple: Route 10+ seats to enterprise pool; <10 to SMB pool"
}

// 9. Book Meeting
{
  name: "chilipiper_book_meeting",
  description: "Schedule qualified meeting with assigned rep",
  service: "ChiliPiper Booking API",
  parameters: {
    lead_data: "object",
    rep_email: "string",
    preferred_times: "array",
    meeting_type: "demo|consultation|technical",
    qualification_context: "object"
  },
  returns: {
    booking_id: "string",
    meeting_time: "timestamp",
    calendar_link: "string",
    confirmation_sent: "boolean"
  },
  vapi_native: true,
  implementation: "VAPI native calendar booking",
  conversation_flow: "Agent: 'Perfect! I've scheduled you with John on Tuesday at 2pm ET. You'll get a calendar invite right away.'"
}

// 10. Enterprise Eligibility Check
{
  name: "check_enterprise_eligibility",
  description: "Determine if lead qualifies for enterprise sales track",
  service: "Internal Rules Engine",
  parameters: {
    team_size: "number",
    conversation_signals: ["integration_needs", "api_requirements", "security_questions"],
    monthly_volume: "number"
  },
  returns: {
    is_enterprise: "boolean",
    qualification_score: "number",
    routing_recommendation: "string"
  },
  vapi_native: false,
  implementation: "Webhook with business logic",
  criteria: "10+ seats + (integrations OR API needs OR enterprise security)"
}
```

---

#### Category 3: Communication & Follow-Up (3 functions)

**Keeping the conversation going after the call**

```javascript
// 11. Send Resource Email
{
  name: "hubspot_send_email",
  description: "Email relevant resources/guides post-call",
  service: "HubSpot Email API",
  parameters: {
    to_email: "string",
    template_type: "case_study|integration_guide|pricing|setup_guide",
    personalization_data: "object",
    conversation_context: "string"
  },
  returns: {
    email_id: "string",
    send_status: "sent|queued|failed"
  },
  vapi_native: false,
  implementation: "HubSpot transactional email via webhook",
  timing: "Sent within 5 minutes post-call"
}

// 12. Log Call Activity
{
  name: "hubspot_log_call_activity",
  description: "Record call in HubSpot timeline for rep visibility",
  service: "HubSpot Engagements API",
  parameters: {
    contact_id: "string",
    call_duration: "number",
    outcome: "qualified|nurtured|support|no_action",
    transcript_summary: "string",
    next_steps: "array"
  },
  returns: {
    activity_id: "string"
  },
  vapi_native: false,
  implementation: "Async webhook post-call",
  use_case: "Sales rep sees full context before their meeting"
}

// 13. Create Sales Task
{
  name: "hubspot_schedule_follow_up_task",
  description: "Create task for human follow-up when needed",
  service: "HubSpot Tasks API",
  parameters: {
    assignee_email: "string",
    task_type: "send_pricing|custom_demo|security_review",
    due_date: "date",
    description: "string",
    priority: "high|medium|low"
  },
  returns: {
    task_id: "string"
  },
  vapi_native: false,
  implementation: "Webhook creates task in CRM",
  use_case: "Agent promises custom pricing → creates task for rep"
}
```

---

#### Category 4: Analytics & Tracking (3 functions)

**Learning from every conversation**

```javascript
// 14. Log Qualified Lead
{
  name: "salesforce_create_lead",
  description: "Create lead record in Salesforce with conversation context",
  service: "Salesforce API",
  parameters: {
    company_info: "object",
    qualification_signals: "object",
    conversation_summary: "string",
    lead_source: "voice_agent_inbound|voice_agent_outbound"
  },
  returns: {
    lead_id: "string",
    success: "boolean"
  },
  vapi_native: false,
  implementation: "Async webhook → SFDC API",
  timing: "Created post-call if qualified"
}

// 15. Store Call Summary
{
  name: "log_call_summary",
  description: "Store call record in Snowflake for analytics",
  service: "Snowflake via S3 + Snowpipe",
  parameters: {
    call_metadata: "object",
    outcome: "enum",
    structured_outputs: "object",  // From VAPI's native extraction
    cost_breakdown: "object"
  },
  returns: {
    record_id: "string"
  },
  vapi_native: "partial",  // VAPI provides data, we store it
  implementation: "VAPI end-of-call webhook → S3 → Snowpipe auto-ingest",
  data: "See section 10.6 for schema"
}

// 16. Receive Call Analytics
{
  name: "log_call_analytics",
  description: "Receive VAPI's native call analysis",
  service: "VAPI End-of-Call Report",
  webhook: "end-of-call-report",
  parameters: {
    call_analysis: "object",  // AI-generated summary
    structured_outputs: "object",  // JSON matching our schema (section 10.5)
    cost_breakdown: "object",
    success_evaluation: "boolean"
  },
  vapi_native: true,  // 100% VAPI-generated
  implementation: "Configure JSON schema in VAPI dashboard → automatic extraction",
  note: "NO custom extraction code needed - VAPI's LLM does this automatically"
}
```

---

#### V2 Functions (Not MVP - Add After Validation)

```javascript
// Sentiment Analysis (Real-time)
{
  name: "sentiment_analysis_live",
  description: "Mid-call sentiment detection for strategy adjustment",
  timing: "V2 - requires real-time streaming integration",
  use_case: "Detect frustration → escalate to human"
}

// Advanced Amplitude Queries
{
  name: "amplitude_query_behavioral_cohort",
  description: "Compare user to similar cohorts for risk scoring",
  timing: "V2 - after basic usage data proves valuable"
}

// VAPI Squads Functions (Multi-Agent)
{
  name: "transfer_to_technical_specialist",
  description: "Hand off to technical specialist agent",
  timing: "V2 - requires VAPI Squads setup (section 10.2)"
}
```

---

**Function Count Summary:**
- **MVP Core: 16 functions** (5 VAPI-native, 11 custom webhooks)
- **V2 Expansion: 5+ functions** (specialists, advanced analytics)
- **Implementation Time: 2 weeks** (MVP webhooks + VAPI configuration)

### 10.4 Analytics & Observability - Native VAPI Features

**Philosophy: Configure, Don't Build**

VAPI provides enterprise-grade analytics out of the box. We define what to track, VAPI extracts and analyzes it automatically.

**What VAPI Provides Automatically:**
- AI-generated call summaries
- Success/failure evaluation per call
- Structured data extraction (via JSON schema)
- Granular cost breakdowns
- Full transcripts and recordings

**What We Configure:**

**1. Structured Outputs (Automatic KPI Extraction)**

Define JSON schema in assistant configuration → VAPI extracts data automatically:

```javascript
// In VAPI Assistant Definition
{
  "structuredDataSchema": {
    "type": "object",
    "properties": {
      "qualification_score": {
        "type": "integer",
        "description": "Lead qualification score 0-100",
        "minimum": 0,
        "maximum": 100
      },
      "team_size": {
        "type": "integer",
        "description": "Number of seats mentioned"
      },
      "monthly_doc_volume": {
        "type": "integer",
        "description": "Estimated monthly document volume"
      },
      "intent_signals": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["pricing_inquiry", "demo_request", "integration_need", "competitor_comparison"]
        }
      },
      "objections_raised": {
        "type": "array",
        "items": {"type": "string"}
      },
      "next_action": {
        "type": "string",
        "enum": ["meeting_booked", "nurture", "support_escalation", "no_action"]
      }
    },
    "required": ["qualification_score", "next_action"]
  }
}
```

**Result:** Every call automatically returns structured JSON with extracted KPIs. No custom extraction code needed.

**2. Call Analysis Configuration**

Enable in assistant settings:

```javascript
{
  "analysisPlan": {
    "summaryPrompt": "Summarize the trialist's main pain points, what was resolved, and recommended next steps in 3-4 bullets.",
    "successEvaluationPrompt": "Evaluate if the call successfully: 1) Resolved the trialist's issue, 2) Advanced them toward conversion, 3) Qualified them for sales. Return true only if at least 2 of 3 criteria met.",
    "successEvaluationRubric": "NumericScale"
  }
}
```

**Result:** VAPI's LLM analyzes every call and returns:
- `summary`: Concise call summary
- `successEvaluation`: true/false success determination
- `structuredData`: Extracted JSON matching schema

**What We Get vs What We Build:**

| Capability | VAPI Provides | We Build |
|------------|---------------|----------|
| Call summaries | ✅ AI-generated | - |
| Success evaluation | ✅ LLM-judged | - |
| KPI extraction | ✅ Structured outputs | Schema definition only |
| Cost tracking | ✅ Per-call breakdown | - |
| Transcripts | ✅ Full text | - |
| Analytics aggregation | ❌ | Snowflake queries |
| Custom dashboards | ❌ | Tableau/Looker |

**Total Implementation: 1-2 hours to define schemas and configure analysis**

### 10.5 Webhook Implementation (How Actions Execute)

**Simple HTTP POST Pattern:**

All VAPI functions call a single API Gateway endpoint that routes to appropriate handlers:

```
VAPI Function Call
    ↓
POST https://api.pandadoc.com/voice-agent/webhook
    ↓
AWS API Gateway
    ↓
Lambda Function Router
    ↓
┌────────────────┬─────────────────┬──────────────────┐
↓                ↓                 ↓                  ↓
User Context   ROI Calculator   Meeting Booking   Analytics
Handler        Handler          Handler           Handler
```

**No Complex Orchestration Needed:**
- VAPI manages conversation state automatically
- Functions execute independently via webhooks
- Results return to VAPI to continue conversation
- Context preservation is automatic in VAPI

**Example Webhook Handler (Python):**

```python
@app.post("/voice-agent/webhook")
async def handle_function_call(request: FunctionCallRequest):
    """Single endpoint, routes to appropriate handler"""

    function_name = request.function_name
    parameters = request.parameters

    if function_name == "get_user_trial_context":
        return await get_trial_context(parameters["email"])

    elif function_name == "calculate_roi":
        return await calculate_roi(
            team_size=parameters["team_size"],
            doc_volume=parameters["monthly_doc_volume"]
        )

    elif function_name == "schedule_meeting":
        return await book_meeting_chilipiper(parameters["lead_data"])

    # ... other handlers

    return {"error": "Unknown function"}
```

### 10.6 Data Pipeline - VAPI to Snowflake

**Philosophy: Simple, Linear, Fast**

VAPI sends rich analytics data → We batch it to Snowflake → Query for insights. Implementation: < 1 day.

**Architecture:**

```
┌──────────────────────────────────────┐
│    VAPI End-of-Call Report           │
│  (sent via webhook after each call)  │
├──────────────────────────────────────┤
│ • Call metadata (duration, cost)     │
│ • AI-generated summary               │
│ • Success evaluation                 │
│ • Structured outputs (our schema)    │
│ • Full transcript                    │
│ • Cost breakdown                     │
└───────────────┬──────────────────────┘
                │ POST webhook
                ↓
┌──────────────────────────────────────┐
│     Webhook Receiver (Lambda)        │
│  • Validate payload                  │
│  • Quick transform                   │
│  • Batch to S3 (every 5 min)        │
└───────────────┬──────────────────────┘
                │ S3 trigger
                ↓
┌──────────────────────────────────────┐
│     Snowflake Auto-Ingest            │
│  (Snowpipe loads within 1 minute)    │
└───────────────┬──────────────────────┘
                │
                ↓
        ┌───────┴─────────┐
        ↓                 ↓
┌─────────────┐   ┌──────────────────┐
│  calls_fact │   │ call_analysis_dim│
│  (core data)│   │ (VAPI analysis)  │
└─────────────┘   └──────────────────┘
        ↓                 ↓
┌──────────────────────────────────────┐
│  structured_outputs_fact             │
│  (extracted KPIs from our schema)    │
└──────────────────────────────────────┘
```

**Core Tables (3 only):**

```sql
-- 1. Call facts (one row per call)
calls_fact (
    call_id UUID PRIMARY KEY,
    vapi_call_id VARCHAR,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INT,

    -- Trialist
    email VARCHAR,
    company VARCHAR,
    trial_day INT,

    -- Costs (from VAPI)
    total_cost DECIMAL(10,4),
    llm_cost DECIMAL(10,4),
    tts_cost DECIMAL(10,4),
    stt_cost DECIMAL(10,4),

    -- Outcomes
    success_evaluation BOOLEAN,  -- from VAPI
    meeting_booked BOOLEAN,

    -- Reference
    transcript_url VARCHAR,
    recording_url VARCHAR
)

-- 2. Call analysis (VAPI's AI analysis)
call_analysis_dim (
    analysis_id UUID PRIMARY KEY,
    call_id UUID REFERENCES calls_fact,

    -- VAPI-generated
    summary TEXT,  -- 3-4 bullet summary
    success_reason TEXT,  -- why success/failure

    created_at TIMESTAMP
)

-- 3. Structured outputs (our defined schema)
structured_outputs_fact (
    output_id UUID PRIMARY KEY,
    call_id UUID REFERENCES calls_fact,

    -- From our JSON schema (see 10.4)
    qualification_score INT,
    team_size INT,
    monthly_doc_volume INT,
    intent_signals ARRAY,
    objections_raised ARRAY,
    next_action VARCHAR,

    -- Any additional fields from schema
    raw_json VARIANT  -- full structured output
)
```

**What We Track vs What We Ignore:**

✅ **Track:**
- Call outcomes (booked, qualified, resolved)
- Qualification signals (team size, needs)
- Success rate per agent/persona
- Common objections and questions
- Cost per successful call
- Conversion funnel metrics

❌ **Ignore (for MVP):**
- Sentiment analysis (VAPI provides, we don't use yet)
- Detailed turn-by-turn analysis
- Voice characteristics
- Real-time alerts during calls
- Predictive models (V2)

**Implementation: < 1 Day**

Day 1 (6 hours):
- Set up webhook endpoint (1 hour)
- Configure S3 bucket + Snowpipe (2 hours)
- Create 3 Snowflake tables (1 hour)
- Test end-to-end flow (2 hours)

That's it. VAPI handles the hard parts (analysis, extraction, cost tracking).

**Key Insight:** We spend 1 day on data pipeline, not 1 week, because VAPI's structured outputs eliminate custom extraction logic.

### 10.7 Cost Per Call

- VAPI platform: $0.30/min (includes STT, TTS, LLM, analysis)
- Webhooks: ~$0.01/call (Lambda)
- Data storage: ~$0.001/call
- **Total: ~$2.40 per 7-minute call**

VAPI's structured outputs and built-in analysis mean no additional cost for KPI extraction or call summarization.

### 10.8 Implementation Phases

**Phase 1: MVP (Single Agent) - 2 Weeks**
- Deploy one SDR agent with 9 core functions
- Basic webhook handlers for essential actions
- Configure VAPI structured outputs (1-2 hours)
- Set up data pipeline to Snowflake (< 1 day)
- Manual escalation to sales team

**Success Criteria:**
- Agent can handle 80% of common questions
- Successfully books meetings for qualified leads
- Logs all conversations to Snowflake with structured outputs
- <500ms function execution time
- VAPI analytics capturing 100% of KPIs automatically

**Phase 2: VAPI Squads (Multi-Agent) - 2 Weeks**
- Add Technical Specialist agent (deep product questions)
- Add Enterprise Specialist agent (complex deals)
- Implement transfer functions
- Enhanced analytics

**Success Criteria:**
- Seamless handoffs with preserved context
- Technical questions resolved without escalation
- Enterprise deals properly qualified
- No degradation in conversation quality

**Phase 3: Optimization - Ongoing**
- Refine prompts based on conversation data
- Add new functions as patterns emerge
- A/B test conversation approaches
- Continuous prompt engineering

### 10.9 Why This is Simple

**We DON'T build:**
- ❌ Multi-agent orchestration (VAPI Squads does this)
- ❌ Context management (VAPI handles state)
- ❌ Complex tool coordination (functions are independent)
- ❌ Agent-to-agent communication (automatic in VAPI)
- ❌ Conversation history tracking (built into VAPI)
- ❌ Call analysis/summarization (VAPI's LLM does this)
- ❌ KPI extraction logic (structured outputs handle this)
- ❌ Cost tracking system (VAPI provides granular breakdowns)

**We DO build:**
- ✅ 9-12 webhook functions
- ✅ Agent system prompts (1-2 pages each)
- ✅ JSON schemas for structured outputs (define KPIs)
- ✅ Simple data pipeline (VAPI → Snowflake, < 1 day)
- ✅ Basic analytics dashboards (query Snowflake)

**Total Implementation:**
- ~500 lines of webhook code
- ~3-4 page system prompts
- ~50 lines JSON schema definitions
- ~100 lines of data pipeline code
- ~1 week for MVP, 2 weeks for V2

**Key Simplification:** VAPI's structured outputs eliminate weeks of custom extraction logic. We define what to track (JSON schema), VAPI extracts it automatically.

This is elegant, maintainable, and focuses our engineering effort where it actually matters: crafting great conversations and learning from data.

---

## 10.10 Technical Stack (Actual Tools Used)

**Voice Infrastructure:**
- **Platform:** VAPI.ai
- **STT:** Deepgram Nova-2
- **LLM:** OpenAI GPT-4o
- **TTS:** ElevenLabs Turbo v2.5
- **Cost:** $0.30/min all-in

**Backend:**
- **Webhooks:** AWS Lambda (Python)
- **API Gateway:** AWS API Gateway
- **Queue:** AWS SQS (for async processing)

**Data:**
- **Analytics:** Snowflake
- **Knowledge Base:** Unleash API
- **CRM:** Salesforce API (V2)

**Integrations:**
- **Calendar:** ChiliPiper API (only native integration besides Google Calendar)
- **Notifications:** Slack webhooks
- **Email:** SendGrid/Postmark

**Monitoring:**
- **Logging:** CloudWatch
- **Errors:** Sentry
- **Analytics:** Amplitude (for product usage data)

**Total Engineering Footprint:**
- Backend: 1 engineer, 2 weeks
- Prompts: 1 AI/ML engineer, 1 week
- Data pipeline: 1 data engineer, 1 week
- **Total: 4 engineer-weeks for full V2 implementation**

This is the power of building on VAPI's platform instead of reinventing voice AI infrastructure.

### 10.11 Amplitude Integration - Product Intelligence Layer

**Purpose: Give agents real-time understanding of how trialists actually use PandaDoc**

#### Why Amplitude Matters

Unlike CRM data (what we *know* about them) or conversation data (what they *tell us*), Amplitude reveals what they *actually do*. This prevents the agent from suggesting features they've already mastered or missing critical adoption gaps.

**Key Insight:** A trialist saying "I'm all set" while having only sent 1 document in 10 days is a churn risk signal. Amplitude catches this.

---

#### 10.11.1 Amplitude MCP Integration Pattern

```
Voice Agent Call Initiated
        ↓
┌────────────────────────────────────┐
│  get_user_trial_context called     │
└───────────────┬────────────────────┘
                │ Triggers webhook
                ↓
┌────────────────────────────────────┐
│   Lambda Handler Routes to         │
│   Amplitude MCP Query              │
└───────────────┬────────────────────┘
                │ Calls MCP tool
                ↓
┌────────────────────────────────────┐
│  mcp__amplitude__get_user_events   │
│  • Queries user's event stream     │
│  • Aggregates key metrics          │
│  • Returns structured JSON         │
└───────────────┬────────────────────┘
                │ Returns to webhook
                ↓
┌────────────────────────────────────┐
│   Webhook Transforms Data          │
│   • Calculates engagement score    │
│   • Identifies adoption gaps       │
│   • Flags risk signals             │
└───────────────┬────────────────────┘
                │ Returns to VAPI
                ↓
        Agent uses context in conversation
```

---

#### 10.11.2 Core Amplitude Queries for Agent Context

**Query 1: Trial Activity Summary**

```javascript
{
  tool: "mcp__amplitude__get_user_events",
  parameters: {
    user_id: "trialist_email",
    event_types: [
      "document_created",
      "document_sent",
      "template_created",
      "team_member_invited",
      "integration_connected",
      "pricing_page_viewed"
    ],
    date_range: {
      start: "trial_start_date",
      end: "now"
    }
  },
  returns: {
    event_counts: {
      document_created: 3,
      document_sent: 1,
      template_created: 0,
      team_member_invited: 0
    },
    last_active: "2024-01-20T14:30:00Z",
    trial_day: 7
  }
}
```

**Agent Interpretation:**
- 3 documents created but only 1 sent = stuck on sending workflow
- No templates = hasn't discovered time-saving features
- No team invites = solo usage (potential SMB self-serve)
- Day 7 with low activity = intervention needed

---

**Query 2: Feature Adoption Gaps**

```javascript
{
  tool: "mcp__amplitude__get_feature_adoption",
  parameters: {
    user_id: "trialist_email",
    feature_list: [
      "templates",
      "e_signature",
      "integrations_salesforce",
      "integrations_hubspot",
      "content_library",
      "approval_workflows"
    ]
  },
  returns: {
    adoption_status: {
      templates: {used: false, value_score: 95},
      e_signature: {used: true, frequency: "daily"},
      integrations_salesforce: {used: false, value_score: 85},
      content_library: {used: false, value_score: 70},
      approval_workflows: {used: false, value_score: 60}
    }
  }
}
```

**Agent Conversation Leverage:**

```
Agent: "I noticed you're using e-signature which is great!
Have you discovered our template library yet? It could
cut your document creation time from 20 minutes to 3 minutes.
Want me to show you how to set up your first template?"
```

---

**Query 3: Engagement Cohort Comparison**

```javascript
{
  tool: "mcp__amplitude__query_behavioral_cohort",
  parameters: {
    user_id: "trialist_email",
    cohort_definition: {
      trial_day_range: [5, 9],
      company_size: "1-10",
      industry: "saas"
    }
  },
  returns: {
    percentile_ranking: 25,  // Bottom quartile of engagement
    cohort_avg_metrics: {
      documents_sent: 5,  // They sent 1, avg is 5
      logins: 8,          // They had 3, avg is 8
      features_tried: 4   // They tried 2, avg is 4
    },
    churn_risk_score: 72  // High risk
  }
}
```

**Agent Action:**
- Percentile 25 = at-risk trialist
- Proactive intervention: "I noticed you might be stuck. Let me help you get more value..."
- Qualification signal: Low engagement = not sales-ready, needs enablement

---

#### 10.11.3 Implementation: Amplitude MCP via Lambda

**Lambda Handler Pattern:**

```python
# voice_agent/webhooks/amplitude_context.py

from amplitude_mcp_client import AmplitudeMCP

async def get_user_trial_context(email: str, pandadoc_user_id: str):
    """
    Aggregates Amplitude data into conversation-ready context
    """

    # Query Amplitude via MCP
    mcp = AmplitudeMCP()

    # Get event counts
    events = await mcp.get_user_events(
        user_id=email,
        event_types=[
            "document_created",
            "document_sent",
            "template_created",
            "pricing_page_viewed"
        ],
        date_range={"days_ago": 14}
    )

    # Get feature adoption
    features = await mcp.get_feature_adoption(
        user_id=email,
        feature_list=["templates", "integrations", "e_signature"]
    )

    # Calculate engagement score (0-100)
    engagement_score = calculate_engagement(events, features)

    # Identify adoption gaps (features not tried yet)
    gaps = identify_gaps(features)

    # Package for agent
    return {
        "trial_day": calculate_trial_day(events["first_event"]),
        "documents_created": events["counts"]["document_created"],
        "documents_sent": events["counts"]["document_sent"],
        "engagement_score": engagement_score,
        "engagement_level": "high" if engagement_score > 70 else "at_risk",
        "adoption_gaps": gaps,
        "last_login": events["last_event_time"],
        "conversion_signals": {
            "viewed_pricing": events["counts"]["pricing_page_viewed"] > 0,
            "created_template": events["counts"]["template_created"] > 0,
            "sent_multiple_docs": events["counts"]["document_sent"] > 3
        }
    }
```

---

#### 10.11.4 Agent Conversation Patterns Using Amplitude Data

**Pattern 1: Low Engagement Rescue**

```
[Amplitude shows: 2 logins, 1 document, trial_day: 9]

Agent: "Hi Sarah! I'm calling because I noticed you started
your trial 9 days ago but haven't had a chance to explore much
yet. Trials move fast, so I wanted to make sure you get the
most value before it ends. What's been preventing you from
diving in deeper?"
```

**Pattern 2: Power User Upsell**

```
[Amplitude shows: 15 documents sent, 5 templates, daily logins]

Agent: "Wow, I can see you're really getting value from
PandaDoc - 15 documents sent in just 8 days! That tells me
you have a real workflow going. Quick question: are others
on your team involved in this process? I ask because our team
plans include features like approval workflows that could save
you even more time..."
```

**Pattern 3: Feature Discovery**

```
[Amplitude shows: No template usage despite 10 documents created]

Agent: "I noticed you've created 10 documents from scratch
- that's impressive! But here's a time-saver most people miss:
our template library. It would cut your creation time by about
75%. Want me to walk you through setting up your first template?"
```

---

#### 10.11.5 Amplitude Data → Qualification Signals

**Translation Table:**

| Amplitude Signal | Qualification Meaning | Agent Action |
|-----------------|----------------------|--------------|
| 10+ documents sent | High engagement | Qualify for sales |
| Pricing page viewed 2+ times | Buying intent | Accelerate to booking |
| 0 templates despite 5+ docs | Adoption gap | Enablement call |
| Last login >5 days ago | Churn risk | Proactive outreach |
| Team invites sent | Organizational adoption | Enterprise signal |
| Integration attempted | Technical sophistication | Route to solutions engineer |

---

#### 10.11.6 MVP vs V2 Amplitude Integration

**MVP (Launch Week 1):**
- Basic event counts (documents, logins, templates)
- Simple engagement score (0-100)
- Last activity timestamp
- Implementation: 1 day, single webhook + MCP query

**V2 (Month 2):**
- Cohort comparison and percentile ranking
- Churn risk prediction model
- Feature-specific adoption scoring
- Real-time behavioral triggers (e.g., detect stuck patterns)
- Implementation: 1 week, ML model integration

---

#### 10.11.7 Key Implementation Notes

**Why Amplitude MCP:**
- Pre-built Anthropic MCP tool for Amplitude exists
- Eliminates custom API integration work
- Provides structured, conversation-ready data
- Handles authentication and rate limiting

**Data Freshness:**
- Amplitude updates: 5-10 minute delay typical
- Acceptable for voice agent (users won't notice)
- Critical signals (last login) are fresh enough

**Caching Strategy:**
- Cache Amplitude responses for 5 minutes
- Reduces API costs and latency
- Refresh on subsequent calls if >5 min elapsed

**Cost:**
- Amplitude API calls: $0.001/query
- Typical call uses 2-3 queries: ~$0.003
- Negligible compared to $2.40 VAPI call cost

---

#### 10.11.8 RevOps Configuration Requirements

**What RevOps/Growth Team Must Do:**

1. **Define Key Events in Amplitude:**
   - Ensure these events are tracked:
     - `document_created`
     - `document_sent`
     - `template_created`
     - `team_member_invited`
     - `pricing_page_viewed`
     - `integration_connected`

2. **Set Up MCP Access:**
   - Grant API credentials for Amplitude MCP
   - Define rate limits and query quotas
   - Configure user ID mapping (email vs internal ID)

3. **Define Engagement Thresholds:**
   - What score = "high engagement"? (e.g., 70+)
   - What score = "at risk"? (e.g., <30)
   - What behavior = "qualified"? (e.g., 10+ docs + pricing view)

4. **Create Adoption Gap Definitions:**
   - Which features are "must discover" in trial?
   - Which gaps justify proactive outreach?

---

**This completes the elegant, production-ready function architecture. MVP launches with 16 focused functions, grows strategically to V2 with specialized capabilities, and leverages VAPI's native features wherever possible. Amplitude integration provides the critical "what they actually do" intelligence layer that transforms generic support into personalized enablement.**

---

## 11. Data Flow Architecture

### 11.1 Architecture Philosophy
**Principle: Simple, Linear, Reliable**
- Snowflake as single source of truth
- No complex orchestration - VAPI handles state
- Webhook-first integration pattern
- Async downstream sync for resilience

### 11.2 Three-Layer Data Flow

```
Layer 1: Real-Time (During Call)
┌─────────────────────────────────────┐
│          VAPI Voice Call            │
│   • Trialist speaks with agent      │
│   • Functions called as needed      │
└──────────────┬──────────────────────┘
               │ Function Calls
               ↓
┌──────────────────────────────────────┐
│        Webhook Functions (8)         │
├──────────────────────────────────────┤
│ • get_user_trial_context             │
│ • calculate_roi                      │
│ • schedule_meeting (ChiliPiper)      │
│ • send_resource                      │
│ • log_qualified_lead                 │
│ • search_knowledge_base              │
│ • check_enterprise_eligibility       │
│ • log_call_summary                   │
└──────────────────────────────────────┘
               ↓ Results
        Return to VAPI

Layer 2: Post-Call (< 30 seconds)
┌──────────────────────────────────────┐
│     VAPI end-of-call-report          │
│   • Complete transcript              │
│   • Cost breakdown                   │
│   • Call metadata                    │
│   • Analysis results                 │
└──────────────┬──────────────────────┘
               │ Webhook
               ↓
┌──────────────────────────────────────┐
│         Snowflake Ingestion          │
│   • voice_calls table                │
│   • call_events table                │
│   • qualification_signals table      │
└──────────────────────────────────────┘

Layer 3: Downstream Sync (< 5 minutes)
┌──────────────────────────────────────┐
│      Snowflake Triggers/Tasks        │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    ↓          ↓          ↓          ↓
Salesforce  HubSpot    Slack    Analytics
(Leads)    (Activity)  (Alerts)  (Dashboards)
```

### 11.3 Critical Path Functions

**During Call (Synchronous - Must Complete)**
1. **schedule_meeting** → ChiliPiper API
   - Input: Lead data, qualification signals
   - Process: Check ownership → Route to rep → Book time
   - Output: Meeting confirmation to continue conversation

2. **get_user_trial_context** → Quick lookup
   - Cached data from previous syncs
   - Falls back gracefully if unavailable

**Post Call (Asynchronous - Can Retry)**
- All data logging to Snowflake
- CRM updates
- Email sends
- Alert notifications

### 11.4 ChiliPiper Meeting Booking Flow

```
Voice Agent Qualifies Lead (10+ seats)
            ↓
┌──────────────────────────────────────┐
│   schedule_meeting Function Call     │
└──────────────┬──────────────────────┘
               ↓
┌──────────────────────────────────────┐
│      ChiliPiper Routing Logic        │
├──────────────────────────────────────┤
│ 1. Check Salesforce ownership        │
│    → If owned: Route to owner        │
│                                      │
│ 2. Check territory assignment        │
│    → If territory: Route to rep      │
│                                      │
│ 3. Check company size                │
│    → Enterprise: Enterprise pod      │
│    → SMB: SMB pod                    │
│                                      │
│ 4. Round-robin within pod            │
│    → Skip OOO reps                   │
│    → Balance distribution            │
└──────────────┬──────────────────────┘
               ↓
┌──────────────────────────────────────┐
│     Return Booking to Voice Agent    │
│   "I've scheduled you with John      │
│    on Tuesday at 2pm ET"             │
└──────────────────────────────────────┘
```

### 11.5 Snowflake Central Schema

```sql
-- Primary call record (one per call)
voice_calls (
    call_id UUID PRIMARY KEY,
    vapi_call_id VARCHAR,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INT,

    -- Trialist info
    email VARCHAR,
    company VARCHAR,
    phone VARCHAR,

    -- Call details
    transcript TEXT,
    recording_url VARCHAR,

    -- Costs
    total_cost DECIMAL(10,4),
    cost_breakdown VARIANT,

    -- Outcomes
    qualified BOOLEAN,
    meeting_booked BOOLEAN,
    lead_score INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Function calls during conversation
call_functions (
    function_id UUID PRIMARY KEY,
    call_id UUID REFERENCES voice_calls,
    function_name VARCHAR,
    parameters VARIANT,
    result VARIANT,
    executed_at TIMESTAMP
)

-- Downstream sync status
sync_status (
    sync_id UUID PRIMARY KEY,
    call_id UUID REFERENCES voice_calls,
    system VARCHAR, -- 'salesforce', 'hubspot', 'slack'
    status VARCHAR, -- 'pending', 'completed', 'failed'
    error_message VARCHAR,
    synced_at TIMESTAMP
)
```

### 11.6 Resilience & Error Handling

**Graceful Degradation**
- If ChiliPiper unavailable → Provide booking link
- If Snowflake down → Queue locally, retry
- If CRM sync fails → Manual queue for ops team

**Retry Logic**
- Real-time functions: No retry (fail gracefully)
- Post-call webhooks: Exponential backoff
- Downstream syncs: Up to 3 retries over 15 min

**Data Consistency**
- Snowflake = source of truth
- All systems sync FROM Snowflake
- No direct system-to-system sync

### 11.7 Performance Targets

**Real-Time Functions**
- Latency: < 500ms per function call
- Success rate: > 99%
- Timeout: 2 seconds max

**Post-Call Processing**
- Snowflake ingestion: < 30 seconds
- CRM sync: < 5 minutes
- Full pipeline: < 10 minutes end-to-end

**Scale Targets**
- 1,000 calls/day initially
- 10,000 calls/day within 6 months
- No architectural changes needed for scale

### 11.8 RevOps Integration Points

**What RevOps Needs to Configure**

1. **ChiliPiper Setup**
   - Define rep pods (Enterprise, SMB)
   - Set territory rules
   - Configure round-robin weights
   - Set working hours per rep

2. **Salesforce Mapping**
   - Lead fields for voice data
   - Custom fields for call metadata
   - Lead source = "Voice Agent"
   - Auto-convert rules for qualified leads

3. **Slack Alerts**
   - Channel for high-value leads (#voice-agent-wins)
   - Notification format
   - @mention rules for urgent leads

4. **Dashboard Access**
   - Snowflake reader accounts
   - Tableau/Looker permissions
   - Standard report templates

**What Happens Automatically**

1. **Lead Routing**
   - ChiliPiper handles all logic
   - No manual assignment needed
   - Immediate booking confirmation

2. **Data Flow**
   - All call data → Snowflake
   - Triggered sync to CRM
   - Automated alerting

3. **Compliance**
   - Call recordings stored (30 days)
   - Consent logged
   - PII masked in logs

---

## 14. Competitive Advantage

### Why This Wins
1. **First-Mover:** No competitor has trial success voice agents
2. **Data Network Effect:** Every conversation improves the system
3. **Brand Differentiation:** Premium support experience at scale
4. **Revenue Multiplier:** Success + Sales in one motion
5. **Scalable Quality:** Consistent excellence without human constraints

### Defensibility
- Proprietary conversation data
- Deep product integration
- Refined qualification models
- Brand permission to engage
- Organizational learning

---

## 15. Success Criteria by Phase

### MVP Success (Month 1)
- **Volume:** 100+ completed conversations
- **Qualification:** 20%+ qualification rate
- **Bookings:** 10+ meetings booked via Chili Piper
- **Quality:** Sales team confirms lead quality (via manual review)
- **Stability:** <5% technical failure rate
- **Learning:** Clear insights on what trialists need
- **Operational:** Manual routing process proves manageable and validates lead quality

### V2 Success (Month 3)
- **Scale:** 300+ conversations monthly
- **Intelligence:** MQL scoring accuracy >70%
- **Attribution:** Full funnel visibility in Snowflake
- **Automation:** 90% of qualified leads auto-routed
- **ROI:** Measurable lift in trial-to-paid conversion
- **Integration:** Seamless HubSpot/SFDC data flow

### V3 Success (Month 6)
- **Conversion:** 25%+ improvement in trial-to-paid
- **Revenue:** $500K+ attributed pipeline
- **Efficiency:** Cost per qualified opp <$100
- **Advocacy:** Sales team actively requests more volume
- **Intelligence:** Predictive models driving outreach timing


---

## Appendix A: Example Conversations

### Inbound Success Conversation
```
User: "I'm trying to create a template but it's not working"
Agent: "I can definitely help you with that! Templates are one of our most powerful features. What type of document are you trying to create a template for?"
User: "Sales proposals - we send about 50 a month"
Agent: "Perfect! With 50 proposals monthly, templates will save your team hours. Let me guide you through this - are you in the template section now?"
[Guides through creation]
Agent: "Fantastic! You just created your first template. Quick question - will other people on your sales team be using these templates too?"
User: "Yes, we have 12 sales reps"
Agent: "With 12 reps sending 50 proposals, you're looking at huge time savings. Our team plan includes advanced features like template locking and approval workflows that sales teams love. Would you like me to connect you with a specialist who can show you how other sales teams your size are using PandaDoc?"
```

### Outbound Success Conversation
```
Agent: "Hi Sarah, this is Alex from PandaDoc. I'm calling because I noticed your team at TechCorp started evaluating our platform. I wanted to make sure you're getting everything you need from your trial. Do you have 2 minutes?"
User: "Sure, we're still figuring it out"
Agent: "Totally understand - there's a lot to explore. What's the main problem you're trying to solve with documents?"
User: "Our sales proposals take forever and we can't track them"
Agent: "That's exactly what we solve best. How many proposals does your team typically send?"
User: "About 200 a month across the team"
Agent: "With that volume, I can show you how to cut proposal creation time by 75% and see exactly when clients view them. Do you have your PandaDoc account open? I can guide you through setting up your first trackable template right now..."
```
