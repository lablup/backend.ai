package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func writeFile(t *testing.T, root, rel, content string) {
	t.Helper()
	p := filepath.Join(root, rel)
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

func readFile(t *testing.T, root, rel string) string {
	t.Helper()
	b, err := os.ReadFile(filepath.Join(root, rel))
	if err != nil {
		t.Fatal(err)
	}
	return string(b)
}

func TestParseName(t *testing.T) {
	tests := []struct {
		name     string
		wantKey  string
		wantKind string
		wantErr  string
	}{
		{"BAI-1160.feature.md", "BAI-1160", "feature", ""},
		{"BA-7.fix.md", "BA-7", "fix", ""},
		{"BAI-1160.md", "", "", "name must be"},
		{"BAI-1160.feature.txt", "", "", "name must be"},
		{"1160.feature.md", "", "", "not an issue key"},
		{"bai-1160.feature.md", "", "", "not an issue key"},
		{"BAI-1160.chore.md", "", "", "unknown kind"},
		{"BAI-1160.test.md", "", "", "unknown kind"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			key, kind, err := parseName(tt.name)
			if tt.wantErr != "" {
				if err == nil || !strings.Contains(err.Error(), tt.wantErr) {
					t.Fatalf("err = %v, want containing %q", err, tt.wantErr)
				}
				return
			}
			if err != nil || key != tt.wantKey || kind != tt.wantKind {
				t.Fatalf("got (%q, %q, %v)", key, kind, err)
			}
		})
	}
}

func TestCheck(t *testing.T) {
	tests := []struct {
		name    string
		files   map[string]string
		wantErr string
	}{
		{"empty directory", map[string]string{".gitkeep": ""}, ""},
		{"valid", map[string]string{"BAI-1.feature.md": "Added x.\n", "BAI-1.fix.md": "Fixed y."}, ""},
		{"bad kind", map[string]string{"BAI-1.chore.md": "x"}, "unknown kind"},
		{"bad key", map[string]string{"foo.fix.md": "x"}, "not an issue key"},
		{"empty content", map[string]string{"BAI-1.fix.md": " \n\n"}, "content is empty"},
		{"stray file", map[string]string{"notes.txt": "x"}, "name must be"},
		{"reports all", map[string]string{"a.fix.md": "x", "BAI-1.fix.md": ""}, "content is empty"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := t.TempDir()
			writeFile(t, root, unreleasedDir+"/.gitkeep", "")
			for n, c := range tt.files {
				writeFile(t, root, unreleasedDir+"/"+n, c)
			}
			err := check(root)
			if tt.wantErr == "" {
				if err != nil {
					t.Fatal(err)
				}
				return
			}
			if err == nil || !strings.Contains(err.Error(), tt.wantErr) {
				t.Fatalf("err = %v, want containing %q", err, tt.wantErr)
			}
		})
	}
}

const titleChangelog = "Changes\n=======\n\nOld notes.\n"

func TestBatch(t *testing.T) {
	root := t.TempDir()
	writeFile(t, root, changelogFile, titleChangelog)
	writeFile(t, root, unreleasedDir+"/.gitkeep", "")
	writeFile(t, root, unreleasedDir+"/BAI-10.fix.md", "Fixed a crash.\n")
	writeFile(t, root, unreleasedDir+"/BAI-2.fix.md", "Fixed a leak.\nIt happened on exit.\n")
	writeFile(t, root, unreleasedDir+"/BAI-3.feature.md", "Added the thing.\n")
	writeFile(t, root, unreleasedDir+"/BAI-3.breaking.md", "Renamed the flag.\n")
	writeFile(t, root, unreleasedDir+"/BAI-4.misc.md", "Tidied up.\n")

	if err := batch(root, "1.0.0", time.Date(2026, 12, 1, 0, 0, 0, 0, time.UTC)); err != nil {
		t.Fatal(err)
	}

	wantSection := `## 1.0.0 (2026-12-01)

### Breaking Changes

- Renamed the flag. (BAI-3)

### Features

- Added the thing. (BAI-3)

### Fixes

- Fixed a leak.
  It happened on exit. (BAI-2)
- Fixed a crash. (BAI-10)

### Miscellaneous

- Tidied up. (BAI-4)
`
	if got := readFile(t, root, "changes/1.0.0.md"); got != wantSection {
		t.Errorf("changes/1.0.0.md:\n%s\nwant:\n%s", got, wantSection)
	}
	wantChangelog := "Changes\n=======\n\n" + wantSection + "\nOld notes.\n"
	if got := readFile(t, root, changelogFile); got != wantChangelog {
		t.Errorf("CHANGELOG.md:\n%s\nwant:\n%s", got, wantChangelog)
	}
	entries, _ := os.ReadDir(filepath.Join(root, unreleasedDir))
	if len(entries) != 1 || entries[0].Name() != ".gitkeep" {
		t.Errorf("fragments remain: %v", entries)
	}
}

func TestBatchRejects(t *testing.T) {
	tests := []struct {
		name    string
		version string
		setup   func(t *testing.T, root string)
		wantErr string
	}{
		{"existing version", "1.0.0", func(t *testing.T, root string) {
			writeFile(t, root, "changes/1.0.0.md", "x")
		}, "already exists"},
		{"invalid fragment", "1.0.0", func(t *testing.T, root string) {
			writeFile(t, root, unreleasedDir+"/BAI-1.chore.md", "x")
		}, "unknown kind"},
		{"no fragment", "1.0.0", func(t *testing.T, root string) {}, "no fragment"},
		{"bad version", "../x", func(t *testing.T, root string) {
			writeFile(t, root, unreleasedDir+"/BAI-1.fix.md", "x")
		}, "invalid version"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := t.TempDir()
			writeFile(t, root, changelogFile, titleChangelog)
			writeFile(t, root, unreleasedDir+"/.gitkeep", "")
			tt.setup(t, root)
			err := batch(root, tt.version, time.Now())
			if err == nil || !strings.Contains(err.Error(), tt.wantErr) {
				t.Fatalf("err = %v, want containing %q", err, tt.wantErr)
			}
			if got := readFile(t, root, changelogFile); got != titleChangelog {
				t.Errorf("CHANGELOG.md changed on failure: %q", got)
			}
		})
	}
}

func TestInsertAfterTitle(t *testing.T) {
	tests := []struct{ name, in, want string }{
		{"setext", "T\n=\n\nbody\n", "T\n=\n\nS\n\nbody\n"},
		{"atx", "# T\n\nbody\n", "# T\n\nS\n\nbody\n"},
		{"no title", "body\n", "S\n\nbody\n"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := insertAfterTitle(tt.in, "S\n"); got != tt.want {
				t.Errorf("got %q, want %q", got, tt.want)
			}
		})
	}
}

func git(t *testing.T, root string, args ...string) {
	t.Helper()
	cmd := exec.Command("git", append([]string{"-C", root, "-c", "user.name=t", "-c", "user.email=t@t"}, args...)...)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("git %v: %v\n%s", args, err, out)
	}
}

func TestCheckRequire(t *testing.T) {
	root := t.TempDir()
	git(t, root, "init", "-q", "-b", "main")
	writeFile(t, root, unreleasedDir+"/.gitkeep", "")
	git(t, root, "add", ".")
	git(t, root, "commit", "-q", "-m", "base")
	git(t, root, "checkout", "-q", "-b", "topic")

	if err := checkRequire(root, "main"); err == nil || !strings.Contains(err.Error(), "no fragment added") {
		t.Fatalf("without a fragment: err = %v", err)
	}

	writeFile(t, root, unreleasedDir+"/BAI-1.fix.md", "Fixed.\n")
	git(t, root, "add", ".")
	git(t, root, "commit", "-q", "-m", "fragment")
	if err := checkRequire(root, "main"); err != nil {
		t.Fatalf("with a fragment: %v", err)
	}

	if err := checkRequire(root, "no-such-ref"); err == nil {
		t.Fatal("unknown base: want an error")
	}
}

func TestRun(t *testing.T) {
	root := t.TempDir()
	writeFile(t, root, unreleasedDir+"/BAI-1.fix.md", "")
	if err := run([]string{"check", "--root", root}); err == nil {
		t.Fatal("check: want an error for an empty fragment")
	}
	if err := run([]string{"check", "--root", root, "--require"}); err == nil {
		t.Fatal("--require without --base: want an error")
	}
	if err := run([]string{"batch"}); err == nil {
		t.Fatal("batch without a version: want an error")
	}
	if err := run([]string{"batch", "1.0.0", "--root", root, "--date", "nope"}); err == nil {
		t.Fatal("bad --date: want an error")
	}
	if err := run([]string{"nope"}); err == nil {
		t.Fatal("unknown command: want an error")
	}
}
