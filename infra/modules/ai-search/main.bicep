// Azure AI Search Module
param environmentName string
param location string

var searchName = 'srch-discovery-${environmentName}'

resource aiSearch 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchName
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    publicNetworkAccess: 'disabled'
  }
}

output searchEndpoint string = 'https://${aiSearch.name}.search.windows.net'
output searchId string = aiSearch.id
