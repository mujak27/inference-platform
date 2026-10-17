# Retained local model storage

Issue #5 uses the existing K3s local-path provisioner, not another storage service.
The dedicated `local-path-retain` StorageClass is **not default**. The bundled
default `local-path` class remains unchanged with Delete policy; the model PVC
explicitly selects the retained class. A StorageClass reclaim policy cannot be
patched in place, so do not attempt to patch/recreate the bundled class.

## Approved bootstrap boundary

After inspecting the provisioner, free space, ext4 mount, absence of conflicting
resources, and obtaining installation/storage approval, use checksummed Kubernetes
1.35 kubectl over authenticated, TLS-verifying private access:

```sh
kubectl create --dry-run=server -f bootstrap/storage/local-path-retain.yaml
kubectl create -f bootstrap/storage/local-path-retain.yaml
kubectl create -f apps/vllm/base/namespace.yaml
kubectl -n inference create -f apps/vllm/base/model-cache.yaml
```

These commands are first-install instructions, not a blind rerun/update procedure.
If any resource exists, inspect it rather than deleting/recreating it. Apply **only**
the class, namespace and PVC here, never the entire serving overlay. No Argo CD,
vLLM Deployment, Service, model download, GPU request or firewall change is needed.

The 20 GiB RWO claim uses WaitForFirstConsumer. It is expected to stay Pending
until a schedulable disposable consumer mounts it; do not force `nodeName`, since
that bypasses scheduler volume binding. Verify the bound PV's actual Retain
policy, capacity, claim UID, node affinity and ext4 backing path, not just the
StorageClass YAML. Keep `Prune=false,Delete=false` on both namespace and PVC.

## Persistence and ownership

Use the cached digest-pinned vLLM image with a Python-only entrypoint and **no GPU**
request. Match the future cache profile: root, dropped capabilities, no privilege
escalation, no API token, RuntimeDefault seccomp, PVC mounted at `/models`, and
`HF_HOME=/models/huggingface`. Bound CPU, RAM and pod lifetime.

On the newly provisioned empty volume, create `huggingface` as root:root mode 0750
and `.issue5-storage-probe` mode 0700. Write/fsync a small unique marker, retain its
SHA-256 privately, and require pod exit 0. Delete only the named disposable writer
pod. A distinct replacement pod must read the same checksum and successfully
write another small probe file without chmod/chown. Require exit 0 and delete that
pod too. Preserve the probe directory for the separately approved reboot check.

The provisioner's volume root is root:root mode 0777 by default, beneath its
protected host directory; the prepared Hugging Face cache is mode 0750. This is a
single-owner root-container lab, not multi-tenant isolation. Do not recursively
chmod/chown an existing cache. If contents or ownership differ from the reviewed
state, stop and inspect.

## Capacity and retention limits

- Local-path requests are **not filesystem quotas or preallocation**. `20Gi` on
  the PVC/PV does not prevent a container from filling the host filesystem.
- Data lives on one node's existing ext4 filesystem. It is **not replicated or
  backed up**. Retain avoids automatic reclaim deletion, not disk/node failure.
- Namespace/PVC Argo annotations prevent normal Argo pruning/deletion, not direct
  kubectl deletion, namespace deletion or administrator actions. Never delete
  the real model PVC/namespace to test retention or as routine cleanup.
- Proposed operational free-space floor: **100 GiB**; stop new acquisition below
  **125 GiB** to leave margin. Neither is currently an enforced cluster policy.
  Recheck available bytes before and during any future approved download.
- Inspected pinned model revision: **4,063,515,592 bytes** of safetensors and
  **4,079,450,110 bytes** for the listed repository files. Metadata only; no weights
  downloaded. Budget **20 GiB** for this one revision including temporary/cache
  growth, but enforce a monitored transfer limit before acquisition; do not mistake
  the PVC request for enforcement. Extra revisions/download caches can exceed it.
- Existing containerd directory is about **30.53 GiB** including retained images.
  Image GC thresholds 85%/80% and 5%-free eviction thresholds do not guarantee a
  100-GiB floor. The future serving spec's 20-GiB ephemeral-storage limit does not
  bound persistent-volume bytes, image pulls, or all host logs. Review each new
  image's compressed/unpacked footprint and monitor growth; do not prune the
  accepted CUDA/vLLM image as test cleanup.
- Observed kubelet log rotation is **10 MiB × 5 files per container** (a rotation
  target, not an instantaneous hard cap). Pod churn, system journal/syslog and
  unrelated desktop workloads can grow independently. No dedicated project-wide
  log quota/100-GiB disk guard is installed. Journal/syslog settings were inspected,
  not modified; journal usage was 24 MiB and pod logs about 200 KiB at inspection.
- Stage-B free space was **395.52 GiB**, leaving about **275.52 GiB** above the
  proposed floor after budgeting a full 20 GiB model cache. This is a point-in-time
  budget, not a guarantee. NTFS disks remain untouched.

See `docs/versions.md` for actual run timestamps, results and private evidence
locators. Pod-replacement persistence and the separately approved reboot check
passed, including the original marker, cache ownership and a fresh write.
Backups and explicit destruction approval are required before any final data
cleanup.
