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
/Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/
│
├── my-app/                           # LiveKit Agents voice AI application
│   ├── src/                          # Agent source code
│   ├── tests/                        # Test suites and evaluations
│   ├── README.md                     # Quick start guide
│   └── AGENTS.md                     # Development best practices
│
├── docs/                             # Comprehensive documentation
│   ├── implementation/               # Implementation guides
│   │   ├── IMPLEMENTATION_PLAN.md    # Detailed implementation plan
│   │   ├── REQUIREMENTS_MAP.md       # Requirements mapping
│   │   ├── REQUIREMENTS_MATRIX.csv   # Requirements matrix
│   │   └── ANALYSIS.md               # Requirements analysis
│   │
│   ├── research/                     # Technical research
│   │   ├── livekit/                  # LiveKit-specific research
│   │   └── quick-references/         # Quick reference guides
│   │
│   └── specs/                        # Product specifications
│       ├── PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md
│       └── PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md
│
└── anthropic-agent-guides/           # Best practices for AI assistants
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
- **[docs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md](docs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md)** - Complete product specification
- **[docs/PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md](docs/PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md)** - Streamlined specification

## Key Documents

### Implementation Planning
- **[Implementation Plan](docs/implementation/IMPLEMENTATION_PLAN.md)** - Comprehensive plan covering all development phases
- **[Requirements Map](docs/implementation/REQUIREMENTS_MAP.md)** - Detailed mapping of requirements to implementation
- **[Requirements Matrix](docs/implementation/REQUIREMENTS_MATRIX.csv)** - Structured requirements matrix

### Testing and Quality
- **[TESTING_INTEGRATION_GUIDE.md](TESTING_INTEGRATION_GUIDE.md)** - Testing integration guide
- **[TESTING_DOCUMENTATION_INDEX.md](TESTING_DOCUMENTATION_INDEX.md)** - Testing documentation index
- **[TESTING_RESEARCH_SUMMARY.md](TESTING_RESEARCH_SUMMARY.md)** - Testing research summary

### Analysis and Research
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation summary
- **[INDEX_REQUIREMENTS_ANALYSIS.md](INDEX_REQUIREMENTS_ANALYSIS.md)** - Requirements analysis index
- **[RESEARCH_INDEX.md](RESEARCH_INDEX.md)** - Research materials index

## Getting Help

### I want to...

**...get started quickly**
- Read [my-app/README.md](my-app/README.md) for setup instructions
- Review [my-app/AGENTS.md](my-app/AGENTS.md) for development best practices

**...understand the product requirements**
- Start with [docs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md](docs/PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md)
- Review [docs/implementation/REQUIREMENTS_MAP.md](docs/implementation/REQUIREMENTS_MAP.md) for detailed mapping

**...implement a specific feature**
- Check [docs/implementation/IMPLEMENTATION_PLAN.md](docs/implementation/IMPLEMENTATION_PLAN.md) for the plan
- Review [docs/implementation/REQUIREMENTS_MAP.md](docs/implementation/REQUIREMENTS_MAP.md) for requirements details

**...learn about LiveKit Agents**
- Read [my-app/AGENTS.md](my-app/AGENTS.md) for project-specific guidance
- Browse [docs/research/livekit/](docs/research/livekit/) for research materials
- Install the [LiveKit Docs MCP server](https://docs.livekit.io/mcp) for integrated documentation

**...write tests**
- See [my-app/AGENTS.md](my-app/AGENTS.md) for testing best practices
- Review [TESTING_INTEGRATION_GUIDE.md](TESTING_INTEGRATION_GUIDE.md) for integration testing
- Check existing tests in [my-app/tests/](my-app/tests/)

**...understand the architecture**
- Review [docs/implementation/ANALYSIS.md](docs/implementation/ANALYSIS.md)
- Check [docs/implementation/IMPLEMENTATION_PLAN.md](docs/implementation/IMPLEMENTATION_PLAN.md)
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
