# Azure DevOps Setup Guide

## 1. Create an Azure DevOps organisation (free)

Go to https://dev.azure.com and sign in with `BillyGibendi@my.uopeople.edu`.
Create an organisation (e.g. `discoveryai`) and a project named `azure-discovery-orchestrator`.

## 2. Connect the GitHub repository

Project Settings → Repos → GitHub connections → connect `GibzB/azure-discovery-orchestrator`.

Or: import the repo directly into Azure Repos if you prefer.

## 3. Create the Azure Resource Manager service connection

> **Note:** The UoPeople tenant blocks service principal creation (`az ad app create`).
> Use the **Workload Identity Federation with existing App** option is also blocked.
> Use **Service principal (manual)** with your own credentials or use the
> **Azure Resource Manager with Publish Profile** approach.
>
> **Simplest working option for Azure for Students:**
> Use "Azure Resource Manager" → "Workload identity federation (automatic)" — 
> this uses Azure DevOps' own managed identity which doesn't require you to create an SP.

Steps:
1. Project Settings → Service connections → New service connection
2. Choose: **Azure Resource Manager**
3. Authentication: **Workload identity federation (automatic)**
4. Scope: **Subscription** → select `Azure for Students` → `3cd9291d-...`
5. Resource group: leave blank (pipeline creates it)
6. Service connection name: `azure-discoveryai-sc`
7. Grant access permission to all pipelines: ✅

## 4. Create a Container Registry service connection (for backend pipeline)

> First create the ACR:
```bash
az acr create \
  --resource-group rg-discoveryai-dev \
  --name discoveryaiacr \
  --sku Basic
```

Then in Azure DevOps:
1. Project Settings → Service connections → New service connection
2. Choose: **Docker Registry**
3. Registry type: **Azure Container Registry**
4. Service connection: select `azure-discoveryai-sc` (from step 3)
5. ACR: `discoveryaiacr`
6. Service connection name: `acr-discoveryai-sc`

## 5. Create variable groups

Project Settings → Pipelines → Library → + Variable group

**Group name: `discoveryai-dev`**

| Variable | Value | Secret |
|---|---|---|
| `ACR_LOGIN_SERVER` | `discoveryaiacr.azurecr.io` | No |
| `VITE_API_BASE_URL` | `https://discoveryai-ca-backend-dev.lemonisland-694723bc.italynorth.azurecontainerapps.io` | No |
| `SWA_DEPLOYMENT_TOKEN` | *(from Static Web App resource)* | Yes |

## 6. Create pipelines

For each file in `azure-pipelines/`:

1. Pipelines → New pipeline
2. Where is your code: **GitHub** (or Azure Repos if imported)
3. Select your repository
4. Configure: **Existing Azure Pipelines YAML file**
5. Branch: `main`, Path: `azure-pipelines/infra-deploy.yml` (repeat for each)
6. Save (don't run yet)

Pipeline names:
- `infra-deploy` → `azure-pipelines/infra-deploy.yml`
- `backend-deploy` → `azure-pipelines/backend-deploy.yml`
- `frontend-deploy` → `azure-pipelines/frontend-deploy.yml`

## 7. Create DevOps environments

Pipelines → Environments → New environment:
- Name: `dev` (no resources needed, just approval tracking)
- Repeat for `test` and `prod`

## 8. Run first deployment

Pipelines → `infra-deploy` → Run pipeline → environment: `dev`

The pipeline will:
1. Lint the Bicep
2. Run what-if
3. Deploy all resources to `rg-discoveryai-dev` in `italynorth`

## 9. Disable GitHub Actions (optional)

Since pipelines are now in Azure DevOps, you can disable GitHub Actions:
- In the GitHub repo: Settings → Actions → General → Disable actions

Or simply delete the `.github/workflows/` folder.
