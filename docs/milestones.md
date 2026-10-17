# Implementation milestones

## Milestone 0 — supported environment

Status: **in progress; host baseline verified, CUDA/runtime and Kubernetes gates pending**

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
- Checks not executed: continuous idle monitoring, reboot persistence, container
  CUDA computation, Kubernetes GPU allocation/storage, or inference. No runtime
  packages were installed and no reboot occurred. Passwordless sudo was enabled
  by the owner, not this agent, and remains a security limitation.
- Manifest validation: GitOps/bootstrap and vLLM candidate added; see preparation
  status below. This does not verify a host, cluster, or model deployment.
- Measured inference/performance results: none. Host inventory is not CUDA acceptance.
- Known limitations: host preflight covers inventory/driver visibility only;
  desktop processes consume VRAM; dual boot interrupts availability.
- Next concrete action: review the host-baseline evidence and repository changes,
  then obtain separate runtime-installation approval for issue #4. Verify candidate
  artifacts before installing the runtime and implementing asserted CUDA checks.

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

Checks not executed: API-server apply, Argo Synced/Healthy, model downloads,
GPU/container computation, real streaming inference, PVC reuse, reconciliation,
and rollback. The GPU host is reachable, but no cluster has been installed;
all runtime results remain pending.

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
