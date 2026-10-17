# Version and evidence record

Documentation research date: **2026-10-17**. No GPU host has been accessed. No
runtime combination is claimed supported end-to-end by this project yet.

## Proposed baseline, not installed versions

- Host: Ubuntu Desktop 24.04 LTS, amd64 (Server is an alternative).
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
- Driver branch: discover from the actual host before CUDA runtime selection.
- Runtime, NVIDIA Container Toolkit, Kubernetes, device-plugin chart, CUDA test
  image/digest, Argo CD, vLLM image/digest, model revision: not selected/deployed.
- llm-d/LMCache: deferred until prerequisite milestones pass.

## Observations supplied by the owner (not independently verified)

- Target GPU: NVIDIA RTX 3090, 24 GB VRAM; host RAM: 128 GB.
- Target currently lacks Linux; intended installation coexists with Windows.
- Management client: Mac; private network access will be established after installation.
- CPU, disk capacity, network performance, firmware, driver, runtime, and cluster: unknown.

## Record after installation

Record install date, ISO filename/digest/source, OS release, kernel, CPU, available
RAM/storage, GPU model/VRAM, driver and exact package versions, Secure Boot state,
and redacted evidence paths. Use `/etc/os-release`, `uname -r`, `dpkg-query`, and
the preflight output. Never infer installed versions from a documentation page.

For each later runtime component record image digest/chart/package version,
compatibility source, configuration commit, command, verification date, and
evidence. Keep host driver checks, container computation, Kubernetes allocation,
manifest rendering, and model inference as separate results.
