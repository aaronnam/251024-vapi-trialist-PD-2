# Calendar Tool Testing - Quick Reference

## Run Tests
```bash
uv run pytest tests/test_calendar_tool_invocation.py -v
```

## Test Coverage

| Scenario | Setup | Expected | Status |
|----------|-------|----------|--------|
| Team Size ≥5 | `team_size: 8` | Tool called ✅ | PASSING |
| Volume ≥100 | `monthly_volume: 200` | Tool called ✅ | PASSING |
| Salesforce | `integration_needs: ["salesforce"]` | Tool called ✅ | PASSING |
| API Needs | `integration_needs: ["api"]` | Tool called ✅ | PASSING |
| Date/Time | `preferred_date: "tomorrow", time: "2pm"` | Parsed correctly ✅ | PASSING |
| Multi-Signal | `team_size: 15 + salesforce + high urgency` | Tool called ✅ | PASSING |

## Critical Setup
Every test must include:
```python
agent.user_email = "aaron.nam@pandadoc.com"
```

This simulates the email from participant metadata in production.

## What's Being Verified

1. **Tool is actually called** - Not just considered, but executed
2. **Correct parameters** - customer_name, email, date, time are passed
3. **Calendar API invoked** - Proves end-to-end execution
4. **Response confirms booking** - User feedback is provided

## Test Results
```
6 passed in 16.35s
```

All qualification scenarios verified. Tool is production-ready.