# Documentation

This directory contains feature-specific documentation and implementation guides for the PandaDoc Voice Agent.

## Features

### [features/](./features/)
Implementation guides and technical documentation for voice agent features.

- **[error-recovery/](./features/error-recovery/)** - Error handling patterns and graceful failure recovery
  - Production-ready circuit breakers, retry logic, and error responses
  - Ensures agent maintains conversation flow despite service failures

- **[google-calendar-booking/](./features/google-calendar-booking/)** - Meeting booking integration
  - Google Calendar API integration for qualified lead meetings
  - Qualification-driven booking with natural conversational flow

## Archived Documentation

### [.archived/](../.archived/)
Historical work-in-progress notes and debugging records preserved for reference.

These documents are preserved for historical context but are not part of the active development guides:
- Test failure analysis from debugging sessions
- Detailed debugging notes
- Historical test results

**Use these for**: Understanding past issues if similar problems recur, or reviewing how problems were solved.

## Getting Started

1. **Start with** [../AGENTS.md](../AGENTS.md) - Core development guide
2. **Find feature docs** in `features/[feature-name]/` directories
3. **Each feature has**:
   - `README.md` - Feature overview
   - Implementation guides (e.g., GUIDE.md, DESIGN.md)
   - Implementation notes if available

## Related Documentation

- **Development Guide**: [../AGENTS.md](../AGENTS.md)
- **Project Setup**: [../README.md](../README.md)
- **Deployment**: [../DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md)

---

**Last Updated**: October 29, 2025
