# Version and evidence record

## llm-d issue #16 — source-only qualification slice, 2026-10-18

Fixed base `8eb55b437994afee49e79335617f602e9cc47d44`; reviewed preparation from
uncommitted `llmd-next` at `d0c1608d7e8641f6391514525b88650afc7b1697` without
modifying that worktree. [Provenance, pins and compatibility/evidence matrix](llmd-preparation.md).
No active registration, cluster/host operation, image execution or chart download
was performed. The owner subsequently approved local kubeconform installation
and schema execution; no broader candidate-runtime authorization was inferred.

- Fresh offline real and synthetic renders passed using the previously cached,
  independently checksum-reverified chart and installed Helm/Kustomize. New
  generated outputs are ignored, not committed proof. Real discovery RBAC is
  explicitly narrowed to namespaced Pod and GA InferencePool get/list/watch;
  simulator remains Pod-only. Proven vLLM 0.31.0 is unchanged.
- `LLMD_CHART=<approved-cached-chart> python3 -B -m unittest discover -s tests -v`:
  **35 tests passed, no skips** (23 unchanged baseline + 12 public CLI tests).
  Actual red→green checks covered absent inputs, real rendering/RBAC, supplied
  policy checks, stale output, required missing schema, selector overlap,
  scheduler-disable overrides and model-download arguments. Additional negative
  controls cover GPU/PVC, namespace/discovery crossover, public exposure and writes.
- Shell syntax checks for the three existing scripts and two new render wrappers,
  plus `git diff --check`, passed. Source tests used Python 3.9.6/PyYAML 6.0.3 on
  Darwin arm64; they do not execute EPP, Envoy or the simulator.
- Initial required validator commands failed because kubeconform was absent.
  After explicit approval, installed kubeconform 0.8.0 under `.local/tools` from
  the official Darwin arm64 archive, SHA256
  `f84f4dfbebf4a6b0b230385fa065a39ea35e02608c2b50d025dcf64775a69d67`,
  verified against upstream CHECKSUMS. Both full candidate commands then passed:
  real **8 valid**, simulator **10 valid**, no invalid/errors/skips. Their schema
  negative controls also passed. Real validation used the checksum-pinned cached
  GAIE CRD asset. Baseline `validate-manifests.sh` passed: **71 valid**, no invalid
  or errors, **3 CRDs intentionally skipped** by its existing policy.
  CI now declares pinned source acquisition, rerenders both candidates and
  requires their full source/schema checks. It was not run remotely.
- Pinned EPP (`a5cbe60`) phase-one/phase-two plugin-registry validation
  (`darwin/arm64`), isolated Envoy `distroless-v1.37.8` `--mode validate`
  (`linux/arm64`), and supply-chain verification with explicit owner risk
  acceptance (2026-10-18) for the unsigned Simulator `v0.11.2`, Envoy
  `distroless-v1.37.8` and standalone chart `v0.11.0` pins are recorded in
  `docs/llmd-preparation.md`. Kubernetes/CRD admission, target `linux/amd64`
  execution, live `ext_proc`, telemetry and routed SSE remain **pending**
  (blocked on #7 and #15). This does not complete #16 or unblock #17; #7 retains
  all host work.

Documentation research and host inspection dates: **2026-10-17–18**. Private SSH
inventory and approved host-baseline changes have been verified. The selected
runtime combination passed observed CUDA, allocation, storage and streaming
checks under issues #4–#6. Rollback, stop/start and a quiescent SQLite/token
backup were subsequently executed and observed under issue #7 (below); **full K3s
restore remains untested**, and these checks do not establish HA or performance
claims.

## Kubernetes GPU allocation — issue #5, Stage A

Owner explicitly approved plugin installation and disposable GPU checks; storage,
firewall/runtime changes, service interruption, and reboot were not authorized.
Source: fresh `origin/main` base `c4ef0f9`, task branch `gpu-storage-issue-5`;
configuration is `bootstrap/nvidia-device-plugin/values.yaml` and its accompanying
runbook. Configuration/evidence snapshot committed after approved execution at
`f1da27dca926080274c03d280c24abe0b53efc2b`; this records the executed configuration,
not a GitOps-managed installation. PR review/merge remains pending.

- Installed chart/app **0.20.1**, chart SHA-256
  `b705142f03ac17906bfcface9319e2f7b9a570d2af7f04f23252723ce2c0bb8e`.
  Chart-rendered kubectl deployment, **not** a Helm release; only plugin and RBAC
  templates were applied, excluding the chart's otherwise-rendered MPS DaemonSet.
  Rendered manifest SHA-256:
  `c99c26b4d650273a5fea29867d4609f5b8735246cd41867a8b8f56efd42c58a8`.
- Plugin image/pod image ID uses index
  `sha256:27c1b2553a690ca3d29889dcd61df97525d46f58272c0be8dc63c2b18f120075`;
  linux/amd64 manifest
  `sha256:d279ecdb47b252c4cd96f4224650e9808c36012f6979570c9611ddbc5b0749a7`.
  Registry index body hash matched its digest header. Exactly **one** DaemonSet
  and one plugin pod are present; no Operator, discovery services, or GPU sharing.
  NVIDIA RuntimeClass explicit; runc default and driver/runtime unchanged.
- Apply recorded **2026-10-18 01:00:59 WIB / 2026-10-17 18:00:59 UTC**.
  First rollout-readiness check preceded publication of the node GPU field and
  failed its immediate assertion. No retry install or restart: read-only recheck
  confirmed successful kubelet registration and capacity/allocatable **1**. This
  propagation race was not treated as acceptance until the fresh node assertion
  passed. No `.shared` capacity resource was present.
- Management client **kubectl v1.35.9**, darwin/arm64 binary SHA-256
  `652548e6a9405266c5acd2719703bc8d36befa46e79e151a0d646904aa32c89b`,
  verified against the official release checksum. Authenticated `/readyz`, version,
  server-side dry-run, apply and proof requests passed through a loopback-bound
  SSH tunnel, with CA/server and client-certificate verification enabled. Kubeconfig
  and raw evidence are owner-only; tunnel processes were closed after each stage.
- At **01:08:42–01:08:49 WIB / 18:08:42–18:08:49 UTC**, a disposable NVIDIA
  RuntimeClass pod requesting/limiting one GPU ran the exact #4 CUDA payload from
  the cached vLLM digest. Synchronized GPU float32 matrix assertion passed with
  `[[58.0,64.0],[139.0,154.0]]`, PyTorch **2.13.0+cu130**, CUDA **13.0**.
  While it held its allocation, the second full-GPU pod remained Pending with no
  assigned node, `PodScheduled=False`, reason `Unschedulable`, and message
  `Insufficient nvidia.com/gpu`; scheduler events and concurrent Running holder
  evidence retained. Contender removed first, holder released and observed
  Succeeded with container **exit 0**, then deleted. No model download or serving.
- Post-check **01:08:58 WIB / 18:08:58 UTC**: system/plugin pods healthy, no
  disposable GPU pods remain, `/readyz` ok, driver **595.99.02**, GPU **222 MiB /
  0%**. Root free **424,674,897,920 bytes** (about 395.51 GiB). No PVC exists;
  default local-path still has **Delete** reclaim policy. Storage/Retain and
  reboot survival remain **unverified**. Existing runtime advisories remain
  owner-accepted, not patched. Scheduling exclusivity does not isolate GPU access
  from host desktop processes.
- Local checks: all **20** existing unit tests, Bash syntax checks, and
  `git diff --check` passed. Selected chart render assertions and live server-side
  dry-runs passed. Full offline schema validation was initially unavailable, then
  passed during final verification below. No new public validator/test seam was
  introduced.

Private evidence: `<workspace-docs>/inference-platform-private/gpu-storage-issue5-2026-10-18/`:
`plugin-apply.json`, `registration-recheck.txt`, `proof-nodes-before.json`,
`proof-plugin-pods.json`, `proof-plugin-logs.json`, `holder-final-logs.json`,
`holder-final.json`, `holder-during-contention.json`, `contender-pending.json`,
`contender-events.json`, cleanup records, and `post-stage-a.txt`. Static rendering
checks are not hardware evidence; the live pod/status/log records above are.

## Persistent storage — issue #5, Stage B

Owner separately approved a dedicated retained StorageClass, protected model PVC
and pod-replacement checks. Executed **2026-10-18 01:32:34–01:32:56 WIB /
2026-10-17 18:32:34–18:32:56 UTC** (individual operation timestamps in evidence).
Configuration: `bootstrap/storage/local-path-retain.yaml`,
`apps/vllm/base/namespace.yaml`, and `apps/vllm/base/model-cache.yaml`; same task
branch/base and configuration snapshot commit as Stage A; PR review/merge pending.

- Existing healthy **rancher/local-path-provisioner v0.0.37** reused; no second
  provisioner. Dedicated nondefault **local-path-retain** has **Retain** and
  **WaitForFirstConsumer**, without expansion. Existing default **local-path**
  remains **Delete**, deliberately unchanged; no immutable StorageClass policy
  patch/recreation attempted. The model claim explicitly selects the retained
  class so later GitOps deployment cannot silently select the Delete default.
- `inference/vllm-models`: **20Gi**, RWO, **Bound** after its first consumer.
  Actual PV capacity **20Gi**, **Retain**, matching claim UID, node-local path
  on existing root **ext4**. Namespace and PVC retain
  `argocd.argoproj.io/sync-options: Prune=false,Delete=false`. Argo CD not installed.
- Two distinct disposable CPU-only pods reused the cached vLLM image, Python-only
  entrypoint, root/drop-all-capabilities/no-escalation profile, no API token, and
  RuntimeDefault seccomp. First created a new root:root **0750** Hugging Face cache
  and a **0700** probe directory with an fsynced marker, then exited **0** and was
  deleted. Replacement read the identical SHA-256 marker, verified ownership/mode,
  successfully wrote another probe, exited **0**, and was deleted. No chmod/chown
  of existing data, GPU allocation, model download, or serving process.
- Provisioner-created volume root is root:root **0777** beneath its protected host
  directory; the Hugging Face cache is **0750**. This proves compatibility with
  the prepared root-container cache, not non-root/multi-tenant storage security.
  Only disposable pods removed; real namespace/PVC/PV and small probe data kept
  for the separately approved reboot gate. No NTFS access or disk-layout changes.
- Free space after checks: **424,688,947,200 bytes / 395.52 GiB**. Budgeting a full
  20 GiB cache leaves **275.52 GiB above** the proposed 100-GiB floor. Local-path
  requests are **not quotas or preallocation**; data is **not replicated/backed up**.
  Retain and Argo annotations do not prevent direct administrator deletion or
  node/disk failure. No deletion-based retention test was performed.
- Growth review: pinned model-revision API lists **4,063,515,592 bytes** of weights,
  **4,079,450,110 bytes** total repository files (metadata inspection only). A
  proposed 20-GiB single-revision acquisition budget must be monitored, not assumed
  enforced by the PVC. Containerd currently about **30.53 GiB**; no image pruned.
  Kubelet log rotation **10Mi / 5 files**, image GC **85% / 80%**, eviction free
  thresholds **5%**; these do **not** enforce the proposed 100-GiB floor. Journal
  24 MiB, pod logs about 200 KiB; journal/syslog settings inspected, unchanged.
  Broader host/image/log growth is not hard-bounded. Operational floor, acquisition
  stop-margin and limitations are documented in `bootstrap/storage/README.md`.
- Existing **20** local unit tests, Bash syntax checks and `git diff --check`
  passed after these changes. New storage resources and both disposable pods
  passed live server-side dry-run before creation; persistence assertions above
  are live host evidence, not simulated results.

Private Stage-B evidence in the same `gpu-storage-issue5-2026-10-18/` directory:
`storage-preflight.txt`, `storage-class-create.json`, `storage-model-pvc-create.json`,
`storage-bound-pvc.json`, `storage-bound-pv.json`, `storage-ext4.json`,
`issue5-storage-{writer,reader}-{final,logs,delete}.json`, `storage-marker.sha256`,
`storage-path-ownership.json`, `storage-default-after.json`,
`storage-namespace-after.json`, `storage-pods-after.json`, `storage-free-after.json`,
`model-revision-file-sizes.json`, and `storage-growth-review.txt`.
No service interruption or firewall/runtime change occurred during Stage B.

### Reboot gate — approved, blocked before shutdown

Owner subsequently approved reboot now with console recovery available. Preflight
at **2026-10-18 01:35:41 WIB / 2026-10-17 18:35:41 UTC** confirmed only the four
system/plugin pods, node Ready, GPU allocatable 1, retained claim Bound, and
SSH/K3s/UFW active and enabled. At **01:36:01 WIB / 18:36:01 UTC**, the single
`sudo -n systemctl reboot` request exited **1**:
`Call to Reboot failed: Operation denied due to active block inhibitor`.
No forced reboot, inhibitor bypass, session termination, or automatic retry.

Read-only checks confirmed the boot ID unchanged, node/plugin healthy and PVC
still Bound. The shutdown block belongs to the GNOME user session; its session
manager inhibitor reports **"A foreground process is running"** (logout flag 1,
empty application ID). Other power-key/lid inhibitors are not shutdown blockers.
At that checkpoint, owner intervention or explicit inhibitor-bypass approval was
required before retrying. Reboot survival was **unverified**, not failed post-reboot.
Private artifacts: `reboot-preflight.txt`, `reboot-command.json`,
`reboot-inhibitors.txt`, `gnome-inhibitor-paths.txt`, and
`gnome-inhibitor-details.txt` in the same evidence directory.

### Reboot gate — inhibitor bypass separately approved, survival passed

Owner then explicitly authorized proceeding despite the desktop inhibitor.
At **2026-10-18 01:37:40 WIB / 2026-10-17 18:37:40 UTC**, executed exactly one
`sudo -n systemctl --check-inhibitors=no reboot`. This bypassed the GNOME
inhibitor but retained normal systemd service shutdown; no `--force`, hard reset,
power cycle, driver/package update, or firewall/configuration change. The ordinary
blocked attempt above remains recorded rather than overwritten.

- Fresh SSH returned with a **different boot ID**, normal known-host verification
  and key authentication. SSH, K3s and UFW active/enabled. Initial immediate pod
  snapshot showed transient Unknown/Completed states; bounded rollout waits then
  required all three system Deployments and the plugin DaemonSet ready. Final
  inventory has exactly the same four pods Running/Ready, each restart count 1.
- K3s **v1.35.9+k3s1**, containerd **2.2.7-k3s1**, runc **1.4.2**, driver
  **595.99.02** unchanged. Actual CRI info confirms **runc** remains default;
  NVIDIA RuntimeClass handler remains `nvidia`. Exactly one plugin; node Ready,
  capacity/allocatable **nvidia.com/gpu=1** after reboot. Runtime advisories still
  owner-accepted, **not patched**.
- Checksummed **kubectl 1.35.9** used the existing owner-only kubeconfig via a new
  loopback SSH tunnel; authenticated TLS-verifying API access and version checks
  passed without certificate/hostname bypass. Firewall/listeners inspected again:
  IPv4/IPv6 filter INPUT DROP remains; wildcard API/kubelet listeners are not
  loopback-only. Direct management TCP SSH succeeded; API/kubelet probes remained
  blocked. No external-source/UDP exposure test; Kubernetes ACCEPT-chain caveat
  from issue #4 remains. No access rule was changed.
- A disposable NVIDIA RuntimeClass one-GPU pod mounted the **same PVC/PV UIDs and
  backing path**, still Bound with **Retain**, preserving namespace/PVC Argo
  protections. It verified the original pre-reboot marker SHA-256 and replacement
  pod's file, root:root **0750** cache ownership, and an fsynced **new post-reboot
  write**. Then the unchanged #4 CUDA payload again asserted synchronized
  `[[58.0,64.0],[139.0,154.0]]`, PyTorch **2.13.0+cu130**, CUDA **13.0**. Pod
  Succeeded with **exit 0**, observed **01:39:42 WIB / 18:39:42 UTC**, and was
  deleted. PVC, namespace and probe data retained. No models/serving deployed.
- Final host snapshot **01:40:00 WIB / 18:40:00 UTC**: GPU **208 MiB / 0%**, node
  and system/plugin health restored, `/readyz` ok; root available
  **424,696,938,496 bytes** (about 395.53 GiB). Desktop GPU processes resumed;
  no claim about preserving unsaved desktop application state.
- Final static verification: all **20** existing unit tests, Bash syntax and
  `git diff --check` passed. Full existing schema/render suite: **74 resources,
  71 valid, 0 invalid/errors, 3 upstream CRDs explicitly skipped**. Separately,
  retained StorageClass plus selected plugin/RBAC render: **5 resources, all
  valid**. Used official-checksummed kubeconform **v0.8.0** and Kubernetes 1.35.0
  schema baseline. These static checks are separate from live reboot evidence.

Additional private evidence in the same directory: `reboot-bypass-command.json`,
`reboot-bypass-reconnect.json`, `post-reboot-host.txt`, `reboot-nodes.json`,
`reboot-{runtimeclass,pvc,pv,namespace}.json`, `reboot-pod-{final,logs,delete}.json`,
`reboot-pods-after.json`, `reboot-plugin-logs.json`, `post-reboot-final.txt`, and
`post-reboot-direct-port-probes.json`. Hardware allocation, storage replacement
and reboot gates passed; configuration snapshot is committed above, with PR
review/merge still pending.

## Observed host baseline — issue #3

- Ubuntu Desktop 26.04.1 LTS, x86_64; kernel 7.0.0-38-generic; cgroup v2.
- Core i7-13700K; approximately 123 GiB usable RAM; RTX 3090 with 24,576 MiB
  VRAM. Driver remains 595.99.02; post-change idle GPU use was 224 MiB.
- Root ext4 filesystem: approximately 427 GiB free. Other disks and firmware
  were not changed. Existing working Ubuntu NVIDIA driver was preserved.
- Owner confirmed desktop console recovery and explicitly approved protected
  backups, key-only SSH, management-client-only incoming SSH, and persistent
  swap disablement. Owner separately enabled passwordless sudo; `sudo -n true`
  succeeds. This agent did not grant it. Broad passwordless sudo remains a risk;
  remove or narrowly scope it after the experiment.
- Root-only configuration backups were saved before changes. `sshd -t` and
  connection-specific `sshd -T -C` passed: public-key authentication enabled,
  password and keyboard-interactive authentication disabled. Fresh independent
  key-based SSH connections passed after both SSH and firewall changes.
- UFW is active and enabled at boot, with default deny incoming/allow outgoing
  and one TCP SSH allow rule for the observed management client's IPv4 address.
  IPv6 filtering remains enabled. No Kubernetes ports were opened. These are
  inspected rules and authorized-client checks, not an unauthorized-client probe.
- Swap is off, its sole fstab entry is commented, no swap units remain loaded,
  and the existing 8 GiB swap file is retained for reversal. `findmnt --verify`
  passed without warnings. Ubuntu hibernation is not part of this lab profile.
  Before changes, login1 reported hibernation unavailable; no hibernate/resume
  test was performed. Reboot persistence is configured but not reboot-tested.
- Active desktop settings report mains suspend timeout 0 and screen locking
  enabled. SSH succeeded while the graphical session reported approximately
  48 minutes idle; continuous availability was not measured. No power settings
  were changed and no sleep targets were masked.
- Wi-Fi DHCP remains unchanged. Router reservation is unavailable; the owner
  accepts manually updating the private access record when the host IP changes.
  A management-client IP change also requires a console-reviewed firewall update.
- `bash scripts/preflight.sh`, streamed over private SSH, exited 0 before and
  after changes. Raw policy, change, and post-change preflight evidence remains
  in owner-only local storage outside Git. No identifiers or raw inventory are
  published here. No packages were installed, cluster created, GPU computation
  performed, models downloaded, service stopped, or host rebooted. SSH was
  reloaded; the desktop and driver remained available.

CUDA computation, Kubernetes allocation/storage, inference, recovery, and
post-reboot checks remain separate acceptance gates. See
[issue #3](https://github.com/mujak27/inference-platform/issues/3).

Redacted evidence locator: `<workspace-docs>/inference-platform-private/`, where
`<workspace-docs>` is the owner's shared local workspace documentation directory,
outside every repository/worktree. Supporting artifacts dated 2026-10-17:
`approved-ssh-change-2026-10-17.txt`, `approved-firewall-change-2026-10-17.txt`,
`approved-swap-change-2026-10-17.txt`, `post-change-verification-2026-10-17.txt`,
and `host-preflight-after-changes-2026-10-17.txt`. The private `host-access.md`
in that directory records the exact access and backup locations. These files
are owner-only; do not upload them without reviewing and redacting their contents.

## Observed runtime and asserted CUDA acceptance — issue #4

Observed on **2026-10-18 WIB (UTC+7) / 2026-10-17 UTC**:

- K3s **v1.35.9+k3s1 (58877f27)** enabled/running, bundled containerd
  **2.2.7-k3s1**, runc **1.4.2**. Four NVIDIA Toolkit/libnvidia-container packages
  are **1.20.1-1**. Packaged CDI refresh reports success/0; NVIDIA RuntimeClass
  exists, with runc retained as default. NVIDIA wrapper under the actual daemon
  PATH resolves bundled runc; the direct CUDA invocation below passed.
- Node Ready; CoreDNS/local-path/metrics pods Running/Ready; authenticated
  `/readyz` succeeds. Ordinary disposable-pod DNS/TLS/API test passed below.
- Prior Stage B verified the CA/client-certificate SSH tunnel and blocked direct
  management API/kubelet connections. Necessary private pod networking was added;
  no public ingress. Generated Kubernetes/Flannel ACCEPT chains precede UFW, so
  narrow UFW rules do not constitute exclusive effective pod filtering.
- Owner accepted identified containerd/runc advisory risks, **not** evidence of
  patches. Additional optional hardening is deferred until working inference.
- Public command `sudo bash scripts/validate-cuda.sh` is implemented at source
  commit `187524a8debae25346a2a97a51ed9d5a31c5a201`. Five fake-runner contract tests
  pass; three red→green cycles and the full **20-test** suite are recorded. They
  are not hardware evidence. Missing-GPU/mismatch and runner failures are covered
  at the fake-runner seam, not by deliberately failing hardware runs.
- Earlier bundled-ctr pulls failed with HTTPS timeouts. Source inspection of the
  exact containerd fork found `ctr images pull --local --max-concurrent-downloads`
  does not apply its advertised limit; local fetch dispatch uses a nil limiter.
  CRI local pulls also have unbounded layer concurrency. CRI omits `AllMetadata`
  and avoids non-target-platform metadata traversal; success does **not** prove
  serialization or establish the earlier TLS failure's root cause. The index has
  exactly two platforms (amd64/arm64), so the earlier ~45 sockets are not evidence
  of ~45 platforms. No containerd config change or restart was needed.
- Owner-approved acquisition used bundled `sudo /usr/local/bin/crictl pull`
  with `docker.io/vllm/vllm-openai@sha256:c1c9f6fd5c109ba7f0546a59f5b2f15fb87f64c77782e90a27b648b42a8e67c3`.
  Pull exited **0 after 1534 seconds** inside the approved 5400-second deadline;
  growth **33,145,036,800 bytes**, minimum sampled free **424,923,029,504 bytes**.
  No disk guard fired (200-GiB growth cap, 125-GiB abort, 100-GiB absolute floor).
  Sampled minima are not guaranteed instantaneous peaks. Image registered in
  `k8s.io`, CRI-managed and unpacked; retained for issue #5. The index and amd64
  manifest are the pinned digests below; `sha256:c76d0e2225a4b1cb1e2109ace39639f55e714abd1a7a427acc8b0bbd7f6a83b3`
  is the amd64 **config/image ID**, not a different manifest.
- CUDA command ran once, **00:04:51–00:04:54 WIB / 17:04:51–17:04:54 UTC**,
  using the unmodified script (SHA-256
  `c2a24d67875bf074f3d92a371b1d2a66c7a57396cbd23b1897117d0b11d3cca7`).
  `k3s ctr --namespace k8s.io run --rm --platform linux/amd64` used
  `io.containerd.runc.v2` with `/usr/bin/nvidia-container-runtime`, GPU 0,
  compute/utility capabilities, systemd cgroups, 2 CPUs and 4 GiB RAM; the script
  contains the complete argument vector and entrypoint override. No model download.
  CUDA float32 `2x3 @ 3x2` tensors, synchronization, CPU copy and independent
  expected-value assertion passed: exit **0**, empty stderr, 3 seconds wall time.

  ```json
  {"schema":1,"status":"pass","operation":"float32_matmul_2x3_3x2","cuda":true,"result":[[58.0,64.0],[139.0,154.0]],"torch":"2.13.0+cu130","torch_cuda":"13.0"}
  ```

- Ordinary CPU-only pod ran once at **00:06:35–00:06:36 WIB /
  17:06:35–17:06:36 UTC**, reusing the same image without a pull. Stdout asserted
  `{"schema":1,"dns":true,"tls_verified":true,"api_http_status":200}`:
  `kubernetes.default.svc` resolved, mounted-CA and hostname verification stayed
  enabled, and HTTP 200 was required. Exit **0**, not merely phase `Succeeded`;
  pod deleted and verified absent. No device-plugin GPU allocation was tested.
- Listener/firewall recheck at **00:11:21 WIB / 17:11:21 UTC** used `ss -lntup`,
  `ufw status verbose`, `iptables-save` and `ip6tables-save`. API TCP 6443,
  kubelet TCP 10250 and VXLAN UDP 8472 bind wildcard addresses, **not** private-only
  listeners. IPv4/IPv6 INPUT default DROP; only management SSH and interface-scoped
  pod-to-private-API/kubelet allows exist in UFW user input rules, with no VXLAN
  allow. Direct management TCP 6443/10250 probes timed out; TCP 22 connected.
  Prior authenticated SSH-tunnel API access passed. No public ingress configured;
  no untrusted-source, external-router, UDP reachability or reboot test performed.
  Kubernetes ACCEPT chains precede UFW; this is not exclusive pod isolation.
- Driver remains **595.99.02**, GPU memory **222 MiB**, utilization **0%**;
  desktop/terminal processes retained. Fresh strict SSH/sudo and the existing
  private access succeed. No active pull/watchdog or owned CUDA container/network
  pod remains. Earlier failed transient units/artifacts were not reset or pruned.

Private evidence under `<workspace-docs>/inference-platform-private/`:
`runtime-issue4-stage-c-*` (earlier failure), `crictl-pull-run2-2026-10-17/`
and the host-side successful-pull cache, `cuda-validation-2026-10-18/`
(`validator-run.txt`, `post-run-evidence.md`), `network-pod-gate-2026-10-18/evidence.md`,
and `runtime-issue4-firewall-recheck-2026-10-18.md`.
Do not publish raw logs, access identities, tokens or recovery socket paths.
CUDA passed; Kubernetes GPU allocation/storage and inference remain separate gates.

### Installation provenance — 2026-10-17 Stage A/B

Configuration evidence was captured at repository base `d0c1608`; installation
was an approved host operation, **not** a Git-managed deployment. The private
`runtime-issue4-continuation-install.sh` records the exact configuration/program,
and `runtime-issue4-continuation-install.json` records its execution. Its redacted
configuration shape: wildcard bind; private node advertise/node IP; localhost and
127.0.0.1 TLS SANs; pod/service CIDRs `10.42.0.0/16` / `10.43.0.0/16` (route
overlap checked); kubeconfig mode 0600; only Traefik and ServiceLB disabled.
SQLite and the default runc runtime were retained; generated containerd config
was not edited.

- K3s [release](https://github.com/k3s-io/k3s/releases/tag/v1.35.9%2Bk3s1)
  checksums matched binary SHA-256
  `897acb21cca57d477a211102251a6591450ce767344a9faaa121a1007ca9fa9a`.
  Installer source revision `58877f27435fe86ee292859db3d0df2ca5423991`, SHA-256
  `8598e002e61d658fed7b7542fc6d2c66d8da6eae69e088830105d2ee1ffb6d91`,
  was staged/rehashed, not piped from the network. After installing the verified
  binary and reviewed config, root ran the staged installer with
  `INSTALL_K3S_VERSION=v1.35.9+k3s1 INSTALL_K3S_SKIP_DOWNLOAD=true
  INSTALL_K3S_SKIP_SELINUX_RPM=true INSTALL_K3S_SKIP_START=true
  INSTALL_K3S_SKIP_ENABLE=true sh <staged-installer> server`, then separately
  `systemctl enable --now k3s.service`.
- Toolkit followed the [NVIDIA production-repository installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
  The scoped signed source was `https://nvidia.github.io/libnvidia-container/stable/deb/amd64`;
  primary signing-key fingerprint `C95B321B61E88C1809C4F759DDCAE044F796ECB0`.
  Authenticated metadata and the exact dependency simulation passed before root
  executed `apt-get --assume-yes --no-install-recommends --no-remove --no-upgrade
  install nvidia-container-toolkit=1.20.1-1 nvidia-container-toolkit-base=1.20.1-1
  libnvidia-container-tools=1.20.1-1 libnvidia-container1=1.20.1-1`, with
  `DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l`. Only those four packages
  were installed. Exact command/result: private
  `runtime-issue4-stage-b-toolkit-install-command-2026-10-17.txt` and
  `runtime-issue4-stage-b-toolkit-install-2026-10-17.json`; signed-source evidence:
  `runtime-issue4-stage-a-repository-result-2026-10-17.json`.

Compatibility references: [K3s NVIDIA runtime support](https://docs.k3s.io/advanced#nvidia-container-runtime-support)
and [CUDA minor-version compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html).
These inform the candidate choice; the observed CUDA assertion above, not the
documentation, establishes this host's computation result. They do not establish
security-advisory fixes or Kubernetes GPU allocation compatibility.

## Observed GitOps bootstrap and first serving — issue #6

All operations used the checksummed kubectl 1.35.9 and the owner-only
kubeconfig over strict-host-key SSH loopback tunnels with certificate
verification; Argo API access pinned TLS to the `argocd-secret` serving
certificate. Argo and inference Services stayed ClusterIP with loopback
port-forwards only. Both Applications track `main`; every sync used an
explicit reviewed SHA, no prune, no force/replace, no auto-sync.

### Argo CD bootstrap — Stage A, 2026-10-17 18:51–19:00 UTC

- Installed Argo CD **v3.5.5** (release commit
  `a5038b0e2bbac1715754380ae0084df8e3d5b48b`) by server-side apply of the
  reviewed render (60 objects; render SHA-256
  `03318b68026bf7861388afbed2e5f08e252d8b6c89adaa87d94d08f9ee0e07cb`) from the
  exact merged source `21cd1c6` (PR #11). Argo pods created
  2026-10-17T18:56:39–18:56:50Z; three CRDs Established; six Deployments and
  the application-controller StatefulSet observed 1/1 ready across three
  checks at 18:59:54–19:00:29 UTC. Observed image IDs: argocd
  `sha256:13db7b10db23283b1b36f855046602e18539a8a8204c9f6f039e8896c8897518`,
  dex `sha256:8499afd690c437f52301efd2b05b2455da5bd2dfc20332cd697dc9937f808462`,
  redis `sha256:08ad0b1d280850169a790dba1393ff7a90aef951fc19632cf4d3ce4f78e679ba`.
  Upstream image tags are not digest locks; the observed IDs above are the
  runtime record. Historical Redis secret-init startup warnings resolved
  naturally: zero restarts, no waiting containers, pod UID set unchanged.

### Credentials and root Application — Stage B, 2026-10-17 19:40 UTC

- A cancelled earlier worker had left the credential state unprovable from
  evidence; the initial admin password was tested by live login and was still
  valid. It was rotated to a locally generated password; the replacement
  login was independently verified and the old password rejected before
  `argocd/argocd-initial-admin-secret` was deleted at **2026-10-17T19:40:34Z**.
  No password or token appears in Git, evidence, or transcripts; the
  replacement password is stored owner-only (0600) outside the repository.
- Root Application `argocd/root` registered server-side from the reviewed
  manifest and synced **once** at `21cd1c6`: operation Succeeded, resources
  exactly `AppProject inference` + `Application vllm`. Both Applications are
  manual (`syncPolicy` empty/absent) with no deletion finalizers.
- Known benign difference: root reports `OutOfSync` because the child's
  declared manifest carries an empty `syncPolicy: {}` that the API server does
  not materialize live; the only spec-level diff is that empty object, a
  semantic no-op. Not remediated; no re-sync was performed.

### Child sync, observed defect, and fix — Stage C, 2026-10-18 03:37–04:34 UTC

- First manual child sync at `21cd1c6` succeeded (operation Succeeded;
  Namespace/ConfigMap/PVC/Service/Deployment created), ~**3.80 GiB** of
  Qwen3-1.7B weights downloaded into the PVC, and the GPU allocation
  succeeded — but the pod then crash-looped with exit 1:
  `ValueError: VLLM_PORT 'tcp://<ip>:8000' appears to be a URI`. Root cause:
  the Service named `vllm` in the pod's namespace makes the kubelet inject
  `VLLM_PORT=tcp://…`; vLLM parses `VLLM_PORT` and rejects the URI form,
  dying after model load. Fixed by **PR #13** (`enableServiceLinks: false`
  on the pod template; issue #12), merged as **`e2b9b8f`**; a regression
  test at the rendered-manifest seam reproduces the injected value.
- Re-sync at `e2b9b8f`: pod `vllm-57fb69c78b-f2mrj` became Ready **71 s**
  after sync with zero restarts; the child reached Synced/Healthy at the
  reviewed SHA. Model-cache growth during this rollout was **0 B** (weights
  reused from the PVC).

### Observed serving acceptance — 2026-10-18 03:37–04:42 UTC

- Serving pod `vllm-57fb69c78b-f2mrj` (uid `e37f4149-d677-4e0a-b284-7dc4246ea9d9`):
  image `vllm/vllm-openai@sha256:c1c9f6fd5c109ba7f0546a59f5b2f15fb87f64c77782e90a27b648b42a8e67c3`
  (vLLM v0.31.0), model Qwen/Qwen3-1.7B revision
  `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`; one replica, one full
  `nvidia.com/gpu`, TP=1, FP16, context 4096, concurrency 4, prefix caching,
  GPU memory utilization 0.80, `runtimeClassName: nvidia`.
- **Real streaming smoke test passed twice** (loopback port-forward to the
  ClusterIP Service): SSE content type, nonempty incremental content before
  completion, no server error, terminal `[DONE]`, 64 chunks. First content
  **0.135 s** / **0.189 s**, end-to-end **0.483 s** / **0.482 s** on the two
  runs. These are client-side smoke observations from a single 64-token
  request at temperature 0 — **not** benchmark or throughput results.
- GPU memory: **19,082 MiB used of 24,576 MiB** idle with the model loaded
  (configured 0.80 utilization); ~19,084 MiB during the smoke request across
  ~77 rapid (~0.1 s) samples. Desktop headroom preserved.
- Disk: minimum root free **390.33 GiB** during serving; containerd growth
  +2.5 MB; approved monitored ceilings (model +20 GiB, containerd +20 GiB,
  logs +5 GiB, root aggregate +45 GiB; 125 GiB stop line) never approached.
- **Pod-replacement / cache-reuse proof** (owner-approved): deleting only the
  serving pod `vllm-57fb69c78b-f2mrj` produced replacement
  `vllm-57fb69c78b-r78kw` Ready in **80.3 s** with zero restarts. The model
  cache was byte-identical before and after (71 entries, 39 regular files;
  every weight size and mtime unchanged; zero additions, removals or changes
  — no re-download). PVC uid `cd714b12-fe18-452b-9e26-e7159fa5277d` and PV uid
  `896e4e17-a4f6-4786-bb0f-25e9a53287f5` stayed Bound/20Gi/**Retain** with the
  same claim mounted. The smoke test passed again after replacement.

### Limitations — issue #6

- Smoke timings are single-request observations, not calibrated benchmarks;
  no concurrency, load, or long-run stability testing was performed.
- The in-window GPU load sample relied on ~0.1 s sampling around a sub-second
  request; the observed in-request delta (~2 MiB) is within sampling noise for
  a tiny request.
- Root's cosmetic `OutOfSync` (empty `syncPolicy: {}`) remains unfixed by
  choice; it does not affect the child or serving.
- One host, one GPU, one replica. Reboot survival of the serving workload was
  not re-tested after deployment; the cluster itself survived a reboot earlier
  under issue #5.
- Existing containerd/runc advisories remain owner-accepted, **not patched**.
  Argo CD's own components render without CPU/memory requests/limits.
- Argo's in-container render parity with local Kustomize was not proven;
  rendered manifests were inspected through the Argo API before each sync.
- Static validation (23 unit tests; schema suite 74 resources, 71 valid,
  0 invalid/errors, 3 CRDs skipped) is separate from the live results above.

## Observed rollback, stop/start, and SQLite backup — issue #7 (2026-10-18)

All operations used the checksummed kubectl 1.35.9 and the owner-only kubeconfig
over strict-host-key SSH loopback tunnels with certificate verification; the Argo
API TLS pin was read from the live `argocd-secret` serving certificate. Both
Applications track `main`; every sync used an explicit reviewed SHA with
`prune=false` and no force/replace or auto-sync. Smoke figures are single-request
client observations, not benchmarks.

### Fresh baseline — 2026-10-18T05:28–05:33Z

- Read-only single observer. Started from integrated commit
  `8eb55b437994afee49e79335617f602e9cc47d44`; the operational tree
  (`apps`, `bootstrap`, `infra`, `scripts/smoke-test.py`) is identical to the
  child-synced `e2b9b8f4c0757df0b37ba8f66982bcd405d66afa`. No repository edit,
  sync, backup, service interruption or cluster/host mutation.
- Pod `vllm-57fb69c78b-r78kw` Ready (1/1, 0 restarts); child Application
  Synced/Healthy; the root cosmetic `OutOfSync` difference was unchanged.
  Deployment generation 2.
- Live generated ConfigMap `vllm-config-479km22f89` carried `MAX_NUM_SEQS=4`;
  startup logs independently exposed parsed engine `max_num_seqs=4`.
- Model cache byte-identical to the issue-6 listing: 71 entries, 39 regular files,
  4,063,515,592 weight bytes. Idle GPU **19,084 / 24,576 MiB**, 0%; root free about
  390.33 GiB. One real SSE smoke test passed (exit 0, 64 chunks, first content
  0.076 s, end-to-end 0.421 s).

### Manual configuration change `MAX_NUM_SEQS: 4 → 3` — 2026-10-18T06:08–06:25Z

- Reviewed PR #28 (feature `546c815`, merged
  `90db167f23a247ba0a8debc2c8d967f228fb855a`) changed only the two reviewed lines
  in `apps/vllm/base/kustomization.yaml` and `tests/test_gitops.py`. One manual
  child `vllm` sync was submitted (`prune=false`, no force/replace/auto-sync) and
  Succeeded at `2026-10-18T06:08:15Z`.
- **Honest reconciliation deviation:** `origin/main` had advanced with unrelated
  llm-d preparation (#29/#30) while the child `targetRevision` tracks `main`, so
  Argo reconciled and recorded revision
  `a5a857469bec333c516c2452e72f3a86d724a93d`, not the pinned `90db167`. The diff
  between the two for `apps/vllm`, `bootstrap`, `infra` and `scripts/smoke-test.py`
  is empty, so the deployed operational content is exactly the reviewed two-line
  change. The evidence does not claim a sync at `90db167`.
- Replacement pod `vllm-56794c6c45-v9j2s` Ready about **61 s** after the sync
  (0 restarts, Deployment generation 2→3). New generated ConfigMap
  `vllm-config-9fdmtttt97` carried `MAX_NUM_SEQS=3`; pod env and startup logs
  independently showed runtime `MAX_NUM_SEQS=3` and parsed `max_num_seqs=3`.
- Cache byte-identical (71 entries, 39 regular files, 4,063,515,592 weight bytes;
  no re-download). One real SSE smoke test passed (exit 0, 64 chunks, first content
  0.166 s, end-to-end 0.516 s).

### Git revert `MAX_NUM_SEQS: 3 → 4` — 2026-10-18T08:26–08:59Z

- Normal `git revert` of `90db167` (no history rewrite), pushed to `main` as
  `53f83131fab218c980c4a4d565c6b59a6285fd46`. One manual child `vllm` sync
  (`prune=false`) Succeeded at `2026-10-18T08:26:59Z` with Argo recorded revision
  `53f83131fab218c980c4a4d565c6b59a6285fd46`.
- Replacement pod `vllm-57fb69c78b-5fkm7` Ready about **74 s** after the sync
  (0 restarts, Deployment generation 3→4).
- Active ConfigMap restored to `vllm-config-479km22f89` (`MAX_NUM_SEQS=4`) while
  the unpruned `vllm-config-9fdmtttt97` (`MAX_NUM_SEQS=3`) remained in the
  namespace, demonstrating `prune=false`; the child consequently reported
  `OutOfSync`/`Healthy`. Runtime env and parsed engine logs both showed 4.
- Cache byte-identical. One real SSE smoke test passed (exit 0, 64 chunks, first
  content 0.154 s, end-to-end 0.503 s); idle GPU 19,082 MiB.

### Storage-preserving stop/start `replicas: 1 → 0 → 1` — 2026-10-18T09:04–09:11Z

- Stop commit `7660b4477f466ccd3c3a95ad848992f39bd44139` (`count: 1 → 0` in
  `apps/vllm/overlays/single-replica/kustomization.yaml`). One manual child sync
  (`prune=false`) Succeeded at exact revision `7660b44…` at `2026-10-18T09:05:44Z`.
- At zero: Deployment generation **5** (`observedGeneration` 5; desired/current/
  ready/available replicas 0); **0 pods** in `inference`; no ready Service
  endpoints; GPU memory fell **19,084 → 120 MiB**, releasing the ~18.5 GiB model
  allocation while leaving desktop VRAM. Namespace (`a204aa2e…`), PVC (`cd714b12…`)
  and PV (`896e4e17…`) UIDs were unchanged, Bound **20Gi**, PV **Retain**, the
  `Prune=false,Delete=false` annotations intact, and the model cache byte-identical.
- Start commit `b96d69a901ef845ac6a22e305a64e15bf7ac787a` (normal `git revert` of
  `7660b44`, restoring `count: 1`). One manual child sync (`prune=false`) Succeeded
  at exact revision `b96d69a…`. Replacement pod `vllm-57fb69c78b-h4kbv` Ready about
  **75.6 s** after the sync (0 restarts, Deployment generation 6).
- Weights loaded from the retained PVC in **0.61 s** with zero `Downloading` events
  and no cache file additions/removals/modifications (71 entries, 39 files,
  4,063,515,592 weight bytes). GPU memory restored to 19,082 MiB. One real SSE
  smoke test passed (exit 0, 64 chunks, first content 0.122 s, end-to-end 0.476 s).

### Quiescent K3s SQLite and paired server-token backup — 2026-10-18T09:17–09:20Z

- One fail-safe root capture on the host: `systemctl stop k3s.service` at
  `09:17:46Z`; verified `inactive` / `MainPID=0` at `09:17:48Z` and **zero** open
  handles on `/var/lib/rancher/k3s/server/db` (`/proc/*/fd`, `lsof`, `fuser`).
  Copied the complete `server/db/` directory (`state.db`, `state.db-shm`,
  `state.db-wal`: 3 files, 13,648,472 logical bytes) plus the paired `server/token`
  and allowlisted service/config/node-password prerequisites; verified
  byte-for-byte equality against the stopped sources. Started `k3s.service` back to
  `active` at `09:18:16Z` — **30 s total service interruption**.
- Packaged into `/var/backups/k3s/issue7-20261018T091745Z/backup.tar`
  (13,680,640 bytes, SHA-256
  `95bbe80b9ccb9bc1bbfdb1bbae194ca93fb0cba6a4cdf5712b738dd57da70c56`; directories
  0700, files 0600), transferred over strict-host-key SSH to FileVault-encrypted
  off-host private storage (0700/0600), verified a matching SHA-256 and a safe tar
  member allowlist, and validated a disposable writable extraction with Python
  3.12.15 / SQLite 3.53.1 (`PRAGMA integrity_check` = `ok`,
  `PRAGMA foreign_key_check` = `[]`, nonempty `kine` table; disposable copy removed).
- Post-start cluster health passed (`/readyz` ok, 1 Ready node, GPU allocatable 1,
  pod `vllm-57fb69c78b-h4kbv` Ready, storage identities/protections intact) and a
  real SSE smoke test passed (exit 0, 64 chunks, 0.44 s).
- Honest boundary: **“Quiescent SQLite directory and paired token archived;
  source-to-stage byte checks, archive/transfer SHA-256 and disposable-copy SQLite
  integrity checks passed; post-start serving checks passed. Full K3s restore and
  token bootstrap/decryption have not been tested.”**

## Other proposed or unverified baseline items

- Host: Ubuntu Desktop 26.04 LTS, amd64 (Server is an alternative); selected by
  the owner, superseding the original 24.04 proposal. See
  [the decision record](adr/0001-ubuntu-desktop-26-04.md).
- Ubuntu 26.04 ISO filename/digest/signature and USB creation: unverified. The
  installed OS was inspected; the 24.04 media below does not verify 26.04 media.
- Driver: observed above, not a reason to install another branch.
- Runtime/Toolkit/Kubernetes installation, CUDA image acceptance, device-plugin
  allocation/storage and first serving are observed above under issues #4–#6.
- llm-d/LMCache: deferred until prerequisite milestones pass.

## Prepared GitOps candidates — now deployed and observed

The pins below were verified before deployment and are recorded as observed
above; see the issue #6 section for live results.

- Argo CD v3.5.5, release commit `a5038b0e2bbac1715754380ae0084df8e3d5b48c`.
  Installed and ready; observed image IDs in the issue #6 section.
- vLLM v0.31.0, manifest-list digest
  `sha256:c1c9f6fd5c109ba7f0546a59f5b2f15fb87f64c77782e90a27b648b42a8e67c3`.
  Inspected amd64 manifest digest:
  `sha256:a4a4c0437bf7240089da5f08aa370c4aee17ae5290f7a3b468825ee26c4c3a6b`;
  registry config declares CUDA 13.0.2, root default user, `vllm serve`
  entrypoint, and build commit `db9527a46873454610df6dbedf79a36d6bf1a7f6`.
- Qwen/Qwen3-1.7B model/tokenizer revision
  `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` from Hugging Face metadata.
- Static tools: kubectl v1.37.1 / Kustomize v5.8.1; kubeconform v0.8.0;
  PyYAML 6.0.3. Kubernetes schema baseline 1.35.0 from schema-repository commit
  `aff1ca44984cbbcfa376c1cb6fdc4bb6aa0381fd`. No cluster version is selected by this.
- Image/configuration/schema research date: 2026-10-17. Actual driver, PyTorch and
  package inventory, storage provisioning and streaming inference are recorded
  above; rollback, storage-preserving stop/start and a quiescent SQLite/paired-token
  backup with off-host transfer and disposable SQLite integrity validation were
  subsequently observed under issue #7 (above). **Full restore remains pending and
  untested.**

See [GitOps bootstrap, validation limits, and sources](gitops.md).

## Historical media evidence — Ubuntu 24.04, not the selected baseline

- Verified installation media (2026-10-17): `ubuntu-24.04.5.1-desktop-amd64.iso`,
  6,250,332,160 bytes, downloaded from
  `https://releases.ubuntu.com/24.04/ubuntu-24.04.5.1-desktop-amd64.iso`.
  SHA-256: `4da4a0c9035da8e68a59a838674f403f0a54472c78a83b4fb7f78d03588f85a7`.
  `SHA256SUMS.gpg` verified against `SHA256SUMS` using the Ubuntu CD Image
  Automatic Signing Key (2012), full fingerprint
  `843938DF228D22F7B3742BC0D94AA3F0EFE21092`, matching Canonical's verification
  guide. The downloaded ISO's `shasum -a 256` matches its signed entry.
  USB creation: owner-reported successful Terminal execution on 2026-10-17.
  Wrote 6,250,332,160 bytes to the approved SanDisk USB, read back the full ISO
  byte range with the same SHA-256, and successfully ejected the device.
  This verifies installation media, not actual PC boot or the installed host.

## Historical owner context

The reference host was initially described as an RTX 3090/128 GB Windows desktop
without Linux, managed from a Mac. Linux installation and private SSH have since
been observed as recorded above; network performance and runtime acceptance
remain unmeasured. Installation-media provenance is separate from host inventory.

## Record after installation

Record install date, ISO filename/digest/source, OS release, kernel, CPU, available
RAM/storage, GPU model/VRAM, driver and exact package versions, Secure Boot state,
and redacted evidence paths. Use `/etc/os-release`, `uname -r`, `dpkg-query`, and
the preflight output. Never infer installed versions from a documentation page.

For each later runtime component record image digest/chart/package version,
compatibility source, configuration commit, command, verification date, and
evidence. Keep host driver checks, container computation, Kubernetes allocation,
manifest rendering, and model inference as separate results.
