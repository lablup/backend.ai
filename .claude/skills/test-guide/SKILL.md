---
name: test-guide
description: Guide for writing Go tests. Agree the scenarios first, then follow the criteria for choosing between a unit test, -short, dbtest.New and an integration test, how to write them and the commands to run them. Use when writing or running tests.
tags:
  - testing
  - test-scenarios
---

> Steps 3 and 4 of the workflow (the "Workflow" table in AGENTS.md).

# Test guide

Agree the scenarios first, then report the verification status of each scenario as you implement. The center is the scenario list and its verification status. Writing the test first (TDD) is optional.

## 1. Propose the scenarios first

Before writing code or tests, draft the scenarios and get the user's input.

1. Draft the success, error and boundary scenarios from the requirement.
2. Show them to the user and take the missing cases and the expected results.
3. Fix the merged list. This list is the criterion for "done".

```markdown
## Test target: <feature>

### Success
1. <primary case> → <expected result>

### Error
1. <invalid input> → <returned error>
2. <missing target> → <returned error>

### Boundary
1. <empty value, zero, maximum, last page> → <expected result>
```

The axes that derive scenarios:

| Axis | Question | Example |
|---|---|---|
| Primary path | What is the primary success? | Valid input → created |
| Variation | Is there another valid input or state? | Optional field omitted → default applied |
| Missing | Is a referenced target missing? | Unknown id → `ErrNotFound` |
| Validation | Is there an invalid input? | Negative quantity → validation error |
| Conflict, state | Is it a duplicate, or does the current state not fit? | Create with an existing name → conflict error |
| Boundary | Is there an empty value, zero or a maximum? | Offset past the total count → empty list |
| Idempotency, concurrency | Is the call repeated or parallel? | Run again → no duplicate effect |

Take the error scenarios from the errors the code returns (the values told apart with `errors.Is` and `errors.As`). Give every scenario a concrete expected result or error. "Should fail" is not a criterion.

## 2. Report the verification status per scenario

| Scenario | Test | Status |
|---|---|---|
| Returns the record when present | `TestGet_Found` | pass |
| Returns `ErrNotFound` when missing | `TestGet_NotFound` | pass |
| Offset past the end | none | not covered yet |

- Do not hide a missing scenario (`not covered yet`).
- When the user adds a scenario during the work, add it to the list and the table.
- A scenario is done only when its test exists and passes.

## 3. Choose the kind of test

| Kind | Criterion | Location | `go test -short` |
|---|---|---|---|
| Unit test | No external dependency. Pure logic, conversion, validation | `_test.go` in the target package | Runs |
| Test skipped by `-short` | Waits for an external service or real time | `_test.go` in the target package | Skipped |
| `dbtest.New` test | Checks the behavior of a real PostgreSQL: queries, constraints, transactions | `_test.go` in the target package | Skipped |
| Integration test | Sends requests to a running server | `tests/integration/` | Not built |

- A unit test does not mock the database. Check the database behavior with `dbtest.New`.
- Do not wait with `time.Sleep` under `-short`.
- Skip a test that waits for an external service or time under `-short`, as `dbtest.New` does.

## 4. Write

One scenario is one test: prepare, run, check. Write several inputs table-driven.

### Unit test

```go
func TestNormalizeName(t *testing.T) {
	const in, want = "  Default ", "default"
	if got := example.NormalizeName(in); got != want {
		t.Errorf("NormalizeName(%q) = %q, want %q", in, got, want)
	}
}
```

### Test skipped by `-short`

```go
func TestSlowThing(t *testing.T) {
	if testing.Short() {
		t.Skip("skipped by -short")
	}
	// ...
}
```

### `dbtest.New`

`dbtest.New(t)` returns the `*pgxpool.Pool` of a new PostgreSQL database with the migrations applied.

- It skips the test under `-short` or without `TEST_DATABASE_URL`. It fails when `CI` is set and `TEST_DATABASE_URL` is missing.
- When the test ends, it closes the pool and deletes the database. It can be called from a `t.Parallel` test.

```go
func TestCountDomains(t *testing.T) {
	pool := dbtest.New(t)

	got, err := example.CountDomains(t.Context(), pool)
	if err != nil {
		t.Fatal(err)
	}
	if want := 0; got != want {
		t.Errorf("CountDomains() = %d, want %d", got, want)
	}
}
```

### Integration test

- Put it in `tests/integration/` and add `//go:build integration` at the top of every Go file. `ci-gate` rejects a file without the tag.
- The test file is `package integration` and gets the server address with `Endpoint(t)`. It skips the test without `INTEGRATION_ENDPOINT`.
- CI does not run it.

```go
//go:build integration

package integration

func TestSomething(t *testing.T) {
	endpoint := Endpoint(t)
	// send requests to endpoint
}
```

## 5. Run

Run only the tests you changed or added.

| Do | Command |
|---|---|
| All unit tests | `go test -short ./...` |
| One package, one test | `go test -short -run <test name> ./<package>/` |
| With the database | `TEST_DATABASE_URL=<postgres URL> go test -race ./<package>/` |
| Integration | `INTEGRATION_ENDPOINT=<server address> go test -tags integration -count=1 -v ./tests/integration/...` |

- Start the local database with `/halfstack` and use the `TEST_DATABASE_URL` written there.
- The PR checks of CI are fmt, lint and build, and `go test -short ./...` only reports. The full test runs on a push to `v2` and on a release.
- Fix a warning and an error; do not suppress or skip it. Do not use `//nolint`.

## Related documents

- `/halfstack`: the PostgreSQL for local database tests
- `/submit`: the commit and the PR after the tests
- `internal/dbtest/dbtest.go`: the behavior of `dbtest.New`

Next: `/writing`
