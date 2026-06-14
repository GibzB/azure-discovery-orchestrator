// Azure Front Door Module
param environmentName string
param location string = 'global'
param backendFqdn string

var frontDoorName = 'afd-discovery-${environmentName}'

resource frontDoor 'Microsoft.Cdn/profiles@2023-05-01' = {
  name: frontDoorName
  location: location
  sku: {
    name: 'Standard_AzureFrontDoor'
  }
}

resource endpoint 'Microsoft.Cdn/profiles/afdEndpoints@2023-05-01' = {
  parent: frontDoor
  name: 'endpoint-${environmentName}'
  location: location
  properties: {
    enabledState: 'Enabled'
  }
}

output frontDoorId string = frontDoor.id
output endpointHostname string = endpoint.properties.hostName
