# Implementation milestones

## Milestone 0 — supported environment

Status: **host/runtime, asserted CUDA, Kubernetes GPU allocation, persistent storage and reboot verified; issue-#5 PR review/merge pending**

- Changes: generic host contract; Ubuntu Desktop USB/install guide; private SSH,
  driver/bootstrap guide; read-only host preflight and local tests.
- Commands executed: local repository initialization and task worktree creation;
  documentation sources retrieved; `bash -n scripts/preflight.sh`;
  `python3 -m unittest discover -s tests -v`; `git diff --check`.
- Checks passed and evidence paths: source review, Bash syntax, and all 6 mocked
  preflight tests on the management Mac (2026-10-17). Tests are repeatable in
  `tests/test_preflight.py`; none constitutes Linux/GPU host validation.
- Installation media: owner supplied successful flash/read-back/ejection output
  on 2026-10-17. All 6,250,332,160 ISO bytes matched the signed SHA-256; see
  `docs/versions.md`. Agent-launched attempts were blocked by macOS raw-device
  permissions; the owner completed the guarded flash script in Terminal.
- OS selection changed to Ubuntu Desktop 26.04 LTS by owner decision. The media
  result above is for Ubuntu 24.04 only; 26.04 media provenance remains unverified,
  but the installed Ubuntu 26.04.1 host has now been inspected over SSH.
  See `docs/adr/0001-ubuntu-desktop-26-04.md`.
- Host-baseline work ([issue #3](https://github.com/mujak27/inference-platform/issues/3),
  2026-10-17): owner-approved root-only configuration backups, key-only SSH,
  management-client-only incoming SSH through UFW, and persistent swap disablement
  with the swap file retained. Independent key logins passed after access changes;
  SSH syntax/effective-policy and fstab verification passed; post-change host
  preflight exited 0. Driver 595.99.02 and the desktop were preserved. See
  `docs/versions.md` for observed inventory, commands, and evidence limitations.
- Power/addressing: mains auto-suspend timeout 0 and screen locking enabled;
  fresh SSH succeeded while the graphical session reported approximately 48
  minutes idle. Wi-Fi DHCP is retained by owner decision because router reservation
  is unavailable. Address changes require private-record/firewall maintenance.
- Checks not executed during issue #3: continuous idle monitoring, reboot persistence,
  container CUDA computation, Kubernetes GPU allocation/storage, or inference. No runtime
  packages were installed during issue #3 and no reboot occurred. Passwordless sudo was enabled
  by the owner, not this agent, and remains a security limitation.
- Manifest validation: GitOps/bootstrap and vLLM candidate added; see preparation
  status below. This does not verify a host, cluster, or model deployment.
- Measured inference/performance results: none. Host inventory is not CUDA acceptance.
- Known limitations: host preflight covers inventory/driver visibility only;
  desktop processes consume VRAM; dual boot interrupts availability.
- Runtime continuation (issue #4, 2026-10-17–18): approved pinned Toolkit/K3s installed;
  node and system pods Ready, NVIDIA runtime/RuntimeClass detected. Public CUDA
  validator source `187524a` has three recorded red→green cycles and the full
  20-test suite passes. Mocked tests do not prove hardware execution.
- Earlier bundled-ctr pulls timed out; the advertised local concurrency flag is
  ineffective in this fork. Owner-approved bundled `crictl pull` of the same digest
  passed (exit 0, 1534 seconds, 33,145,036,800-byte growth, minimum sampled free
  424,923,029,504 bytes). Deadline/disk guards did not fire. CRI omits all-platform
  metadata traversal but **does not serialize layers**; no runtime/config change.
- Real `sudo bash scripts/validate-cuda.sh` passed once at **2026-10-18
  00:04:51–00:04:54 WIB / 2026-10-17 17:04:51–17:04:54 UTC**: asserted CUDA
  float32 matrix product `[[58,64],[139,154]]`, PyTorch **2.13.0+cu130**, CUDA
  **13.0**, exit 0, empty stderr. Driver **595.99.02** and desktop preserved.
- Ordinary pod independently passed DNS, CA/hostname-verified TLS and asserted
  API HTTP 200 at **00:06:35–00:06:36 WIB / 17:06:35–17:06:36 UTC**, then was
  deleted. Firewall/listeners rechecked **00:11:21 WIB / 17:11:21 UTC**: wildcard
  API/kubelet/VXLAN listeners remain firewall-restricted, direct management API/
  kubelet probes time out, SSH succeeds; no public ingress configured. These are
  not external-source or UDP reachability tests. Full limits in `docs/versions.md`.
- No active pull/watchdog or owned CUDA container/network pod remains; image is
  retained for #5. No device plugin, storage test, model or serving deployment.
  Raw evidence stays private; redacted results and locators are in `docs/versions.md`.
  Known runtime advisory risks remain owner-accepted, **not fixed**. Hardware
  failure paths were not deliberately induced; public-command failure tests use
  the agreed fake-runner seam.
- Issue #4 was merged/closed in PR #9; issue #5 Stage A separately approved and
  executed **2026-10-18 01:00–01:09 WIB / 2026-10-17 18:00–18:09 UTC**. One pinned
  NVIDIA plugin 0.20.1 installed, no sharing/discovery/MPS workloads. Node capacity
  and allocatable each report one GPU. A real one-GPU Kubernetes pod passed the
  #4 synchronized CUDA assertion and exited 0; concurrent second full-GPU request
  was Pending/Unschedulable with `Insufficient nvidia.com/gpu`. Both test pods
  deleted; plugin/system pods healthy, desktop GPU baseline preserved. Authenticated
  TLS-verifying SSH-tunnel access used checksummed kubectl 1.35.9. Versions,
  configuration paths, initial node-status propagation race, and private evidence
  locators are recorded in `docs/versions.md`.
- Issue #5 Stage B separately approved and executed **01:32:34–01:32:56 WIB /
  18:32:34–18:32:56 UTC**. Dedicated nondefault local-path-retain class reuses the
  bundled provisioner; the default Delete class stays unchanged. Protected
  inference/vllm-models claim Bound at **20Gi**, actual PV **Retain**, ext4 backing
  verified. Root-owned cache write/fsync/read-checksum and another write passed
  across distinct pods (both exit 0, deleted afterward). Real namespace/PVC/PV
  and probe data preserved. Free **395.52 GiB**; non-quota/non-replicated storage
  and disk-growth/floor limitations recorded in `docs/versions.md` and storage
  runbook. No model download, serving or GitOps deployment exists yet.
- Reboot now/console recovery subsequently approved. At **01:36:01 WIB /
  18:36:01 UTC**, the normal reboot request exited 1 because GNOME blocked shutdown:
  **"A foreground process is running"**. No bypass/forced retry; boot ID unchanged,
  node/plugin healthy and retained PVC Bound. This is a pre-shutdown blocker, not
  a post-reboot failure. Owner then separately authorized inhibitor bypass.
- One normal systemd reboot with `--check-inhibitors=no` at **01:37:40 WIB /
  18:37:40 UTC** changed the boot ID; no hard reset/`--force`. Fresh SSH, active
  firewall, TLS-verifying private kubectl access, unchanged driver/runtime with
  default runc, Ready node, exactly one ready plugin, and GPU allocatable 1 all
  returned. All four system/plugin pods ready after transient startup states.
  At **01:39:42 WIB / 18:39:42 UTC**, a new one-GPU pod proved the original retained
  marker, replacement-pod file, cache ownership, new persistent write, and the
  asserted CUDA matrix result; exit 0, pod removed, actual PVC/PV UIDs preserved.
  No model download/serving; advisories remain unpatched. See `docs/versions.md`
  for versions, observations, exposure limitations and private evidence.
- Configuration/evidence snapshot: `f1da27dca926080274c03d280c24abe0b53efc2b`,
  committed after approved host execution. Next: PR review/merge and issue-#5 closeout.
  Do not start issue #6/GitOps/model serving automatically. All 20 unit tests and
  schema checks passed: existing suite 74 resources (71 valid, 3 upstream CRDs
  skipped), plus 5 valid storage/plugin resources; no invalid/errors.

## GitOps and first-serving preparation — in progress, not runtime verified

Changes: `bootstrap/`, `infra/`, and `apps/` layout; pinned Argo CD and vLLM/model
candidates; manual non-cascading Applications; private Service and retained model
PVC; probes and bounded shared memory; streaming smoke test; CI/static checks.
See `docs/gitops.md` for gates, commands, rollback, and cleanup.

Static checks passed on the management Mac (2026-10-17):
`python3 -m unittest discover -s tests -v` (15 tests),
`bash -n scripts/preflight.sh scripts/validate-manifests.sh`, and
`bash scripts/validate-manifests.sh` (with kubeconform v0.8.0 on PATH):
74 rendered resource instances, 71 valid, 0 invalid/errors, 3 explicitly skipped
upstream CRD objects. An intentionally invalid Application with a numeric
`spec.source.repoURL` was rejected by the extracted Argo schema. Generated
artifacts are local under `.local/`; rerun commands to reproduce the checks.

Checks not executed for GitOps/serving: Application apply, Argo Synced/Healthy,
model downloads, real streaming inference, PVC reuse, reconciliation and rollback.
K3s bootstrap, standalone CUDA computation and Kubernetes GPU allocation are
observed above; pod-replacement storage and reboot survival are verified, but all
GitOps/serving runtime results remain pending.

Next concrete action: finish milestone 0 hardware gates before any child Application
sync; GitOps preparation is already merged. llm-d, sharing, and LMCache are deferred.

## Runtime milestones — not verified

1. One real vLLM replica: pinned runtime/model, persistent weights, probes,
   bounded shared memory, private Service, real streaming smoke test.
2. GitOps: Argo CD, declared desired state, readiness ordering, schema/render
   checks, reconciliation/rollback proof, persistent-data retention guidance.
3. Two real replicas on one shared GPU: separate output verification, stable
   concurrency/memory, safe rolling updates without a third GPU share.
4. llm-d: compatible gateway/scheduler, endpoint-selection evidence, pod-removal
   recovery, load-aware then cache-aware routing only with validated signals.
5. Observability/benchmarks: discovered metrics, controlled workloads, TTFT/token
   latency/throughput/error distributions, run IDs/versions/Git SHA/cache state.
6. LMCache: pinned compatible stack, bounded CPU tier, verified KV writes/reads,
   cold/warm/eviction controls and failure tests; two-replica reuse is a separate result.
7. Portfolio: reproducible quickstart, architecture/limitations, runbooks, measured
   results and demo. Simulator data must never be presented as real inference.

Every milestone must separate static validation from observed runtime behavior.
No later acceptance criterion is satisfied by this initial scaffold.
