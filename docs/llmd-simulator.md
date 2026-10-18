# CPU-only llm-d simulator — isolated source candidate

Reviewed from uncommitted `llmd-next` preparation (base `d0c1608`) on 2026-10-18;
not registered, deployed or runtime-qualified. See [qualification and evidence
matrix](llmd-preparation.md) for source provenance, checks and pending gates.

Two independent one-replica `Recreate` Deployments run pinned
`ghcr.io/llm-d/llm-d-inference-sim:v0.11.2@sha256:32144df791330a0006b747edfdf2b114a0fe728e023a9d1b3463eeb48d32abb9`
in `llmd-sim`. Echo mode serves only `synthetic-llmd-sim-only`, with bounded
queues and artificial constant latency. Fake running/waiting/KV gauges are
synthetic inputs, not measured load or cache reuse. No GPU, model/tokenizer
download, PVC, backend Service or backend API token is configured.

The EPP/Envoy router is a separate instance. No-pool discovery uses namespaced
Pods and both `app.kubernetes.io/name=llmd-inference-sim` and
`inference.platform/experiment=synthetic-only`, port 8000. Its Role permits only
Pod get/list/watch. The queue-only profile excludes real cache scorers. Only the
router Service is exposed, as ClusterIP HTTP 80 → 8081; there is no public
ingress, host port or active apps/infra registration. Namespace/selector separation
prevents accidental real-engine selection, not malicious cross-pod networking.

```sh
bash scripts/render-llmd-sim.sh
python3 -B scripts/validate-llmd.py --candidate sim
```

These offline commands require the already acquired pinned chart and approved
local tools. The required validator rerenders, checks effective policies and
validates built-in resource schemas; it does not accept stale output or skip
missing inputs. `--policy-only` is a partial source inspection, not qualification.

Future approval must cover runtime context, resources, durations, fault controls
and cleanup. EPP plugin loading, read-only filesystem support, identity headers,
metrics, incremental SSE, queue-preference reversal and scheduler-failure
behavior remain unverified here. A stopped collocated router is not a live-proxy
EPP-failure test; NetworkPolicy cannot block same-pod loopback ext_proc.
No request/load/fault experiment is implemented in this ticket slice.

Synthetic results never establish vLLM 0.31.0 interoperability, real tokens,
GPU sharing/capacity, true cache reuse, throughput gains or HA. #17 owns later
synthetic runtime proof after its prerequisites and separate operational approval.

[Pinned simulator source](https://github.com/llm-d/llm-d-inference-sim/tree/7639395743c76f1cb37222981b33e8ea56cce69b)
