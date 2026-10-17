# Version and evidence record

Documentation research and host inspection dates: **2026-10-17–18**. Private SSH
inventory and approved host-baseline changes have been verified. No runtime
combination is claimed supported end-to-end by this project yet.

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

## Other proposed or unverified baseline items

- Host: Ubuntu Desktop 26.04 LTS, amd64 (Server is an alternative); selected by
  the owner, superseding the original 24.04 proposal. See
  [the decision record](adr/0001-ubuntu-desktop-26-04.md).
- Ubuntu 26.04 ISO filename/digest/signature and USB creation: unverified. The
  installed OS was inspected; the 24.04 media below does not verify 26.04 media.
- Driver: observed above, not a reason to install another branch.
- Runtime/Toolkit/Kubernetes installation and CUDA image acceptance are observed
  above. Device-plugin allocation/storage acceptance remains pending in issue #5.
- llm-d/LMCache: deferred until prerequisite milestones pass.

## Prepared GitOps candidates — not deployed or hardware verified

- Argo CD v3.5.5, release commit `a5038b0e2bbac1715754380ae0084df8e3d5b48c`.
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
  package inventory are recorded above; storage provisioning and inference remain pending.

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
