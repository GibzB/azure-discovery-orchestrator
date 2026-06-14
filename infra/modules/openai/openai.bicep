// ── Azure OpenAI Module ───────────────────────────────────────────────────────
param prefix string
param env string
param location string

var openAiName = '${prefix}-oai-${env}'

resource openAi 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    publicNetworkAccess: 'Enabled' // API-key demo mode — no VNet required
    customSubDomainName: openAiName
    disableLocalAuth: false
  }
}

// GPT-4o deployment for chat
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAi
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: 30 // TPM in thousands; adjust per quota
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-05-13'
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}

// text-embedding-ada-002 for RAG
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAi
  name: 'text-embedding-ada-002'
  sku: {
    name: 'Standard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '2'
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
  dependsOn: [gpt4oDeployment]
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output endpoint string = openAi.properties.endpoint
output openAiName string = openAi.name
output openAiId string = openAi.id
