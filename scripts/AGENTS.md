# `scripts/` — Guardrails

## Keep `scripts/README.md` in sync

`scripts/README.md` indexes every top-level script by **when it runs** and **who
calls it**. It is hand-maintained, so it only stays true if the same PR updates it.

Update the index in the same change that:

- adds a script — put the row in the section matching when it runs, and name its
  caller (a person, or the workflow / hook that runs it);
- deletes a script — remove its row;
- changes who calls a script — a new workflow step, a hook installation, a call
  added to or dropped from another script.

`.github/scripts/` is indexed by the same file; a script added there gets a row too.

## Do NOT move or rename existing scripts

Scripts are called by path from documentation, CI workflows, git hooks, and other
repositories. Renaming one breaks callers this repository cannot see.
