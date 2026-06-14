// Azure Speech Services Module
param environmentName string
param location string

var speechName = 'spch-discovery-${environmentName}'

resource speech 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: speechName
  location: location
  kind: 'SpeechServices'
  sku: {
    name: 'S0'
  }
  properties: {
    publicNetworkAccess: 'Disabled'
  }
}

output speechEndpoint string = speech.properties.endpoint
output speechId string = speech.id
