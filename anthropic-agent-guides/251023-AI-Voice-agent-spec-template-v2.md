# AI Voice Agent Specification Template V2
*A pragmatic, battle-tested template for AI product engineering teams building voice agents*
*Version 2.0 - MVP-First, Learn-Fast, Iterate-Relentlessly Approach*

**TL;DR:** Build in 2 weeks, test with 10 users, fix 3 things, measure KPI. Everything else is details.

---

## 🚀 Table of Contents (Jump Here)

1. **[Quick Start MVP](#quick-start-mvp)** - Get something working in 14 days
2. **[Problem & Reality Check](#problem--reality-check)** - Make sure voice is right
3. **[Agent Design](#agent-design)** - Architecture and personality
4. **[Voice UX](#voice-ux)** - Conversation flows and patterns
5. **[System Setup](#system-setup)** - Tech stack and knowledge bases
6. **[Prompts (Keep Lean!)](#prompts-keep-lean)** - <100 lines for MVP
7. **[Testing & Learning](#testing--learning)** - How to find your first 100 bugs
8. **[Safety & Compliance](#safety--compliance)** - Legal and safety basics
9. **[Scale or Kill](#scale-or-kill)** - When to keep going vs pivot

---

## Quick Start MVP

### 🎯 Two-Week Sprint Plan

**Week 1: Build (Days 1-7)**

| Day | Morning | Afternoon | Evening |
|-----|---------|-----------|---------|
| 1-2 | Infrastructure setup (LiveKit/Vapi) | Basic conversation flow | Internal testing |
| 3-4 | Connect 1-2 tools | Create KB structure | Edge case testing |
| 5-6 | Bug fixes only | Team UAT | Documentation |
| 7 | Code review + cleanup | Deployment prep | Final testing |

**Week 2: Learn (Days 8-14)**

| Day | Morning | Afternoon | Evening |
|-----|---------|-----------|---------|
| 8-10 | Deploy to 10 users | Monitor conversations | Fix critical issues |
| 11-14 | Analyze patterns | Implement quick fixes | Measure primary KPI |

### ✅ MVP Definition: What Success Looks Like

**At the end of 2 weeks:**
- ✓ 50+ completed conversations
- ✓ <500ms response latency
- ✓ 70%+ natural endings (no crashes)
- ✓ 3-5 clear insights about what users want
- ✓ Measurable improvement in primary KPI

**At the end of 4 weeks:**
- ✓ 100+ conversations analyzed
- ✓ Top 3 issues fixed
- ✓ 100 users enrolled
- ✓ Primary KPI shows 15%+ improvement
- ✓ Clear features to build next

---

## Problem & Reality Check

### 1️⃣ The One Problem to Solve

**Write this in one sentence:**
```
Trial users who get stuck during setup abandon
within 48 hours, causing $X lost revenue monthly.
```

**Evidence it matters:**
- [ ] Data point 1: ___ (e.g., 73% of dropoffs happen at setup)
- [ ] Data point 2: ___ (e.g., support tickets spike on Day 2)
- [ ] Data point 3: ___ (e.g., each saved trial = $2,400 LTV)

### 2️⃣ Is Voice Actually the Right Answer?

**Voice is RIGHT when:**
- ✅ Users already try to call you
- ✅ Text-based support has <50% satisfaction
- ✅ Task needs back-and-forth conversation
- ✅ Emotional tone affects outcome
- ✅ Users explicitly ask for voice option

**Voice is WRONG when:**
- ❌ Simple lookup (just use search/FAQ)
- ❌ Sensitive data entry (use secure form)
- ❌ Users prefer async (email/chat better)
- ❌ Noisy environments (text is better)

### 3️⃣ Success Metrics (Pick 1-2 to Start)

| Timeline | Metric | Target | Why It Matters |
|----------|--------|--------|-------------------|
| Week 2 | Completion rate | >70% | Proof voice works |
| Week 2 | Response time | <500ms | Proof it's usable |
| Week 4 | Primary KPI | +20% | Proof it's valuable |
| Week 8 | Unit economics | <alternative cost | Proof it's scalable |

### Real Example:
> **Problem:** PandaDoc trial users abandon when they don't know how to send their first document (Day 1-2)
>
> **Evidence:**
> - 10,000 trials/month → 7,300 abandon (73%)
> - Support tickets: "Don't know what to do next" (67% of messages)
> - Each saved trial = $2,400 lifetime value
>
> **Why Voice:** Users already call support 3,000x/month but 78% hang up waiting
>
> **Success Targets:**
> - Week 2: 100 completed calls, 80% finish task
> - Week 4: 25% of trial users with agent convert (vs 15% baseline)

---

## Agent Design

### Architecture Choice (Pick One)

| Type | When | Complexity | Example |
|------|------|-----------|---------|
| **Autonomous** | Tasks vary a lot | Hard | Open-ended support |
| **Workflow** | Clear process | Easy | Appointment booking |
| **Hybrid** | Core flow + smart points | Medium | Qualification + escalation |

**MVP Recommendation:** Start with **Workflow** (easier to debug), switch to Hybrid when you understand the problem better.

### Conversation Architecture (4-Layer Pattern)

```
┌─ LAYER 1: Opening (0-30s)
│  └─ Greeting + context + rapport
│
├─ LAYER 2: Discovery (30s-2min)
│  └─ Understand problem + identify friction
│
├─ LAYER 3: Value (2-5min)
│  └─ Solve problem + demonstrate value
│
└─ LAYER 4: Next Steps (5-7min)
   └─ Summarize + momentum + callback
```

### Persona Template (Fill This Out)

```
Name: [e.g., "The Overwhelmed Evaluator"]

Context:
- Who: [e.g., Day 12 of trial, created 2 docs]
- Why: [e.g., Trying to decide if tool is worth cost]
- Emotional: [e.g., Stressed about deadline]

Goals:
1. [Primary goal]
2. [Secondary goal]

Friction Points:
- [What blocks them]
- [What frustrates them]

Success Looks Like:
- [Their definition of winning]
```

**Example:**
```
Name: The Overwhelmed Evaluator
Context: Day 12 of 14-day trial, created 2 documents
Why: Trying to decide if product is worth $99/mo
Emotional: Stressed, skeptical, decision fatigue

Goals:
1. Understand real ROI (not marketing ROI)
2. Feel confident about decision

Friction:
- Advanced features confuse her
- Pricing vs value disconnect
- Doesn't know if trial success = real usage

Success:
- Clear ROI = converts to paid
- Unclear = churns but impressed with support
```

---

## Voice UX

### Agent Personality (Choose Your Vibe)

**Pick Level of Formality:**
- Formal: "PandaDoc Assistant at your service"
- Business Casual: "Sarah from the PandaDoc team"
- Friendly: "Hey! I'm your doc buddy"
- Casual: "What's up? Let's solve this"

**Pick Energy Level:**
- Calm (for anxious users)
- Moderate (for neutral)
- Enthusiastic (for excited users)

**Pick Expertise Signal:**
- Peer: "I totally get the confusion..."
- Advisor: "Here's what typically works..."
- Expert: "This is how we designed it..."
- Assistant: "Let me help you through this..."

### Voice Characteristics (Template)

```
Gender: [Male | Female | Neutral | User Choice]
Age: [Young | Middle | Mature]
Accent: [Neutral | Regional]
Pace: [Slow for explanations | Fast for confirmation]
Energy: [Calm | Moderate | Enthusiastic]
```

### Voice-Specific Behaviors (CRITICAL FOR QUALITY)

**Latency Handling:**
- Always respond within 2 seconds (use fillers if needed)
- While processing: "Let me check that..." "Great question..."
- Users hate silence more than delay + filler

**Interruption Handling:**
- Detect overlap within 500ms
- Immediately yield: "Yes, absolutely..."
- Never say "Sorry, what?" - say "You know what..."

**Error Recovery:**
```
If misunderstood:
"I want to make sure I understand. Did you mean...?"

If can't find answer:
"That's a great question. Let me find the right person for this."

If system fails:
"I'm having technical issues. Let me get someone who can help."
```

### Conversation Patterns (Copy These)

**Opening (Inbound):**
```
"Hi [Name]! I see you're on Day X of your trial
and [specific context]. How can I help?"
```

**Discovery:**
```
"Tell me about [their use case]"
→ "When you say X, do you mean...?"
→ "How many [users/docs/etc]?"
→ "What's most important: [speed/quality/ease]?"
```

**Value Moment:**
```
"Here's what I'd recommend: [specific action]
It'll probably take 2 minutes and then you can
[specific outcome]."
```

**Closing (Success):**
```
"Perfect! You've now [accomplishment].
[Next step] will happen [timing].
Anything else?"
```

**Closing (Escalation):**
```
"This sounds like you need [specialist help].
I can [transfer/schedule callback].
What works better?"
```

---

## System Setup

### Tech Stack (Proven Defaults)

**LLM:**
- Primary: GPT-4o (reasoning) or Claude 3.5 Sonnet (cost)
- Fallback: GPT-3.5-turbo (for classification only)
- Token limit: Keep responses under 150 tokens

**Voice (Deepgram + ElevenLabs combo is best):**
- STT: Deepgram Nova-2 (best accuracy)
- TTS: ElevenLabs (most natural voice)
- VAD: Built-in to both services

**Infrastructure:**
- Platform: LiveKit Cloud (best for real-time)
- Alternative: Vapi.ai (faster to start)
- State: Redis for session data (if <1000 concurrent)

**Knowledge Base:**
- Store: Markdown files in Git (versioned, searchable)
- Update: Business team can edit directly (no code)
- Tool: Use simple text search (don't need vector DB yet)

### Knowledge Base Structure (CRITICAL FOR VOICE)

```
/knowledge-base/
├── 00-core.md              # General info, always search first
├── 01-pricing.md           # Pricing tiers, discounts
├── 02-features.md          # Feature explanations
├── 03-how-to.md            # Step-by-step guides
├── 04-troubleshooting.md   # Common errors
├── 05-objections.md        # Objection handling
└── 06-integrations.md      # Third-party tools
```

**Why KB > Prompt (For Voice):**
- Prompts with embedded knowledge get stale fast
- Large prompts = slow response times (death for voice)
- Business teams can update KB without code changes
- <300ms voice response requires minimal prompt processing

### Tools (Keep It Simple)

**MVP Tools (You probably only need 2-3):**

```yaml
Tool 1: search_knowledge_base
  Input: user_question (string)
  Output: relevant articles + snippets
  Purpose: Answer knowledge questions

Tool 2: check_user_status
  Input: user_id
  Output: trial_day, docs_created, plan_eligible
  Purpose: Understand context for personalization

Tool 3: schedule_human_callback
  Input: reason, preferred_time
  Output: confirmation + callback window
  Purpose: Escalation when stuck
```

**Tool Design Rule:** If it takes >2 seconds to describe, don't build it yet.

---

## Prompts (Keep Lean!)

### 🔑 The Most Important Insight

> **Lean Prompt + Rich Knowledge Base = Fast Voice Agent**
>
> Large prompts slow down response times. Voice requires <300ms responses. Move everything changeable into KB.

### Prompt Size Guide

| Phase | Size | Content |
|-------|------|---------|
| MVP | <100 lines | Identity + KB instructions + Tools + Boundaries |
| V2 | <200 lines | Add edge cases + personality variations |
| Prod | <300 lines | Comprehensive but still lean |

### MVP Prompt Template

```markdown
# System Prompt: [Agent Name]

## Identity
You are [Name], a [role] for [Company].
Your job: [One sentence - what you help with]

## Knowledge Base Query Protocol (CRITICAL)
When users ask questions:
1. Identify query type (pricing/how-to/error/feature)
2. Search KB using 2-3 word queries
3. Start with specific category, broaden if needed
4. While searching, use: "Let me check that..."
5. Respond naturally (don't say "according to KB")
6. If not found: "That's a great question..."

## Voice Behaviors (CRITICAL)
- Respond within 2 seconds using fillers if needed
- Keep responses under 3 sentences initially
- Acknowledge interruptions: "Yes, absolutely..."
- Handle silence: "I'm still here..."
- Match user energy (calm→calm, urgent→responsive)

## Available Tools
1. search_knowledge_base - Answer questions
2. check_user_status - Understand context
3. schedule_callback - Hand off to human

## Conversation Boundaries
Never:
- Make purchases or promises
- Access other users' data
- Provide legal/medical advice

Always:
- Be helpful first
- Qualify second
- Escalate when stuck

## If Stuck
"I want to get you the right help. Let me connect you with [specialist]."
```

### What NOT to Put in Prompt

❌ Pricing information (put in KB 01-pricing.md)
❌ Objection handling scripts (put in KB 05-objections.md)
❌ Long lists of examples (put in KB)
❌ Detailed business logic (put in Tools)
❌ Information that changes frequently (put in KB)

---

## Testing & Learning

### Week 1: Internal Testing Checklist

**Day 1-2: Can It Talk?**
```
□ Responds to greeting
□ Understands basic questions
□ Completes one task without errors
□ Says goodbye naturally
```

**Day 3-4: Is It Usable?**
```
□ Responds in <500ms
□ Voice sounds natural (not robotic)
□ Handles background noise
□ Recovers from interruptions
```

**Day 5-7: What Breaks It?**
```
□ Interruptions mid-sentence
□ Long silences (3+ seconds)
□ Confused/unclear inputs
□ Multiple speakers
□ Tool failures
```

### Week 2: Real User Testing

**Test with 10 Friendly Users:**
1. Give them real problem to solve with agent
2. Don't help - see what happens
3. Record conversation (with permission)
4. Ask: "Would you use this again?" (target: >60%)

**Metrics to Track:**
- Completion rate (target: >70%)
- Duration (target: <5 min)
- Would use again (target: >60%)
- Common failure points (list all)

### Daily Learning Process

```
Each Day:
1. Listen to 5 random conversations (15 min)
2. List "WTF moments" where it failed (5 min)
3. Find patterns - same issues repeating? (5 min)
4. Root cause: Prompt? KB? Tool? Latency? (5 min)
5. Fix it or log for later (if not critical)

Each Week:
1. Analyze all 50+ conversations
2. Identify top 3 issues
3. Fix only those 3
4. Measure improvement
5. Tell stakeholders what you learned
```

### Pattern Detection Template

```
Pattern: [What keeps happening]
Frequency: [X times in Y conversations]
Impact: [High/Medium/Low]
Root Cause: [Prompt/KB/Tool/Latency/Other]
Fix: [Specific change]
Verification: [How you'll know it worked]
```

---

## Safety & Compliance

### Minimum Guardrails (for MVP)

**Content Filtering:**
- [ ] Detect obvious profanity
- [ ] Don't echo passwords or credit cards
- [ ] Flag threats/emergency language → escalate

**Boundaries (Put in Prompt):**
- [ ] Cannot access other user accounts
- [ ] Cannot make purchases
- [ ] Cannot promise features
- [ ] Cannot provide legal/medical advice

### Compliance Basics

**Tell users it's AI (within 30 seconds):**
```
"Hi! This is Sarah, an AI assistant from PandaDoc..."
```

**Get recording consent (for outbound calls):**
```
"This call may be recorded for quality purposes.
That okay with you?"
```

**Don't assume PII is safe to discuss:**
```
"I can see your account info but not your
payment details for security."
```

### Error Handling Patterns

| What Fails | What You Say |
|-----------|-------------|
| Complete system crash | "I'm having technical issues. Let me get a human to help." |
| Tool fails | "I can't access that right now, but I can help with..." |
| Don't understand | "I want to get this right - could you say that differently?" |
| Not authorized | "I don't have access to that. Let me find someone who can help." |

---

## Scale or Kill

### The Decision Point (Week 4)

**If YES to all of these, keep going:**
- ✅ Primary KPI shows 15%+ improvement
- ✅ Positive user feedback trend
- ✅ Unit economics < alternative cost
- ✅ Clear path to more users
- ✅ Team excited (not frustrated)

**If NO to any of these, pause and learn:**
- ❌ KPI flat or negative
- ❌ User feedback is mediocre
- ❌ Costs are higher than expected
- ❌ Uncertain about next step
- ❌ Technical issues blocking progress

### Week 3-4: Prove Value

| Week | Action | Success Metric |
|------|--------|-----------------|
| 3 | Fix top 3 issues | Success rate →70%+ |
| 4 | Expand to 100 users | KPI shows +20% |
| 5 | Calculate unit economics | Cost < alternative |
| 6 | Get testimonials | User quotes |
| 7 | Plan scale | Roadmap for 10x |
| 8 | Deploy or pivot | Decision made |

### Common Failures (And What to Do)

**Failure: "Users don't complete conversations"**
- Root cause: Usually latency or understanding
- Fix: Measure response time + listen to 10 calls
- Decision: If >80% latency issue, switch platforms

**Failure: "KPI didn't improve"**
- Root cause: Maybe wrong problem or wrong solution
- Fix: Read conversation transcripts, ask users why
- Decision: Pivot target problem or approach

**Failure: "Costs too high"**
- Root cause: Probably too many LLM calls
- Fix: Reduce KB searches per conversation
- Decision: Use cheaper model or batch process

---

## Real Timeline Example

> **Week 1:** Built basic agent, found that users wanted different help than we thought
>
> **Week 2:** Pivoted approach, 50 test conversations showed 30% success rate
>
> **Week 3:** Fixed top 3 issues, success rate jumped to 70%
>
> **Week 4:** Expanded to 500 users, found scale issues with concurrent calls
>
> **Week 5:** Optimized for parallelization, cut cost 60%
>
> **Week 6:** Hit target KPI (25% vs 15% baseline), got executive approval to expand
>
> **Week 8:** Running 5,000 conversations/day profitably

---

## Key Reminders

### 1. Speed Beats Perfection
```
Bad:   6 weeks building → 1 day testing
Good:  1 week building → 5 weeks iterating
```

### 2. Knowledge Bases Are Your Secret Weapon
```
Prompts: HOW to think
KB: WHAT to know
Tools: WHAT to do

This separation keeps latency low and
lets business teams own their content.
```

### 3. Every Conversation Teaches Something
```
Day 1: Building
Day 2: Learning
Day 3: Learning (faster now)
Day 4: Already fixed the thing you learned on Day 2
```

### 4. Your Assumptions Will Be Wrong
```
You think: Users want X
Reality: Users want Y (something you didn't think of)
Good news: You'll find this in Week 1, not Month 6
```

### 5. Real Users Beat Planning Every Time
```
1 hour with real user > 10 hours of planning
5 real users > 100 customer interviews
```

---

## Document Info

**Version:** 2.0
**Created:** October 23, 2025
**For:** AI product teams building voice agents
**Based on:** Anthropic's agent guides + production experience + failure patterns

**Key Changes from V1:**
- MVP-first instead of comprehensive
- Knowledge base integration emphasis
- Real timeline examples
- Common pitfall warnings
- 2-week sprint structure

---

**Remember:** The best voice agent is the one that's actually on the phone with users, learning what they need. Not the one still being perfected in the lab.

Now go build something. 🚀