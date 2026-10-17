# Version and evidence record

Documentation research date: **2026-10-17**. No GPU host has been accessed. No
runtime combination is claimed supported end-to-end by this project yet.

## Proposed baseline, not installed versions

- Host: Ubuntu Desktop 26.04 LTS, amd64 (Server is an alternative); selected by
  the owner, superseding the original 24.04 proposal. See
  [the decision record](adr/0001-ubuntu-desktop-26-04.md).
- Ubuntu 26.04 ISO filename/digest/signature, USB creation, installation, and
  host compatibility checks: pending. The 24.04 media below does not verify 26.04.
- Driver branch: discover from the actual host before CUDA runtime selection.
- Runtime, NVIDIA Container Toolkit, Kubernetes, device-plugin chart, CUDA test
  image/digest: not selected/deployed.
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
