---
name: release
description: Guide the Backend.AI release process: run release.sh, generate changelog via towncrier, consolidate RC entries for final releases with subsection grouping.
tags:
  - release
  - changelog
  - towncrier
---

# Release workflow

Run the Backend.AI release process: version bump, changelog generation, and RC consolidation for final releases.

## Parameters

- **target_version** (required): release version, for example `26.2.0` or `26.2.0rc2`
- **webui_version** (optional): WebUI version to bundle

## Workflow

### Phase 1: Pre-flight

1. **Parse the parameters**
   - Extract `target_version` from the user input (required)
   - Extract `webui_version` when provided

2. **Check the current state**
   - Read the `VERSION` file for the current version
   - Verify the working tree is clean with `git status`
   - Confirm the expected base branch, usually `main`

3. **Determine the release type**
   - **Pre-release** - the version contains `rc`, `alpha`, `beta` or `dev`, for example `26.2.0rc1`
   - **Final release** - a clean semver, for example `26.2.0`

4. **Locate the changelog file**
   - The changelog is split per version branch: `CHANGELOG/{major}.{minor}.md`. For example, `26.9.0rc1`, `26.9.0` and `26.9.1` all live in `CHANGELOG/26.9.md`
   - The root `CHANGELOG.md` archives the releases made before the split. Do not write to it
   - The file may not exist yet; the first release of the version branch creates it

5. **For final releases, check for prior RC sections**
   - Scan `CHANGELOG/{major}.{minor}.md` for sections matching `## {major}.{minor}.{patch}rc\d+`
   - List the RC sections found to the user
   - These are consolidated in Phase 3

6. **For a `{major}.{minor}.0rc1` target, settle the support level**
   - That form is the rc that cuts a new release line, and the release script recognizes it on its own, so nothing else has to be classified by hand
   - Ask the user whether the line is LTS. The March and September sprints are LTS, per the versioning scheme. A year of support is a commitment and is never inferred
   - When it is LTS, pass `--lts` to the release script below

7. **Confirm with the user before proceeding**
   - Show the target version, the release type, the WebUI version when any, the RC sections to consolidate when any, and for a branch cut whether the line is LTS
   - Wait for user approval

### Phase 2: Release script execution

Run `scripts/release.sh`, which performs these steps:

```bash
scripts/release.sh {target_version} [webui_version]
```

When the line being cut is LTS:

```bash
scripts/release.sh --lts {target_version} [webui_version]
```

What the script does:

1. Creates the branch `release/{target_version}`
2. Downloads the WebUI release when `webui_version` is provided
3. Updates the `VERSION` file
4. Freezes `NEXT_RELEASE_VERSION` placeholders to the actual version. This runs for stable releases only and is skipped for `rc`, `a`, `b`, `dev` and `post`
5. Runs `scripts/run-towncrier.py {target_version}`, which consumes the `changes/` fragments into `CHANGELOG/{major}.{minor}.md`. It is skipped entirely when there are no fragments
6. Runs `.github/scripts/update-maintained-versions.sh {target_version}`, which registers the line when the target is an `X.Y.0rc1` cut and retires the lines that are due. An LTS line retires once its recorded `retire_after` has passed; a regular line retires as soon as any newer line exists. **Report its output to the user**: a retirement means that version stops receiving backports and drops out of the installer channel selection from that point on
7. Generates sample config files
8. Generates API docs (OpenAPI, GraphQL schema)
9. Runs quality checks: `pants tailor --check` and `pants check ::`. These run for final and patch releases only and are skipped for `a` and `rc`, whose release PR CI runs the same checks
10. Commits everything as `release: {target_version}`

Advancing `NEXT_RELEASE_VERSION`:

- `release.sh` does not advance it. When an `X.Y.0rc1` release PR merges and cuts `X.Y`, `create-version-branch.yml` opens a `release: freeze X.Y.0 and bump NEXT_RELEASE_VERSION to X.(Y+1).0` PR against `main`
- That PR also freezes the `NEXT_RELEASE_VERSION` references of `main` to `X.Y.0`, the same value the version branch freezes them to at its final release. When it rewrites a migration's `# Part of:` marker, it carries the `allow:migration-edit` label
- No PR is opened when `main` is already at that version or past it
- For a year rollover or a sprint skip, set the `NEXT_DEV_VERSION` repository variable (for example `27.1.0`) before the rc1 merges, and clear it afterwards

Error handling:

- When quality checks fail, report the errors and stop
- When towncrier fails, check the towncrier config in `pyproject.toml` and the `changes/` directory
- When no changelog block was produced, check whether `changes/` held any fragment. `run-towncrier.py` skips towncrier when there is none, by design
- When config generation fails, check component CLI availability
- On any failure, suggest that the user fix the issue and run the script manually again

### Phase 3: Changelog editing

#### Pre-release

- towncrier generates a flat bullet list under `## {version} (date)`
- No editing is needed; the flat list is the final format for pre-releases
- Skip directly to Phase 4

#### Final release

When releasing a final version such as `26.2.0`, consolidate all previous RC changelog sections, such as `26.2.0rc1` and `26.2.0rc2`, into the final version section.

**Step 1: Collect the RC entries**

- Find all RC sections for the same major, minor and patch in `CHANGELOG/{major}.{minor}.md`, with the pattern `## {major}.{minor}.{patch}rc\d+ \(.*\)`
- Extract all bullet items from each RC section, grouped by category (`### Features`, `### Improvements`, `### Fixes` and so on)

**Step 2: Merge with the new entries**

- towncrier has already generated the new final version section with any remaining `changes/` fragments
- Combine the new entries and all RC entries, deduplicated by PR or issue number
- Group by category: Features, Improvements, Fixes and so on

**Step 3: Remove the RC sections**

- Delete the RC section blocks from `CHANGELOG/{major}.{minor}.md`
- Only the final version section remains for this patch level. Sections for earlier patch releases of the same version branch stay untouched below it; for example `## 26.9.0` when releasing `26.9.1`

**Step 4: Subsection grouping**

- For each category (Features, Improvements, Fixes), group related items into `#### Subsection Title` blocks
- Each subsection gets a 1 to 2 sentence description of the group
- Follow the pattern of previous final releases, for example 26.1.0:

```markdown
### Features

#### Fair Share Scheduler
Implemented a Fair Share scheduling system for equitable resource distribution.

* Add Fair Share row models with tests and migration ([#8008](https://...))
* Implement Fair Share repository layers ([#8030](https://...))

#### Other Features
* Standalone items that don't form a natural group ([#XXXX](https://...))

### Improvements

#### Storage Proxy Improvements
Introduced StorageTarget abstraction for flexible storage configuration.

* Introduce StorageTarget abstraction ([#7938](https://...))

#### Other Improvements
* Standalone improvement items ([#XXXX](https://...))
```

Grouping criteria, in priority order:

1. **Feature initiative** - PRs that serve the same goal or project, even when they span multiple layers (model, repository, service, API, CLI). A single initiative is a single group.
   - For example, "Fair Share Scheduler" includes row models, repository, service, API, CLI, observer and sequencer
   - For example, "Sokovan Scheduler Redesign" includes handler unification, status transitions and coordinator redesign
   - For example, "Email Notification System" includes SMTP channel implementation and endpoint lifecycle notifications

2. **System or subsystem** - PRs that improve a specific system across multiple areas, under the system name.
   - For example, "RBAC System Improvements" includes Creator, Purger and Granter, entity_fields, and data migration
   - For example, "RBAC System Data Migration" includes batch entity migration to the RBAC DB

3. **Domain entity** - PRs that target the Action, repository and service work of the same entity, under the entity name.
   - For example, "Scaling Group Management" includes Create, Modify, Associate and Disassociate actions
   - For example, "Model Deployment Data Model Extension" includes revision, autoscaling, and the policy row, repository and API work

4. **Technical pattern** - PRs that apply the same technical pattern across multiple entities, under the pattern name.
   - For example, "Repository Pattern Standardization" includes batch Admin*Repository consolidation
   - For example, "GraphQL DataLoader Extension" includes DataLoader implementation for multiple entities
   - For example, "Code Quality and Consistency" includes batch linter rule enablement and refactoring

5. **Infrastructure** - PRs that address infrastructure-level changes, under the infrastructure area name.
   - For example, "Agent RPC Connection Pooling" includes pool implementation and migration
   - For example, "CSV Export Infrastructure" includes foundation implementation and per-domain exports

Grouping rules:

- When a PR could belong to multiple groups, place it in the most specific initiative group
- A group requires 2 or more PRs, except for significant standalone features, which may form a single-PR group
- Items that fit no group go under `#### Other {Category}`, for example `#### Other Features`
- Subsection descriptions use the past tense and summarize the purpose and result of the group in 1 or 2 sentences
- Do not group by component (manager, agent, storage-proxy). Group by functional area

**Step 5: User review**

- Present the reorganized changelog to the user
- Wait for approval or requested changes
- Iterate until the user is satisfied

**Step 6: Amend the release commit**

```bash
git add CHANGELOG/{major}.{minor}.md
git commit --amend --no-edit
```

### Phase 4: Summary

Report the final status:

```
Release Prepared

  Version:     {target_version}
  Branch:      release/{target_version}
  Type:        {Final Release | Release Candidate | Pre-release}
  WebUI:       {webui_version or "not updated"}
  Changelog:   {N} entries across {M} categories
  RC Merged:   {list of merged RC versions, or "N/A"}
```

## Error handling

### Release script failure

```
Release script failed at: {step}

Error:
{error_output}

Options:
1. Fix the issue and re-run: scripts/release.sh {target_version} [webui_version]
2. Run remaining steps manually
3. Abort: git checkout main && git branch -D release/{target_version}
```

### No changes/ fragments

```
No changelog fragments found in changes/ directory.

This means no new changes since the last release.
If this is a final release consolidating RCs, this is expected - proceed to Phase 3.
```

### Changelog merge conflict

```
Found duplicate entries during RC consolidation (same PR number in multiple RCs).

Deduplicated entries:
{list}

Using the latest version of each entry.
```

## Examples

RC release:

```
User: /release 26.2.0rc2
Agent: [Checks VERSION, runs release.sh, towncrier generates flat list, reports summary]
```

Final release with RC consolidation:

```
User: /release 26.2.0
Agent: [Checks VERSION, finds rc1/rc2 sections in CHANGELOG/26.2.md, runs release.sh,
        consolidates RC entries + new entries, groups into subsections,
        presents for review, amends commit, reports summary]
```

Release with WebUI:

```
User: /release 26.2.0 25.3.2
Agent: [Runs release.sh with WebUI version, full workflow]
```

## Related documents

- `scripts/release.sh` - The release automation script
- `scripts/run-towncrier.py` - Runs towncrier against `CHANGELOG/{major}.{minor}.md`
- `scripts/changelog_files.py` - Version to changelog path mapping
- `pyproject.toml` - towncrier configuration (fragment types, template)
- `changes/` - Changelog fragment directory
- `CHANGELOG/` - Per-version-branch changelogs; the root `CHANGELOG.md` archives the pre-split releases
- `/submit` - For regular PR submissions, not releases
