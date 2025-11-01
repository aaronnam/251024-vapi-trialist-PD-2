# Calendar Tool Invocation Verification Guide

## The Critical Challenge

**Core Problem**: Verifying that an LLM agent actually calls a specific tool is non-deterministic. We need multiple verification strategies to ensure the `book_sales_meeting` tool is invoked when qualified users request meetings.

## Quick Start

```bash
# Run the focused invocation tests
uv run python tests/test_calendar_tool_invocation.py

# Or with pytest
uv run pytest tests/test_calendar_tool_invocation.py -v
```

## Verification Strategies

### Strategy 1: Function Call Event Detection
```python
# Check if the agent emits a function_call event
event = result.expect.next_event()
if hasattr(event, 'is_function_call'):
    event.is_function_call(name="book_sales_meeting")
    # ✅ Tool was called
```

### Strategy 2: Mock Calendar API Tracking
```python
# Track if the Google Calendar API is actually invoked
calendar_api_called = False

def track_insert(*args, **kwargs):
    nonlocal calendar_api_called
    calendar_api_called = True
    # Return mock result...

# Later assert:
assert calendar_api_called, "Calendar API never invoked - tool didn't execute!"
```

### Strategy 3: Tool Method Interception
```python
# Replace the tool method with a tracking wrapper
original_method = agent.book_sales_meeting
invocation_count = 0

async def tracking_wrapper(context, **kwargs):
    nonlocal invocation_count
    invocation_count += 1
    print(f"🎯 TOOL INVOKED with: {kwargs}")
    return await original_method(context, **kwargs)

agent.book_sales_meeting = tracking_wrapper
```

## Critical Test Scenarios

### 1. Team Size Qualification (≥5 users)
```python
# Setup
agent.discovered_signals = {"team_size": 8}

# Prompt
"We have 8 sales reps using PandaDoc. Let's schedule a call to discuss enterprise features."

# Verification
✅ Tool MUST be called
✅ Calendar API MUST be invoked
✅ Response MUST confirm booking
```

### 2. Volume Qualification (≥100 docs/month)
```python
# Setup
agent.discovered_signals = {"monthly_volume": 200}

# Prompt
"We process over 200 contracts monthly. I'd like to schedule a meeting about enterprise pricing."

# Verification
✅ Tool MUST be called
✅ Meeting details MUST be returned
```

### 3. Salesforce Integration
```python
# Setup
agent.discovered_signals = {"integration_needs": ["salesforce"]}

# Prompt
"We use Salesforce CRM. Can we book a call to discuss the integration?"

# Verification
✅ Tool MUST be called
✅ Event description MUST include "salesforce"
```

### 4. API/Embedded Needs
```python
# Setup
agent.discovered_signals = {"integration_needs": ["api"]}

# Prompt
"We need API access for programmatic document generation. Schedule a technical discussion?"

# Verification
✅ Tool MUST be called
✅ API qualification MUST be captured
```

### 5. Date/Time Preferences
```python
# Setup
agent.discovered_signals = {"team_size": 10}

# Prompt
"Our 10-person team uses HubSpot. Can we book a meeting tomorrow at 2pm?"

# Verification
✅ Tool MUST be called with preferred_date="tomorrow", preferred_time="2pm"
✅ Calendar event MUST have correct datetime
```

### 6. Multiple Qualification Signals
```python
# Setup
agent.discovered_signals = {
    "team_size": 15,
    "integration_needs": ["salesforce", "api"],
    "urgency": "high"
}

# Prompt
"Our 15-person tech team needs Salesforce integration urgently. Book a call ASAP."

# Verification
✅ Tool MUST be called immediately
✅ High priority MUST be reflected
```

## Implementation Pattern

```python
@pytest.mark.asyncio
async def test_tool_actually_invoked():
    """The definitive test that tool is called"""

    async with _llm() as llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # 1. SET QUALIFICATION SIGNALS
        agent.discovered_signals = {
            "team_size": 8,  # Qualified
            "qualification_tier": "sales_ready"
        }

        # 2. MOCK CALENDAR SERVICE
        calendar_invoked = False

        with patch.object(agent, '_get_calendar_service') as mock_service:
            def track_calendar_call(*args, **kwargs):
                nonlocal calendar_invoked
                calendar_invoked = True
                # Return mock event...

            # Setup mock chain
            mock_service.return_value.events.return_value.insert = track_calendar_call

            # 3. START SESSION & RUN PROMPT
            await session.start(agent)
            result = await session.run(
                user_input="We have 8 reps. Schedule a sales call."
            )

            # 4. VERIFY TOOL WAS CALLED
            # Method A: Check function call event
            event = result.expect.next_event()
            event.is_function_call(name="book_sales_meeting")

            # Method B: Verify calendar was invoked
            assert calendar_invoked, "Tool did not execute!"

            # Method C: Check response mentions booking
            await result.expect.contains_message(role="assistant").judge(
                llm,
                intent="Confirms meeting is scheduled"
            )
```

## Key Verification Points

### ✅ MUST VERIFY
1. **Tool is actually invoked** (not just considered)
2. **Correct parameters are passed** (customer_name, date, time)
3. **Calendar API is called** (proves execution)
4. **Response confirms booking** (user feedback)

### ❌ NOT SUFFICIENT
- Only checking the response text
- Only looking for keywords
- Testing unqualified scenarios
- Assuming tool was called without verification

## Troubleshooting Non-Deterministic Behavior

### Issue: Tool not called consistently

**Solutions:**
1. **Make prompt more explicit**: "Schedule a call" → "Book a sales meeting now"
2. **Ensure qualification is clear**: Set `qualification_tier = "sales_ready"`
3. **Add urgency**: "We need to book this today"
4. **Mention specific features**: "discuss enterprise pricing"

### Issue: Can't detect tool invocation

**Solutions:**
1. Use multiple verification methods simultaneously
2. Add logging inside the tool method itself
3. Mock at different levels (tool method, calendar API, HTTP client)
4. Check agent session's tool call history if available

### Issue: Parameters not captured correctly

**Solutions:**
1. Mock the tool to capture exact parameters
2. Intercept the calendar event creation
3. Parse the function call event arguments
4. Add assertions on the event description content

## Success Criteria

Tests pass when:

1. **100% tool invocation rate** for qualified users with booking intent
2. **Correct parameter extraction** (name, email, date/time preferences)
3. **Calendar API called** (proves end-to-end execution)
4. **No false negatives** (tool always called when it should be)

## Running the Tests

```bash
# Basic run
uv run pytest tests/test_calendar_tool_invocation.py

# With verbose output
uv run pytest tests/test_calendar_tool_invocation.py -v

# With coverage
uv run pytest tests/test_calendar_tool_invocation.py --cov=src.agent

# Run specific test
uv run pytest tests/test_calendar_tool_invocation.py::test_qualified_team_size_books_meeting

# Run with detailed logging
uv run pytest tests/test_calendar_tool_invocation.py -v -s --log-cli-level=INFO
```

## Key Insight

The most reliable verification combines:
1. **Function call event detection** (agent's intent)
2. **Calendar API mocking** (actual execution)
3. **Tool method interception** (direct invocation tracking)

Using all three methods ensures we catch the tool invocation regardless of how the agent internals work.