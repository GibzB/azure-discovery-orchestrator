using '../main.bicep'

param env = 'dev'
param location = 'italynorth'
param prefix = 'discoveryai'
// backendImage is set by the backend-deploy pipeline after the Docker build.
// Using the latest ACR image tag here so infra deploys don't reset to helloworld.
param backendImage = 'discoveryaiacr.azurecr.io/backend:latest'

// Runtime secrets — passed securely via pipeline variable group or az deployment create --parameters
// DO NOT commit actual secret values here. Use pipeline secrets or Key Vault references.
// These are read by the infra-deploy pipeline from the 'discoveryai-dev' variable group.
param azureOpenAiKey = ''
param azureSpeechKey = ''
param searchKey = ''
param cosmosKey = ''
param storageConnectionString = ''
