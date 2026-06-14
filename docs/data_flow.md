# Data Flow

## Conversation Turn

```
User Input
    │
    ▼
Frontend (React)
    │  POST /api/v1/chat
    ▼
Backend (FastAPI)
    │
    ▼
OrchestratorAgent
    ├── retrieve context ──► RAGRetriever ──► Azure AI Search
    ├── load history    ──► CosmosService ──► Cosmos DB
    │
    ├── route to BusinessAgent?
    ├── route to ArchitectAgent?
    └── route to SecurityAgent?
          │
          ▼
    Specialist Agent
          │  call Azure OpenAI
          ▼
    ChatCompletion response
          │
          ▼
    OrchestratorAgent (synthesise)
          │
          ▼
    Save to Cosmos DB
          │
          ▼
    Return response to Frontend
```

## Report Generation

```
POST /api/v1/reports/{session_id}/generate
    │
    ▼
ReportAgent
    ├── load all session messages from Cosmos DB
    ├── call Azure OpenAI with report_generator prompt
    └── save Markdown to Azure Blob Storage
          │
          ▼
    Return download URL
```
