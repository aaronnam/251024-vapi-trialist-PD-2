# LiveKit Voice Agent Tool Testing Questions

## Testing Guide
- Run the agent with verbose logging enabled: `uv run python src/agent.py console --verbose`
- Watch for tool invocation logs: `Tool call: <tool_name>`
- Check for errors in the console output
- Verify state changes in agent's internal tracking

---

## 1. Unleash Knowledge Search Tool (`unleash_search_knowledge`)

### Question 1.1: Basic Feature Search
**Ask:** "How do I create a template in PandaDoc?"

**Expected Behavior:**
- Tool should be invoked with `query="How do I create a template in PandaDoc?"` and `category="features"`
- Agent should say "Let me find that for you..." before searching
- Should return answer with suggested next action (likely "offer_walkthrough")
- Response format should default to "concise"

**Error Indicators:**
- No "Let me find that for you..." message = tool not called
- Timeout error = API connection issue (check UNLEASH_API_KEY env var)
- Empty results = API endpoint or query format issue

**Tracing:**
```python
# Look for in logs:
"Tool call: unleash_search_knowledge"
"Unleash API error:" # If error occurs
```

### Question 1.2: Integration Information Request
**Ask:** "Does PandaDoc integrate with Salesforce and what are the pricing options?"

**Expected Behavior:**
- Tool should be called twice or with combined query
- Should identify "integration" and "pricing" keywords
- Action should be "check_specific_integration" or "discuss_roi"
- May switch to "detailed" response format for comprehensive info

**Error Indicators:**
- Only partial information returned = tool not recognizing both topics
- No follow-up suggestion = `_determine_next_action` helper not working

**Tracing:**
```python
# Check for multiple tool calls or combined processing:
"category": "integrations"
"category": "pricing"
```

### Question 1.3: API Failure Scenario
**Ask:** "What advanced analytics features does PandaDoc offer?" (with UNLEASH_API_KEY intentionally misconfigured)

**Expected Behavior:**
- Tool should attempt search and fail gracefully
- Should raise ToolError with message: "I'll help you another way..."
- Should offer alternatives (support team or walkthrough)
- No crash or unhandled exception

**Error Indicators:**
- Agent crashes = ToolError not properly handled
- Generic error message = Not using custom fallback messages
- No alternative offered = Fallback logic not implemented

**Tracing:**
```python
# Look for:
"ToolError:" # Should see this instead of crash
"Unleash API error:" # Should be logged
```

---

## 2. Calendar Management Agent Tool (`calendar_management_agent`)

### Question 2.1: Check Availability
**Ask:** "What times are you available for a demo tomorrow?"

**Expected Behavior:**
- Tool should parse "tomorrow" and determine this is an availability check
- Should say "Let me check the calendar for you..."
- Request should include natural language: "What times are you available for a demo tomorrow?"
- Should not require email for checking availability

**Error Indicators:**
- No calendar checking message = tool not invoked
- "handoff_initiated" without actual calendar check = sub-agent not implemented
- Request for email when just checking = logic error

**Tracing:**
```python
# Look for:
"Tool call: calendar_management_agent"
"request": "What times are you available for a demo tomorrow?"
```

### Question 2.2: Book a Meeting with Email
**Ask:** "Schedule a PandaDoc demo for next Tuesday at 2pm. My email is john.doe@company.com"

**Expected Behavior:**
- Tool should recognize booking intent
- Should extract email from the message
- Should pass both request and email to sub-agent
- Response should confirm booking details

**Error Indicators:**
- Email not captured = parameter parsing issue
- No confirmation = booking logic not complete
- Missing meeting details = sub-agent response not formatted

**Tracing:**
```python
# Check parameters:
"user_email": "john.doe@company.com"
"request": "Schedule a PandaDoc demo for next Tuesday at 2pm"
```

### Question 2.3: Ambiguous Request without Email
**Ask:** "I'd like to set up some time to go through the platform"

**Expected Behavior:**
- Tool should recognize scheduling intent
- Should handle missing specific time gracefully
- Should either prompt for email or indicate it's needed for booking
- Should ask for time preference

**Error Indicators:**
- Crashes due to missing email = poor None handling
- No follow-up questions = agent not handling ambiguity
- Proceeds without email = state management issue

**Tracing:**
```python
# Should see:
"user_email": null  # or None
# Agent should then ask for email/time preference
```

---

## 3. Qualification Signal Logging Tool (`log_qualification_signal`)

### Question 3.1: Team Size Discovery
**Ask:** "We have a sales team of 12 people who all need to send proposals"

**Expected Behavior:**
- Tool should be called with `signal_type="team_size"` and `value=12`
- Agent's internal state should update: `self.discovered_signals["team_size"] = 12`
- Should auto-determine qualification_tier as "sales_ready" (12 > 5)
- Should log: "Qualification signal: team_size=12"

**Error Indicators:**
- No tool invocation = agent not recognizing qualification signals
- State not updated = internal tracking broken
- Wrong tier = `_determine_qualification_tier` logic error

**Tracing:**
```python
# Look for:
"Tool call: log_qualification_signal"
"Qualification signal: team_size=12"
"qualification_tier": "sales_ready"
```

### Question 3.2: Integration Need Discovery
**Ask:** "We need this to sync with our Salesforce CRM automatically"

**Expected Behavior:**
- Tool called with `signal_type="integration"` and `value="salesforce"`
- Should append to integration_needs list
- Qualification tier should become "sales_ready" (Salesforce = enterprise)
- Event payload should include all discovered signals so far

**Error Indicators:**
- Integration not logged = keyword detection failing
- Not marked as sales_ready = tier logic not checking integrations
- Previous signals missing = state not persisting

**Tracing:**
```python
# Check for:
"signal_type": "integration"
"value": "salesforce"
"all_signals": {...}  # Should include team_size from previous question
```

### Question 3.3: Multiple Signals in One Statement
**Ask:** "We're a team of 8 sending about 150 documents per month, and the manual process is killing our productivity"

**Expected Behavior:**
- Multiple tool calls OR agent recognizes multiple signals
- Should log: team_size=8, volume=150, pain_point="manual process killing productivity"
- Qualification tier should be "sales_ready" (volume > 100)
- Each signal should update internal state

**Error Indicators:**
- Only one signal captured = agent missing multiple data points
- No pain_point logged = not recognizing qualitative signals
- State updates incomplete = partial processing

**Tracing:**
```python
# Should see multiple calls or batched update:
"signal_type": "team_size", "value": 8
"signal_type": "volume", "value": 150
"signal_type": "pain_point", "value": "manual process killing productivity"
# Final state should have all three
```

---

## General Debugging Tips

1. **Enable Verbose Logging:**
   ```bash
   export LOG_LEVEL=DEBUG
   uv run python src/agent.py console --verbose
   ```

2. **Check Tool Registration:**
   Look for startup logs showing tools are registered:
   ```
   Registered tool: unleash_search_knowledge
   Registered tool: calendar_management_agent
   Registered tool: log_qualification_signal
   ```

3. **Monitor State Changes:**
   Add debug prints in tools to see state:
   ```python
   logger.debug(f"Current signals: {self.discovered_signals}")
   ```

4. **Test Tool Isolation:**
   Test each tool individually before integration testing

5. **Check Environment Variables:**
   ```bash
   env | grep -E "UNLEASH|GOOGLE|OPENAI"
   ```

## Success Criteria

✅ All 9 questions trigger appropriate tool calls
✅ No unhandled exceptions or crashes
✅ State persists across multiple tool invocations
✅ Error messages are user-friendly, not technical
✅ Tools work together (e.g., qualification signals accumulate)
✅ Fallback behaviors work when APIs fail