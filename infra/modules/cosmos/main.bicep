// Azure Cosmos DB Module
param environmentName string
param location string

var cosmosName = 'cosmos-discovery-${environmentName}'

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: cosmosName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    publicNetworkAccess: 'Disabled'
  }
}

output cosmosEndpoint string = cosmos.properties.documentEndpoint
output cosmosId string = cosmos.id
