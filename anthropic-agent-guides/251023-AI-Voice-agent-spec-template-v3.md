# AI Voice Agent Specification Template
*Version 3.0 - A clean, fillable template with examples*

---

## 1. Objective

**Goal:** [What success looks like]
*Example: Convert 25% of stuck trial users into paying customers through guided assistance*

**Scope:** [What's in/out of bounds]
*Example: In: Setup help, pricing questions | Out: Technical support, billing changes*

**Target conversation duration:** [Optimal length]
*Example: 3-7 minutes (enough to help, not too long)*

**⚡ Max conversation duration:** [Hard timeout]
*Example: 10 minutes (transfer to human if exceeded)*

**Success metrics:** [How you measure winning]
*Example: Completion rate >70%, Conversion +20%, User satisfaction >4/5*

---

## 2. System Prompt

**Role & identity:** [Who the agent is - influences voice/tone]
*Example: "You are Sarah, a friendly Trial Success Specialist for PandaDoc"*

**Core job:** [One sentence - what you help with]
*Example: "Help trial users experience value quickly and guide them to become customers"*

**Conversation style:** [Formal/casual, pacing, verbosity]
*Example: Business casual, moderate pace, concise responses (max 2-3 sentences)*

**Operating principles:** [3-5 key behaviors]
- *Example: Help first, sell second*
- *Example: Acknowledge frustration before solving*
- *Example: Use their language, not jargon*

**⚡ Voice-specific behaviors:**
- Response time: [Target latency] *Example: <500ms using fillers if needed*
- Interruption handling: [Protocol] *Example: Yield immediately, say "Yes, absolutely..."*
- Silence handling: [After X seconds] *Example: After 3s: "I'm still here when you're ready"*
- Turn-taking: [When to pause] *Example: Pause after questions for 1.5s*

**Knowledge base usage:** [How to query during conversation]
*Example: Search KB with 2-3 word queries, use "Let me check that" while searching*

**Tool usage guidelines:**
- Sync tools: [Which ones block conversation] *Example: account_lookup - use during natural pauses*
- Async tools: [Background operations] *Example: send_email - trigger while talking*

**Error handling:** [Recovery strategies]
*Example: If misunderstood: "Let me make sure I understood - did you mean...?"*

---

## 3. Capabilities

### Voice Pipeline

| Component | Provider/Model | Target | Fallback |
|-----------|---------------|--------|----------|
| **STT** | [Provider, model] *Ex: Deepgram Nova-2* | [Latency] *<200ms* | [Backup] *Whisper* |
| **TTS** | [Provider, voice] *Ex: ElevenLabs, Rachel* | [Speed] *1.1x* | [Backup] *OpenAI TTS* |
| **VAD** | [Sensitivity] *Ex: WebRTC, balanced* | [Threshold] *500ms* | [Mode] *Conservative* |

**⚡ Total latency budget:** [End-to-end target] *Example: <800ms from user stops to agent starts*

### Tools

| Tool Name | Sync/Async | Purpose | Max Latency | Fallback Strategy |
|-----------|------------|---------|-------------|-------------------|
| [search_knowledge_base] | Async | [Answer questions] | [500ms] | [Use cached common answers] |
| [check_account_status] | Sync | [Get user context] | [200ms] | [Continue without personalization] |
| [schedule_callback] | Async | [Book human follow-up] | [2s] | [Provide direct phone number] |

*Example tool spec:*
```yaml
tool: search_knowledge_base
when_to_use: User asks question about product/pricing
during_call: Say "Let me find that for you..." while searching
max_wait: 500ms before giving partial answer
```

### Knowledge Bases

| Source | Type | Query Strategy | Update Frequency |
|--------|------|----------------|------------------|
| [Core KB] | Pre-loaded | [Search first for all questions] | [Daily] |
| [Pricing] | Live lookup | [Only for specific quotes] | [Real-time] |
| [FAQs] | Cached | [Fuzzy match on keywords] | [Weekly] |

*Example KB structure:*
```
/kb/00-core.md (always check first)
/kb/01-pricing.md (pricing questions)
/kb/02-how-to.md (step-by-step guides)
```

### Sub-agents (if applicable)

| Agent | Trigger | Handoff Protocol | Context Passed |
|-------|---------|------------------|----------------|
| [Billing specialist] | [Payment issues] | [Warm transfer with intro] | [Account, issue summary] |
| [Technical support] | [Bug reports] | [Schedule callback] | [Error details, attempted fixes] |

---

## 4. Conversation Flow

### State Machine

```
[GREETING] → [DISCOVERY] → [SOLUTION] → [NEXT_STEPS] → [CLOSING]
     ↓            ↓            ↓             ↓
[ESCALATION] ←────────────────────────────────
```

**State definitions:**
- GREETING: [First 15 seconds] *Example: "Hi [Name]! I see you're on day 3 of your trial..."*
- DISCOVERY: [Understanding need] *Example: "Tell me what you're trying to accomplish"*
- SOLUTION: [Delivering value] *Example: "Here's how to do that..." [guide through steps]*
- NEXT_STEPS: [Ensuring momentum] *Example: "Your next step is... Should I schedule a follow-up?"*
- CLOSING: [Graceful exit] *Example: "Perfect! You're all set. Anything else?"*

### Conversation Patterns

**Opening (Inbound):**
```
"Hi [Name]! This is [Agent] from [Company].
I see you [specific context].
How can I help you today?"
```

**Opening (Proactive):**
```
"Hi [Name], I noticed you've been [specific activity]
for a few minutes. I can help you [complete task] quickly
if you'd like - takes about 2 minutes."
```

**⚡ Active listening cues:** [When and what]
*Example: Every 20-30s: "mm-hmm", "I see", "got it"*

**⚡ Backchanneling:** [Frequency and variety]
*Example: Rotate between: "uh-huh", "right", "okay", "sure"*

**Discovery questions:** [Progression]
1. Broad: *"What brings you here today?"*
2. Clarifying: *"When you say X, do you mean..."*
3. Quantifying: *"How many [users/documents]?"*
4. Prioritizing: *"What's most important: [speed/accuracy/ease]?"*

**Objection handling:** [Pattern for each]
| Objection | Response Pattern |
|-----------|-----------------|
| "Too expensive" | Acknowledge → Calculate ROI → Compare to time saved |
| "Too complex" | Empathize → Simplify to one task → Guide through it |
| "Need approval" | Understand → Provide materials → Schedule follow-up |

**Closing patterns:**
- Success: *"Perfect! You've [accomplished X]. [Next step] will [happen when]."*
- Partial: *"We made progress on [X]. For [Y], [next action]."*
- Escalation: *"[Human] would be better for this. Should I [transfer/schedule]?"*

---

## 5. Guardrails

**Safety constraints:** [What it absolutely cannot do]
- *Example: Cannot access payment methods*
- *Example: Cannot promise features not in roadmap*
- *Example: Cannot share other users' data*

**⚡ Real-time escalation triggers:** [Immediate handoff]
- *Example: Angry tone detected (sentiment <-0.7)*
- *Example: Request for manager 2x*
- *Example: Legal/compliance questions*
- *Example: Technical issue beyond scope*

**Human handoff protocol:** [How to transfer]
```
"I want to make sure you get the right help.
Let me connect you with [specialist type] who can
[specific value]. One moment..."
[Transfer or schedule based on availability]
```

**Rate limits:** [API calls during conversation]
- *Example: Max 10 KB searches per call*
- *Example: Max 3 tool calls per turn*

**Compliance requirements:**
- Recording consent: *"This call may be recorded for quality. Is that okay?"*
- AI disclosure: *"I'm an AI assistant" (within 30 seconds)*
- TCPA compliance: *For outbound only with explicit consent*
- Data handling: *No storage of payment/medical/legal info*

---

## 6. Voice UX Design

**Personality attributes:**
| Attribute | Setting | Example Behavior |
|-----------|---------|------------------|
| Energy | [Calm/Moderate/High] | *Moderate: Match user's energy level* |
| Expertise | [Peer/Advisor/Expert] | *Advisor: "Here's what typically works..."* |
| Formality | [Casual/Business/Formal] | *Business casual: Professional but approachable* |
| Empathy | [Low/Medium/High] | *High: Acknowledge frustration before solving* |

**Voice characteristics:**
- Gender: [Male/Female/Neutral] *Example: Female*
- Age: [Young/Middle/Mature] *Example: Middle (30-40 perceived)*
- Accent: [Regional/Neutral] *Example: Neutral American*
- Speed: [WPM range] *Example: 150-170 WPM (moderate)*
- Pitch variance: [Monotone/Natural/Expressive] *Example: Natural*

**⚡ Prosody controls:**
- Emphasis: [When to stress words] *Example: Numbers, key benefits*
- Pausing: [Strategic silence] *Example: After questions, before important info*
- Speed changes: [When to vary] *Example: Slow for instructions, normal for chat*

---

## 7. Configuration & Testing

### Technical Configuration

**Model settings:**
```yaml
model: [LLM choice]  # Example: gpt-4o or claude-3.5-sonnet
temperature: [0.3-0.5 for voice]  # Lower = more consistent
max_tokens: [150 for voice]  # Keep responses concise
streaming: [true]  # Required for low latency
```

**Audio settings:**
```yaml
sample_rate: [Hz]  # Example: 16000 Hz
codec: [Type]  # Example: μ-law
noise_suppression: [Level]  # Example: Moderate
echo_cancellation: [On/Off]  # Example: On
```

### Testing Scenarios

**Core flows (Must work perfectly):**
- [ ] Happy path: [Main use case] *Example: User gets stuck → Gets help → Completes task*
- [ ] Interruption: [Mid-sentence cutoff] *Example: Agent yields immediately*
- [ ] Confusion: [Unclear input] *Example: Agent asks for clarification*
- [ ] Silence: [Dead air] *Example: Agent prompts after 3 seconds*
- [ ] Escalation: [Needs human] *Example: Smooth handoff with context*

**Edge cases (Should handle gracefully):**
- [ ] Background noise *Example: Still understands with moderate noise*
- [ ] Multiple speakers *Example: Focuses on primary speaker*
- [ ] Network issues *Example: Recovers from brief disconnection*
- [ ] Accent variation *Example: Handles major English accents*
- [ ] Emotional users *Example: De-escalates, shows empathy*

### Success Metrics

**Conversation quality:**
- Completion rate: [Target %] *Example: >70% reach natural end*
- Duration: [Target range] *Example: 3-7 minutes average*
- Turns: [Target count] *Example: 8-15 exchanges*
- Sentiment delta: [Change] *Example: +0.3 or better*

**Technical performance:**
- Response latency: [p50/p95/p99] *Example: 400ms/600ms/800ms*
- STT accuracy: [Target %] *Example: >95%*
- Interruption handling: [Success %] *Example: >90% clean yields*
- Tool success rate: [Target %] *Example: >95% return useful results*

**Business impact:**
- Primary KPI: [Metric and target] *Example: Trial conversion +20%*
- Cost per conversation: [Target] *Example: <$0.50*
- Escalation rate: [Target] *Example: <15%*
- NPS/CSAT: [Target score] *Example: >4.0/5.0*

---

## 8. Implementation Checklist

### Week 1: Build Core
- [ ] Set up voice pipeline (STT/TTS/VAD)
- [ ] Create basic system prompt
- [ ] Implement 2-3 core tools
- [ ] Build simple conversation flow
- [ ] Test with team (10+ conversations)

### Week 2: Add Intelligence
- [ ] Set up knowledge base structure
- [ ] Implement KB search tool
- [ ] Add conversation patterns
- [ ] Handle interruptions/silence
- [ ] Test with friendly users (20+ conversations)

### Week 3: Polish & Learn
- [ ] Analyze conversation logs
- [ ] Fix top 3 issues only
- [ ] Add error recovery
- [ ] Implement escalation flow
- [ ] Expand test group (50+ conversations)

### Week 4: Measure & Decide
- [ ] Calculate success metrics
- [ ] Document patterns/failures
- [ ] Get user feedback
- [ ] Make scale/pivot decision
- [ ] Plan next iteration

---

## Quick Reference Card

### 🚨 Voice-Specific Must-Haves
- **Latency:** <500ms response time (use fillers if needed)
- **Interruptions:** Yield immediately when user speaks
- **Silence:** Prompt after 3 seconds of dead air
- **Conciseness:** Max 2-3 sentences per turn initially
- **Backchanneling:** Active listening cues every 20-30s
- **Natural speech:** Handle "um", "uh", restarts
- **Error recovery:** Never say "error" - use natural language

### 📚 Knowledge Base Over Prompt
- **Prompt:** HOW to think and respond (<100 lines)
- **KB:** WHAT to know (unlimited, updated anytime)
- **Tools:** WHAT to do (keep under 5 for MVP)

### ⏱️ Latency Budget Breakdown
```
User stops speaking: 0ms
VAD detection: +50ms
STT processing: +150ms
LLM thinking: +200ms
TTS first byte: +100ms
Audio playback starts: =500ms total
```

### 🎯 MVP Success Criteria
- ✓ 50+ conversations completed
- ✓ 70%+ reach natural end
- ✓ Primary KPI improving
- ✓ Users choosing voice over alternatives
- ✓ Clear next features identified

---

*Template based on Anthropic's agent building guides and production voice agent patterns. Fill in [bracketed] sections, use examples as guidance, and pay special attention to ⚡ lightning bolt items for voice-critical elements.*