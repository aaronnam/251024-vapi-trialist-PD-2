# Vapi Dashboard Configuration - PandaDoc Trial Success Agent (Sarah)
*Production-ready configuration for PandaDoc trial success voice agent*

---

## 📋 Assistant Basic Information

**Assistant Name:**
```
PandaDoc Trial Success Agent - Sarah
```

---

## 🤖 Model Tab Configuration

### First Message
**First Message Mode:**
```
[X] assistant-speaks-first-with-fixed-message
[ ] assistant-speaks-first-with-model-generated-message
[ ] assistant-waits-for-user
```

**First Message Content (if fixed):**
```
Hi! This is Sarah from PandaDoc. I noticed you're exploring our platform - I'm here to help you get the most from your trial. How's your experience going so far?
```

### Model Provider & Selection

**Provider:**
```
[X] OpenAI
[ ] Anthropic (Claude)
[ ] Google (Gemini)
[ ] Groq
[ ] Together AI
[ ] Anyscale
[ ] OpenRouter
[ ] Perplexity
[ ] DeepInfra
[ ] Runpod
[ ] Fireworks
[ ] Custom OpenAI-compatible
[ ] Azure OpenAI
[ ] Vapi
[ ] LangChain
```

**Model:**
```
gpt-4o
```

### System Prompt
```
# Role & identity: You are Sarah, a friendly and knowledgeable Trial Success Specialist for PandaDoc who helps trialists experience value quickly and naturally guides them toward becoming successful customers"

# Core job: Help trial users overcome friction points, demonstrate specific value for their use case, and ensure they achieve their first success moment within the trial period
## Core Responsibilities
1. Identify and resolve friction points preventing trial success
2. Demonstrate specific value for their use case
3. Calculate and communicate ROI based on their needs
4. Naturally qualify leads through helpful discovery
5. Book meetings for qualified enterprise opportunities (10+ seats)
# Conversation style: Friendly, Business casual, moderate pace (150-170 WPM), concise responses (max 2-3 sentences per turn initially)

# Operating principles:
- Success first, sales second - focus on user achievement
- Acknowledge frustration before offering solutions
- Use their industry language, not document management jargon
- Celebrate small wins to build momentum
- Natural qualification through helpful discovery

#⚡ Voice-specific behaviors:
- Response time: <500ms using fillers ("Let me check that..." "Great question...")
- Interruption handling: Yield immediately with "Yes, absolutely..." or "Oh, sure..."
- Silence handling: After 3s: "I'm still here when you're ready" or "Take your time"
- Turn-taking: Pause 1.5s after questions, use rising intonation for prompts

# Qualification Signals (Track these naturally)
HIGH VALUE (Book meeting immediately):
- 10+ team members
- 100+ documents per month
- Needs Salesforce/HubSpot integration
- Requires API or whitelabeling
- Enterprise security requirements
- Current competitor spend >$500/month

MEDIUM VALUE (Nurture and guide):
- 5-9 team members
- 20-100 documents per month
- Basic CRM needs
- Growing company signals

SELF-SERVE (Pure enablement):
- <5 team members
- <20 documents per month
- Individual user
- Simple use cases

# Knowledge base usage:
Search Unleash KB with 2-3 word queries during natural pauses. Use "Let me find that for you..." while searching. Never say "according to our documentation" - integrate information conversationally.

# Tool Usage Instructions
- Use unleash_search_knowledge for product questions
- Use calculate_pandadoc_roi after discovering team size and volume
- Use chilipiper_check_availability before offering meeting times
- Use chilipiper_book_meeting for qualified 10+ seat opportunities
- Use webhook_send_conversation_event to track all qualification signals
- Use hubspot_send_resource to email relevant guides and templates

# Error handling:
If misunderstood: "Let me make sure I understood - you're trying to [restate], right?"
If tool fails: "I'll need to grab that information another way - tell me more about..."

# Never Do
- Don't access or modify user accounts directly
- Don't make promises about features not on roadmap
- Don't provide legal advice on contracts
- Don't share other customers' specific data
- Don't be pushy - success first, sales second
- Don't offer to book meetings or put the  unless the trialist is qualified as "HIGH VALUE"
- Don't call the customer "High value" or not

# Always Do
- Acknowledge frustration before solving
- Celebrate their progress
- Provide specific, actionable next steps
- Be transparent about what you can and cannot do
- Maintain a helpful, supportive tone even if they're not qualified

Remember: Your success is measured by how many trialists you help achieve value, not just by how many meetings you book. Every positive interaction builds the PandaDoc brand.
```

### Model Parameters

**Temperature:**
```
0.3
```

**Max Tokens:**
```
150
```

**Emotion Recognition:**
```
[X] Enabled
[ ] Disabled
```

### Knowledge Base (if applicable)

**Knowledge Base Files:**
```
[Upload these files to Unleash or configure via webhook]
- trialist-journey-stages.md
- pricing-and-plans.md
- feature-comparison.md
- objection-handlers.md
- roi-benchmarks.md
- competitor-comparisons.md
- integration-guides.md
```

---

## 🎙️ Voice Tab Configuration

### Voice Provider

**Provider:**
```
[X] ElevenLabs
[ ] Cartesia
[ ] LMNT
[ ] Deepgram (Aura)
[ ] Play.ht
[ ] Azure
[ ] RimeAI
[ ] NEETS
[ ] OpenAI
[ ] Vapi (Basic)
[ ] Custom
```

### Voice Selection

**Voice ID/Name:**
```
Rachel - 21m00Tcm4TlvDq8ikWAM
```
*Note: Rachel is warm, professional, and conversational - perfect for Sarah*

**Voice Model (if applicable):**
```
eleven_turbo_v2_5
```

**Filler Injection:**
```
[X] Enabled (natural "um", "uh" sounds)
[ ] Disabled
```

### Voice Settings

**Speed/Rate:**
```
1.1
```
*Slightly faster for energy and engagement*

**Pitch (if supported):**
```
Default
```

**Stability (ElevenLabs):**
```
0.5
```
*Balanced for natural variation*

**Similarity Boost (ElevenLabs):**
```
0.75
```
*High consistency while maintaining naturalness*

---

## 🎧 Transcriber Tab Configuration

### Transcriber Provider

**Provider:**
```
[X] Deepgram
[ ] Assembly AI
[ ] Gladia
[ ] Talkscriber
[ ] Azure
[ ] Google (Speech-to-Text)
[ ] AWS Transcribe
[ ] RevAI
[ ] Vapi
[ ] Custom
```

### Transcriber Model

**Model:**
```
nova-2
```
*Best accuracy for conversation*

**Language:**
```
en-US
```

### Transcription Settings

**Endpointing:**
```
[X] Enabled
[ ] Disabled
```

**Endpointing Threshold (ms):**
```
300
```
*Quick response to user pauses*

**Smart Format:**
```
[X] Enabled (formats numbers, dates, etc.)
[ ] Disabled
```

**Profanity Filter:**
```
[ ] Enabled
[X] Disabled
```
*Professional context, unlikely to need*

---

## 🔧 Tools Tab Configuration

### Predefined Tools

**Default Tools to Enable:**
```
[X] End Call
[X] Transfer Call
[ ] Check Availability (Calendar)
[ ] Book Appointment (Calendar)
[ ] Send Message
```

### Custom Tools/Functions

**Tool 1: Knowledge Base Search**
```yaml
Name: unleash_search_knowledge
Description: Search PandaDoc knowledge base for product information, pricing, features, and troubleshooting
Type: function
Server URL: https://api.pandadoc.com/voice-agent/webhook
Parameters:
  - name: query
    type: string
    description: Natural language search query
    required: true
  - name: category
    type: string
    description: Optional category filter - features, pricing, integrations, troubleshooting
    required: false
  - name: max_results
    type: number
    description: Maximum results to return (default 3)
    required: false
```

**Tool 2: Competitor Comparison**
```yaml
Name: unleash_get_competitor_comparison
Description: Get competitive differentiation when user mentions competitors
Type: function
Server URL: https://api.pandadoc.com/voice-agent/webhook
Parameters:
  - name: competitor
    type: string
    description: Competitor name - docusign, hellosign, proposify, adobe_sign
    required: true
  - name: feature_focus
    type: string
    description: Specific feature to compare (optional)
    required: false
```

**Tool 3: ROI Calculator**
```yaml
Name: calculate_pandadoc_roi
Description: Calculate personalized ROI based on team size and document volume
Type: function
Server URL: https://api.pandadoc.com/voice-agent/webhook
Parameters:
  - name: team_size
    type: number
    description: Number of team members who will use PandaDoc
    required: true
  - name: documents_per_month
    type: number
    description: Monthly document volume
    required: true
  - name: average_doc_value
    type: number
    description: Average deal/document value in dollars
    required: false
  - name: current_process
    type: object
    description: Current process metrics (hours_per_doc, approval_days, error_rate)
    required: false
  - name: use_case
    type: string
    description: Primary use case - sales, hr, legal, procurement
    required: false
```

**Tool 4: Check Calendar Availability**
```yaml
Name: chilipiper_check_availability
Description: Check sales rep calendar availability before offering meeting times
Type: function
Server URL: https://api.pandadoc.com/voice-agent/webhook
Parameters:
  - name: meeting_type
    type: string
    description: Type of meeting - always use pandadoc_enterprise_demo
    required: true
  - name: date_range
    type: object
    description: Date range to check (start and end dates)
    required: true
```

**Tool 5: Book Meeting**
```yaml
Name: chilipiper_book_meeting
Description: Schedule meeting with sales team for qualified opportunities
Type: function
Server URL: https://api.pandadoc.com/voice-agent/webhook
Parameters:
  - name: lead
    type: object
    description: Lead information (email, first_name, last_name, company, phone)
    required: true
  - name: meeting_type
    type: string
    description: Meeting type - pandadoc_enterprise_demo
    required: true
  - name: qualification
    type: object
    description: Qualification data (team_size, monthly_volume, integration_needs, urgency)
    required: true
  - name: preferred_times
    type: array
    description: Array of preferred meeting times (ISO timestamps)
    required: true
  - name: notes
    type: string
    description: Context notes for sales rep
    required: false
```

**Tool 6: Send Conversation Event**
```yaml
Name: webhook_send_conversation_event
Description: Track conversation events, qualification signals, and objections
Type: function
Server URL: https://api.pandadoc.com/voice-agent/webhook
Parameters:
  - name: event_type
    type: string
    description: Event type - qualification, objection, booking, support
    required: true
  - name: call_id
    type: string
    description: Unique call identifier
    required: true
  - name: trialist
    type: object
    description: Trialist information (email, company)
    required: true
  - name: data
    type: object
    description: Event data (qualification_score, intent_signals, objections, topics)
    required: true
```

**Tool 7: Send Resource Email**
```yaml
Name: hubspot_send_resource
Description: Email relevant resources, guides, and case studies to trialist
Type: function
Server URL: https://api.pandadoc.com/voice-agent/webhook
Parameters:
  - name: to
    type: string
    description: Recipient email address
    required: true
  - name: template_id
    type: string
    description: Email template - case_study_template, integration_guide_template, pricing_overview_template
    required: true
  - name: dynamic_data
    type: object
    description: Template variables (first_name, resource_type, industry, resource_url)
    required: true
```

---

## 📊 Analysis Tab Configuration

### Call Summary

**Summary Prompt:**
```
Generate a concise summary of this trial support call including:
1. Trialist's main challenge or question
2. Solution provided
3. Qualification signals detected (team size, use case, urgency)
4. Next steps agreed upon
5. Meeting booked (if applicable)
Keep it under 5 sentences.
```

**Summary Enabled:**
```
[X] Yes
[ ] No
```

### Success Evaluation

**Success Criteria:**
```
A successful call means:
1. User's immediate question/blocker was resolved
2. User expressed satisfaction or gratitude
3. Clear next step was established
4. If qualified (10+ seats), meeting was booked
5. If not qualified, user knows how to proceed independently
```

**Success Evaluation Enabled:**
```
[X] Yes
[ ] No
```

**Success Evaluation Rubric:**
```yaml
Problem Resolution: Was the user's issue/question addressed?
Weight: 10

Qualification: Were key qualification signals identified?
Weight: 7

Value Communication: Was ROI/value clearly communicated?
Weight: 8

Next Steps: Were clear next steps established?
Weight: 9

Meeting Booking: If qualified, was meeting successfully booked?
Weight: 10

User Sentiment: Did user sentiment improve during call?
Weight: 8
```

### Structured Data Extraction

**Data Schema:**
```json
{
  "type": "object",
  "properties": {
    "company_name": {
      "type": "string",
      "description": "Name of the trialist's company"
    },
    "team_size": {
      "type": "number",
      "description": "Number of potential users"
    },
    "monthly_document_volume": {
      "type": "number",
      "description": "Documents sent per month"
    },
    "current_solution": {
      "type": "string",
      "description": "What they use today"
    },
    "primary_use_case": {
      "type": "string",
      "description": "Main use case (sales/hr/legal/procurement)"
    },
    "integration_needs": {
      "type": "array",
      "description": "Required integrations (Salesforce, HubSpot, etc.)"
    },
    "trial_day": {
      "type": "number",
      "description": "Day of trial (1-14)"
    },
    "qualification_tier": {
      "type": "string",
      "description": "HIGH/MEDIUM/SELF_SERVE"
    },
    "objections": {
      "type": "array",
      "description": "Any objections raised"
    },
    "meeting_booked": {
      "type": "boolean",
      "description": "Whether sales meeting was scheduled"
    },
    "next_step": {
      "type": "string",
      "description": "Agreed upon next action"
    }
  }
}
```

**Structured Data Enabled:**
```
[X] Yes
[ ] No
```

---

## ⚙️ Advanced Tab Configuration

### Messages

**Voice Input Delay (ms):**
```
100
```
*Minimal delay for natural conversation*

**Background Sound:**
```
[X] Off
[ ] Office environment
[ ] Coffee shop
[ ] White noise
```

**Background Sound Volume:**
```
N/A
```

**Model Output in Messages:**
```
[X] Enabled
[ ] Disabled
```

### Speaking Behavior

**Backchannel Words:**
```
[X] Enabled (mm-hmm, yeah, okay)
[ ] Disabled
```

**Backchannel Frequency:**
```
0.4
```
*Natural but not excessive*

### Timeouts & Detection

**End Call After Silence (seconds):**
```
20
```
*Give users time to think*

**Idle Timeout (seconds):**
```
120
```
*2 minutes of complete inactivity*

**Max Call Duration (seconds):**
```
600
```
*10 minutes max*

**Silence Threshold (ms):**
```
300
```
*Quick turn-taking*

**Interruption Threshold (ms):**
```
100
```
*Responsive to interruptions*

### Voice Activity Detection

**VAD Provider:**
```
[X] Default
[ ] Custom
[ ] Disabled
```

**VAD Sensitivity:**
```
[ ] Low
[X] Medium
[ ] High
```

### Transport

**Transport Provider:**
```
[ ] Twilio
[ ] Vonage
[X] Vapi (default)
[ ] Daily
[ ] Custom WebRTC
```

**Recording:**
```
[X] Enabled
[ ] Disabled
```

### HIPAA Compliance (if applicable)

**HIPAA Enabled:**
```
[ ] Yes (Enterprise only)
[X] No
```

---

## 🔐 Compliance Tab Configuration

### Recording Consent

**Consent Message:**
```
Quick heads up - I'm an AI assistant and this call may be recorded to help us improve. Is that okay with you?
```

**Consent Required:**
```
[X] Yes
[ ] No
```

---

## 🌐 Widget Tab Configuration

### Web Widget Settings

**Widget Position:**
```
[X] Bottom right
[ ] Bottom left
[ ] Top right
[ ] Top left
```

**Widget Color:**
```
#FF6B35
```
*PandaDoc brand orange*

**Widget Size:**
```
[ ] Small
[X] Medium
[ ] Large
```

**Auto-open:**
```
[ ] Enabled
[X] Disabled
```

**Auto-open Delay (seconds):**
```
N/A
```

---

## 🔄 Webhook Configuration

### Server URL
```
https://api.pandadoc.com/voice-agent/webhook
```
*For MVP, use: https://your-ngrok-url.ngrok.io/webhook*

### Events to Subscribe

**Call Events:**
```
[X] assistant-request
[X] call-started
[X] call-ended
[ ] phone-call-control
[X] transcript
[X] tool-calls
[X] speech-started
[X] speech-ended
[X] user-interrupted
[ ] voice-input
[X] function-call
[X] hang
[X] metadata
```

### Webhook Headers (if needed)
```json
{
  "Authorization": "Bearer YOUR_PANDADOC_WEBHOOK_SECRET",
  "Content-Type": "application/json",
  "X-Source": "vapi-voice-agent"
}
```

### Webhook Secret (for verification)
```
YOUR_WEBHOOK_SECRET_HERE
```

---

## 📞 Phone Number Configuration

### Phone Number Type
```
[X] Vapi Number (for testing)
[ ] Twilio Number (for production)
[ ] Vonage Number
[ ] Telnyx Number
```
*Note: Start with Vapi number, move to Twilio for production*

### Fallback Destination (if assistant fails)
```
+1-415-555-0100
```
*PandaDoc support line*

---

## 🎯 Squad Configuration (V2 - Future Enhancement)

### Squad Members

**Primary Assistant:**
```
Sarah - Trial Success Specialist
```

**Specialist Assistants:**
```
1. Technical Specialist - API/Integration expert
2. Enterprise Specialist - 50+ seat deals
3. Billing Specialist - Pricing/payment questions
```

### Transfer Rules
```yaml
From: Sarah
To: Technical Specialist
Condition: User asks about API, webhooks, or custom integrations

From: Sarah
To: Enterprise Specialist
Condition: Team size >50 or mentions compliance/security requirements

From: Sarah
To: Billing Specialist
Condition: Questions about discounts, payment terms, or billing
```

---

## 📝 Notes & Additional Configuration

**Special Requirements:**
```
MVP Phase:
1. Start with single assistant (Sarah)
2. Use manual webhook forwarding for development (vapi listen)
3. Manual lead routing to sales team
4. Focus on 10+ seat qualification

V2 Enhancements:
1. Add squad members for specialized support
2. Implement automated Salesforce routing
3. Add pandadoc_api_get_trial_status tool
4. Integrate with live trial activity data
```

**Testing Notes:**
```
Test Scenarios Required:
1. Day 1 trialist exploration
2. Day 7 active user with questions
3. Day 13 decision stage with pricing objection
4. Technical blocker scenario
5. Competitor comparison flow
6. 10+ seat qualification and booking
7. Interruption handling
8. Background noise handling
9. Silence recovery
10. Tool failure graceful degradation
```

---

## ✅ Pre-Launch Checklist

```
[X] System prompt finalized
[X] Voice tested and approved (Rachel/ElevenLabs)
[X] Tools configured and tested
[ ] Webhooks endpoint ready (in progress)
[X] Knowledge base uploaded (via Unleash)
[ ] Phone number configured (ready to purchase)
[X] Success criteria defined
[X] Compliance requirements met
[X] Widget settings configured
[ ] Squad members configured (V2)
[X] Cost estimates reviewed ($0.18/min)
[ ] Backup configuration exported
```

---

## 💰 Cost Estimates

**Per Minute Costs:**
- Deepgram STT: $0.01
- OpenAI GPT-4o: ~$0.08
- ElevenLabs TTS: $0.036
- Vapi Platform: $0.05
- **Total: ~$0.18/minute**

**Per Call (5 min avg):**
- ~$0.90 per conversation

**Monthly (1000 calls):**
- ~$900/month platform costs
- Additional: Phone numbers, webhooks, storage

---

## 🚀 Quick Copy Commands for Dashboard

**For Testing:**
```bash
# Local webhook forwarding
vapi listen --forward-to http://localhost:3000/webhook

# Test the assistant
vapi assistant test [assistant-id]

# Monitor logs
vapi logs calls --tail --follow
```

**Webhook URL for Development:**
```
https://YOUR-NGROK-URL.ngrok.io/webhook
```

**Webhook URL for Production:**
```
https://api.pandadoc.com/voice-agent/webhook
```

---

*Configuration Version: 1.0*
*Created for: PandaDoc Trial Success Voice Agent*
*Last Updated: October 2025*
*Ready for: Copy-paste into Vapi Dashboard*