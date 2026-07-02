// ── Container Apps Module ─────────────────────────────────────────────────────
param prefix string
param env string
param location string
param logAnalyticsWorkspaceId string

@secure()
param logAnalyticsSharedKey string

@description('Container image to deploy — override in pipeline after build')
param backendImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// ── App configuration params (set in bicepparam / pipeline) ──────────────────
param azureOpenAiEndpoint string = ''
@secure()
param azureOpenAiKey string = ''
param azureOpenAiDeployment string = 'gpt-oss-120b'
param azureOpenAiApiVersion string = '2024-12-01-preview'

@secure()
param azureSpeechKey string = ''
param azureSpeechRegion string = 'italynorth'
param azureSpeechVoice string = 'en-US-AvaMultilingualNeural'

param searchEndpoint string = ''
@secure()
param searchKey string = ''
param searchIndex string = 'knowledgebase'

param cosmosEndpoint string = ''
@secure()
param cosmosKey string = ''
param cosmosDatabase string = 'discovery'
param cosmosContainer string = 'sessions'

@secure()
param storageConnectionString string = ''
param storageReportsContainer string = 'reports'
param storageKnowledgebaseContainer string = 'knowledgebase'

param corsOriginsRaw string = 'http://localhost:5173'

var caeName = '${prefix}-cae-${env}'
var caName = '${prefix}-ca-backend-${env}'

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: caeName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspaceId
        sharedKey: logAnalyticsSharedKey
      }
    }
  }
}

resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: caName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'ENV',                             value: env }
            { name: 'LOG_LEVEL',                       value: env == 'prod' ? 'WARNING' : 'INFO' }
            { name: 'AZURE_OPENAI_ENDPOINT',           value: azureOpenAiEndpoint }
            { name: 'AZURE_OPENAI_KEY',                value: azureOpenAiKey }
            { name: 'AZURE_OPENAI_DEPLOYMENT',         value: azureOpenAiDeployment }
            { name: 'AZURE_OPENAI_API_VERSION',        value: azureOpenAiApiVersion }
            { name: 'AZURE_SPEECH_KEY',                value: azureSpeechKey }
            { name: 'AZURE_SPEECH_REGION',             value: azureSpeechRegion }
            { name: 'AZURE_SPEECH_VOICE',              value: azureSpeechVoice }
            { name: 'SEARCH_ENDPOINT',                 value: searchEndpoint }
            { name: 'SEARCH_KEY',                      value: searchKey }
            { name: 'SEARCH_INDEX',                    value: searchIndex }
            { name: 'COSMOS_ENDPOINT',                 value: cosmosEndpoint }
            { name: 'COSMOS_KEY',                      value: cosmosKey }
            { name: 'COSMOS_DATABASE',                 value: cosmosDatabase }
            { name: 'COSMOS_CONTAINER',                value: cosmosContainer }
            { name: 'STORAGE_CONNECTION_STRING',       value: storageConnectionString }
            { name: 'STORAGE_REPORTS_CONTAINER',       value: storageReportsContainer }
            { name: 'STORAGE_KNOWLEDGEBASE_CONTAINER', value: storageKnowledgebaseContainer }
            { name: 'CORS_ORIGINS_RAW',                value: corsOriginsRaw }
          ]
        }
      ]
      scale: {
        minReplicas: env == 'prod' ? 2 : 1
        maxReplicas: env == 'prod' ? 20 : 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output environmentId string = containerAppsEnv.id
output fqdn string = backendApp.properties.configuration.ingress.fqdn
output containerAppName string = backendApp.name
output principalId string = backendApp.identity.principalId
