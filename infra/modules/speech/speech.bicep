// ── Azure Speech Services Module (STT + TTS) ──────────────────────────────────
param prefix string
param env string
param location string

var speechName = '${prefix}-spch-${env}'

resource speech 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: speechName
  location: location
  kind: 'SpeechServices'
  sku: { name: 'S0' }
  properties: {
    publicNetworkAccess: 'Enabled' // API-key demo mode
    disableLocalAuth: false
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output speechId string = speech.id
output speechName string = speech.name
// Endpoint format Speech SDK expects: wss://<region>.stt.speech.microsoft.com
// The SDK only needs the region + key, not the endpoint URL directly
output speechRegion string = location
