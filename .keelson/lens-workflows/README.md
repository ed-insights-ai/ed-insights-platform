# Chamber lens workflows

These are **not** loaded from here. Chamber contributes a lens-refresh workflow only from
its own directory, so a file must be copied to:

```
~/.keelson/rib-chamber/lens-workflows/<name>.yml   →  contributed as chamber-lens-<name>
```

The filename decides the contributed name, overriding the file's own `name:` field. The
harness runs a pinned lens panel's refresh **only** for a rib-contributed workflow, so a
copy left in the global workflows directory will never drive a cadence however correct it is.

Contributions are collected at startup, so after adding or editing one:

```bash
keelson workflow status          # check nothing is mid-run — a restart CANCELS running workflows
keelson stop && keelson start
```

They live in the repo so they survive the machine, and so a change to one shows up in review
like any other code.

## beads.yml → `chamber-lens-beads`

Backs the `touchline-queue` lens. A deterministic bash node measures the work queue with `bd`,
and exactly one agent turn composes the board from that measurement — the numbers are never the
agent's to invent. Pin the lens on the Chamber surface and it refreshes every 30 minutes.

Note the hardcoded repo path in its bash node: a panel refresh passes no project, so the
workflow has to know where to `cd`.
