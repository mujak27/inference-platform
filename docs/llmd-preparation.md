# llm-d qualification — source checks, not runtime adoption

Issue [#16](https://github.com/mujak27/inference-platform/issues/16), fixed source
base `8eb55b437994afee49e79335617f602e9cc47d44`. No Application, CRD installation,
cluster operation, GPU sharing or model/image download is authorized here.
The single-engine vLLM 0.31.0 image, model and resource settings remain unchanged.

## Provenance and deliberate integration

Reviewed uncommitted preparation on branch `llmd-next`, base
`d0c1608d7e8641f6391514525b88650afc7b1697`, on 2026-10-18. Its original worktree
and ignored artifacts were preserved. The real values and four simulator source
files were deliberately integrated, with equivalent compact YAML. README links
were added without replacing newer baseline documentation. The two old render
scripts were replaced by offline wrappers and one atomic renderer; validation
and tests were rewritten at the approved public CLI seams, not copied blindly.
Historical generated output and downloaded tools were not integrated as evidence.

Both inspected cached chart archives match SHA-256
`d5d94816d4075d56028d937e2134d66bc561b2d752259b18f01084b4d7f1602b`.
That archive includes `templates/rbac.yaml` granting pool AND objective/rewrite
reads, in addition to library Pod reads. The final real render replaces chart
Role/RoleBinding resources with reviewed `candidate/discovery-rbac.yaml`: only
namespaced Pod and GA InferencePool get/list/watch for `llmd-epp`. Simulator
no-pool mode keeps only its namespaced Pod reads. No ClusterRole or writes.
CRD administration/retention belongs to a separately approved operator, outside
workload cleanup. No additional CRD is installed to satisfy optional watches.

## Pinned source artifacts and tools

- Standalone chart `oci://ghcr.io/llm-d/charts/llm-d-router-standalone:v0.11.0`;
  archive checksum above; recorded OCI manifest
  `sha256:56a5635f5fd6e1252f802e06186cf9c4c60bcb95b7911b0867660a7db4d04c1c`.
- EPP `ghcr.io/llm-d/llm-d-router-endpoint-picker:v0.11.0@sha256:39257d24552d16d8f215d3de25cc734fd44af3b282b67032db01aff900c610cf`.
- Envoy evaluation override `docker.io/envoyproxy/envoy:distroless-v1.37.8@sha256:036ffe3333bd35828fd229d79cb5f2216082bd8a9732cff69db0413d96ae0150`.
  Upstream 1.33.2 is EOL and blocked; this override is not certified interoperability.
- GAIE v1.5.0 `v1-manifests.yaml`, SHA-256
  `cd7cc63149943627f92d401991886a631d938de28edb416312c443a1b7f42ded`.
  Real pool API is `inference.networking.k8s.io/v1`; simulator needs no pool CRD.
- Helm 4.3.1, kubectl 1.37.1/Kustomize 5.8.1, kubeconform 0.8.0, PyYAML 6.0.3;
  CI Python 3.12. Exact release/checksum commands are in the validation workflow.
  Local source checks used Python 3.9.6 on Darwin arm64; not target execution.

The coordinating session reported fresh registry/source metadata verification on
2026-10-18 matching these image/chart pins and amd64 availability. This source
implementation independently rehashed cached chart bytes only. Signature
verification results, Trivy SARIF contents, full SBOM/package scanning and
explicit acceptance of any new risks are recorded above and remain open before
runtime use. Prior containerd/runc risk acceptance is not blanket acceptance of
these images.

## Pinned EPP configuration acceptance — no supported dry-run seam

Upstream EPP v0.11.0 (commit `a5cbe600ebade00cf3e9885beaf2bfacddeabce1`) exposes
no `--validate`, `--dry-run` or equivalent CLI mode. `Options.AddFlags` accepts
configuration inputs; `Runner.Run` parses, then requires Kubernetes
configuration or starts file-discovery serving — file discovery is not a dry
run, and a missing-kubeconfig failure happens before phase-two plugin
validation.

- `loader.LoadRawConfig` performs strict structural parsing only; it does not
  instantiate plugins. Unknown plugin types survive this phase.
- `loader.InstantiateAndConfigure` performs genuine registry/factory
  validation: registered types, duplicate names, strict parameter decoding,
  system defaults and reference checks. It uses unexported production
  registration and does not perform all production phase-two work.
- Compile-only builds (`go build`, `go test -c`) prove compilation, not
  configuration acceptance. Upstream unit targets build a builder image;
  “hermetic” integration tests acquire envtest binaries. Neither is a
  validated acceptance of our mounted files.

Any acceptance of the mounted EPP ConfigMap requires a new, separately
approved harness using upstream internals with the exact pinned toolchain
(`go.mod` requires Go 1.26.6), network disabled, no credentials/model files,
bounded resources, and negative controls. Production phase two auto-creates
approximate-prefix (cleanup goroutine) and tokenizer (local estimation with
zero config; other configurations start renderer warmup) producers, so factory
side effects require bounded input and network isolation. YAML equality with a
fixture is not this evidence.

## Envoy validation seam — proposed, not executed

Envoy `--mode validate` performs filesystem-only validation with no network
traffic and no hot restart. A proposed isolated invocation is recorded here for
approval, not execution:

```sh
docker run --rm --pull=never --platform=linux/<arch> \
  --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  --user=65532:65532 --cpus=1 --memory=512m --pids-limit=64 \
  --mount "type=bind,src=${BOOTSTRAP},dst=/etc/envoy/envoy.yaml,readonly" \
  --entrypoint /usr/local/bin/envoy \
  docker.io/envoyproxy/envoy:distroless-v1.37.8@sha256:036ffe3333bd35828fd229d79cb5f2216082bd8a9732cff69db0413d96ae0150 \
  --mode validate -c /etc/envoy/envoy.yaml \
  --service-node <rendered service-node> --concurrency 1 --log-level warn
```

Validate the exact rendered bytes. Do not use `envsubst`, fabricated addresses
or `--config-yaml` to make validation pass; the pinned preset renders host/TLS
values through Helm and invokes Envoy directly. `linux/arm64` execution is not
target amd64 proof. Validation does not prove DNS, TLS handshakes, discovery,
ext_proc interoperability or SSE.

## Reproduce source checks

First obtain separate approval for any tool installation/artifact retrieval. CI
declares pinned acquisitions; no CI run or executable/chart download was performed
by this source-only implementation. With approved tools and source inputs:

1. Put the approved chart archive at `.local/llmd/llm-d-router-standalone-v0.11.0.tgz`
   and the GAIE asset at `.local/llmd/crds.yaml`. Checksums are checked before use.
2. Run the following; no render command fetches artifacts or contacts a cluster:

```sh
bash scripts/render-llmd.sh
bash scripts/render-llmd-sim.sh
python3 -B -m unittest discover -s tests -v
bash scripts/validate-manifests.sh
python3 -B scripts/validate-llmd.py --candidate real
python3 -B scripts/validate-llmd.py --candidate sim
git diff --check
```

Render commands accept `--chart PATH --output PATH`. Tests accept `LLMD_CHART`
to read an approved cached archive without copying it. Final outputs are replaced
only after all rendering succeeds. Missing tools/chart/render/schema inputs fail;
tests do not skip. Validators rerender into a temporary directory and compare
bytes with supplied output, so old or edited YAML cannot satisfy the required
gate. They use `--rendered PATH --chart PATH --crds PATH`; `KUBECONFORM` selects
an explicitly approved tool. Built-in schema lookup may retrieve schema DATA from
the repository's commit-pinned remote; no downloaded Python converter is executed.

`--policy-only` is an explicitly partial, supplied-YAML inspection seam used by
mutation tests. It does NOT check freshness/schemas and is never the required CI
gate. CLI success reports that distinction and pending runtime gates. Policy
checks parse actual mounted ConfigMaps, request-path ext_proc, discovery flags,
selectors, RBAC, private Services and CPU/no-volume boundaries. Invalid controls
cover stale/missing input, fail-open/bypass overrides, schema unknown fields,
GPU/PVC, namespace/selector crossover, public exposure and discovery writes.

Pool schema extraction follows the existing repository extraction pattern and
adds strict object properties; this pinned pool schema has no nullable/union/ref
conversion requirement. Explicit selector/port/ref policy checks cover this
candidate's CEL constraints. General CEL, ObjectMeta, referenced-resource and
admission/controller behavior are NOT proven by JSON Schema. Required schema
checks include positive resources and explicit invalid-enum/port/unknown-field
controls; missing schema/tool errors do not count as successful negative controls.

## Supply-chain verification status, 2026-10-18

Upstream publishes an authoritative verification procedure in
[verifying-releases.md](https://github.com/llm-d/llm-d-router/blob/a5cbe600ebade00cf3e9885beaf2bfacddeabce1/docs/verifying-releases.md).
Checksums establish artifact identity only; signature verification is a separate,
executed gate. `gh attestation verify` is read-only metadata retrieval.

| Artifact | Signature | SBOM | Evidence |
| --- | --- | --- | --- |
| EPP `v0.11.0` (`39257d24…`) | **VERIFIED** | SPDX, 116 pkgs | `gh attestation verify oci://ghcr.io/llm-d/llm-d-router-endpoint-picker@sha256:39257d… --repo llm-d/llm-d-router --signer-workflow llm-d/llm-d-router/.github/workflows/ci-build-images.yaml` exits **0**. Discriminating negative control (`ci-release.yaml`) exits **1**. Signer identity is the reusable workflow path, not the caller. |
| Simulator `v0.11.2` (`32144df7…`) | **NOT AVAILABLE** | **NOT AVAILABLE** | `gh attestation verify` exits **1** against both `ci-release.yaml` and `ci-pr-checks.yaml`; EPP positive control re-run in the same shell exits **0**, so the tool works and the image is unsigned. Build action `.github/actions/docker-build-and-push/action.yml` does plain `docker buildx build --push` — **no cosign, no SLSA generator**. No SPDX layer; only image layers plus an unsigned in-toto document. |
| Simulator in-toto document | **PRESENT but UNSIGNED** | — | Two `unknown/unknown` index children are `application/vnd.in-toto+json`, `predicateType: https://slsa.dev/provenance/v1`. But no `signatures`/`dsseEnvelope`/`payloadType`; `buildDefinition`, `builder` and `buildType` are null/empty; covers linux/amd64 only; BuildKit's own `buildkit_completeness.resolvedDependencies: false`. This is BuildKit auto-provenance, **not** an SLSA-generated release attestation. It has **zero cryptographic verification value** — do not cite it as supply-chain assurance. |
| Helm chart | **NOT COVERED** | **NOT COVERED** | Upstream explicitly excludes `ghcr.io/llm-d/charts/` from signature and SBOM coverage. Archive checksum is identity, not provenance. |
| Envoy `distroless-v1.37.8` (`036ffe33…`) | **NOT AVAILABLE (VERIFIED)** | **NOT AVAILABLE** | Separate upstream project; no llm-d procedure applies. See below. |

### Envoy verification and advisories

- **No container signature, provenance or SBOM.** The OCI referrers endpoint for
  the exact digest returns `{"manifests":[]}` — the authoritative location for
  cosign signatures, SLSA/in-toto provenance and SPDX/CycloneDX referrers. This
  negative is corroborated by build-path source: `_publish_release_container.yml`
  calls `envoyproxy/toolshed/actions/oci/collector`, whose `action.yml` contains
  zero cosign/slsa/sigstore/syft keywords and only runs `buildah manifest
  create/add/push`. The sole `signing.key` in the pipeline is a Debian APT key,
  not container signing. No documented container verification procedure exists;
  `SECURITY-INSIGHTS.yml` declares only Dependabot SCA and CodeQL SAST.
- **Envoy does GPG-sign release archives** (`checksums.txt.asc`, key in
  `releases.asc`, "Envoy maintainers"), with source and linux binaries. That
  covers release archives, **not** the container image this candidate uses.
- **Advisory disposition: 0 advisories leave 1.37.8 vulnerable.** Of 132 total
  GHSA advisories, 7 explicitly name 1.37. Evaluating `vulnerable_version_range`
  against 1.37.8 *including* `patched_versions` leaves none open; every 1.37.x fix
  point in the database is 1.37.1, 1.37.3, 1.37.5, 1.37.6 or 1.37.8. The two
  newest advisories (2026-10-06, before 1.37.8 shipped at 14:43:43Z) both list
  **1.37.8 as the patched version**. Naive range parsing is misleading here:
  scopes such as `>=1.37,<1.39` are advisory coverage, not unpatched status.
- **Known advisory-database lag:** 1.37.9 shipped 2026-10-12 with no advisory
  explaining it; the newest GHSA entry is 2026-10-06. Treat as an open question,
  not a clean bill of health.
- **EOL confirmed:** `RELEASES.md` lists 1.37 supported until **2027-01-13**,
  supporting 1.37.8 as the smallest justified evaluation override. 1.33.2 remains
  blocked (EOL 2026-01-14); 1.36 EOL was 2026-10-14.

Simulator mitigating evidence: its release workflow runs a Trivy scan
(`trivy-action@v0.36.0`, `format: sarif`, `severity: HIGH,CRITICAL`, `exit-code: 1`)
and uploads SARIF via `codeql-action/upload-sarif`. A HIGH/CRITICAL finding fails
the build, so the successful release run implies a clean scan **at build time
only**. SARIF contents were not readable (403); treat as unverified. Releases
carry zero downloadable assets. Advisories: `llm-d/llm-d-router` **0**,
`llm-d/llm-d` **0**, `llm-d/llm-d-inference-sim` **0** — all verified. Empty
component advisories do not mean clean dependencies.

EPP SBOM disposition is not a vulnerability scan. Envoy and vLLM advisory
volumes (132 and 104) require per-advisory disposition against the exact pins,
not blanket acceptance. Prior containerd/runc risk acceptance is not blanket
acceptance of these images. Signature verification and SBOM findings above do not
constitute explicit risk acceptance, which remains an owner decision.

## Compatibility/evidence matrix

| Gate | Evidence class / status |
| --- | --- |
| Pinned chart/image metadata, amd64 variants | Reported verified by coordinating source research, 2026-10-18; no image execution |
| Cached chart checksum/source inspection | Fresh local pass; not publisher signature verification |
| Fresh local render and public source-policy controls | Source-only checks; see execution results in coordinating handoff |
| Earlier Envoy bootstrap acceptance | Historical native Linux arm64 Docker checks in prior preparation; not rerun, not amd64 proof |
| Fresh full candidate schema suite | Passed locally with approved checksum-verified kubeconform 0.8.0: real 8 valid, simulator 10 valid, negative controls passed; CI green on PR #29; suite re-verified on merged base |
| Actual mounted Envoy/EPP config acceptance | PENDING. No upstream dry-run seam exists; `--mode validate` invocation and EPP harness recorded above require separately approved execution scope |
| K3s 1.35.9 / GAIE 1.5.0 admission and discovery | PENDING separately approved API/controller verification; Helm 1.35 capabilities are not admission |
| Target Linux amd64 interoperability | PENDING, including TLS/ext_proc/health behavior |
| vLLM 0.31.0 vs released llm-d vLLM 0.30.0 | Preserve proven 0.31.0; compatibility pending, no silent downgrade (older baseline has fixed-vulnerability concerns) |
| Metrics parser, cache signals, real SSE | PENDING; existing direct-vLLM serving does not prove routed compatibility |
| Provenance signatures, SBOM/advisory disposition | EPP signature **VERIFIED** with discriminating negative control; simulator and Envoy signatures **NOT AVAILABLE** (build paths contain no signing step); Envoy advisory disposition leaves 0 open against 1.37.8 with a known DB lag; chart excluded from upstream coverage. Full detail above. Explicit risk acceptance remains an owner decision before runtime use |

Do not close #16 from source checks alone. #7 owns host recovery operations;
#15 owns numeric experiment limits; #17 remains blocked. Real profile includes
unproven cache scorers. Defaults include very long route/ext_proc/backend
timeouts; do not call them approved experiment limits. Private ClusterIP is not
authentication or network isolation. Header-driven ORIGINAL_DST destination
handling must be checked for untrusted-header bypass during approved runtime
qualification. Do not infer failure behavior or transport security from YAML.

## Primary source pointers

- [Pinned router/chart source](https://github.com/llm-d/llm-d-router/tree/a5cbe600ebade00cf3e9885beaf2bfacddeabce1/config/charts)
- [llm-d v0.10.0 baseline](https://github.com/llm-d/llm-d/tree/f22bbaf3173a326d214f06d7c769b905cb3f489a/guides/optimized-baseline)
- [GAIE v1.5.0 CRD asset](https://github.com/kubernetes-sigs/gateway-api-inference-extension/releases/download/v1.5.0/v1-manifests.yaml)
- [Envoy release policy](https://github.com/envoyproxy/envoy/blob/main/RELEASES.md)
- [Envoy HTTP/2 advisory](https://github.com/envoyproxy/envoy/security/advisories/GHSA-22m2-hvr2-xqc8)
- [Preserved vLLM 0.31.0 metrics source](https://github.com/vllm-project/vllm/blob/v0.31.0/vllm/v1/metrics/loggers.py)
