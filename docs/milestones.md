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
- Checks not executed: Ubuntu installation, SSH to GPU host, host inventory,
  container CUDA computation, Kubernetes GPU allocation. The target is not accessible.
- Manifest validation: not applicable; no deployment manifests added yet.
- Measured results: none.
- Known limitations: host preflight covers inventory/driver visibility only;
  desktop processes consume VRAM; dual boot interrupts availability.
- Next concrete action: owner verifies installation media and completes host
  installation/private SSH; run preflight on Linux, then select/pin the GPU runtime
  and cluster and implement the CUDA/container/allocation acceptance checks.

## Remaining milestones — not started

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
