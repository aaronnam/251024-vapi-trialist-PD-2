# AI Voice Agent Spec

## 1. Objective
**Goal:** [What success looks like]  
**Scope:** [What's in/out of bounds]  
**Exit conditions:** [When to end the call]  
**⚡ Max conversation duration:** [Timeout for the call]

## 2. System Prompt
**Role & identity:** [Who the agent is - influences voice/tone]  
**Conversation style:** [Formal/casual, pacing, verbosity]  
**Operating principles:** [How it should behave]  
**Tool usage guidelines:** [**CRITICAL: Synchronous vs. async tools**]  
- Sync tools: Use during pauses/holds (user waits)
- Async tools: Gather info before/after speaking
**Memory strategy:** [What to remember during conversation]  
**Error handling:** [How to recover gracefully in real-time]  
**⚡ Interruption protocol:** [How to handle user cutting in]

## 3. Capabilities

### Voice Pipeline
**STT:** [Provider, model, latency target]  
**TTS:** [Provider, voice ID, speed, emotional range]  
**VAD:** [Voice activity detection sensitivity]  
**Latency budget:** [Target response time, e.g., <800ms]

### Tools
- Tool name | **Sync/Async** | Purpose | Max latency | Fallback if slow

### Knowledge Bases
- Source | **Pre-loaded vs. live lookup** | Query strategy during call

### Sub-agents (if applicable)
- **Live handoffs** | Transfer protocol | Context passed

## 4. Conversation Flow

### State Management
**Call state:** [greeting → discovery → action → closing]  
**Context window:** [How to compress as conversation grows]  
**Turn-taking:** [When to yield, when to hold floor]  
**Backchanneling:** ["mm-hmm", "I see" - when/how often]

### Interaction Patterns
**Opening:** [First 10 seconds script/framework]  
**Active listening cues:** [Acknowledgments, clarifications]  
**Handling silence:** [How long to wait, what to say]  
**Handling confusion:** [Rephrase strategy, escalation path]  
**Closing:** [Graceful exit, next steps, goodbye]

## 5. Guardrails
**Safety constraints:** [What it cannot discuss/do]  
**Human escalation triggers:** [When to transfer to human]  
**⚡ Real-time abort conditions:** [Anger detection, compliance issues]  
**Rate limits:** [API calls during live conversation]  
**Recording/compliance:** [Consent, TCPA, data retention]

## 6. Configuration
**Model:** [Which LLM, streaming mode]  
**Parameters:** [Temperature - **lower for voice**, max tokens]  
**Audio settings:** [Sample rate, codec, noise suppression]  
**Logging:** [Call recordings, transcripts, tool usage]  
**Monitoring:** [Latency, interruption rate, completion rate]  
**Testing strategy:** [Simulated calls, edge case scenarios]

---

## Key Differences for Voice Agents:

**Added:**
- Voice pipeline specs (STT/TTS/VAD)
- Latency constraints throughout
- Conversation flow & turn-taking rules
- Interruption handling
- Real-time error recovery
- Backchanneling/active listening patterns
- Sync vs. async tool designation

**Changed:**
- Tools must specify if they block conversation
- Memory must work within real-time constraints
- System prompt includes conversation style/pacing
- Testing focuses on conversational quality, not just task completion
- Guardrails include real-time escalation (can't retry silently)

**Same:**
- Core objective structure
- Tool/knowledge base organization
- Overall philosophy of goal → tools → autonomy