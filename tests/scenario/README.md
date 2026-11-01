# Scenario tests

Runs one adapter against a real database and a real Valkey to verify what a single request returns.
Rules are in `AGENTS.md`, background in `KNOWLEDGE.md`.

## How a row runs

```python
class ADomainAndSomeone(Given[SeedingSession, ADomainAndACaller]):
    async def lay(self, seeding: SeedingSession) -> ADomainAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="host", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ADomainAndACaller(seeding.made(domain), seeding.made(caller))


class ReadingByName(When[ADomainAndACaller, DomainAdapter, DomainNode]):
    def operation(self) -> str:
        return "get"

    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> DomainNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.domain.name)


class TheDomainNode(Then[ADomainAndACaller, DomainNode]):
    def look(self, laid, answered) -> list[Verdict]:
        node = answered.response
        return [
            Same("name", node.basic_info.name, laid.domain.name),
            Skipped("id", "the database generates it"),
            Held("created_at", node.lifecycle.created_at, WrittenByThisRun(self.started)),
        ]
```

1. Each test copies the template database. The template holds the schema and no rows.
2. `given` writes its rows in one transaction and returns the written values. That write closes before `when`
   starts, because the adapter reads over its own connection.
3. `when` calls with only that value and the adapter.
4. `then` takes what was seeded and the answer or exception, and returns what it saw for each place.

## Where things are

| Path | Contents |
|---|---|
| `bai_scenario/manager/<component>/` | Scenario tables and the conftest that assembles the adapter |
| `bai_scenario/seeds/` | Seed classes that each represent one row, and `TestSeeder` |
| `bai_scenario/components/` | Vocabulary the tables use: scenario types, common groups |
| `bai_scenario/runner/` | Scenario execution and checks, seeding with fixtures |
| `bai_scenario/setup/` | Tests that check what the shared setup creates |
| `bai_scenario/fakes/` | Stand-ins for external services |
| `bai_scenario/{db,schema,config,valkey,monitors}.py` | What one run needs |

Add a package only for what will grow. Keep what fits in one file flat, like the modules above.

## How to run

```bash
pants test tests/scenario::
```

## Report

Generates what each domain guarantees from the run results, for release PRs.

```bash
BACKEND_SCENARIO_LOG=dist/scenarios.jsonl pants test tests/scenario::
python scripts/scenario-report.py dist/scenarios.jsonl -o dist/scenarios.md
```

`--split` writes a `report.md` per entity package. `--verify` reports only whether that file disagrees with the
run and does not overwrite it.

```bash
python scripts/scenario-report.py dist/scenarios.jsonl --split src/ai/backend/manager/api/adapters
python scripts/scenario-report.py dist/scenarios.jsonl --verify src/ai/backend/manager/api/adapters
```

There are three formats.

| `--format` | Contents |
|---|---|
| `markdown` (default) | Document for people. Attach it to release PRs |
| `json` | The same content for tools |
| `summary` | Counts only. One line of build log |

A row looks like this. Only the first sentence is written by a person, and the three parts below it come from the
run. Rows seeded in a group are indented under that group. Report text is still Korean; this example shows it in
English.

```markdown
#### a-user-granted-folder-create-makes-one-of-their-own — pass

When a user granted vfolder create permission in their own scope creates a vfolder, the user owns it

Given

- Domain home-1, vfolders of this domain can be placed on local:volume1
- Prepare a user who can create vfolders
  - Prepare one user in the domain
    - Project policy default, the personal project created with the user finds it by this name
    - User policy user-policy-1, up to 10 vfolders per user
    - Keypair policy keypair-policy-1, up to 5 concurrent sessions, vfolders can be placed on local:volume1
    - Regular user user-1, in domain home-1, with their own key and personal project  ← actor
  - Role folder-owner-1, valid only within the scope of regular user user-1
  - Role folder-owner-1: CREATE allowed on all vfolders
  - Regular user user-1: holds role folder-owner-1

When

- create call by regular user user-1
  - CreateVFolderInput(name='mine', host='local:volume1')

Then

- vfolder.access_control.ownership_type = 'user'
```

The report also lists the calls an adapter provides that no scenario calls.

The `describe` sentences are Korean drafts. They move to English after they pass review.
