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
verification, full SBOM/package/advisory scanning and explicit acceptance of any
new risks remain pending before runtime use. Prior containerd/runc risk acceptance
is not blanket acceptance of these images.

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

## Compatibility/evidence matrix

| Gate | Evidence class / status |
| --- | --- |
| Pinned chart/image metadata, amd64 variants | Reported verified by coordinating source research, 2026-10-18; no image execution |
| Cached chart checksum/source inspection | Fresh local pass; not publisher signature verification |
| Fresh local render and public source-policy controls | Source-only checks; see execution results in coordinating handoff |
| Earlier Envoy bootstrap acceptance | Historical native Linux arm64 Docker checks in prior preparation; not rerun, not amd64 proof |
| Fresh full candidate schema suite | Passed locally with approved checksum-verified kubeconform 0.8.0: real 8 valid, simulator 10 valid, negative controls passed; CI not run remotely |
| Actual mounted Envoy/EPP config acceptance | PENDING pinned-binary execution approval and supported EPP config-loader seam |
| K3s 1.35.9 / GAIE 1.5.0 admission and discovery | PENDING separately approved API/controller verification; Helm 1.35 capabilities are not admission |
| Target Linux amd64 interoperability | PENDING, including TLS/ext_proc/health behavior |
| vLLM 0.31.0 vs released llm-d vLLM 0.30.0 | Preserve proven 0.31.0; compatibility pending, no silent downgrade (older baseline has fixed-vulnerability concerns) |
| Metrics parser, cache signals, real SSE | PENDING; existing direct-vLLM serving does not prove routed compatibility |
| Provenance signatures, SBOM/advisory disposition | PENDING; new risks need explicit resolution/acceptance before runtime use |

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
