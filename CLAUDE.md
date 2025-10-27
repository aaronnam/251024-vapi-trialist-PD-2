# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains a PandaDoc trial success voice AI agent implementation, built with LiveKit Agents. The project aims to increase trial-to-paid conversion through proactive voice-based enablement.

## Repository Structure

### `/my-app/` - LiveKit Voice AI Application
The core voice agent implementation using LiveKit Agents Python SDK.

**Key files:**
- `my-app/AGENTS.md` - Detailed project guide (defer to this for agent development)
- `my-app/src/agent.py` - Main agent entrypoint
- `my-app/pyproject.toml` - Dependencies and project config
- `my-app/tests/` - Evaluation suite using LiveKit testing framework

**Common commands (run from `/my-app/` directory):**
```bash
# Install dependencies
uv sync

# Download required models (first time only)
uv run python src/agent.py download-files

# Run agent in console mode (terminal-based testing)
uv run python src/agent.py console

# Run agent in dev mode (for use with frontend/telephony)
uv run python src/agent.py dev

# Run tests
uv run pytest

# Format code
uv run ruff format

# Lint code
uv run ruff check
```

### `/docs/` - Documentation & Specifications
Voice agent specifications, implementation plans, and technical research for PandaDoc trial success use case.

**Key files:**
- `PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md` - Complete production specification including:
  - Business context and problem statement
  - Agent definitions (inbound vs outbound)
  - Conversation architecture and user flows
  - Technical architecture with VAPI integration
  - Function definitions and tool integrations
  - Data flow and Amplitude/Salesforce integration

This spec provides the business requirements and design rationale for the voice agent implementation.

**Documentation structure:**
- `docs/implementation/` - Implementation plans and guides
  - `IMPLEMENTATION_PLAN.md` - Detailed implementation roadmap
  - `REQUIREMENTS_MAP.md` - Spec-to-implementation mapping
  - `ANALYSIS.md` - Technical analysis
- `docs/research/` - Technical research and deep dives
  - `docs/research/livekit/` - LiveKit framework research
  - `docs/research/quick-references/` - Condensed reference guides for common patterns

### `/anthropic-agent-guides/` - Best Practice Documentation
Anthropic's official guides on building effective agents and voice AI systems.

**Key documents:**
- Agent building best practices
- Tool design patterns
- Voice AI prompting guides (ElevenLabs, Google, OpenAI, VAPI)
- Agent specification templates

These guides inform the design decisions in the implementation.

## Development Workflow

### Working on the Voice Agent
1. **Always reference `my-app/AGENTS.md`** - This is the authoritative guide for the LiveKit agent implementation
2. **Use TDD for agent behavior changes** - Write tests first, then implement (per AGENTS.md guidelines)
3. **Run tests before committing** - `uv run pytest` from `/my-app/`
4. **Maintain code quality** - Use `ruff format` and `ruff check`

### Understanding Requirements
- Reference `/docs/PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md` for business requirements
- This spec defines what the agent should do and why
- It includes detailed user personas, qualification logic, and integration requirements

## Documentation Organization

The `/docs/` directory is organized into three main areas:

### Core Specifications (Root Level)
- `PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md` - Primary product specification
- `PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md` - Detailed specification variant
- `VAPI_DASHBOARD_PANDADOC_FILLED.md` - VAPI configuration reference

### Implementation Documentation (`/docs/implementation/`)
Implementation plans, analysis, and requirement mappings:
- `IMPLEMENTATION_PLAN.md` - Step-by-step implementation roadmap with phases
- `REQUIREMENTS_MAP.md` - Maps spec requirements to implementation tasks
- `REQUIREMENTS_MATRIX.csv` - Tabular view of requirement coverage
- `ANALYSIS.md` - Technical analysis and architectural decisions
- `README.md` - Overview of implementation documentation

Use these when planning development work or tracking progress against requirements.

### Research Documentation (`/docs/research/`)
Technical deep dives and condensed reference guides:
- `docs/research/livekit/` - LiveKit framework research and patterns
- `docs/research/quick-references/` - Quick reference guides including:
  - `function-tools-summary.md` - LiveKit function/tool patterns
  - `voice-pipeline-quick-ref.md` - Voice pipeline component reference
  - `testing-quick-ref.md` - Testing patterns and examples
  - `README.md` - Guide to using quick references

Use these for quick lookups when implementing specific features or debugging.

### Environment Setup
The voice agent requires LiveKit Cloud credentials. Set these in `/my-app/.env.local`:
```
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

Use LiveKit CLI to populate automatically:
```bash
lk cloud auth
lk app env -w -d my-app/.env.local
```

## Architecture Context

### Voice Pipeline (from my-app/src/agent.py:62-79)
- **STT**: AssemblyAI Universal Streaming
- **LLM**: OpenAI GPT-4.1-mini
- **TTS**: Cartesia Sonic 2
- **Turn Detection**: LiveKit Multilingual Model
- **Noise Cancellation**: LiveKit BVC

### Integration Points (from spec)
The production design calls for integrations with:
- **Amplitude** - Product usage intelligence
- **ChiliPiper** - Meeting booking and routing
- **Salesforce** - Lead management
- **HubSpot** - CRM activity logging
- **Snowflake** - Analytics and data warehouse

*Note: Current implementation is baseline. Production integrations are defined in spec but not yet implemented.*

## Key Design Principles

1. **Test-Driven Development** - Always write tests for agent behavior before implementation
2. **Latency Sensitivity** - Voice AI requires fast responses; avoid unnecessary context
3. **Graceful Degradation** - Agent should handle missing data or API failures elegantly
4. **Structured Workflows** - Use LiveKit tasks/handoffs rather than long instructions
5. **Voice-Optimized Responses** - Keep responses concise, avoid complex formatting

## LiveKit Documentation

The LiveKit Agents framework evolves rapidly. Always consult current documentation via the LiveKit MCP server:

**To install (if not already available):**
```bash
claude mcp add --transport http livekit-docs https://docs.livekit.io/mcp
```

## Important Notes

- This is **not a git repository** (noted in environment context)
- The `/my-app/` subdirectory has its own complete CLAUDE.md that defers to AGENTS.md
- When working in `/my-app/`, follow the guidance in its AGENTS.md file
- The spec in `/docs/` is the source of truth for business requirements
- Use `uv` package manager, not pip or poetry
