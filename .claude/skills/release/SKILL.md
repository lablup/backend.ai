---
name: release
description: Guide the Backend.AI release process - run release.sh, generate changelog via towncrier, consolidate RC entries for final releases with subsection grouping.
---

# Release Workflow

Guides the Backend.AI release process: version bump, changelog generation, and RC consolidation for final releases.

## Parameters

- **target_version** (required): Release version (e.g., `26.2.0`, `26.2.0rc2`)
- **webui_version** (optional): WebUI version to bundle

## Workflow

### Phase 1: Pre-flight

1. **Parse parameters**
   - Extract `target_version` from user input (required)
   - Extract `webui_version` if provided

2. **Check current state**
   - Read `VERSION` file for current version
   - Verify clean working tree (`git status`)
   - Confirm on expected base branch (usually `main`)

3. **Determine release type**
   - **Pre-release**: version contains `rc`, `alpha`, `beta`, or `dev` (e.g., `26.2.0rc1`)
   - **Final release**: clean semver (e.g., `26.2.0`)

4. **For final releases, check for prior RC sections**
   - Scan `CHANGELOG.md` for sections matching `## {major}.{minor}.{patch}rc\d+`
   - List found RC sections to user
   - These will be consolidated in Phase 3

5. **Confirm with user before proceeding**
   - Show: target version, release type, WebUI version (if any), RC sections to consolidate (if any)
   - Wait for user approval

### Phase 2: Release Script Execution

Run `scripts/release.sh` which performs these steps:

```bash
scripts/release.sh {target_version} [webui_version]
```

**What the script does:**
1. Creates branch `release/{target_version}`
2. Downloads WebUI release (if `webui_version` provided)
3. Runs quality checks: `pants tailor --check`, `pants check ::`
4. Updates `VERSION` file
5. Runs towncrier to generate changelog entries
6. Generates sample config files
7. Generates API docs (OpenAPI, GraphQL schema)
8. Commits everything as `release: {target_version}`

**Error handling:**
- If quality checks fail, report errors and stop
- If towncrier fails, check `pyproject.toml` towncrier config and `changes/` directory
- If config generation fails, check component CLI availability
- On any failure, suggest user fix the issue and re-run the script manually

### Phase 3: Changelog Editing

#### For Pre-release (RC/alpha/beta/dev)

- towncrier generates a flat bullet list under `## {version} (date)`
- **No editing needed** - the flat list is the final format for pre-releases
- Skip directly to Phase 4

#### For Final Release (RC Consolidation Required)

This is the core value of the skill. When releasing a final version (e.g., `26.2.0`), all previous RC changelog sections (e.g., `26.2.0rc1`, `26.2.0rc2`) must be consolidated into the final version section.

**Step 1: Collect RC entries**
- Find all RC sections for the same major.minor.patch in `CHANGELOG.md`
  - Pattern: `## {major}.{minor}.{patch}rc\d+ \(.*\)`
- Extract all bullet items from each RC section, grouped by category (`### Features`, `### Improvements`, `### Fixes`, etc.)

**Step 2: Merge with new entries**
- towncrier has already generated the new final version section with any remaining `changes/` fragments
- Combine: new entries + all RC entries, deduplicated by PR/issue number
- Group by category: Features, Improvements, Fixes, etc.

**Step 3: Remove RC sections**
- Delete the RC section blocks from `CHANGELOG.md`
- Only the final version section should remain

**Step 4: Subsection grouping**
- For each category (Features, Improvements, Fixes), group related items into `#### Subsection Title` blocks
- Each subsection gets a 1-2 sentence description explaining the group
- Follow the established pattern from previous final releases (e.g., 26.1.0):

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

**Grouping criteria (priority order):**

1. **Feature Initiative**: Group PRs that serve the same goal or project, even if they span multiple layers (model, repository, service, API, CLI). A single initiative = a single group.
   - e.g., "Fair Share Scheduler" — includes row models, repository, service, API, CLI, observer, sequencer
   - e.g., "Sokovan Scheduler Redesign" — includes handler unification, status transitions, coordinator redesign
   - e.g., "Email Notification System" — includes SMTP channel implementation + endpoint lifecycle notifications

2. **System/Subsystem**: Group PRs that improve a specific system across multiple areas under the system name.
   - e.g., "RBAC System Improvements" — Creator/Purger/Granter, entity_fields, data migration
   - e.g., "RBAC System Data Migration" — batch entity migration to RBAC DB

3. **Domain Entity**: Group PRs that target the same entity's Action/Repository/Service work under the entity name.
   - e.g., "Scaling Group Management" — Create/Modify/Associate/Disassociate actions
   - e.g., "Model Deployment Data Model Extension" — revision, autoscaling, policy row/repository/API

4. **Technical Pattern**: Group PRs that apply the same technical pattern across multiple entities under the pattern name.
   - e.g., "Repository Pattern Standardization" — batch Admin*Repository consolidation
   - e.g., "GraphQL DataLoader Extension" — DataLoader implementation for multiple entities
   - e.g., "Code Quality and Consistency" — batch linter rule enablement, refactoring

5. **Infrastructure**: Group PRs that address infrastructure-level changes under the infrastructure area name.
   - e.g., "Agent RPC Connection Pooling" — pool implementation + migration
   - e.g., "CSV Export Infrastructure" — foundation implementation + per-domain exports

**Grouping rules:**
- If a PR could belong to multiple groups, place it in the most specific initiative group
- A group requires 2+ PRs, except for significant standalone features which may form a single-PR group
- Items that don't fit any group go under `#### Other {Category}` (e.g., `#### Other Features`)
- Subsection descriptions should be past tense, summarizing the group's purpose/outcome in 1-2 sentences
- Never group by component (manager, agent, storage-proxy) — always group by functional area

**Step 5: User review**
- Present the reorganized changelog to the user
- Wait for approval or requested changes
- Iterate until user is satisfied

**Step 6: Amend the release commit**
```bash
git add CHANGELOG.md
git commit --amend --no-edit
```

### Phase 4: Summary

Report final status:

```
Release Prepared

  Version:     {target_version}
  Branch:      release/{target_version}
  Type:        {Final Release | Release Candidate | Pre-release}
  WebUI:       {webui_version or "not updated"}
  Changelog:   {N} entries across {M} categories
  RC Merged:   {list of merged RC versions, or "N/A"}
```

## Error Handling

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
No news fragments found in changes/ directory.

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

### RC release
```
User: /release 26.2.0rc2
Agent: [Checks VERSION, runs release.sh, towncrier generates flat list, reports summary]
```

### Final release with RC consolidation
```
User: /release 26.2.0
Agent: [Checks VERSION, finds rc1/rc2 sections in CHANGELOG, runs release.sh,
        consolidates RC entries + new entries, groups into subsections,
        presents for review, amends commit, reports summary]
```

### Release with WebUI
```
User: /release 26.2.0 25.3.2
Agent: [Runs release.sh with WebUI version, full workflow]
```

## Related

- `scripts/release.sh` - The release automation script
- `pyproject.toml` - towncrier configuration (fragment types, template)
- `changes/` - News fragment directory
- `/submit` - For regular PR submissions (not releases)
