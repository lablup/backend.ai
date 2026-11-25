# Changelog fragments

A change that users notice adds one file per issue and kind to `changes/unreleased/`:

```
changes/unreleased/<issue key>.<kind>.md
```

- `<issue key>`: `BAI-123`, `BA-123`.
- `<kind>`: `breaking`, `feature`, `deprecation`, `fix`, `doc`, `misc`. One issue may have several files of different kinds.
- Content: a description for users, not for developers. An empty file is rejected.

## Commands

Run from the repository root.

| Command | Does |
|---|---|
| `go run ./tools/changelog check` | Checks the name, kind and content of every fragment. CI (`build` job) and pre-commit run it |
| `go run ./tools/changelog check --require --base <ref>` | Also fails when no fragment was added since `<ref>` |
| `go run ./tools/changelog batch <version> [--date YYYY-MM-DD] [--allow-empty]` | Writes `changes/<version>.md`, adds the same section under the title of `CHANGELOG.md` and deletes the fragments. Fails when the version exists or there is no fragment; `--allow-empty` writes `No user-facing changes.` instead. The date defaults to today (UTC) |

Release output per version:

```
## <version> (<date>)

### <Kind title>

- <description> (<issue key>)
```
