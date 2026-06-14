# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────┐
│                    Azure Front Door                  │
└───────────────────────┬─────────────────────────────┘
                        │
          ┌─────────────┴──────────────┐
          │                            │
   ┌──────▼──────┐             ┌───────▼──────┐
   │  Frontend   │             │   Backend     │
   │ (Static Web │             │ (Container    │
   │    App)     │             │    Apps)      │
   └─────────────┘             └───────┬───────┘
                                       │
        ┌──────────────────────────────┼────────────────────────┐
        │                              │                        │
 ┌──────▼──────┐               ┌───────▼──────┐        ┌───────▼──────┐
 │  Azure      │               │  Cosmos DB   │        │  AI Search   │
 │  OpenAI     │               │  (sessions)  │        │ (knowledge   │
 │  (GPT-4o)   │               └──────────────┘        │   base)      │
 └─────────────┘                                       └──────────────┘
```

## Agent Architecture

The orchestrator uses a multi-agent pattern:

1. **Orchestrator Agent** — intent classification and routing
2. **Business Agent** — requirements elicitation
3. **Architect Agent** — Azure service recommendations (RAG-augmented)
4. **Security Agent** — compliance and risk review
5. **Report Agent** — final report generation

## Data Flow

See [data_flow.md](./data_flow.md) for the detailed message sequence.
