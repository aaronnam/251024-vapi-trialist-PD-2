# Third-Party Integrations

This directory contains documentation for integrating the PandaDoc Voice Agent with third-party platforms and services.

## Current Integrations

### [unleash/](./unleash/)
**Feature flagging and experimentation platform**

Unleash integration enables feature flags and A/B testing for the voice agent.

**Files:**
- `00-README.md` - Unleash overview and quick start
- `API_REFERENCE.md` - Unleash API reference for agent integration
- `FEATURE_FLAGGING_GUIDE.md` - How to implement feature flags
- `INTERCOM_SOURCE_FILTERING.md` - Filtering and source management
- Images and reference materials

**Key Points:**
- Feature flag evaluation in agent
- A/B testing support
- Remote configuration management
- Gradual feature rollouts

**Status**: Research & Planning

---

## Integration Categories

### Data & Analytics
- **Salesforce** - Lead management and CRM integration (referenced in implementation plan)
- **HubSpot** - Activity logging and engagement tracking
- **Amplitude** - Product usage intelligence and analytics
- **Snowflake** - Data warehouse and analytics (see [../analytics/](../analytics/))

### Platforms
- **Unleash** - Feature flags and experimentation
- **ChiliPiper** - Meeting booking and routing
- **LiveKit** - Voice infrastructure (core dependency)

### Communication
- **Email Systems** - Lead follow-up and communication
- **SMS/Telephony** - Call routing and inbound management

---

## Adding New Integrations

When documenting a new integration:

1. **Create a subdirectory** under `integrations/` with the platform name (lowercase)
2. **Create README.md** with platform overview
3. **Add supporting files** for API reference, guides, configuration
4. **Include code examples** for the Python agent
5. **Document error handling** and fallback patterns

Template structure:
```
platform-name/
├── README.md                    # Overview & quick start
├── API_REFERENCE.md            # API documentation
├── IMPLEMENTATION_GUIDE.md      # Step-by-step integration
└── examples/                    # Code examples
    └── agent-integration.py
```

---

## Integration Best Practices

### Error Handling
- Always implement graceful degradation
- Log integration errors without breaking agent flow
- Provide fallback behavior when integration unavailable

### Configuration
- Store API keys and credentials in environment variables
- Support multiple deployment environments
- Document all required configuration

### Testing
- Include integration tests in [../../../my-app/tests/](../../../my-app/tests/)
- Mock external APIs in unit tests
- Document testing procedures

### Monitoring
- Log integration calls for debugging
- Track integration success/failure rates
- Alert on integration failures

---

## Related Documentation

- **Implementation Plan**: [../IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md)
- **Requirements Mapping**: [../REQUIREMENTS_MAP.md](../REQUIREMENTS_MAP.md)
- **Analytics Pipeline**: [../analytics/](../analytics/)
- **Agent Code**: [../../../my-app/src/](../../../my-app/src/)

---

**Last Updated**: October 29, 2025
