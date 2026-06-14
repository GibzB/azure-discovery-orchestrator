# Azure Discovery Orchestrator

An AI-powered conversational engine that runs Azure architecture discovery workshops — replacing weeks of manual pre-sales work with a guided, multi-agent dialogue that produces a professional discovery report.

## How It Works

1. Customer describes their business and technical needs via a chat interface.
2. The **Orchestrator Agent** routes the conversation to specialist agents.
3. The **Business Agent** captures requirements and constraints.
4. The **Architect Agent** designs an Azure architecture (RAG-augmented with CAF/WAF).
5. The **Security Agent** reviews for compliance and risk.
6. The **Report Agent** produces a structured Markdown/PDF discovery report.

## Project Structure

```
azure-discovery-orchestrator/
├── infra/          # Bicep IaC for all Azure resources
├── backend/        # FastAPI + multi-agent AI orchestration engine
├── frontend/       # React conversational UI
├── prompts/        # System prompts for each agent
├── knowledgebase/  # RAG documents (CAF, WAF, SAP, landing zones)
├── docs/           # Architecture and design docs
├── workflows/      # GitHub Actions CI/CD pipelines
└── tests/          # Test suite
```

## Prerequisites

- Azure subscription with Contributor access
- Azure CLI + Bicep CLI
- Python 3.12+
- Node.js 20+
- Docker

## Getting Started

### 1. Infrastructure

```bash
az login
az deployment sub create \
  --location eastus \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev.bicepparam
```

### 2. Backend

```bash
cd backend
cp ../.env.example .env   # fill in your values
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## CI/CD

GitHub Actions workflows in `workflows/` handle:
- `infra-deploy.yml` — Bicep deployment via OIDC
- `backend-deploy.yml` — Docker build → ACR → Container Apps
- `frontend-deploy.yml` — Vite build → Azure Static Web Apps

## Contributing

See [docs/architecture.md](docs/architecture.md) and [docs/agent_design.md](docs/agent_design.md) before contributing.

## License

MIT
