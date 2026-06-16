// ── Azure AI Services Module ──────────────────────────────────────────────────
// Used as the primary LLM endpoint when Azure OpenAI quota is unavailable.
// Provides gpt-oss-120b (OpenAI-OSS format) with 5000 TPM quota on
// Azure for Students subscriptions.
param prefix string
param env string
param location string

var aiSvcName = '${prefix}-aisvc-${env}'

resource aiServices 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: aiSvcName
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: aiSvcName
    disableLocalAuth: false
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
  }
}

// gpt-oss-120b — uses AIServices.GlobalStandard.gpt-oss-120b quota (5000 TPM)
// OpenAI-OSS format: compatible with Azure OpenAI SDK, same chat completions API
resource gptOss 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: aiServices
  name: 'gpt-oss-120b'
  sku: {
    name: 'GlobalStandard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI-OSS'
      name: 'gpt-oss-120b'
      version: '1'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
// Use the OpenAI-compatible endpoint — same format as Azure OpenAI SDK expects
output endpoint string = 'https://${aiServices.properties.customSubDomainName}.openai.azure.com/'
output aiServicesName string = aiServices.name
output aiServicesId string = aiServices.id
output chatDeployment string = gptOss.name
