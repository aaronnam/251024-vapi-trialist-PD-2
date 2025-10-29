# PandaDoc Trial Success Voice Agent

A comprehensive voice AI agent project built with LiveKit Agents to enhance trial user success and activation for PandaDoc.

## Overview

This project implements an intelligent voice AI assistant designed to guide PandaDoc trial users through their onboarding journey. The agent provides personalized support, answers questions, and helps users discover key features to maximize trial success and conversion.

**Key Capabilities:**
- Natural conversational interactions via phone or web interface
- Contextual guidance based on user behavior and trial stage
- Real-time integration with PandaDoc systems
- Multi-channel support (telephony, web, mobile)
- Comprehensive testing and evaluation framework

## Quick Start

To get started with development:

1. Navigate to the agent application:
   ```bash
   cd my-app
   ```

2. Follow the setup instructions in [my-app/README.md](my-app/README.md)

3. For detailed development guidance, see [my-app/AGENTS.md](my-app/AGENTS.md)

## Repository Structure

```
251024-vapi-trialist-PD-2/
│
├── CLAUDE.md                         # Guide for AI coding assistants
├── README.md                         # This file - project overview
│
├── my-app/                           # LiveKit Agents voice AI application
│   ├── src/                          # Agent source code
│   ├── tests/                        # Test suites and evaluations
│   ├── README.md                     # Quick start guide
│   └── AGENTS.md                     # Development best practices
│
├── docs/                             # Permanent reference documentation
│   ├── specs/                        # Product specifications
│   │   ├── README.md                 # Specification index
│   │   ├── PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md
│   │   ├── PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md
│   │   └── VAPI_DASHBOARD_PANDADOC_FILLED.md
│   │
│   ├── implementation/               # Implementation guides & plans
│   │   ├── README.md                 # Implementation overview
│   │   ├── IMPLEMENTATION_PLAN.md    # Detailed implementation roadmap
│   │   ├── REQUIREMENTS_MAP.md       # Spec → LiveKit mapping
│   │   ├── REQUIREMENTS_MATRIX.csv   # Requirement traceability
│   │   ├── ANALYSIS.md               # ROI analysis & timeline
│   │   │
│   │   ├── features/                 # Feature implementation guides
│   │   │   ├── README.md             # Feature index
│   │   │   ├── email-tracking/       # Email capture & metadata
│   │   │   └── silence-detection/    # Silence detection
│   │   │
│   │   ├── integrations/             # Third-party integrations
│   │   │   ├── README.md             # Integration index
│   │   │   └── unleash/              # Feature flagging platform
│   │   │
│   │   ├── analytics/                # Analytics pipeline & data flow
│   │   │   ├── README.md
│   │   │   ├── 01-DEPLOYMENT_REFERENCE.md
│   │   │   ├── architecture/
│   │   │   ├── guides/
│   │   │   └── project-history/
│   │   │
│   │   └── observability/            # Monitoring & tracing strategy
│   │       ├── README.md
│   │       ├── OBSERVABILITY_STRATEGY.md
│   │       └── QUICK_IMPLEMENTATION.md
│   │
│   ├── security/                     # Security & risk analysis
│   │   ├── README.md                 # Security index
│   │   ├── PRODUCTION_READINESS.md   # Production readiness checklist
│   │   ├── AGENT_RISK_MITIGATION_TASKS.md
│   │   ├── MITIGATION_IMPLEMENTATION_GUIDE.md
│   │   └── assessments/              # Detailed risk assessments
│   │
│   └── research/                     # Technical research & deep dives
│       ├── README.md                 # Research overview
│       ├── livekit/                  # LiveKit framework research
│       └── quick-references/         # Quick reference guides
│
├── .project-status/                  # Task tracking & coordination
│   ├── README.md                     # Task tracking guide
│   ├── completed-tasks/              # Archive of finished work
│   └── coordination/                 # Team communications
│
├── anthropic-agent-guides/           # Anthropic best practices
│
└── .gitignore                        # Git ignore rules
```

## Documentation Navigation

### For AI Coding Assistants
- **[CLAUDE.md](CLAUDE.md)** - Quick reference for AI coding assistants working on this project
- **[my-app/AGENTS.md](my-app/AGENTS.md)** - Comprehensive guide for developing with LiveKit Agents

### For Implementation
- **[docs/implementation/IMPLEMENTATION_PLAN.md](docs/implementation/IMPLEMENTATION_PLAN.md)** - Complete implementation plan with phases and milestones
- **[docs/implementation/REQUIREMENTS_MAP.md](docs/implementation/REQUIREMENTS_MAP.md)** - Detailed requirements mapping and traceability
- **[docs/implementation/ANALYSIS.md](docs/implementation/ANALYSIS.md)** - Requirements analysis and technical considerations

### For Technical Research
- **[docs/research/livekit/](docs/research/livekit/)** - LiveKit-specific research and learnings
- **[docs/research/quick-references/](docs/research/quick-references/)** - Quick reference materials

### For Product Specifications
- **[docs/specs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md](docs/specs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md)** - Complete product specification
- **[docs/specs/PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md](docs/specs/PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md)** - Streamlined specification
- **[docs/specs/README.md](docs/specs/README.md)** - Specifications overview

## Key Documents

### Product Specifications
- **[Specifications Overview](docs/specs/README.md)** - Navigation guide for all specs
- **[Complete Specification](docs/specs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md)** - Full requirements and design
- **[Streamlined Specification](docs/specs/PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md)** - Quick reference version

### Implementation Planning
- **[Implementation Plan](docs/implementation/IMPLEMENTATION_PLAN.md)** - Comprehensive roadmap with 9 epics
- **[Requirements Map](docs/implementation/REQUIREMENTS_MAP.md)** - Detailed spec-to-code mapping
- **[Requirements Matrix](docs/implementation/REQUIREMENTS_MATRIX.csv)** - Requirement traceability
- **[Implementation Overview](docs/implementation/README.md)** - Guide to implementation docs

### Features & Integration
- **[Feature Implementation Guides](docs/implementation/features/README.md)** - Email tracking, silence detection, etc.
- **[Third-Party Integrations](docs/implementation/integrations/README.md)** - Unleash, Salesforce, etc.

### Security & Observability
- **[Security & Risk Analysis](docs/security/README.md)** - Risk assessment and mitigations
- **[Production Readiness](docs/security/PRODUCTION_READINESS.md)** - Deployment checklist
- **[Observability Strategy](docs/implementation/observability/README.md)** - Monitoring and tracing

### Analytics & Research
- **[Analytics Pipeline](docs/implementation/analytics/README.md)** - Data flow and deployment
- **[Research Documentation](docs/research/README.md)** - Technical deep dives
- **[Quick References](docs/research/quick-references/README.md)** - Condensed guides

## Getting Help

### I want to...

**...get started quickly**
- Read [my-app/README.md](my-app/README.md) for setup instructions
- Review [my-app/AGENTS.md](my-app/AGENTS.md) for development best practices

**...understand the product requirements**
- Start with [docs/specs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md](docs/specs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md)
- Review [docs/implementation/REQUIREMENTS_MAP.md](docs/implementation/REQUIREMENTS_MAP.md) for detailed mapping

**...implement a specific feature**
- Check [docs/implementation/features/](docs/implementation/features/) for feature-specific guides
- Review [docs/implementation/IMPLEMENTATION_PLAN.md](docs/implementation/IMPLEMENTATION_PLAN.md) for the overall roadmap
- Use [docs/implementation/REQUIREMENTS_MAP.md](docs/implementation/REQUIREMENTS_MAP.md) for spec-to-code mapping

**...set up integrations with third-party services**
- Review [docs/implementation/integrations/README.md](docs/implementation/integrations/README.md) for available integrations
- Check integration-specific guides in [docs/implementation/integrations/](docs/implementation/integrations/)

**...learn about LiveKit Agents**
- Read [my-app/AGENTS.md](my-app/AGENTS.md) for project-specific guidance
- Browse [docs/research/livekit/](docs/research/livekit/) for research materials
- Install the [LiveKit Docs MCP server](https://docs.livekit.io/mcp) for integrated documentation

**...write tests**
- See [my-app/AGENTS.md](my-app/AGENTS.md) for testing best practices
- Check existing tests in [my-app/tests/](my-app/tests/)
- Review [docs/research/quick-references/testing-quick-ref.md](docs/research/quick-references/testing-quick-ref.md)

**...understand security & risks**
- Review [docs/security/README.md](docs/security/README.md) for risk overview
- Check [docs/security/PRODUCTION_READINESS.md](docs/security/PRODUCTION_READINESS.md) before deployment
- Read [docs/security/AGENT_RISK_MITIGATION_TASKS.md](docs/security/AGENT_RISK_MITIGATION_TASKS.md) for mitigation tasks

**...understand the architecture**
- Review [docs/implementation/ANALYSIS.md](docs/implementation/ANALYSIS.md)
- Check [docs/implementation/IMPLEMENTATION_PLAN.md](docs/implementation/IMPLEMENTATION_PLAN.md)
- Read [docs/implementation/observability/OBSERVABILITY_STRATEGY.md](docs/implementation/observability/OBSERVABILITY_STRATEGY.md)
- Review [docs/implementation/analytics/](docs/implementation/analytics/) for data pipeline
- Read the technical research in [docs/research/](docs/research/)

**...work with AI coding assistants**
- Read [CLAUDE.md](CLAUDE.md) for quick reference
- Follow [my-app/AGENTS.md](my-app/AGENTS.md) for development patterns
- Review [anthropic-agent-guides/](anthropic-agent-guides/) for best practices

## Technology Stack

- **Voice AI Framework:** LiveKit Agents (Python)
- **Package Manager:** uv
- **AI Models:** OpenAI (LLM), Cartesia (TTS), AssemblyAI (STT)
- **Infrastructure:** LiveKit Cloud
- **Testing:** pytest with LiveKit evaluation framework

## Development Workflow

1. **Setup:** Follow [my-app/README.md](my-app/README.md)
2. **Plan:** Review [docs/implementation/IMPLEMENTATION_PLAN.md](docs/implementation/IMPLEMENTATION_PLAN.md)
3. **Implement:** Follow TDD approach per [my-app/AGENTS.md](my-app/AGENTS.md)
4. **Test:** Run `uv run pytest` from my-app directory
5. **Deploy:** Follow production deployment guide in [my-app/README.md](my-app/README.md)

## Contributing

When working on this project:
- Always use test-driven development (TDD)
- Maintain code formatting with ruff: `uv run ruff format` and `uv run ruff check`
- Update tests when modifying agent behavior
- Document significant changes in relevant documentation files
- Follow patterns in [anthropic-agent-guides/](anthropic-agent-guides/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Project Status:** Active Development
**Last Updated:** October 2025
**Contact:** For questions or support, refer to the documentation or raise an issue in the repository.
