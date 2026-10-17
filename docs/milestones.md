# Implementation milestones

## Milestone 0 — supported environment

Status: **in progress; hardware verification blocked pending Linux installation/access**

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
  result above is for Ubuntu 24.04 only; 26.04 media and installation remain
  pending. See `docs/adr/0001-ubuntu-desktop-26-04.md`.
- Checks not executed: Ubuntu installation, SSH to GPU host, host inventory,
  container CUDA computation, Kubernetes GPU allocation. The target is not accessible.
- Manifest validation: GitOps/bootstrap and vLLM candidate added; see preparation
  status below. This does not verify a host, cluster, or model deployment.
- Measured results: none.
- Known limitations: host preflight covers inventory/driver visibility only;
  desktop processes consume VRAM; dual boot interrupts availability.
- Next concrete action: owner verifies installation media and completes host
  installation/private SSH; run preflight on Linux, then select/pin the GPU runtime
  and cluster and implement the CUDA/container/allocation acceptance checks.

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
and rollback. No accessible GPU cluster is available; all runtime results remain pending.

Next concrete action: review/merge GitOps preparation, then finish milestone 0
hardware gates before any child Application sync. llm-d, sharing, and LMCache are deferred.

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
