// ── Cosmos DB Module (session + conversation persistence) ─────────────────────
param prefix string
param env string
param location string

var cosmosName = '${prefix}-cosmos-${env}'
var databaseName = 'discovery'

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
        isZoneRedundant: false
      }
    ]
    enableFreeTier: false // free tier limited to 1 per subscription — set manually if needed
    publicNetworkAccess: 'Enabled' // API-key demo mode
    disableLocalAuth: false
    capabilities: [
      { name: 'EnableServerless' } // serverless = no provisioned RU cost in dev
    ]
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmos
  name: databaseName
  properties: {
    resource: { id: databaseName }
  }
}

resource sessionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'sessions'
  properties: {
    resource: {
      id: 'sessions'
      partitionKey: {
        paths: ['/sessionId']
        kind: 'Hash'
      }
      defaultTtl: 86400 // sessions expire after 24 h
    }
  }
}

resource messagesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'messages'
  properties: {
    resource: {
      id: 'messages'
      partitionKey: {
        paths: ['/sessionId']
        kind: 'Hash'
      }
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output endpoint string = cosmos.properties.documentEndpoint
output cosmosName string = cosmos.name
output cosmosId string = cosmos.id
