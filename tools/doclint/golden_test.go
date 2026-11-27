package main

import (
	"bytes"
	"flag"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

var updateGolden = flag.Bool("update", false, "rewrite the expected outputs of testdata/golden")

const (
	goldenDir     = "testdata/golden"
	fixtureSuffix = ".in"
)

// copyFixture copies a directory of testdata into root. A file named `<name>.in` is written as
// `<name>`: the documents of the fixtures must not be documents of this repository.
func copyFixture(t *testing.T, from, root string) {
	t.Helper()
	err := filepath.WalkDir(from, func(path string, entry fs.DirEntry, err error) error {
		if err != nil || entry.IsDir() {
			return err
		}
		rel, err := filepath.Rel(from, path)
		if err != nil {
			return err
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		writeFile(t, root, strings.TrimSuffix(filepath.ToSlash(rel), fixtureSuffix), string(data))
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}

// goldenOutput runs doclint and formats the output with the exit status.
func goldenOutput(t *testing.T, root string, args ...string) string {
	t.Helper()
	out, failed := runCheck(t, root, args...)
	status := 0
	if failed {
		status = 1
	}
	return fmt.Sprintf("%sexit status: %d\n", out, status)
}

func compareGolden(t *testing.T, name, got string) {
	t.Helper()
	path := filepath.Join(goldenDir, name)
	if *updateGolden {
		if err := os.WriteFile(path, []byte(got), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	want, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if string(want) != got {
		t.Fatalf("%s differs, run with -update to see the change in git diff\n--- want\n%s--- got\n%s", name, want, got)
	}
}

// TestGoldenOutput pins the output of the checks over a fixed repository: the spec, the
// registry and the documents are copies, so a change to this repository's glossary does not
// change the output.
func TestGoldenOutput(t *testing.T) {
	root := newGoldenRepo(t)
	compareGolden(t, "check-all.txt", goldenOutput(t, root))
	for _, check := range []string{"frontmatter", "bilingual", "words", "bep-length", "agents-lines"} {
		compareGolden(t, "check-"+check+".txt", goldenOutput(t, root, "--only", check))
	}
}

func TestGoldenOutputSinceBase(t *testing.T) {
	root := newGoldenRepo(t)
	var base bytes.Buffer
	cmd := exec.Command("git", "-C", root, "rev-parse", "HEAD")
	cmd.Stdout = &base
	if err := cmd.Run(); err != nil {
		t.Fatal(err)
	}
	copyFixture(t, filepath.Join(goldenDir, "overlay"), root)
	gitIn(t, root, "add", ".")
	gitIn(t, root, "commit", "-q", "-m", "change")
	ref := strings.TrimSpace(base.String())
	compareGolden(t, "check-base.txt", goldenOutput(t, root, "--base", ref))
	compareGolden(t, "check-base-one-side.txt", goldenOutput(t, root, "--base", ref, "--allow-one-side"))
}

func newGoldenRepo(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	gitIn(t, root, "init", "-q")
	copyFixture(t, filepath.Join(goldenDir, "input"), root)
	gitIn(t, root, "add", ".")
	gitIn(t, root, "commit", "-q", "-m", "base")
	return root
}
