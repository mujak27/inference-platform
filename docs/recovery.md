# Single-node operations and recovery

## Evidence boundary — 2026-10-18

[Issue #7](https://github.com/mujak27/inference-platform/issues/7) exercises have
now been executed and observed. This document remains the operator procedure; the
[version record](versions.md#observed-rollback-stopstart-and-sqlite-backup--issue-7-2026-10-18)
holds the observed results and their limits. That record contains observed
installation, private access, GPU allocation, retained storage, one Ready vLLM
replica and real streaming under issues #3–#6, plus the issue #7 manual
configuration change and Git revert, the storage-preserving `replicas` 1→0→1
exercise, and the quiescent SQLite/paired-token backup with off-host transfer and
disposable SQLite integrity check. Pins and exact OS/kernel/driver/package versions
are in that record; do not substitute a documentation commit for a live revision.

The issue #7 configuration change/Git revert (`90db167` → `53f8313`), replicas
1→0→1 (`7660b44` → `b96d69a`), and the quiescent SQLite/token backup, off-host
transfer and integrity checks were executed and verified on 2026-10-18. **Full K3s
restore and token bootstrap/decryption remain UNTESTED.** Earlier pod-replacement
cache reuse is not the issue #7 stop/start exercise; smoke timings are not
benchmarks. Each future execution still requires its own approval.

Before issue #7's exercises, the last recorded child sync was
`e2b9b8f4c0757df0b37ba8f66982bcd405d66afa`, while the issue #6 integrated baseline
`8eb55b437994afee49e79335617f602e9cc47d44` (PR #14) and the issue #7 runbook
baseline `2fcb799f34d555bafd34e7103c5b7e7f22202004` (PR #27) shared the identical
operational tree. After those exercises (`90db167` → `53f8313`, `7660b44` →
`b96d69a`) the live child `vllm` Application is synced at
`b96d69a901ef845ac6a22e305a64e15bf7ac787a`, with the same baseline operational
settings (`MAX_NUM_SEQS=4`, `replicas=1`).

## Approval and private access

Before acting, obtain owner approval for the exact merged source/sync SHAs,
change and revert interruptions, separate zero/one outage and return path, and
any privileged backup access. K3s stop/start windows, credential-bearing host
staging, encrypted off-host destinations, local validation and retention require
explicit approval too. Restore requires its own target/window/reversal approval.
Merge is not deployment permission. Use one host-mutating operator, with console
recovery and a second SSH connection available; stop on drift or ambiguous results.

Use the established [private SSH path](bootstrap.md#2-establish-a-private-network-path),
not its first-install/package commands. Keep the host alias, username, addresses,
key paths, kubeconfig and Argo credentials outside Git in owner-only storage.
Verify the SSH fingerprint at the console, use key authentication and
`StrictHostKeyChecking=yes`; never bypass a changed host key. Recheck Wi-Fi/DHCP
addresses and the management-source firewall rule without broadening exposure.

On the management client, use the existing approved ports and private variables:

```sh
ssh -N -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes \
  -L "127.0.0.1:${API_LOCAL_PORT}:127.0.0.1:6443" "$HOST_ALIAS"
```

Confirm the actual API port first. Use the owner-only kubeconfig with its verified
CA and certificate-matching TLS server name, setting its server to this loopback
tunnel; never set insecure TLS options or print kubeconfig contents. In another
terminal, select the target explicitly for every kubectl command:

```sh
kubectl --kubeconfig "$KUBECONFIG_PRIVATE" --context "$CONTEXT" get --raw=/readyz
kubectl --kubeconfig "$KUBECONFIG_PRIVATE" --context "$CONTEXT" \
  -n inference port-forward --address 127.0.0.1 svc/vllm 8000:8000
```

Forward Argo's ClusterIP Service similarly on the existing approved loopback port
8080. Verify/pin its serving certificate using the privately retained certificate
(issue #6 used the `argocd-secret` certificate); no insecure Argo login. Keep
passwords/tokens in protected files/client input, not argv, tracing or transcripts.
Do not reuse an unidentified forward or terminate another operator's process.
After readiness, run the reviewed, checksum-verified client from approved source:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/smoke-test.py --base-url http://127.0.0.1:8000
```

Require exit 0, SSE MIME, nonempty incremental content before completion, no error
and terminal `[DONE]`. Record client timings as smoke observations only.

## Fresh baseline and evidence for every transition

Before mutation, inspect SSH/firewall, driver, API/node/device-plugin health,
one allocatable GPU, Argo policy/current operations/revisions, Deployment/pod
readiness and consumed configuration, endpoints, idle GPU memory, disk headroom,
and a real streaming smoke. Stop on unexpected workloads, unhealthy serving,
an active Argo operation, missing cached image/weights or a new pull/download need.
No new acquisition, listener, firewall, pin, security or storage-policy change is
implied. Keep root's known empty-child-`syncPolicy` cosmetic OutOfSync/Healthy
difference classified; do not repair it or sync root for these exercises.

For baseline, changed, reverted, stopped and restarted phases, retain UTC times,
source/merge/requested/observed SHAs, reviewed local and Argo renders/diffs,
operation ID/result, Deployment generation/observedGeneration and replica counts,
pod readiness/restarts/image ID, generated ConfigMap reference and runtime config,
startup logs, endpoints, storage identities/binding/protections, cache and disk/GPU
observations. Use explicit bounded deadlines (workload readiness up to 1800 s);
on timeout report and use only the pre-approved response, not repeated syncs.
Reconcile uncertain submissions read-only before retrying.

Raw evidence stays outside Git in directories 0700/files 0600. Publish only
reviewed redacted summaries: dates, exact software/model/image/Git pins, command
vectors/tool hashes, durations and pass/fail/skipped outcomes. Omit addresses,
usernames, node/storage identities, raw logs/manifests, credentials and token hashes.
Update [versions](versions.md) and [milestones](milestones.md) only with observations.

## Manual configuration change and Git rollback — observed (issue #7, 2026-10-18)

Executed and verified on 2026-10-18: the reviewed `MAX_NUM_SEQS` 4→3 change
(merged `90db167`) and its clean Git revert (`53f8313`) were each manually
child-synced, observed live and confirmed with real streaming — see the
[version record](versions.md#observed-rollback-stopstart-and-sqlite-backup--issue-7-2026-10-18).
The steps below remain the approved procedure; that result does not re-authorize a
new change or sync, and any future execution needs its own approval.

1. Review a demonstration commit changing **only** `MAX_NUM_SEQS=4` to `3` in
   `apps/vllm/base/kustomization.yaml` and its exact expectation in
   `tests/test_gitops.py`. Keep all other settings/pins unchanged. Run the
   [local checks](gitops.md#validate-locally-without-a-cluster), review/CI, and
   obtain owner merge and approval naming the exact merged SHA and both rollouts.
   This document does not make that change; normal desired configuration is 4.
2. Inspect Argo's render at that SHA. Manually sync **child `vllm` only** to the
   exact approved SHA, prune=false, no force/replace or automated sync. Do not
   sync root or a pre-service-link-fix revision. ConfigMap hashing replaces the
   pod with zero surge; expect interruption on one GPU.
3. Require child requested revision/Synced/Healthy, one Ready pod, generated
   config/reference and environment value 3, startup parsed engine setting
   `max_num_seqs=3`, and successful real streaming. Environment alone does not
   prove consumption; if parsed runtime evidence is unavailable, stop short of
   claiming the live effect. Operation Succeeded alone is insufficient.
4. After acceptance, review and merge a normal `git revert <demonstration-commit>`
   including the test expectation; record its original/merge/revert relationship.
   Obtain exact merged revert-SHA approval and repeat child-only manual sync.
   Require consumed value 4, restored baseline operational render, Ready/Healthy
   and successful real streaming. No history rewrite, direct patch, Argo history
   rollback or `kubectl rollout undo` substitutes for this Git recovery proof.

## Storage-preserving stop/start — observed (issue #7, 2026-10-18)

Executed and verified on 2026-10-18 with Git commits `7660b44` (stop) and `b96d69a`
(start); the restarted pod reused cached weights from the retained PVC with no
re-download — see the
[version record](versions.md#observed-rollback-stopstart-and-sqlite-backup--issue-7-2026-10-18).
The steps below remain the approved procedure and still require separate approval.

Use reviewed Git commits to change `count: 1` to `0`, then back to `1` in
`apps/vllm/overlays/single-replica/kustomization.yaml`, each owner-merged and
exact-SHA approved, with the same child-only manual no-prune sync. The static
replica guard accepts only 0/1; normal desired state remains 1. Do not merge the
return commit until zero-state evidence is captured; pre-agree its publication,
outage window and failure response so serving is not silently left stopped.

At zero, require observedGeneration caught up, desired/current/ready replicas 0,
no active inference pod/ready Service endpoints, and released model GPU allocation
(desktop VRAM remains). Require the **same** Namespace/PVC/PV identities, Bound
claim/volume, actual PV Retain and Namespace/PVC `Prune=false,Delete=false`.
Argo Healthy alone does not prove stop; smoke is not expected to work while stopped.

At one, require one new Ready pod requesting one GPU, unchanged runtime/pins and
protections, same retained mount, ready endpoints, cached-weight startup logs and
real streaming. Compare recursive cache `lstat` inventories: relative path/type,
size, nanosecond mtime, symlink target, weight shard links and backing blobs;
retain private listing hashes and explicit additions/removals/changes. Unchanged
metadata plus logs supports cached-file reuse/no observed re-download, not full
content identity or zero metadata network traffic. Model files persist; GPU
APC/KV state does not. Never use pod deletion or `kubectl scale` for this exercise.

[Retention limits](../bootstrap/storage/README.md#capacity-and-retention-limits):
Retain and Argo annotations are guardrails, not backups or replication. Direct
deletion, namespace removal, administrator error and disk/node loss can destroy
data. No retention test by deleting real storage, cascade deletion, uninstall or
routine Namespace/PVC/PV deletion. Root deletion does not stop inference. Inventory
old hashed ConfigMaps left by no-prune sync; do not clean them up as rollback.

## SQLite and paired-token backup — observed and validated; restore UNTESTED

Executed and validated on 2026-10-18: a quiescent stopped copy of `server/db/` plus
the paired server token and allowlisted prerequisites was packaged, SHA-256
verified, transferred over strict-host-key SSH to encrypted off-host storage, and
checked with a disposable SQLite `integrity_check`/`foreign_key_check` — see the
[version record](versions.md#observed-rollback-stopstart-and-sqlite-backup--issue-7-2026-10-18).
**Full K3s restore and token bootstrap/decryption remain UNTESTED**, and this
sequence remains approval-gated for any future execution.

[K3s documents copying the SQLite `server/db/` directory and retaining its matching
server token](https://docs.k3s.io/datastore/backup-restore). It does **not explicitly
require stopping K3s**. This procedure chooses a quiescent stopped copy for
[SQLite consistency](https://sqlite.org/howtocorrupt.html#backup_or_restore_while_a_transaction_is_active).
An idle inference endpoint does not quiesce Kubernetes writes. Live recursive
`tar`/`cp` is not a validated consistent backup; a separately reviewed SQLite
Online Backup API design would be different. Do not use etcd snapshot/reset flags.

1. **Approve and preflight.** Privately confirm SQLite backend, actual data-dir
   (default `/var/lib/rancher/k3s`), service/config/environment paths, token shape,
   existing utilities, no second writer/supervisor and service stop/start semantics.
   Freeze configuration/token rotation and other operators. Enumerate regular
   files/directories; reject unexpected links/devices/mounts, resolving any token
   link to actual bytes privately. Check bytes/inodes and space for raw stage,
   archive, disposable validation copy and startup working space. Proposed bounds,
   requiring explicit approval: source ≤1 GiB, host temporary allocation ≤5 GiB,
   client reservation 5 GiB, ≥125 GiB root free after reservation. Larger inputs
   require reapproval. Confirm encrypted-at-rest off-host destination, key custody,
   credential access, retention and protected cleanup scope; permissions alone
   are not encryption. No new package/encryption-tool installation is implied.
2. **Prepare protected capture.** Use a new unique root-owned host run/stage
   directory, umask 077, directories 0700/files 0600; reject reused/symlinked paths.
   Do not alter source permissions. Include complete `server/db/`, actual paired
   `server/token`, and narrowly allowlisted effective config/drop-ins, service and
   environment files, node password/identity, registry/runtime/custom-manifest
   prerequisites and exact binary checksum/version/Git pins. Retain private
   kubeconfig/Argo access separately. All these contents are credential-bearing.
3. **Bound the consistency window.** Before stopping, review one failure-safe
   execution plan with an EXIT/signal handler that attempts normal service start
   after any stop/copy failure, preserving the original error and reporting restart
   failure. Require initially active K3s; mark recovery responsibility before stop.
   Proposed window: reserve 5 minutes; DB copy deadline 60 s, token copy 10 s,
   post-start API readiness observation 300 s (workload recovery separately bounded).
   Owner must approve these limits and escalation, not treat them as guarantees.
   Stop `k3s.service` normally; verify inactive/MainPID=0 and no open DB/sidecar
   handles or other writers. A missing/failed handle-check tool is not proof.
   Copy the **entire** db directory, including any WAL/journal/SHM, plus its
   contemporaneous server token while stopped; compare exact file inventory/bytes
   against stopped sources with boolean-only output. Never remove sidecars,
   checkpoint/change the live DB, force-kill, run killall/uninstall or reboot.
   If stop/copy/check fails, no valid backup claim; invoke the approved recovery
   response and notify owner. Do not let an SSH timeout bypass restart handling.
4. **Restart promptly.** Start K3s normally before packaging/validation. Containers
   may continue during a K3s service stop, but API/forwards fail and inference
   availability is not guaranteed. Record stop/start duration; re-establish private
   access and verify API/node/plugin/storage, child/pod health and real streaming.
   Never compare the now-changing live database to the stable copy.
5. **Validate stable bytes.** Package only staging into a new private partial
   archive; check member allowlist/types/sizes, exit status, permissions, flush
   durability, and SHA-256 before finalizing. Keep inventory/checksums private,
   never publish a separate token hash. Before extraction reject absolute/`..`
   paths, links/devices and expanded-size overruns. Extract into a new private
   disposable directory, preserving DB sidecars together, never live state.
   Compare extracted bytes before SQLite opens a disposable writable copy, using
   an existing Python sqlite3/SQLite validator with a reviewed timeout (proposed
   120 s). Require `PRAGMA integrity_check` exactly `ok`, no `foreign_key_check`
   rows, and expected nonempty Kine schema. Do not use immutable mode to ignore
   WAL; keep original stage/archive untouched. Suppress SQL/error contents publicly.
6. **Verify off-host retention.** Transfer over strict-host-key SSH without a PTY
   directly into a new private file, not tool/chat stdout. Check transfer exit,
   byte count, flush durability and destination SHA-256 against the independently
   obtained authenticated source digest before finalizing. Use the approved
   encrypted destination; protect encryption keys independently. Record UTC time,
   K3s version/backend, counts/aggregate bytes, permission/copy/archive/SQLite/
   transfer statuses and post-start health. Same-root-disk staging is not disaster
   recovery. No automatic retention deletion is authorized.

Integrity checks prove neither Kubernetes semantics nor token decryption/bootability.
Capture provenance and pairing are not a token bootstrap test. The archive contains
cluster Secrets/bootstrap state and its decryption credential, **not** model PVC
bytes, image layers, OS/packages or other disks. Public pinned weights may be
reconstructed later if available with separate acquisition approval; credentials
and cluster identity are not reconstructible from public Git.

## Restore preparation — full restore UNTESTED

Prefer a separately approved isolated target; never run two active copies of one
cluster identity on the original network. Approve exact target, maintenance and
reversal plan; preserve current state and the only known-good archive. Verify
archive/transfer hashes, safe members, matching token and encryption-key access,
capacity for safety copies/extraction/startup, and backed-up prerequisites first.

Prepare a stopped, uninitialized compatible target with recorded K3s
`v1.35.9+k3s1` and matching effective config/runtime, node identity/password,
data-dir, local-path backing mounts, CIDRs/TLS names, registry/manifests,
driver/Toolkit/plugin and image/model pins. Do not combine restore with upgrades,
blindly rerun installers or allow an empty cluster to initialize first.

With all writers stopped, restore complete db contents as one matched set and
its paired server-token file per upstream into the verified target, preserving
ownership/restrictive modes. Do not overlay another database's WAL/journal or
substitute an agent/new token. Ensure CLI/environment token settings do not
override the restored token; never pass its value in argv. Resolve TLS/bootstrap
conflicts through target-specific review, not deletion/retry loops. Local PV
payload/path recovery, node affinity and claim rebinding need a separate reviewed
plan; restoring cluster objects does not restore cache bytes.

Start normally and observe bounded readiness. Verify fresh SSH/UFW/private TLS
access; OS/kernel/driver/runtime and GPU health; API/node Ready; exactly one plugin
and one allocatable GPU; retained storage identity/binding/path/cache; manual Argo
policy and approved revisions; one pinned Ready vLLM pod, GPU headroom, cached
startup and real streaming. Reconcile only approved Git revisions without prune.
Disposable GPU compute/allocation probes need separate approval and must not
contend with serving. Report every skipped check; backup integrity alone never
counts as tested full recovery.

## Growth, upgrades and availability

- Monitor before/during each operation and approved acquisition: root free bytes/
  inodes, model-cache logical/allocated size, containerd, pod/journal/syslog and
  writable-layer growth, pod churn and GPU memory/process categories. Carry forward
  monitored growth ceilings from the accepted baseline: model +20 GiB, containerd
  +20 GiB, logs/writable +5 GiB, aggregate +45 GiB. Budget backup staging separately.
  Stop new acquisition at 125 GiB free; 100 GiB is the absolute floor. Stop/report
  before ceilings or floors are breached; never auto-prune/delete to regain space.
- These are monitoring policies, not enforced quotas. A 20Gi local-path claim,
  ephemeral limit, kubelet image GC and 10 MiB ×5 per-container log rotation do
  not bound all host growth. Retain only owner-approved backup generations and
  review capacity/retention before each backup; no cron or new policy is installed.
- Before an approved OS/kernel/driver/Toolkit/K3s/plugin/Argo/vLLM/model upgrade,
  record current versions, advisories, pins and health; validate compatibility,
  reviewed render/schema/tests, backup/reversal readiness and disk/VRAM budget.
  Separate upgrade from restore; preserve the working driver/firmware/desktop,
  Linux/NTFS disks and security controls. Never disable security updates simply
  to freeze versions. Reboot/service interruption needs its own approval.
- After upgrade repeat private SSH/firewall, driver and approved container CUDA
  computation/allocation checks, API/node/plugin/GPU capacity, retained storage,
  consumed pins/config, Argo/manual reconciliation and real streaming checks.
  Schedule compute/allocation probes in an approved stopped-serving window. Record exact
  versions/commands/date/outcomes and revalidate backup/restore compatibility;
  an old backup or previous release's evidence does not validate the new release.
- One host/GPU and unreplicated root storage are single failure domains, not HA.
  Wi-Fi loss, DHCP/source-firewall changes, suspend/power loss and management-client
  loss interrupt access; desktop applications compete for VRAM. Dual boot takes
  Linux serving offline. No GPU sharing, llm-d, LMCache, performance calibration
  or unattended recovery is established by this procedure.

Sources reviewed 2026-10-18: [K3s backup/restore](https://docs.k3s.io/datastore/backup-restore),
[server token](https://docs.k3s.io/cli/token),
[service stop/start](https://docs.k3s.io/upgrades/killall),
[configuration precedence](https://docs.k3s.io/installation/configuration),
[SQLite WAL](https://sqlite.org/wal.html),
[integrity checks](https://sqlite.org/pragma.html#pragma_integrity_check).
