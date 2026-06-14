// ── Key Vault Module ──────────────────────────────────────────────────────────
param prefix string
param env string
param location string

@description('Object ID of the principal that will get initial secret access (e.g. deployment SP or your user)')
param adminObjectId string = ''

var kvName = '${prefix}-kv-${env}'

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    // API-key demo mode: use access policies rather than RBAC
    enableRbacAuthorization: false
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    accessPolicies: !empty(adminObjectId)
      ? [
          {
            tenantId: subscription().tenantId
            objectId: adminObjectId
            permissions: {
              secrets: ['get', 'list', 'set', 'delete']
            }
          }
        ]
      : []
  }
}

// Placeholder secrets — values must be set post-deployment via CLI or pipeline
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: 'REPLACE_ME'
    attributes: { enabled: true }
  }
}

resource searchKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'search-api-key'
  properties: {
    value: 'REPLACE_ME'
    attributes: { enabled: true }
  }
}

resource speechKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'speech-api-key'
  properties: {
    value: 'REPLACE_ME'
    attributes: { enabled: true }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output keyVaultId string = keyVault.id
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
