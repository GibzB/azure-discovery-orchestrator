# Agent Design

## Agent Hierarchy

```
OrchestratorAgent
├── BusinessAgent
├── ArchitectAgent
├── SecurityAgent
└── ReportAgent
```

## Agent Interface

All agents implement `BaseAgent`:

```python
class BaseAgent(ABC):
    name: str

    async def run(self, user_input: str, context: dict | None = None) -> str: ...
```

## Memory Strategy

- **Short-term**: `SessionMemory` dataclass holds the current conversation window.
- **Long-term**: Cosmos DB persists sessions across reconnects.
- **Semantic**: Azure AI Search indexes knowledge base chunks for RAG retrieval.

## Prompt Construction

Each agent:
1. Loads its system prompt from `prompts/`
2. Appends relevant RAG chunks
3. Appends the conversation history
4. Calls Azure OpenAI
