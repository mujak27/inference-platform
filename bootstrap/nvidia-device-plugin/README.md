# Standalone NVIDIA device plugin

Owner-approved issue-#5 bootstrap, not an Argo CD Application. Keep runc default;
use `runtimeClassName: nvidia` on this plugin and every GPU workload. No GPU
Operator, sharing, GFD, NFD, or MPS control daemon is installed.

## Pinned inputs

- Upstream chart/app **0.20.1**, from
  <https://nvidia.github.io/k8s-device-plugin/stable/nvidia-device-plugin-0.20.1.tgz>.
- Chart SHA-256:
  `b705142f03ac17906bfcface9319e2f7b9a570d2af7f04f23252723ce2c0bb8e`,
  matched against the upstream chart index before rendering.
- Image: `nvcr.io/nvidia/k8s-device-plugin:v0.20.1`, pinned by index digest in
  `values.yaml`; linux/amd64 manifest:
  `sha256:d279ecdb47b252c4cd96f4224650e9808c36012f6979570c9611ddbc5b0749a7`.
- Review [upstream prerequisites and RuntimeClass guidance](https://github.com/NVIDIA/k8s-device-plugin/blob/v0.20.1/README.md)
  against the actual driver, Toolkit, and K3s runtime before installation.

`affinity: null` removes the chart's default discovery-label requirement. An empty
map does **not** remove it because Helm merges defaults. The single-node lab has
no discovery-label service; Linux/amd64 selectors are sufficient here, not for a
mixed multi-node cluster. Initialization failures are fatal; NVML discovery,
envvar allocation, UUID identity, and no MIG/sharing are explicit.

## Render and apply only after operational approval

Use a protected working directory outside Git for downloaded/rendered files.
Download the exact chart above, verify its SHA-256, and render with the values
from the reviewed configuration commit:

```sh
helm template nvdp "$CHART_ARCHIVE" \
  --namespace nvidia-device-plugin --kube-version 1.35.9 \
  --values bootstrap/nvidia-device-plugin/values.yaml \
  --show-only templates/service-account.yml \
  --show-only templates/role.yml \
  --show-only templates/role-binding.yml \
  --show-only templates/daemonset-device-plugin.yml > "$RENDERED_MANIFEST"
```

Chart 0.20.1 also renders an MPS control DaemonSet whenever the plugin is enabled.
Selecting only the four templates above excludes it entirely. Do not substitute
an unfiltered `helm install`. This is a **chart-rendered kubectl deployment**, not
a Helm-managed release. Rendered Helm labels do not imply a Helm release exists.
The plugin template retains upstream MPS/CDI host-directory mounts; mounts alone
do not enable sharing or start an MPS daemon. Do not remove host directories during
cleanup.

Before applying, inspect for exactly one DaemonSet, one plugin container, the
digest pin, NVIDIA RuntimeClass, absent discovery affinity, no sharing ConfigMap,
and dropped capabilities/no privilege escalation. Check the cluster for an
existing plugin or Operator; never add a second plugin.

Use a checksummed Kubernetes **1.35** kubectl and a mode-0600 kubeconfig over a
loopback-bound SSH tunnel. Keep CA/server/client-certificate verification enabled;
do not expose the API or use `insecure-skip-tls-verify`.

```sh
kubectl create namespace nvidia-device-plugin
kubectl apply --dry-run=server -f "$RENDERED_MANIFEST"
kubectl apply -f "$RENDERED_MANIFEST"
kubectl -n nvidia-device-plugin rollout status \
  daemonset/nvdp-nvidia-device-plugin --timeout=600s
kubectl get nodes -o json
```

Pod readiness can precede the node-status GPU update. Wait for capacity **and**
allocatable `nvidia.com/gpu=1`; if absent, inspect plugin registration logs before
changing anything. Save the actual pod image ID and config/log evidence privately.

## Live acceptance and cleanup

Reuse the exact asserted CUDA payload in `scripts/validate-cuda.sh`, but run it
in a disposable Kubernetes pod requesting/limiting one `nvidia.com/gpu`, with
NVIDIA RuntimeClass and the already-cached digest-pinned vLLM image. Override its
entrypoint; do not start vLLM or download weights. Bound CPU, RAM and lifetime.

Hold the successful pod's allocation briefly after its synchronized numerical
assertion. Submit a second one-GPU pod without `nodeName`, and retain its Pending,
`PodScheduled=False` / `Unschedulable`, `Insufficient nvidia.com/gpu` condition and
scheduler events while the holder is Running. Delete the contender **before**
releasing the holder; then require holder phase Succeeded and container exit 0.
Delete only those named disposable pods. Preserve the plugin and cached image.
This tests scheduler allocation, not isolation from the host's desktop processes.

Any plugin rollback needs operational review: stop disposable GPU tests first,
then remove only this deployment's four rendered resources if approved. Do not
delete a model namespace/PVC, prune cached images, change the default runtime, or
restart K3s as cleanup. Reboot and storage acceptance are separate gates.
