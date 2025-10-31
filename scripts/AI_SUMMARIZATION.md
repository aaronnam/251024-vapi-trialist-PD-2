# AI-Powered Transcript Summarization

## Overview

The Salesforce sync script uses GPT-5-nano to intelligently summarize voice call transcripts before storing them in Salesforce Event records. This provides sales teams with actionable insights instead of raw transcripts.

## Why Summarization?

**Problem:** Raw call transcripts are:
- Too long for quick scanning (often 1000+ words)
- Buried important signals in conversational context
- Difficult to extract qualification status at a glance

**Solution:** AI-generated summaries provide:
- **Qualification signals** (team size, document volume, integrations)
- **Conversation insights** (pain points, friction, feature interest)
- **Sales intelligence** (urgency, decision authority)
- **Clear outcomes** (call result, next steps)

## Technical Implementation

### Model: GPT-5-nano

**Why GPT-5-nano?**
- **Reasoning capabilities:** Better at extracting structured business signals
- **Cost-effective:** Cheapest GPT-5 model (~$0.0003/call)
- **Fast:** Medium reasoning effort provides balanced speed/quality
- **Reliable:** No temperature parameter needed (deterministic by default)

### API Parameters

```python
response = client.chat.completions.create(
    model="gpt-5-nano",
    max_completion_tokens=1000,      # ~400 word summary limit
    reasoning_effort="medium",       # Balanced analysis depth
    verbosity="medium",              # Moderate output detail
)
```

**Key differences from GPT-4o-mini:**
- Uses `max_completion_tokens` instead of `max_tokens`
- No `temperature` parameter (only default value of 1 supported)
- New `reasoning_effort` parameter for analysis depth
- New `verbosity` parameter for output detail

## Summary Structure

The AI extracts information in this priority order:

### Priority 1: Qualification Signals
- Team Size: Flag if 5+ users
- Document Volume: Flag if 100+ docs/month
- Integrations: Salesforce, HubSpot, CRM, API needs
- Use Case: What documents? (proposals, contracts, quotes)
- Industry: Healthcare, legal, real estate, finance

### Priority 2: Conversation Insights
- Primary Pain Points: What's broken in their process?
- Friction Encountered: Where did they get stuck?
- Questions Asked: What did they want to learn?
- Feature Interest: Which capabilities resonated?

### Priority 3: Sales Intelligence
- Urgency: Timeline for decision
- Current Tool: What they use now
- Decision Authority: Buyer, influencer, or needs approval

### Always Included: Outcome
- Call Result: Qualified/Self-serve/Needed help/Dropped off
- Next Steps: Meeting booked/Exploring/Follow-up/No action

## Example Output

### Input (Raw Transcript)
```
AGENT: Hi! I'm Sarah from PandaDoc. How's your trial going?
USER: Good! We're a sales team of 8 people trying to streamline proposals.
AGENT: That's great. How many proposals do you send monthly?
USER: About 150. We're currently using manual Word docs and it's painful.
AGENT: I see. Do you use a CRM like Salesforce?
USER: Yes, we use Salesforce. Can PandaDoc sync with it?
AGENT: Absolutely! Would you like to schedule a call with our sales team?
USER: Yes, let's book something for next week.
```

### Output (AI Summary)
```
QUALIFICATION SIGNALS:
• Team Size: 8 users (sales team) - QUALIFIED
• Document Volume: ~150 proposals/month - QUALIFIED
• Integrations: Salesforce mentioned - QUALIFIED
• Use Case: Sales proposals
• Industry: Not specified

CONVERSATION INSIGHTS:
• Primary Pain Point: Manual Word doc creation is slow/painful
• Friction: None mentioned
• Questions Asked: Salesforce integration capabilities
• Feature Interest: CRM sync, proposal automation

SALES INTELLIGENCE:
• Urgency: Medium (next week timeline)
• Current Tool: Manual Word docs
• Decision Authority: Not specified

OUTCOME:
• Call Result: Qualified for sales (3 qualification signals met)
• Next Steps: Meeting booked for next week
```

## Cost Analysis

**Per-call cost breakdown:**
- Input: ~2,000 tokens (8,000 chars transcript)
- Output: ~250 tokens (1,000 chars summary)
- Total: ~$0.0003 per call

**Monthly cost (1,000 calls):**
- Total: ~$0.30/month

**Comparison to raw transcripts:**
- Storage savings: 87% reduction (8,000 → 1,000 chars)
- Readability: Sales team scans in 30 seconds vs 5 minutes
- Actionability: Immediate qualification status visible

## Fallback Behavior

If `OPENAI_API_KEY` is not set or API fails:
- Script uses raw transcript instead
- Truncates to 32,000 characters (Salesforce limit)
- Logs warning but continues processing
- No summarization errors break the sync

## Configuration

### Required Environment Variable
```bash
OPENAI_API_KEY=sk-...  # Get from https://platform.openai.com/api-keys
```

### Optional Tuning (Future)
The script could be extended to support:
```bash
# Model selection
SUMMARY_MODEL=gpt-5-nano  # or gpt-5-mini, gpt-4o-mini

# Reasoning depth
SUMMARY_REASONING_EFFORT=medium  # minimal, low, medium, high

# Output detail
SUMMARY_VERBOSITY=medium  # low, medium, high

# Token limit
SUMMARY_MAX_TOKENS=1000  # Adjust for longer/shorter summaries
```

## Monitoring

### Success Indicators
- Summary length: 200-600 words typical
- Processing time: <5 seconds per call
- Cost: <$0.001 per call
- Qualification signals extracted: 70%+ of calls

### Warning Signs
- Summary too short (<50 chars): Model failed, check logs
- Summary too long (>1000 chars): Token limit issue
- Cost spike: Model or pricing changed
- Missing qualification signals: Prompt may need tuning

## Prompt Engineering

The system prompt is optimized for PandaDoc trial success:
- Aligned with agent's qualification framework (5+ users, 100+ docs, integrations)
- Structured output format for consistent parsing
- Priority-based information extraction
- Concise but actionable summaries

**Key prompt features:**
1. Clear priority hierarchy (qualification → insights → intelligence)
2. Specific threshold flags (5+ users, 100+ docs)
3. Structured bullet point format
4. Length constraint (under 400 words)
5. Emphasis on numbers and specific tools mentioned

## Future Enhancements

Potential improvements:
1. **Sentiment analysis:** Track user satisfaction and frustration
2. **Intent classification:** Categorize call types (support, sales, churn)
3. **Entity extraction:** Pull company names, competitor mentions
4. **Follow-up suggestions:** AI-recommended next actions
5. **Quality scoring:** Rate call quality and agent performance

## References

- Script location: `scripts/sync_to_salesforce.py`
- Function: `summarize_transcript()` (lines 85-154)
- Prompt: System message (lines 121-145)
- Model docs: [OpenAI GPT-5 Series](https://platform.openai.com/docs/models/gpt-5-mini)
