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

// GPT-4.1 deployment for chat (GlobalStandard — available in italynorth)
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAi
  name: 'gpt-4.1'
  sku: {
    name: 'GlobalStandard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1'
      version: '2025-04-14'
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}

// text-embedding-3-small for RAG (GlobalStandard)
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAi
  name: 'text-embedding-3-small'
  sku: {
    name: 'GlobalStandard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
  dependsOn: [gpt4oDeployment]
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output endpoint string = openAi.properties.endpoint
output openAiName string = openAi.name
output openAiId string = openAi.id
output chatDeployment string = gpt4oDeployment.name
output embeddingDeployment string = embeddingDeployment.name
