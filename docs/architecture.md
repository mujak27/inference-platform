# Platform requirements and boundaries

## Host contract

The platform consumes a Linux GPU host; it does not prescribe how the owner
partitions disks or whether Windows is also installed.

- Native Linux with a supported NVIDIA GPU/driver and container runtime combination.
- A working GPU compute operation inside a container, then a GPU allocation test
  in Kubernetes. `nvidia-smi` alone is not compute validation.
- Sufficient CPU, RAM, VRAM, and Linux filesystem capacity for the chosen model,
  runtime, and persistent volumes; discover these before setting budgets.
- Private administrative access, stable host addressing, DNS, and time sync.
- A GPU-capable Kubernetes runtime and exactly one NVIDIA device plugin installation.
- Persistent Linux storage for model downloads, distinct from disposable caches.

The management client needs SSH and, later, kubectl/Helm; it does not supply CUDA
capacity. A Mac, Linux machine, or Windows SSH client can perform this role.

## Reference host option

Use **Ubuntu Desktop 26.04 LTS, amd64** as the selected documented path for an
Intel/AMD PC. It offers a graphical installer and local troubleshooting tools.
Ubuntu Server 26.04 LTS is a headless alternative; platform
workloads must not depend on the desktop environment.

The owner selected 26.04 LTS instead of the original 24.04 proposal; see
[the decision record](adr/0001-ubuntu-desktop-26-04.md).
As checked on 2026-10-17, NVIDIA Container Toolkit's platform table
lists both Ubuntu 24.04 and 26.04. The selected driver/runtime/Kubernetes/vLLM
combination passed the separate CUDA, allocation, storage and streaming checks
recorded in [versions.md](versions.md). Manual Git rollback, storage-preserving
stop/start, and quiescent SQLite/token backup are verified under issue #7 (full
restore rehearsal untested). No OS release alone establishes compatibility.

The desktop compositor and GUI applications can consume GPU memory. Record idle
VRAM/processes before inference tests, avoid unrelated GPU workloads, and allow
headroom. Disable automatic suspend during serving. A dual-boot host serves
nothing while Windows is booted; that is an availability constraint, not an
application configuration choice.

## Milestone order

Host and GPU validation → one real vLLM replica → GitOps → two shared-GPU replicas
→ llm-d routing → standardized observability/benchmarks → LMCache → portfolio demo.

By owner decision (2026-10-18, issue #19 MVP addendum), single-backend real-model
`llm-d` routing is ordered ahead of the two-replica shared-GPU (`#18`) and
synthetic simulator (`#17`) qualification it depends on, while retaining all
runtime safety and single-GPU guards.

Begin with Qwen/Qwen3-1.7B as a candidate, FP16, tensor parallelism 1, context
4096, and concurrency 4. These settings are encoded in the
[deployed GitOps configuration](gitops.md) with pinned model/runtime references
and observed streaming output under issue #6. They are not performance-calibrated;
other hosts need their own compatibility and serving validation.

Automatic prefix caching reuses token-prefix KV state in local GPU memory;
LMCache can extend KV storage beyond that GPU. Neither is a cache of completed
answers. Measure prefill/TTFT and verify cache reads/writes rather than inferring
cache behavior from latency alone.

Two vLLM processes normally load two copies of the model. GPU time-slicing grants
shared access, not VRAM partitions. CPU limits do not cap VRAM. Both replicas
remain in one hardware failure domain; no linear throughput gain is assumed.
llm-d experiments must use its gateway/scheduler rather than an ordinary Service.

Endpoints, dashboards, and the Kubernetes API stay private. Keep simulator pools
separate from real inference and label all results. Add no custom scheduler,
controller, paid infrastructure, or LMCache dependency before a demonstrated need.

## Sources checked 2026-10-17

- [NVIDIA Container Toolkit platform support](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/supported-platforms.html)
- [Ubuntu Desktop installation](https://documentation.ubuntu.com/desktop/en/latest/tutorial/install-ubuntu-desktop/)
- [Ubuntu NVIDIA driver installation](https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/)
