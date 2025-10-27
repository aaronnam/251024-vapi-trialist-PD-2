# AI Agent Spec

## 1. Objective
**Goal:** [What success looks like]  
**Scope:** [What's in/out of bounds]  
**Exit conditions:** [When to stop]

## 2. System Prompt
**Role & identity:** [Who the agent is]  
**Operating principles:** [How it should behave]  
**Tool usage guidelines:** [When/how to use each tool]  
**Memory strategy:** [What to persist, naming conventions]  
**Error handling:** [How to recover, when to escalate]

## 3. Capabilities

### Tools
- Tool name | Purpose | Input schema | Output format | Cost/latency notes

### Knowledge Bases
- Source | Content type | When to reference | Update frequency

### Sub-agents (if applicable)
- Sub-agent type | Delegation criteria | Communication protocol

## 4. Memory & State
**Persistence layer:** [Files, database, vector store]  
**Read strategy:** [When to retrieve vs. search]  
**Write strategy:** [What to save, format, retention]  
**Context window management:** [How to handle limits]

## 5. Guardrails
**Safety constraints:** [What it cannot do]  
**Human-in-the-loop triggers:** [When to pause for approval]  
**Rate limits & quotas:** [API/cost constraints]  
**Failure modes:** [Timeout, infinite loops, bad outputs]

## 6. Configuration
**Model:** [Which LLM, version]  
**Parameters:** [Temperature, max tokens, top-p]  
**Logging:** [What to track, where]  
**Monitoring:** [Success metrics, alerts]  
**Testing strategy:** [How to validate behavior]