# Documentation Organization Plan

## Current State
17 documentation files in repo root, creating clutter and poor discoverability.

## Proposed Structure

```
251024-vapi-trialist-PD-2/
├── CLAUDE.md                              # Keep - Main guide for Claude Code
├── README.md                              # Create - Project overview
│
├── docs/
│   ├── specs/                             # Product specs (existing)
│   │   ├── PANDADOC_VOICE_AGENT_SPEC_COMPLETE.md
│   │   ├── PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md
│   │   └── VAPI_DASHBOARD_PANDADOC_FILLED.md
│   │
│   ├── implementation/                    # NEW - Implementation guides
│   │   ├── README.md                      # Implementation overview
│   │   ├── IMPLEMENTATION_PLAN.md         # Master plan
│   │   ├── REQUIREMENTS_MAP.md            # PandaDoc → LiveKit mapping
│   │   ├── REQUIREMENTS_MATRIX.csv        # Traceability matrix
│   │   └── ANALYSIS.md                    # ROI and analysis
│   │
│   └── research/                          # NEW - Technical research
│       ├── README.md                      # Research overview
│       ├── livekit/
│       │   ├── README.md                  # LiveKit research index
│       │   ├── function-tools.md          # Function tools deep dive
│       │   ├── voice-pipeline.md          # Voice pipeline config
│       │   └── testing-framework.md       # Testing patterns
│       │
│       └── quick-references/
│           ├── function-tools-summary.md
│           ├── testing-quick-ref.md
│           └── voice-pipeline-quick-ref.md
│
├── anthropic-agent-guides/                # Keep - Anthropic best practices
│
└── my-app/                                # Keep - LiveKit application
```

## Organization Principles

1. **Hierarchy over Flatness** - Group related docs in subdirectories
2. **Purpose-Based Structure** - Specs, implementation, research separated
3. **Progressive Disclosure** - README files guide to deeper content
4. **Discoverability** - Consistent naming, clear hierarchy
5. **Maintainability** - Related files together, easy to update

## File Movements

### Implementation Guides → docs/implementation/
- PANDADOC_VOICE_AGENT_IMPLEMENTATION_PLAN.md → IMPLEMENTATION_PLAN.md
- PANDADOC_LIVEKIT_REQUIREMENTS_MAP.md → REQUIREMENTS_MAP.md
- REQUIREMENTS_TRACEABILITY_MATRIX.csv → REQUIREMENTS_MATRIX.csv
- ANALYSIS_COMPLETE.md → ANALYSIS.md
- IMPLEMENTATION_SUMMARY.md → (merge into README.md)

### Research Docs → docs/research/livekit/
- livekit_function_tools_research.md → function-tools.md
- LIVEKIT_TESTING_FRAMEWORK.md → testing-framework.md
- /tmp/livekit_voice_pipeline_research.md → voice-pipeline.md

### Quick References → docs/research/quick-references/
- FUNCTION_TOOLS_SUMMARY.md → function-tools-summary.md
- TESTING_QUICK_REFERENCE.md → testing-quick-ref.md
- /tmp/quick_reference.md → voice-pipeline-quick-ref.md

### Index/Navigation Files → (Remove after creating READMEs)
- README_ANALYSIS.md → (content into docs/implementation/README.md)
- README_RESEARCH.md → (content into docs/research/README.md)
- INDEX_REQUIREMENTS_ANALYSIS.md → (remove)
- RESEARCH_INDEX.md → (remove)
- TESTING_DOCUMENTATION_INDEX.md → (remove)
- TESTING_INTEGRATION_GUIDE.md → (merge into testing-framework.md)
- TESTING_RESEARCH_SUMMARY.md → (merge into testing-framework.md)

## Files to Create

1. **README.md** (root) - Project overview, quick start, navigation
2. **docs/implementation/README.md** - Implementation guide overview
3. **docs/research/README.md** - Research documentation overview
4. **docs/research/livekit/README.md** - LiveKit research index

## Benefits

1. **Clean Root** - Only essential files (CLAUDE.md, README.md)
2. **Clear Purpose** - Each directory has specific role
3. **Easy Navigation** - README files guide through content
4. **Logical Grouping** - Related docs together
5. **Scalable** - Easy to add new docs in right place
6. **Discoverable** - Clear hierarchy aids finding information

## Implementation Tasks

1. Create new directory structure
2. Move files to new locations (with git mv)
3. Create README files for navigation
4. Update internal links
5. Remove redundant index files
6. Update CLAUDE.md references
7. Verify all links work
