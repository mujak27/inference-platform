# Triage labels

| Skill role | GitHub label | Meaning |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | Maintainer needs to evaluate the issue. |
| `needs-info` | `needs-info` | Waiting for more information. |
| `ready-for-agent` | `ready-for-agent` | Fully specified and ready for agent implementation. |
| `ready-for-human` | `ready-for-human` | Requires human implementation. |
| `wontfix` | `wontfix` | Will not be actioned. |

Use these exact strings when a skill refers to a triage role. Before applying a
label, inspect the remote label list and create missing approved labels as
needed; this mapping does not assert that they already exist on GitHub.
Readiness labels do not override blocking dependencies or operational approvals.
