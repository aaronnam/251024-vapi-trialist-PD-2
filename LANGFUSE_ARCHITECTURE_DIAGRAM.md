# Langfuse + LiveKit Tracing Architecture

## Current Implementation Trace Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SESSION STARTS                                    │
│              (Room created in LiveKit Cloud)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  setup_observability(metadata={"langfuse.session.id": room_name})          │
│                                                                              │
│  - Create OpenTelemetry TracerProvider                                      │
│  - Configure OTLP exporter → Langfuse                                       │
│  - Set session_id in resource attributes                                    │
│  - Return TracerProvider to agent                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   TRACE CREATED IN LANGFUSE  │
                    │   session_id: room-abc-123   │
                    │   user_id: (pending)         │
                    └──────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌─────────────────────────┐   ┌─────────────────────────┐
        │  USER JOINS ROOM        │   │  STT SPAN STARTS        │
        │  (Participant joined)   │   │  (Audio processing)     │
        └─────────────────────────┘   └─────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────┐
        │ set_tracer_provider()   │
        │ Updates with user_id    │
        └─────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
    STT Metrics          User Joins → Langfuse
    Enriched                 Updated with:
                             - user_id: email
                             - participant.identity


═══════════════════════════════════════════════════════════════════════════════

                      DURING CONVERSATION

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                    USER SPEAKS TO AGENT                                     │
│  "How do I integrate PandaDoc with Salesforce?"                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
                 ▼                 ▼                 ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ STT SPAN     │  │ USER TRANS   │  │ CONV ITEM    │
        │ (Deepgram)   │  │ SPAN         │  │ SPAN         │
        │              │  │              │  │              │
        │ Enriched:    │  │ Enriched:    │  │ Enriched:    │
        │ - audio_dur  │  │ - transcript │  │ - role: user │
        │ - cost       │  │ - is_final   │  │ - content    │
        │ - tokens     │  │ - language   │  │ - input: msg │
        └──────────────┘  └──────────────┘  └──────────────┘
                 │                 │                 │
                 └─────────────────┼─────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────┐
        │  LANGFUSE TRACE UPDATED                    │
        │  (New observation: user_transcribed)       │
        │  (New observation: conversation_item)      │
        └─────────────────────────────────────────────┘

                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ LLM GENERATION SPAN STARTS         │
        │ (OpenAI gpt-4.1-mini)              │
        └─────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ METRICS_COLLECTED EVENT             │
        │ (LLMMetrics emitted)                │
        │                                      │
        │ Handler enriches span with:         │
        │ - langfuse.cost.total: 0.0003       │
        │ - langfuse.cost.input: 0.0001       │
        │ - langfuse.cost.output: 0.0002      │
        │ - gen_ai.usage.input_tokens: 234    │
        │ - gen_ai.usage.output_tokens: 89    │
        │ - langfuse.input: (conversation)    │
        │ - gen_ai.request.model: gpt-4...    │
        └─────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ LLM GENERATION SPAN ENDS            │
        │ (With all cost attributes)          │
        └─────────────────────────────────────┘

                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ TOOL SPAN STARTS                    │
        │ unleash_search_knowledge            │
        └─────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    Tool Input       HTTP Call        Tool Output
    (Auto-captured   (to Unleash)      (Auto-captured
     by LiveKit)                        by LiveKit)


                    ┌──────────────────────┐
                    │  HTTP RESPONSE       │
                    │  Status: 200         │
                    │  Results found       │
                    └──────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ TOOL SPAN ENDS                      │
        │ (Duration, success captured)        │
        └─────────────────────────────────────┘

                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ TTS SPAN STARTS                     │
        │ (Cartesia Sonic 3)                  │
        └─────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ METRICS_COLLECTED (TTSMetrics)      │
        │                                      │
        │ Handler enriches with:              │
        │ - langfuse.cost.total: 0.000001     │
        │ - langfuse.usage.input: 245 chars   │
        │ - gen_ai.usage.input_tokens: 245    │
        │ - tts.duration: 1234ms              │
        └─────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │ TTS SPAN ENDS                       │
        │ (With all cost attributes)          │
        └─────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

                      LANGFUSE TRACE STRUCTURE

═══════════════════════════════════════════════════════════════════════════════

trace:
  session_id: room-abc-123
  user_id: john@example.com
  start_time: 2025-10-31T10:00:00Z
  cost_total: $0.0045

  observations:
    ├─ span: user_transcribed
    │   ├─ input: "Hello, how do I..."
    │   ├─ timestamp: 10:00:05
    │   └─ attributes:
    │       ├─ user.transcript: "Hello..."
    │       └─ user.transcript.is_final: true
    │
    ├─ observation: conversation_item
    │   ├─ role: user
    │   ├─ content: "Hello, how do I integrate with Salesforce?"
    │   └─ attributes:
    │       └─ langfuse.input: "..."
    │
    ├─ generation: llm_node (GENERATION)
    │   ├─ model: gpt-4.1-mini
    │   ├─ input_tokens: 234
    │   ├─ output_tokens: 89
    │   ├─ cost: $0.0003
    │   ├─ ttft: 0.234s
    │   ├─ duration: 1.234s
    │   └─ attributes:
    │       ├─ langfuse.cost.total: 0.0003
    │       ├─ langfuse.cost.input: 0.0001
    │       ├─ langfuse.cost.output: 0.0002
    │       ├─ langfuse.input: "system: You are...\n\nuser: Hello..."
    │       ├─ gen_ai.usage.input_tokens: 234
    │       ├─ gen_ai.usage.output_tokens: 89
    │       └─ gen_ai.request.model: gpt-4.1-mini
    │
    ├─ observation: tool (TOOL)
    │   ├─ name: unleash_search_knowledge
    │   ├─ input: {"query": "How do I integrate with Salesforce?"}
    │   ├─ output: {"answer": "You can use Salesforce integration..."}
    │   ├─ duration: 0.834s
    │   └─ success: true
    │
    ├─ observation: conversation_item
    │   ├─ role: assistant
    │   ├─ content: "Great question! PandaDoc integrates..."
    │   └─ attributes:
    │       └─ langfuse.output: "Great question..."
    │
    └─ span: tts
        ├─ duration: 1.456s
        ├─ cost: $0.0000015
        └─ attributes:
            ├─ langfuse.cost.total: 0.0000015
            ├─ tts.characters: 245
            └─ gen_ai.usage.input_tokens: 245

═══════════════════════════════════════════════════════════════════════════════

                      WITH ZAPIER INTEGRATION

═══════════════════════════════════════════════════════════════════════════════

When user requests meeting:

┌─────────────────────────────────────────────────────────────────────────────┐
│ User: "Let me talk to your sales team about implementation"                │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent qualifies user → Calls book_sales_meeting() tool                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────┐
        │ TOOL SPAN: book_sales_meeting               │
        │ (Created automatically by LiveKit)          │
        │                                              │
        │ Auto-captured:                              │
        │ - input: {customer_name, email, dates}      │
        │ - success: true                             │
        └─────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────┐
        │ INSIDE TOOL: call_zapier_webhook()          │
        │ (NEW)                                        │
        │                                              │
        │ Manual span created:                        │
        │ with tracer.start_as_current_span(          │
        │     "zapier_booking_created"                │
        │ ) as span:                                  │
        └─────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┴──────────────────┐
        │                                             │
        ▼                                             ▼
    Set Attributes                            Make Webhook Call
    ├─ integration.vendor: "zapier"           │
    ├─ webhook.event_type: "booking_created"  │  POST https://hooks.zapier.com/
    └─ webhook.payload_size: 487 bytes        │  Payload: {customer_name, email...}
                                              │
                                              ▼
                                        Get Response
                                        Status: 200
                                        Body: {id, status}

        ┌──────────────────────────┬──────────────────┐
        │                          │                  │
        ▼                          ▼                  ▼
    Enrich Span            Success Path         Analytics
    ├─ http.status_code    └─ span.success: true  └─ tool_calls.append({
    ├─ http.response_size  └─ webhook_id: abc123    booking_method:
    ├─ langfuse.cost.total                            "zapier_webhook"
    └─ error: null                                   })

                                   │
                                   ▼
        ┌─────────────────────────────────────────────┐
        │ ZAPIER SPAN ENDS                            │
        │ (Traced in Langfuse)                        │
        └─────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────┐
        │ TOOL SPAN ENDS                              │
        │ book_sales_meeting                          │
        │                                              │
        │ Returns:                                    │
        │ {booking_status: "confirmed",               │
        │  meeting_time: "...",                       │
        │  webhook_id: "abc123"}                      │
        └─────────────────────────────────────────────┘


LANGFUSE TRACE WITH ZAPIER:

trace:
  observations:
    ├─ generation: llm_node
    │   └─ cost: $0.0003
    │
    ├─ observation: tool (TOOL)
    │   ├─ name: book_sales_meeting
    │   ├─ input: {customer_name, email, ...}
    │   ├─ output: {booking_status: confirmed, webhook_id: abc123}
    │   ├─ duration: 1.456s
    │   │
    │   ├─ nested span: zapier_booking_created  ← NEW!
    │   │   ├─ input: None (HTTP body, not exposed)
    │   │   ├─ output: {id: abc123, status: completed}
    │   │   ├─ duration: 1.234s
    │   │   ├─ cost: $0.01  ← Cost tracked!
    │   │   ├─ http.status_code: 200
    │   │   └─ attributes:
    │   │       ├─ integration.vendor: zapier
    │   │       ├─ webhook.event_type: booking_created
    │   │       ├─ langfuse.cost.total: 0.01
    │   │       ├─ gen_ai.usage.cost: 0.01
    │   │       └─ http.success: true
    │   │
    │   └─ success: true
    │
    └─ span: tts (assistant says booking confirmed)

═══════════════════════════════════════════════════════════════════════════════

                      ATTRIBUTE FLOW DIAGRAM

═══════════════════════════════════════════════════════════════════════════════

Session Initialization:
┌─────────────────────────┐
│ setup_observability()   │
│ ↓                       │
│ Set: session_id         │
│      deployment_env     │
│      service.name       │
└─────────────────────────┘
         │
         ▼
   ┌─────────────┐
   │  Trace      │
   │  session_id ├─ room-abc-123
   │  env        ├─ production
   └─────────────┘

User Identification:
┌──────────────────────────────────────┐
│ Participant joins, metadata received │
│ ↓                                    │
│ set_tracer_provider(metadata={       │
│   "langfuse.session.id": room_name,  │
│   "langfuse.user.id": user_email,    │
│   "user.email": user_email,          │
│   "participant.identity": id         │
│ })                                   │
└──────────────────────────────────────┘
         │
         ▼
   ┌─────────────┐
   │  Trace      │
   │  session_id ├─ room-abc-123
   │  user_id    ├─ john@example.com
   │  email      ├─ john@example.com
   │  participant├─ participant-123
   └─────────────┘

Span Enrichment (metrics_collected):
┌────────────────────────────────────────────┐
│ metrics_collected event (LLMMetrics)       │
│ ↓                                          │
│ current_span = otel_trace.get_current_span│
│ ↓                                          │
│ if current_span.is_recording():            │
│   current_span.set_attribute(             │
│     "langfuse.cost.total", llm_cost       │
│   )                                        │
│   current_span.set_attribute(             │
│     "gen_ai.usage.cost", llm_cost         │
│   )                                        │
│   ... (10+ more attributes)               │
└────────────────────────────────────────────┘
         │
         ▼
   ┌──────────────────┐
   │  Span            │
   │  (llm_node)      │
   │                  │
   │  Enriched:       │
   │  ├─ cost.total   │
   │  ├─ cost.input   │
   │  ├─ cost.output  │
   │  ├─ usage tokens │
   │  ├─ model        │
   │  ├─ ttft         │
   │  ├─ duration     │
   │  └─ input text   │
   └──────────────────┘

Webhook Span Creation:
┌──────────────────────────────────────┐
│ with tracer.start_as_current_span(   │
│     "zapier_booking_created"         │
│ ) as span:                           │
│   span.set_attribute(               │
│     "integration.vendor", "zapier"  │
│   )                                 │
│   response = await client.post(...)  │
│   span.set_attribute(               │
│     "http.status_code", 200         │
│   )                                 │
│   span.set_attribute(               │
│     "langfuse.cost.total", 0.01     │
│   )                                 │
└──────────────────────────────────────┘
         │
         ▼
   ┌──────────────────┐
   │  Span            │
   │  (zapier_...)    │
   │                  │
   │  Attributes:     │
   │  ├─ vendor       │
   │  ├─ event_type   │
   │  ├─ status_code  │
   │  ├─ cost.total   │
   │  ├─ payload_size │
   │  └─ success      │
   └──────────────────┘

═══════════════════════════════════════════════════════════════════════════════

                      ERROR HANDLING FLOW

═══════════════════════════════════════════════════════════════════════════════

When webhook fails:

┌──────────────────────────────────┐
│ call_zapier_webhook() called     │
│ ↓                                │
│ Make HTTP request                │
│ ↓                                │
│ Response: 400 Bad Request        │
└──────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ span.set_attribute("error.type", "...")    │
│ span.set_attribute(                        │
│   "http.error_message",                    │
│   "Bad request"                            │
│ )                                          │
│ ↓                                          │
│ raise ToolError(message)                   │
└────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ book_sales_meeting catches ToolError       │
│ ↓                                          │
│ Log analytics error                        │
│ ↓                                          │
│ Re-raise to agent                          │
└────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ Agent responds:                            │
│ "There was an issue booking your meeting"  │
│ ↓                                          │
│ Session continues (doesn't crash)          │
└────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ Langfuse trace shows:                      │
│                                            │
│ ├─ book_sales_meeting tool span           │
│ │  └─ ERROR status                        │
│ │      ├─ zapier_booking_created span     │
│ │      │  ├─ error.type: webhook_error   │
│ │      │  ├─ http.status_code: 400       │
│ │      │  └─ error.message: "Bad req..."  │
│ │      └─ Clearly shows where error was   │
│ └─ (No impact on LLM spans above)         │
└────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

                      DATA EXPORT TIMELINE

═══════════════════════════════════════════════════════════════════════════════

Real-time (0ms):
├─ LiveKit creates span (STT, LLM, TTS)
├─ Your code enriches with attributes
└─ Span ends

Batch Export (30 seconds):
├─ OpenTelemetry BatchSpanProcessor accumulates spans
├─ Sends batch to OTLP endpoint
└─ Langfuse receives OTLP data

Ingestion (15-30 seconds):
├─ Langfuse processes OTLP data
├─ Parses attributes
├─ Stores in ClickHouse
└─ Makes searchable

Available in UI (30-60 seconds total):
├─ Search by session_id: IMMEDIATE
├─ Filter by attributes: ~30s delay
└─ Full-text search: ~1-2 minutes

Example timeline:
10:00:00 - User says "book a meeting"
10:00:05 - Tool execution completes
10:00:35 - Batch export sends to Langfuse
10:01:05 - Trace appears in Langfuse UI
10:01:30 - Can search/filter the trace

═══════════════════════════════════════════════════════════════════════════════

This diagram shows how observability flows through your system:

1. Session initializes with session_id and (later) user_id
2. Each component (STT, LLM, TTS, Tool) creates spans automatically
3. Your code enriches spans with custom attributes (cost, context)
4. Spans are batched and exported to Langfuse via OTLP
5. Langfuse ingests and makes traces searchable
6. With Zapier: New webhook span added without breaking existing structure
