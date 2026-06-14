// Azure Networking Module
param environmentName string
param location string

var vnetName = 'vnet-discovery-${environmentName}'
var nsgName = 'nsg-discovery-${environmentName}'

resource nsg 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: nsgName
  location: location
  properties: {
    securityRules: []
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    subnets: [
      {
        name: 'snet-apps'
        properties: {
          addressPrefix: '10.0.1.0/24'
          networkSecurityGroup: { id: nsg.id }
        }
      }
      {
        name: 'snet-data'
        properties: {
          addressPrefix: '10.0.2.0/24'
          networkSecurityGroup: { id: nsg.id }
        }
      }
      {
        name: 'snet-ai'
        properties: {
          addressPrefix: '10.0.3.0/24'
          networkSecurityGroup: { id: nsg.id }
        }
      }
    ]
  }
}

output vnetId string = vnet.id
output appsSubnetId string = vnet.properties.subnets[0].id
output dataSubnetId string = vnet.properties.subnets[1].id
output aiSubnetId string = vnet.properties.subnets[2].id
