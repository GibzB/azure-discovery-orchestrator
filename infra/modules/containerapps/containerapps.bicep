// ── Container Apps Module ─────────────────────────────────────────────────────
param prefix string
param env string
param location string
param logAnalyticsWorkspaceId string
param logAnalyticsSharedKey string

@description('Container image to deploy — override in pipeline after build')
param backendImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

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
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      // Secrets are referenced from Key Vault at runtime via env vars
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
            {
              name: 'ENV'
              value: env
            }
            {
              name: 'LOG_LEVEL'
              value: env == 'prod' ? 'WARNING' : 'INFO'
            }
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
