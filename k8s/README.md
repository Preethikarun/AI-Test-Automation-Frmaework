# Azure Kubernetes Service — deployment architecture

## Overview

Tests run as Kubernetes Jobs on Azure AKS. Jobs are the correct
Kubernetes primitive for test suites — they run to completion,
report an exit code, and clean up automatically.

## Architecture

```
GitHub Actions CI
       ↓
   docker build + push → Azure Container Registry (ACR)
       ↓
   az aks get-credentials
       ↓
   kubectl apply -f k8s/test-job.yaml
       ↓
   AKS pulls image from ACR → runs pytest in pod
       ↓
   Pod completes → exit code collected → reports uploaded
```

## Files in this folder

| File | Purpose |
|------|---------|
| namespace.yaml | Isolates test workloads in ai-test-framework namespace |
| secret-template.yaml | Template for API key secrets — values injected by CI |
| test-job.yaml | Full test suite — all tests, all markers |
| smoke-job.yaml | Smoke tests only — faster feedback on every push |

## Prerequisites

```bash
# Install Azure CLI
# Windows: winget install Microsoft.AzureCLI
# Mac: brew install azure-cli

# Install kubectl
# Windows: winget install Kubernetes.kubectl
# Mac: brew install kubectl

# Log in to Azure
az login

# Set your subscription
az account set --subscription YOUR_SUBSCRIPTION_ID
```

## One-time cluster setup

```bash
# Create resource group
az group create \
  --name rg-ai-test-framework \
  --location australiaeast

# Create Azure Container Registry
az acr create \
  --resource-group rg-ai-test-framework \
  --name YOURACRNAME \
  --sku Basic

# Create AKS cluster (smallest available — cost-effective)
az aks create \
  --resource-group rg-ai-test-framework \
  --name aks-ai-test-framework \
  --node-count 1 \
  --node-vm-size Standard_B2s \
  --attach-acr YOURACRNAME \
  --generate-ssh-keys

# Get credentials for kubectl
az aks get-credentials \
  --resource-group rg-ai-test-framework \
  --name aks-ai-test-framework

# Verify connection
kubectl get nodes
```

## Deploy test infrastructure

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (values from your .env or GitHub Secrets)
kubectl create secret generic ai-test-secrets \
  --namespace=ai-test-framework \
  --from-literal=GEMINI_API_KEY=your-key-here \
  --from-literal=ANTHROPIC_API_KEY=your-key-here

# Create ACR pull secret
kubectl create secret docker-registry acr-credentials \
  --namespace=ai-test-framework \
  --docker-server=YOURACRNAME.azurecr.io \
  --docker-username=YOURACRNAME \
  --docker-password=$(az acr credential show \
      --name YOURACRNAME \
      --query passwords[0].value -o tsv)
```

## Build and push image to ACR

```bash
# Log in to ACR
az acr login --name YOURACRNAME

# Build and tag
docker build -t YOURACRNAME.azurecr.io/ai-test-framework:latest .

# Push to ACR
docker push YOURACRNAME.azurecr.io/ai-test-framework:latest
```

## Run tests on AKS

```bash
# Run full test suite
kubectl apply -f k8s/test-job.yaml

# Run smoke tests only
kubectl apply -f k8s/smoke-job.yaml

# Watch job progress
kubectl get jobs -n ai-test-framework -w

# Get pod name and view logs
POD=$(kubectl get pods -n ai-test-framework \
  -l app=ai-test-framework \
  --no-headers -o custom-columns=":metadata.name")
kubectl logs $POD -n ai-test-framework

# Check exit code (0 = all tests passed)
kubectl get job ai-test-run \
  -n ai-test-framework \
  -o jsonpath='{.status.conditions[0].type}'
```

## Clean up after demo

```bash
# Delete the job (keeps cluster running)
kubectl delete job ai-test-run -n ai-test-framework

# Delete the cluster entirely (stops all billing)
az aks delete \
  --resource-group rg-ai-test-framework \
  --name aks-ai-test-framework \
  --yes --no-wait
```

## Cost estimate

| Resource | Size | Estimated cost |
|----------|------|---------------|
| AKS cluster | 1x Standard_B2s node | ~$0.04/hour |
| ACR | Basic tier | ~$0.17/day |
| Full test run | ~3 minutes | ~$0.002 |
| Smoke test run | ~1 minute | ~$0.001 |

**Total for a 4-hour demo session: under $1.00**

Delete the cluster after the demo to stop billing entirely.

## Why AKS over other options

See `docs/pm/DECISION_LOG.md` DEC-006 for the full reasoning.
Short answer: AKS is the most commonly required Kubernetes platform
in enterprise environments in NZ/AU/UK markets. The manifests
are Kubernetes-standard and portable to EKS or GKE with only
registry URL changes.
