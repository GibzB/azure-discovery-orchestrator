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
    publicNetworkAccess: 'Enabled'
    customSubDomainName: openAiName
    disableLocalAuth: false
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
  }
}

// ── NOTE ──────────────────────────────────────────────────────────────────────
// Model deployments are intentionally NOT declared here.
// Azure for Students subscriptions require a quota request before deploying models.
// After quota is approved, run:
//   az cognitiveservices account deployment create \
//     --resource-group rg-discoveryai-dev \
//     --name discoveryai-oai-dev \
//     --deployment-name gpt-4.1 \
//     --model-name gpt-4.1 --model-version 2025-04-14 --model-format OpenAI \
//     --sku-name GlobalStandard --sku-capacity 30
//
//   az cognitiveservices account deployment create \
//     --resource-group rg-discoveryai-dev \
//     --name discoveryai-oai-dev \
//     --deployment-name text-embedding-3-small \
//     --model-name text-embedding-3-small --model-version 1 --model-format OpenAI \
//     --sku-name GlobalStandard --sku-capacity 30

// ── Outputs ───────────────────────────────────────────────────────────────────
output endpoint string = openAi.properties.endpoint
output openAiName string = openAi.name
output openAiId string = openAi.id
