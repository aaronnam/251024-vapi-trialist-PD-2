# Definition of an agent

## An agent is an LLM in a control loop, guided by a system prompt, that:

- Receives a goal (success criteria, constraints, guardrails)
- Is equipped with tools (APIs, search, file I/O, code exec, sub-agents)
- Autonomously selects and sequences tools with parameters
- Builds its own context via external memory (files/db) and retrieval
- Observes results, critiques its steps, and iterates to completion
- Stops on explicit exit conditions

### System prompt essentials:
- Role and operating principles (e.g., act as a sales ops agent, be safe, verify before acting)
- Tool contracts and when to use each (capabilities, IO schemas, costs/latency)
- Memory policy (what to persist, naming conventions, read/write cadence)
- Error/retry strategy and uncertainty handling
- Termination criteria and reporting format

## If an AI Engineer told to build an AI Agent, below is the checklist of things they would need to make sure to have:
- Minimal upfront context; provide discovery/search tools along with relevant knowledge base sources
- Clean, model-friendly tool wrappers and JSON schemas
- Persistent scratch space for notes/artifacts. let it write discoveries to files/memory for later retrieval.
- **Recursion capability** - ability to spawn sub-agents for parallel/specialized tasks
- Logging, traceability, and human-in-the-loop hooks where needed
- **Exit conditions** - clear success criteria so it knows when to stop
- **The critical shift:** You're designing the *environment* (tools + goal), not the *procedure*. The LLM reasons about the procedure itself.
- **Tool descriptions** that make their purpose intuitive to the model
