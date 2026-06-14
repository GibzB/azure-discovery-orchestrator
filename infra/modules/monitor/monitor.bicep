// ── Monitor Module (Log Analytics + Application Insights) ────────────────────
param prefix string
param env string
param location string

var logName = '${prefix}-log-${env}'
var appInsightsName = '${prefix}-appi-${env}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output logAnalyticsId string = logAnalytics.id
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId

@secure()
output logAnalyticsSharedKey string = logAnalytics.listKeys().primarySharedKey

@secure()
output appInsightsConnectionString string = appInsights.properties.ConnectionString
// appInsightsInstrumentationKey removed — duplicate secret, use ConnectionString instead
