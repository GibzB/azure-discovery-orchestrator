targetScope = 'resourceGroup'

// ── Parameters ───────────────────────────────────────────────────────────────
@description('Deployment environment (dev | test | prod)')
@allowed(['dev', 'test', 'prod'])
param env string = 'dev'

@description('Primary Azure region')
param location string = resourceGroup().location

@description('Naming prefix for all resources')
param prefix string = 'discoveryai'

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

module containerApps './modules/containerapps/containerapps.bicep' = {
  name: 'containerAppsModule'
  params: {
    prefix: prefix
    env: env
    location: location
    logAnalyticsWorkspaceId: monitor.outputs.logAnalyticsWorkspaceId
    logAnalyticsSharedKey: monitor.outputs.logAnalyticsSharedKey
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output openAiEndpoint string = openai.outputs.endpoint
output searchEndpoint string = aiSearch.outputs.endpoint
output cosmosEndpoint string = cosmos.outputs.endpoint
output containerAppFqdn string = containerApps.outputs.fqdn
output appInsightsConnectionString string = monitor.outputs.appInsightsConnectionString
