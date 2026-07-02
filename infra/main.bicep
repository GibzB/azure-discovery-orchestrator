targetScope = 'resourceGroup'

// ── Parameters ───────────────────────────────────────────────────────────────
@description('Deployment environment (dev | test | prod)')
@allowed(['dev', 'test', 'prod'])
param env string = 'dev'

@description('Primary Azure region')
param location string = resourceGroup().location

@description('Naming prefix for all resources')
param prefix string = 'discoveryai'

@description('Container image to deploy to the backend Container App')
param backendImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// ── Secure runtime secrets ────────────────────────────────────────────────────
@secure()
param azureOpenAiKey string = ''
@secure()
param azureSpeechKey string = ''
@secure()
param searchKey string = ''
@secure()
param cosmosKey string = ''
@secure()
param storageConnectionString string = ''

// ── Modules ───────────────────────────────────────────────────────────────────

module monitor './modules/monitor/monitor.bicep' = {
  name: 'monitorModule'
  params: {
    prefix: prefix
    env: env
    location: location
  }
}

module storage './modules/storage/storage.bicep' = {
  name: 'storageModule'
  params: {
    prefix: prefix
    env: env
    location: location
  }
}

module keyvault './modules/keyvault/keyvault.bicep' = {
  name: 'kvModule'
  params: {
    prefix: prefix
    env: env
    location: location
  }
}

module openai './modules/openai/openai.bicep' = {
  name: 'openaiModule'
  params: {
    prefix: prefix
    env: env
    location: location
  }
}

module aiSearch './modules/ai-search/ai-search.bicep' = {
  name: 'aiSearchModule'
  params: {
    prefix: prefix
    env: env
    location: location
  }
}

module cosmos './modules/cosmos/cosmos.bicep' = {
  name: 'cosmosModule'
  params: {
    prefix: prefix
    env: env
    location: location
  }
}

module aiServices './modules/aiservices/aiservices.bicep' = {
  name: 'aiServicesModule'
  params: {
    prefix: prefix
    env: env
    location: location
  }
}

module speech './modules/speech/speech.bicep' = {
  name: 'speechModule'
  params: {
    prefix: prefix
    env: env
    location: location
  }
}

module containerApps './modules/containerapps/containerapps.bicep' = {
  name: 'containerAppsModule'
  params: {
    prefix: prefix
    env: env
    location: location
    logAnalyticsWorkspaceId: monitor.outputs.logAnalyticsWorkspaceId
    logAnalyticsSharedKey: monitor.outputs.logAnalyticsSharedKey
    backendImage: backendImage
    azureOpenAiEndpoint: 'https://discoveryai-aisvc-dev.openai.azure.com/'
    azureOpenAiKey: azureOpenAiKey
    azureSpeechKey: azureSpeechKey
    searchEndpoint: aiSearch.outputs.endpoint
    searchKey: searchKey
    cosmosEndpoint: cosmos.outputs.endpoint
    cosmosKey: cosmosKey
    storageConnectionString: storageConnectionString
    corsOriginsRaw: 'https://discoveryaiswadev.z38.web.core.windows.net,http://localhost:5173'
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output openAiEndpoint string = openai.outputs.endpoint
output aiServicesEndpoint string = aiServices.outputs.endpoint
output aiServicesChatDeployment string = aiServices.outputs.chatDeployment
output searchEndpoint string = aiSearch.outputs.endpoint
output cosmosEndpoint string = cosmos.outputs.endpoint
output containerAppFqdn string = containerApps.outputs.fqdn

@secure()
output appInsightsConnectionString string = monitor.outputs.appInsightsConnectionString
output speechRegion string = speech.outputs.speechRegion
output speechResourceName string = speech.outputs.speechName
