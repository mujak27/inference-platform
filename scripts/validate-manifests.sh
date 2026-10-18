#!/usr/bin/env bash
# Render/schema validation only: never contacts the configured Kubernetes API.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local/rendered .local/schemas
kubectl kustomize bootstrap/argocd > .local/rendered/argocd.yaml
python3 scripts/argocd-schemas.py .local/rendered/argocd.yaml .local/schemas bootstrap/llmd/crds.yaml
kubectl kustomize infra > .local/rendered/infra.yaml
kubectl kustomize apps > .local/rendered/apps.yaml
kubectl kustomize apps/vllm/base > .local/rendered/vllm-base.yaml
kubectl kustomize apps/vllm/overlays/single-replica > .local/rendered/vllm.yaml
kubectl kustomize apps/llmd/base > .local/rendered/llmd-base.yaml
kubectl kustomize apps/llmd/overlays/single-replica > .local/rendered/llmd.yaml
cp bootstrap/root-app.yaml .local/rendered/root.yaml
# The upstream Kubernetes schema set omits CRD objects. Validate Argo custom
# resources against extracted CRD schemas; report upstream CRDs as skipped.
kubeconform -strict -summary -skip CustomResourceDefinition -kubernetes-version 1.35.0 \
  -schema-location 'https://raw.githubusercontent.com/yannh/kubernetes-json-schema/aff1ca44984cbbcfa376c1cb6fdc4bb6aa0381fd/{{.NormalizedKubernetesVersion}}-standalone{{.StrictSuffix}}/{{.ResourceKind}}{{.KindSuffix}}.json' \
  -schema-location '.local/schemas/{{.ResourceKind}}.json' \
  .local/rendered
