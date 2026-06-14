// Azure Storage Module
param environmentName string
param location string

var storageName = 'stdiscovery${environmentName}'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    publicNetworkAccess: 'Disabled'
    supportsHttpsTrafficOnly: true
  }
}

output storageId string = storage.id
output storageEndpoint string = storage.properties.primaryEndpoints.blob
