using '../main.bicep'

param env = 'dev'
param location = 'italynorth'
param prefix = 'discoveryai'
// backendImage is set by the backend-deploy pipeline after the Docker build.
// Using the latest ACR image tag here so infra deploys don't reset to helloworld.
param backendImage = 'discoveryaiacr.azurecr.io/backend:latest'
