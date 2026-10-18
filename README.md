# Inference platform

A reproducible, GitOps-managed Kubernetes inference platform, built incrementally
with vLLM, llm-d, and LMCache. **Status: one private vLLM replica serving with
observed streaming output (issue #6); rollback and recovery remain unverified
(issue #7).** Smoke timings are not benchmarks; llm-d and LMCache remain deferred.

## Start here

1. Read the [platform requirements](docs/architecture.md).
2. Follow the [Ubuntu Desktop installation guide](docs/host-installation.md), or
   supply an existing Linux host meeting the same requirements.
3. Complete [network access and host bootstrap](docs/bootstrap.md).
4. Run `bash scripts/preflight.sh` **on the Linux GPU host**.
5. Record actual versions and evidence before selecting the container/Kubernetes stack.

After the runtime installation and pinned image pull have been separately approved,
run `sudo bash scripts/validate-cuda.sh` on the Linux GPU host. It uses K3s bundled
containerd, the fixed vLLM image digest, and NVIDIA runtime to check the literal
CUDA float32 matrix result `[[58,64],[139,154]]`. It downloads no models and pulls
no images. Success is one schema-1 JSON record with actual PyTorch/CUDA versions;
missing GPU, incorrect/malformed output, or runner failure is nonzero with stderr
diagnostics and no success stdout. Python 3 standard library is required on the
host. `--runner /path/to/executable` is the argv-safe test seam, not shell text;
fake-runner unit tests do not prove hardware execution. Concurrent runs use the
same disposable container name and are not supported.

Ubuntu Server is **not required**. Ubuntu Desktop is an installation option, not
a dependency of the platform. Disk layout, dual boot, usernames, IP addresses,
and the management computer are operator-specific and are not baked into workloads.

## Planned serving path

```text
Private client → llm-d gateway/scheduler → vLLM A or vLLM B
                                           └── one shared NVIDIA GPU
                                               optional LMCache CPU tier later
```

The initial validation target is a single RTX 3090 (24 GB VRAM) with 128 GB host
RAM. Two replicas on it demonstrate routing and lifecycle behavior, **not**
independent GPU scaling or GPU fault isolation. Other hosts need their own
capacity and compatibility validation.

See [milestones](docs/milestones.md) and the [version/evidence record](docs/versions.md).
No model weights, credentials, installation images, or raw host inventories belong in Git.

## GitOps and serving

[GitOps guide](docs/gitops.md): `bootstrap/`, `infra/`, and `apps/` follow the
[k8s-crossplane layout](https://github.com/mujak27/k8s-crossplane). A pinned Argo CD
bootstrap and single-replica vLLM configuration have been deployed and observed.
Both Applications still require manual sync; merging changes does not authorize
deployment. See the version/evidence record for host, GPU, storage and serving
results and their limits. Manual Git rollback, stop/start and backup/recovery
acceptance remain pending under issue #7.

[Operations and recovery](docs/recovery.md) covers private access, approval-gated
Git rollback and stop/start, SQLite/token backup, and untested restore preparation.

## Local checks

```sh
python3 -m pip install -r requirements-dev.txt
bash -n scripts/preflight.sh scripts/validate-manifests.sh scripts/validate-cuda.sh
python3 -m unittest discover -s tests -v
bash scripts/validate-manifests.sh
git diff --check
```

Manifest checks need kubectl and kubeconform; versions and schema limitations
are documented in the GitOps guide. No configured cluster is contacted.

Host installation is manual and intentionally does not automate partitioning,
flashing, reboots, or firewall changes. Container CUDA computation and Kubernetes
GPU allocation were independently verified before serving; those results do not
establish rollback or recovery acceptance.
