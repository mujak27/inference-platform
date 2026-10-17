# Version and evidence record

Documentation research and host inspection date: **2026-10-17**. Private SSH
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

## Proposed baseline, not installed versions

- Host: Ubuntu Desktop 26.04 LTS, amd64 (Server is an alternative); selected by
  the owner, superseding the original 24.04 proposal. See
  [the decision record](adr/0001-ubuntu-desktop-26-04.md).
- Ubuntu 26.04 ISO filename/digest/signature and USB creation: unverified. The
  installed OS was inspected; the 24.04 media below does not verify 26.04 media.
- Driver: observed above, not a reason to install another branch.
- Runtime, NVIDIA Container Toolkit, Kubernetes, device-plugin chart, CUDA test
  image/digest: approved-plan candidates are recorded in issues #4–#5, not
  installed or hardware verified. Revalidate artifacts before installation.
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
- Image/configuration/schema research date: 2026-10-17. Actual driver, PyTorch,
  package inventory, storage provisioning, and real inference tests remain pending.

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
