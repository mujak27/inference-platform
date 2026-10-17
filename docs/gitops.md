# GitOps foundation (prepared, not deployed)

This follows the directory conventions of
[mujak27/k8s-crossplane](https://github.com/mujak27/k8s-crossplane):

```text
bootstrap/
  argocd/                  pinned Argo CD installation and namespace
  root-app.yaml            manual root Application → infra/
infra/
  kustomization.yaml       project policy and child Application registry
  inference-project.yaml   repository/namespace/resource allowlist
apps/
  kustomization.yaml       child Application registry
  vllm/
    application.yaml       manual child Application → single-replica overlay
    base/                  workload, model PVC, configuration, private Service
    overlays/single-replica/
```

Do not copy the reference repository's Crossplane, ingress, TLS, or progressive
sync components: none is required for the first serving slice. NVIDIA runtime,
Kubernetes distribution, device plugin, and storage remain host-validation gates.
No existing cluster is contacted by validation commands.

## What is prepared

- Argo CD **v3.5.5**, installed from release commit
  `a5038b0e2bbac1715754380ae0084df8e3d5b48c`. Upstream images have explicit version
  tags. Argo CD remains in the documented manual bootstrap boundary for now;
  it does not manage its own installation through an Application yet.
- Root and vLLM Applications point at this public repository's `main` branch.
  Neither has auto-sync or cascading deletion enabled. Merging this PR does not
  install Argo CD, consume a GPU, or change a cluster.
- An inference AppProject permits only this source repository, the `inference`
  destination namespace, Namespace creation, and the workload's required kinds.
  The root uses the built-in `default` project and is an administrative entry
  point. Only trusted administrators should edit/sync it. This is not tenant isolation.
- Single-replica vLLM **v0.31.0**, pinned by Docker Hub manifest-list digest,
  with Qwen/Qwen3-1.7B and tokenizer/chat template pinned to model revision
  `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`.
- FP16, TP=1, context 4096, concurrency 4, APC enabled, GPU utilization budget
  0.80. These are **untested single-replica starting settings**. The later 0.35
  shared-GPU profile is deliberately not included.
- `/health` startup/readiness checks; startup allows 30 minutes for download/load.
  Slow networks may require a longer window. No liveness probe restarts a busy
  engine indiscriminately. Rollouts use zero surge and permit downtime on one GPU.
- A 20 GiB RWO PVC caches downloads under `/models/huggingface`; no credentials
  are needed for this public, ungated model. A bounded 2 GiB memory-backed
  `/dev/shm` counts toward the container's 16 GiB RAM limit. CPU/RAM/ephemeral
  storage requests are provisional; they do not cap VRAM.

The inspected amd64 image declares **CUDA 13.0.2** and includes SM 8.6 in its
build architecture list. Use a compatible driver (vLLM's CUDA 13 guidance calls
for R580 or newer); do not assume CUDA forward compatibility works on a GeForce
3090. Image inspection and documented architecture support are not a successful
CUDA test. Do not install separate PyTorch/CUDA packages into this pinned image.

The image's default user is root. The initial lab workload keeps that default,
drops Linux capabilities, disables privilege escalation, and does not mount a
Kubernetes API token. Model files are created as root-owned on the PVC; verify
CSI permissions before use. A non-root profile requires validating all model,
JIT/compiler, and cache write paths; do not blindly chmod/chown existing data.
This profile is not suitable as an unreviewed multi-tenant deployment.

## Validate locally, without a cluster

Use Python 3.12 in CI, PyYAML 6.0.3, kubectl v1.37.1 (Kustomize v5.8.1), and
kubeconform v0.8.0. Install the matching binaries from official releases and
verify their checksums; the workflow shows exact versions and commands. A local
Python virtual environment can live in ignored `.local/venv`.

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
bash scripts/validate-manifests.sh
```

Rendering needs network access for the commit-pinned Argo CD manifest. Schema
validation uses a commit-pinned Kubernetes schema set at **1.35.0**; that is a
static validation baseline, not a selected/verified cluster version. Select the
host cluster separately and update the baseline if necessary.

Application and AppProject schemas are extracted from the **same pinned Argo CD
CRDs** used for bootstrap. Missing schemas are errors. The three upstream CRD
objects themselves are explicitly skipped by kubeconform because the Kubernetes
schema set does not include a CRD-object schema; they are parsed for extraction,
not claimed API-server validated. CI also checks manual sync, storage retention,
image/model pins, config references, private access, probes, and zero-surge rollout.
Generated YAML/schema files remain ignored under `.local/`.

## Before any deployment

1. Merge the PR. Application sources track `main`, not an unpublished local branch.
2. Validate Linux, exact driver compatibility, **container CUDA computation**,
   and Kubernetes GPU allocation with exactly one device-plugin installation.
3. Confirm the device plugin advertises **`nvidia.com/gpu`**, not only the later
   `nvidia.com/gpu.shared` resource. Confirm the container runtime exposes CUDA
   for this pod profile. Some distributions need an explicit `runtimeClassName`;
   add the observed runtime class through the overlay if required.
4. Verify the selected Argo CD release supports the actual Kubernetes version.
5. Verify a default StorageClass exists, its provisioner is healthy, and at least
   20 GiB is available. The PVC intentionally omits `storageClassName` to use
   that default; select an explicit observed class through Git if needed. A
   WaitForFirstConsumer PVC may bind only when its GPU pod can be scheduled.
6. Check CPU/RAM/VRAM/storage headroom, idle GPU memory, model download access,
   and writable model-cache ownership. Record actual versions/evidence.

## Manual Argo CD bootstrap (operator only, after the gates above)

Choose and verify the target context; all following commands mutate that cluster.
Never run them against a guessed current context. Review the rendered installation
before applying its cluster-scoped RBAC and CRDs.

```sh
kubectl config current-context
mkdir -p .local
kubectl kustomize bootstrap/argocd > .local/argocd-review.yaml
# Inspect .local/argocd-review.yaml before continuing.
kubectl apply --server-side -f .local/argocd-review.yaml
kubectl wait --for=condition=Established --timeout=120s \
  crd/applications.argoproj.io crd/appprojects.argoproj.io crd/applicationsets.argoproj.io
kubectl -n argocd wait --for=condition=Available deployment --all --timeout=600s
kubectl -n argocd rollout status statefulset/argocd-application-controller --timeout=600s
kubectl apply -f bootstrap/root-app.yaml
kubectl -n argocd port-forward svc/argocd-server 8080:443
```

Create `.local/` first if local validation has not run. Argo CD's default Service
stays ClusterIP; the default port-forward binds loopback. Use `https://localhost:8080`
from the kubectl client and verify the expected local certificate warning rather
than publishing ingress. Follow the pinned Argo CD getting-started instructions
to retrieve the initial admin password **locally**, change it, and remove the
initial-password Secret after confirming access. Never save that password in Git,
shell transcripts, or benchmark evidence.

In the UI, manually sync **root without pruning**. It installs the AppProject
and registers the vLLM Application only. The project has an earlier sync wave,
but waves are not a replacement for the controller/CRD readiness checks above.
Do not sync the child until all host gates pass. Then manually sync **vllm
without pruning**, inspect events/logs, and wait for readiness:

```sh
kubectl -n inference rollout status deployment/vllm --timeout=1800s
kubectl -n inference port-forward svc/vllm 8000:8000
```

In a second terminal:

```sh
python3 scripts/smoke-test.py
```

The smoke test prints content as SSE chunks arrive and fails for empty output,
an error, missing SSE content type, or a stream missing `[DONE]`. It records
client first-content and end-to-end times, not a calibrated token benchmark.
Verify content actually arrives before completion on the real endpoint; simulator
fixtures in unit tests do not establish real model output or streaming behavior.
Save pod readiness, logs, idle/load GPU memory, exact commit, and command output
as redacted evidence. Both serving and Argo Synced/Healthy remain pending now.

## Change, rollback, and cleanup

Edit model/revision, precision, context, concurrency, and GPU budget through the
base ConfigMap generator or an overlay merge. Config hashes roll pods when
settings change. Edit images with a digest in Git and replicas in the overlay;
review resource/storage changes with the actual host capacity. A model change
must keep model/tokenizer revision and the client served-model name consistent.

Once real serving works, prove reconciliation by committing a small reviewed
config change, manually syncing vLLM, and recording its observed effect. Revert
that commit and sync again to prove rollback. Do not declare milestone 2 verified
until those runtime observations and Synced/Healthy evidence exist. Auto-sync can
be enabled in a later reviewed change after this manual recovery path works.

Neither Application has a resources finalizer; normal non-cascading deletion
leaves workloads behind. **Do not choose cascading deletion in the UI.** The
PVC and inference Namespace carry `Prune=false,Delete=false`, protecting them
from normal Argo resource deletion/pruning, not from direct `kubectl delete`,
namespace deletion, or storage failures. Audit the live resource inventory and
PV reclaim policy; never delete the Namespace/PVC as routine rollback. Deleting
the root alone does not stop inference or uninstall Argo CD. To stop inference
without losing downloads, commit `replicas: 0` in the overlay, sync the child,
and retain the Namespace/PVC/PV. Backup or explicit data-destruction approval is
required before final storage cleanup.

## Upstream sources reviewed 2026-10-17

- [Argo CD v3.5.5 release](https://github.com/argoproj/argo-cd/releases/tag/v3.5.5)
- [Pinned Argo CD installation/CRDs](https://github.com/argoproj/argo-cd/blob/a5038b0e2bbac1715754380ae0084df8e3d5b48c/manifests/install.yaml)
- [vLLM v0.31.0 Kubernetes guide](https://github.com/vllm-project/vllm/blob/v0.31.0/docs/deployment/k8s.md)
- [vLLM v0.31.0 GPU/CUDA guide](https://github.com/vllm-project/vllm/blob/v0.31.0/docs/getting_started/installation/gpu.cuda.inc.md)
- [vLLM v0.31.0 argument definitions](https://github.com/vllm-project/vllm/blob/v0.31.0/vllm/engine/arg_utils.py)
- [Qwen revision metadata](https://huggingface.co/Qwen/Qwen3-1.7B/tree/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e)

The registry manifest/config was inspected without downloading model weights or
the inference image. Full PyTorch/package inventory remains a runtime evidence item.
