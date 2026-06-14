// ── Azure AI Search Module ────────────────────────────────────────────────────
param prefix string
param env string
param location string

var searchName = '${prefix}-srch-${env}'

resource aiSearch 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchName
  location: location
  sku: { name: 'basic' } // basic is sufficient for sprint 1; upgrade to standard for prod
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled' // API-key demo mode
    disableLocalAuth: false
    semanticSearch: 'free' // enables semantic ranking at no extra cost on basic
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output endpoint string = 'https://${aiSearch.name}.search.windows.net'
output searchName string = aiSearch.name
output searchId string = aiSearch.id
