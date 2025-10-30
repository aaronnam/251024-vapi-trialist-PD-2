# PandaDoc Agent Testing Guide

## Quick Start

### 1. Setup Environment
```bash
# From my-app directory
cd /Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/my-app

# Install dependencies if needed
uv sync

# Set up test environment variables
export OPENAI_API_KEY="your-key-here"  # Required for LLM judge
```

### 2. Run All Tests
```bash
# Run comprehensive test suite
uv run pytest tests/test_pandadoc_comprehensive.py -v

# Run with verbose output for debugging
LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_pandadoc_comprehensive.py -s

# Run specific test category
uv run pytest tests/test_pandadoc_comprehensive.py::test_consent_accepted_flow -v
```

### 3. Manual Console Testing
```bash
# Test interactively in console
uv run python src/agent.py console

# Then use prompts from TEST_PROMPTS_CATALOG.md
```

## Testing Philosophy

### Core Principles
1. **Test Behavior, Not Implementation** - Focus on what the agent does, not how
2. **Use LLM Judge for Intent** - Verify meaning, not exact wording
3. **Mock External Dependencies** - Test agent logic, not third-party services
4. **Test Edge Cases First** - Happy paths usually work; edge cases break

### What Makes a Good Test
- **Specific Intent**: Clear about what behavior is expected
- **Isolated**: Tests one behavior at a time
- **Fast**: Uses mocks to avoid network calls
- **Reliable**: Not flaky or dependent on timing

## Test Categories Explained

### 1. Consent Protocol Tests
**Why Critical**: Legal compliance requirement
**What to Test**:
- Clear consent acceptance → proceeds
- Clear decline → stops gracefully
- Questions → explains and re-asks
- Ambiguous → clarifies

**Red Flags**:
- ❌ Proceeding without clear consent
- ❌ Not explaining why transcription is needed
- ❌ Continuing after user declines

### 2. Knowledge Base Search Tests
**Why Critical**: Cost management and response quality
**What to Test**:
- Greetings → NO search
- PandaDoc questions → YES search
- Search failures → graceful fallback

**Red Flags**:
- ❌ Searching for "Hi" or "Thanks"
- ❌ Not searching for product questions
- ❌ Crashing on API timeout

### 3. Qualification Tests
**Why Critical**: Business routing logic
**What to Test**:
- Team size ≥ 5 → qualified
- Volume ≥ 100/mo → qualified
- Salesforce/HubSpot → qualified
- Small/personal → self-serve

**Red Flags**:
- ❌ Missing qualification signals
- ❌ Offering sales to unqualified users
- ❌ Not recognizing enterprise needs

### 4. Sales Booking Tests
**Why Critical**: Resource allocation
**What to Test**:
- Qualified + request → books meeting
- Unqualified + request → self-serve guidance
- Email handling → uses stored email

**Red Flags**:
- ❌ Booking for unqualified users
- ❌ Not booking for qualified users
- ❌ Exposing booking errors to user

### 5. Instruction Adherence Tests
**Why Critical**: Prevents hallucination
**What to Test**:
- Off-topic → redirects to PandaDoc
- Unknown features → doesn't invent
- Voice responses → concise 2-3 sentences

**Red Flags**:
- ❌ Answering about weather/news
- ❌ Making up features
- ❌ Long explanations for voice

## Using the Test Prompts Catalog

### Manual Testing Process
1. Start console: `uv run python src/agent.py console`
2. Open `TEST_PROMPTS_CATALOG.md`
3. Work through each category systematically
4. Document any failures

### Coverage Checklist
```
□ Consent: All 4 types (affirmative, decline, questions, ambiguous)
□ Qualification: Each signal type (team, volume, integration)
□ Search: Both should/shouldn't search cases
□ Booking: Qualified and unqualified scenarios
□ Adherence: Off-topic and hallucination probes
□ Recovery: Error handling paths
□ Flow: Multi-turn conversations
□ Voice: Conciseness and interruptions
□ Edge: Unusual requests
□ Security: Information fishing attempts
```

## Automated Testing

### Running the Comprehensive Suite
```bash
# Full suite with all categories
uv run pytest tests/test_pandadoc_comprehensive.py

# Just consent tests
uv run pytest tests/test_pandadoc_comprehensive.py -k "consent"

# Just qualification tests
uv run pytest tests/test_pandadoc_comprehensive.py -k "qualification"

# Just tool usage tests
uv run pytest tests/test_pandadoc_comprehensive.py -k "search or book"
```

### Understanding Test Results

#### LLM Judge Results
```python
# Good: Judge confirms intent matched
await result.expect.judge(llm, intent="Greets user friendly")
✅ PASS: LLM confirmed friendly greeting

# Bad: Judge rejects response
❌ FAIL: LLM says "Response was not friendly"
```

#### Function Call Assertions
```python
# Checking tool was called
result.expect.next_event().is_function_call(name="unleash_search_knowledge")

# Checking tool was NOT called
result.expect.no_function_calls()
```

### Adding New Tests

Template for new test:
```python
@pytest.mark.asyncio
async def test_your_new_scenario():
    """What behavior you're testing"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        # Setup
        await session.start(PandaDocTrialistAgent())

        # Action
        result = await session.run(user_input="Your test prompt")

        # Assertion
        await result.expect.next_event().is_message(role="assistant").judge(
            llm,
            intent="Expected behavior description"
        )
```

## Debugging Failed Tests

### 1. Enable Verbose Output
```bash
LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_pandadoc_comprehensive.py::test_that_failed -s
```

### 2. Check Console Manually
```bash
# Test the exact same prompt manually
uv run python src/agent.py console
> Your test prompt here
# See actual response
```

### 3. Add Print Debugging
```python
# In your test
result = await session.run(user_input="Test")
print(f"Events: {result.events}")  # See what actually happened
```

### 4. Mock Inspection
```python
# See what the mock was called with
with mock_tools(PandaDocTrialistAgent, {
    "unleash_search_knowledge": lambda **kwargs: {
        print(f"Called with: {kwargs}")  # Debug mock calls
        return {"answer": "test"}
    }
}):
```

## Common Issues and Solutions

### Issue: Tests Time Out
**Solution**: Add timeout parameter
```python
result = await session.run(user_input="Test", timeout=30)
```

### Issue: Flaky LLM Judge
**Solution**: Make intent more specific
```python
# Bad: Too vague
intent="Responds appropriately"

# Good: Specific
intent="Declines to answer weather question and redirects to PandaDoc topics"
```

### Issue: Tool Not Called
**Solution**: Check agent state
```python
# Agent might need consent first
await session.run(user_input="Hi")
await session.run(user_input="Yes")  # Give consent
# Now test actual behavior
```

### Issue: Different Behavior in Production
**Solution**: Check for environment differences
- API keys configured?
- Mock behavior matches real service?
- Agent initialization parameters?

## Performance Testing

### Load Testing Pattern
```python
@pytest.mark.asyncio
async def test_handles_rapid_questions():
    """Test agent handles multiple rapid questions"""
    async with _llm() as llm, AgentSession(llm=llm) as session:
        await session.start(PandaDocTrialistAgent())

        # Rapid fire questions
        questions = [
            "How do I create a template?",
            "What about signatures?",
            "And payment collection?",
        ]

        for q in questions:
            result = await session.run(user_input=q)
            # Should handle all gracefully
            assert result.events  # Has some response
```

### Latency Testing
```python
import time

start = time.time()
result = await session.run(user_input="How do I add signatures?")
latency = time.time() - start

# Voice target: < 2 seconds total
assert latency < 2.0, f"Response took {latency:.2f}s"
```

## CI/CD Integration

### GitHub Actions Setup
```yaml
# .github/workflows/test.yml
name: Test Agent
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
        working-directory: ./my-app
      - name: Run tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: uv run pytest tests/test_pandadoc_comprehensive.py
        working-directory: ./my-app
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
cd my-app
uv run pytest tests/test_pandadoc_comprehensive.py::test_consent_accepted_flow
if [ $? -ne 0 ]; then
  echo "Tests failed! Fix before committing."
  exit 1
fi
```

## Best Practices Summary

### DO ✅
- Test behavior, not exact wording
- Use mocks for external services
- Test edge cases thoroughly
- Keep tests fast and isolated
- Use TEST_PROMPTS_CATALOG.md systematically
- Run tests before deploying

### DON'T ❌
- Test implementation details
- Rely on network services
- Write vague intent descriptions
- Skip error scenarios
- Test everything in one function
- Deploy without testing

## Quick Test Commands Reference

```bash
# Run all tests
uv run pytest tests/test_pandadoc_comprehensive.py

# Run with debug output
LIVEKIT_EVALS_VERBOSE=1 uv run pytest -s

# Run specific category
uv run pytest -k "consent"
uv run pytest -k "qualification"
uv run pytest -k "search"
uv run pytest -k "booking"

# Run single test
uv run pytest tests/test_pandadoc_comprehensive.py::test_consent_accepted_flow

# Run with coverage
uv run pytest --cov=agent tests/

# Run in watch mode (requires pytest-watch)
uv run ptw tests/test_pandadoc_comprehensive.py

# Interactive console testing
uv run python src/agent.py console
```