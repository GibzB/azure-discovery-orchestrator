// Azure Discovery Orchestrator - Main Bicep Entry Point
targetScope = 'subscription'

@description('Environment name (dev, test, prod)')
param environmentName string

@description('Primary Azure region')
param location string = 'eastus'

@description('Resource group name')
param resourceGroupName string = 'rg-azure-discovery-${environmentName}'

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
}

// Modules
module networking 'modules/networking/main.bicep' = {
  scope: rg
  name: 'networking'
  params: {
    environmentName: environmentName
    location: location
  }
}

module keyvault 'modules/keyvault/main.bicep' = {
  scope: rg
  name: 'keyvault'
  params: {
    environmentName: environmentName
    location: location
  }
}

module storage 'modules/storage/main.bicep' = {
  scope: rg
  name: 'storage'
  params: {
    environmentName: environmentName
    location: location
  }
}

module openai 'modules/openai/main.bicep' = {
  scope: rg
  name: 'openai'
  params: {
    environmentName: environmentName
    location: location
  }
}

module speech 'modules/speech/main.bicep' = {
  scope: rg
  name: 'speech'
  params: {
    environmentName: environmentName
    location: location
  }
}

module aiSearch 'modules/ai-search/main.bicep' = {
  scope: rg
  name: 'ai-search'
  params: {
    environmentName: environmentName
    location: location
  }
}

module cosmos 'modules/cosmos/main.bicep' = {
  scope: rg
  name: 'cosmos'
  params: {
    environmentName: environmentName
    location: location
  }
}

module sql 'modules/sql/main.bicep' = {
  scope: rg
  name: 'sql'
  params: {
    environmentName: environmentName
    location: location
  }
}

module containerApps 'modules/containerapps/main.bicep' = {
  scope: rg
  name: 'containerapps'
  params: {
    environmentName: environmentName
    location: location
  }
}

module monitor 'modules/monitor/main.bicep' = {
  scope: rg
  name: 'monitor'
  params: {
    environmentName: environmentName
    location: location
  }
}

module frontdoor 'modules/frontdoor/main.bicep' = {
  scope: rg
  name: 'frontdoor'
  params: {
    environmentName: environmentName
    location: location
  }
}
