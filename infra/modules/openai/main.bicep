// Azure OpenAI Module
param environmentName string
param location string

var openAiName = 'oai-discovery-${environmentName}'

resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    publicNetworkAccess: 'Disabled'
    customSubDomainName: openAiName
  }
}

output openAiEndpoint string = openAi.properties.endpoint
output openAiId string = openAi.id
