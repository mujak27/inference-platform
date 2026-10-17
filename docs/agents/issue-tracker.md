# Issue tracker: GitHub

Issues and specs live in https://github.com/mujak27/inference-platform/issues.
Use the `gh` CLI with `--repo mujak27/inference-platform` to avoid targeting a
different repository. Local plans and OpenChamber todos are not the ticket tracker.

## Operations

- List before creating to avoid duplicates:
  `gh issue list --repo mujak27/inference-platform --state all --limit 100`.
  Search or paginate further when needed.
- Read the body, labels, and comments:
  `gh issue view <number> --repo mujak27/inference-platform --comments`.
- Create an approved ticket:
  `gh issue create --repo mujak27/inference-platform --title "..." --body-file <path>`.
- Comment:
  `gh issue comment <number> --repo mujak27/inference-platform --body "..."`.
- Update labels:
  `gh issue edit <number> --repo mujak27/inference-platform --add-label "..."`.
- Close only after verifying acceptance criteria:
  `gh issue close <number> --repo mujak27/inference-platform --comment "..."`.

When a skill says to publish to the issue tracker, create a GitHub issue after
the required publication approval. Include scope, non-goals, durable approved
decisions, acceptance criteria, validation methods, and blockers. Local-only
plan links are insufficient context for a remote ticket. Keep credentials,
private host identifiers, and raw inventory out of public issues.

Link issues and pull requests being worked on to the current session with
`session.link` when available. Preserve existing parent issues. Use GitHub
sub-issues for child tickets where available; otherwise use a parent task list
and a `Part of #<parent>` line in each child.

## Dependencies

Prefer GitHub's native blocking relationships:

```sh
gh api --method POST repos/mujak27/inference-platform/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-database-id>
```

Get the numeric database ID with
`gh api repos/mujak27/inference-platform/issues/<blocker> --jq .id`;
it is not the issue number or node ID. If native dependencies are unavailable,
put `Blocked by: #<number>` links in the child and report the fallback. Verify
prerequisite implementation and checks before starting dependent work; closing
an issue alone does not integrate its code.

## Pull requests as a triage surface

**PRs as a request surface: no.**

Issues and pull requests share GitHub's number space; resolve the object type
before using an issue or PR command. Ticket publication does not authorize
implementation, pushing, PR creation, merging, or deployment.
