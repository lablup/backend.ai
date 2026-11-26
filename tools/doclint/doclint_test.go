package main

import (
	"bytes"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

const glossaryEN = `# Glossary

| Do not write | Write |
|---|---|
| refuse | reject |
| leave out (a flag) | omit |
| bring up, brought up | start |

| Name | Value | Note |
|---|---|---|
| after | before | x |
`

const glossaryKO = `# 용어집

| 사용하지 않는 표현 | 대신 |
|---|---|
| 지우다 | 삭제하다 |
| 막다 / 풀다 (조건) | 차단하다 |
`

const termsEN = `# Terms

| English | Meaning | Do not write | Note |
|---|---|---|---|
| agent heartbeat | A signal. | heartbeat, bgtask | |
| Agent | The agent. | agent | |
`

const termsKO = `# 용어

| 한글 | English | 뜻 | 사용하지 않는 어휘 | 메모 |
|---|---|---|---|---|
| 컬럼 | column | 열 | 컬럼, 칼럼 | |
`

func writeFile(t *testing.T, root, rel, content string) {
	t.Helper()
	path := filepath.Join(root, rel)
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

func newRepo(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	if out, err := exec.Command("git", "-C", root, "init", "-q").CombinedOutput(); err != nil {
		t.Fatalf("git init: %v: %s", err, out)
	}
	writeFile(t, root, "GLOSSARY.md", glossaryEN)
	writeFile(t, root, "GLOSSARY.ko.md", glossaryKO)
	writeFile(t, root, "glossary/process.md", termsEN)
	writeFile(t, root, "glossary/process.ko.md", termsKO)
	return root
}

func TestMatchWords(t *testing.T) {
	root := newRepo(t)
	english, korean, err := loadWords(root)
	if err != nil {
		t.Fatal(err)
	}
	tests := []struct {
		name     string
		words    []word
		line     string
		want     string
		advisory bool
	}{
		{"expression", english, "We refuse the request.", "refuse", false},
		{"inflection", english, "It refused it.", "refuse", false},
		{"inside a word", english, "refusenik", "", false},
		{"hyphen joined", english, "non-refuse", "", false},
		{"qualifier is advisory", english, "Please leave out the flag.", "leave out", true},
		{"alternative", english, "Brought up late.", "", false},
		{"alternative lowercase", english, "it was brought up", "brought up", false},
		{"term variant is advisory", english, "the heartbeat arrives", "heartbeat", true},
		{"same word as term skipped", english, "an agent", "", false},
		{"second table is not read", english, "after that", "", false},
		{"korean verb form", korean, "파일을 지운다", "지우다", false},
		{"korean verb past", korean, "파일을 지웠다", "지우다", false},
		{"korean other word", korean, "파일을 삭제한다", "", false},
		{"korean single token alternative", korean, "문을 푼다", "풀다", true},
		{"korean qualifier advisory", korean, "길을 막는다", "막다", true},
		{"korean noun with particle", korean, "칼럼을 둔다", "칼럼", true},
		{"korean term equal to its own name", korean, "컬럼을 둔다", "", false},
		{"korean noun inside word", korean, "스칼럼", "", false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var found *word
			for i := range tt.words {
				if tt.words[i].pattern.MatchString(tt.line) {
					found = &tt.words[i]
					break
				}
			}
			if tt.want == "" {
				if found != nil {
					t.Fatalf("matched %q in %q", found.text, tt.line)
				}
				return
			}
			if found == nil {
				t.Fatalf("no match in %q", tt.line)
			}
			if found.text != tt.want || found.advisory != tt.advisory {
				t.Fatalf("got %q advisory=%v, want %q advisory=%v", found.text, found.advisory, tt.want, tt.advisory)
			}
		})
	}
}

func TestProseLines(t *testing.T) {
	text := "---\nname: x\n---\nkeep `code span` here\n```\nfenced\n```\nafter\n"
	got := proseLines(text)
	if len(got) != 2 || got[4] != "keep   here" || got[8] != "after" {
		t.Fatalf("got %v", got)
	}
}

func TestIsSkipped(t *testing.T) {
	for path, want := range map[string]bool{
		"glossary/process.md": true, "GLOSSARY.md": true, "a/report.ko.md": true,
		"CHANGELOG/26.9.md": true, "proposals/BEP-1.md": false, "AGENTS.md": false,
	} {
		if got := isSkipped(path); got != want {
			t.Errorf("isSkipped(%q) = %v, want %v", path, got, want)
		}
	}
}

func runCheck(t *testing.T, root string, args ...string) (string, bool) {
	t.Helper()
	var out bytes.Buffer
	failed, err := run(append([]string{"check", "--root", root}, args...), &out)
	if err != nil {
		t.Fatalf("run: %v", err)
	}
	return out.String(), failed
}

func TestCheckWordsFiles(t *testing.T) {
	root := newRepo(t)
	writeFile(t, root, "bad.md", "# Bad\n\nWe refuse it.\n")
	writeFile(t, root, "review.md", "# Review\n\nThe heartbeat arrives.\n")
	writeFile(t, root, "good.md", "# Good\n\nWe `refuse` it.\n")
	tests := []struct {
		file       string
		wantFailed bool
		wantOut    string
	}{
		{"bad.md", true, "bad.md:3: refuse -> reject: We refuse it.\n"},
		{"review.md", false, "review: review.md:3: heartbeat -> agent heartbeat: The heartbeat arrives.\n"},
		{"good.md", false, ""},
	}
	for _, tt := range tests {
		t.Run(tt.file, func(t *testing.T) {
			out, failed := runCheck(t, root, "--only", "words", tt.file)
			if failed != tt.wantFailed || out != tt.wantOut {
				t.Fatalf("failed=%v out=%q, want failed=%v out=%q", failed, out, tt.wantFailed, tt.wantOut)
			}
		})
	}
}

func TestCheckAgentsLines(t *testing.T) {
	root := newRepo(t)
	writeFile(t, root, "AGENTS.md", strings.Repeat("rule\n", 200))
	writeFile(t, root, "sub/AGENTS.md", strings.Repeat("rule\n", 201))
	out, failed := runCheck(t, root, "--only", "agents-lines")
	if !failed || out != "sub/AGENTS.md:1: 201 lines, limit 200\n" {
		t.Fatalf("failed=%v out=%q", failed, out)
	}
	out, failed = runCheck(t, root, "--only", "agents-lines", "AGENTS.md")
	if failed || out != "" {
		t.Fatalf("failed=%v out=%q", failed, out)
	}
}

func TestCheckBilingualPairs(t *testing.T) {
	tests := []struct {
		name string
		en   string
		ko   string
		want string
	}{
		{"same headings", "# A\n\n## B\n", "# 가\n\n## 나\n", ""},
		{"headings differ", "# A\n\n## B\n", "# 가\n", "doc.ko.md: headings differ from doc.md: [(1, 1)] and [(1, 1), (2, 1)]\n"},
		{"fenced heading ignored", "# A\n", "# 가\n```\n# x\n```\n", ""},
		{"frontmatter ignored", "---\n# a\n---\n# A\n", "# 가\n", ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRepo(t)
			writeFile(t, root, "doc.md", tt.en)
			writeFile(t, root, "doc.ko.md", tt.ko)
			out, failed := runCheck(t, root, "--only", "bilingual")
			if out != tt.want || failed != (tt.want != "") {
				t.Fatalf("failed=%v out=%q, want %q", failed, out, tt.want)
			}
		})
	}
	root := newRepo(t)
	writeFile(t, root, "alone.ko.md", "# 가\n")
	out, failed := runCheck(t, root, "--only", "bilingual")
	if !failed || out != "alone.ko.md: alone.md is missing\n" {
		t.Fatalf("failed=%v out=%q", failed, out)
	}
}

func TestCheckBilingualBase(t *testing.T) {
	root := newRepo(t)
	writeFile(t, root, "doc.md", "# A\n")
	writeFile(t, root, "doc.ko.md", "# 가\n")
	gitRun := func(args ...string) {
		t.Helper()
		full := append([]string{"-C", root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"}, args...)
		if out, err := exec.Command("git", full...).CombinedOutput(); err != nil {
			t.Fatalf("git %v: %v: %s", args, err, out)
		}
	}
	gitRun("add", ".")
	gitRun("commit", "-q", "-m", "base")
	gitRun("tag", "base")
	writeFile(t, root, "doc.md", "# A\n\nNew 한글 line.\n")
	gitRun("commit", "-qam", "change")
	out, failed := runCheck(t, root, "--only", "bilingual", "--base", "base")
	want := "doc.md: Korean added, move it to the .ko.md file: New 한글 line.\ndoc.md: changed without doc.ko.md\n"
	if !failed || out != want {
		t.Fatalf("failed=%v out=%q, want %q", failed, out, want)
	}
}

func TestCheckFrontmatter(t *testing.T) {
	const valid = "---\nname: sample\ntype: guide\ndescription: A sample.\nscope: src\ngenerated:\n  by: human:x\n  at: 2026-01-02\nkeywords: [a, b]\n---\n\n# Body\n\n[ok](other.md) [bad](missing.md) [web](https://x.y) [anchor](#top)\n"
	tests := []struct {
		name string
		doc  string
		want string
	}{
		{"valid with a broken link", valid, "KNOWLEDGE.md: broken body link: missing.md\n"},
		{"no fence", "# Body\n", "KNOWLEDGE.md: frontmatter line 1: missing or unclosed '---' frontmatter fence\n"},
		{"not kebab", strings.Replace(valid, "name: sample", "name: Sample_X", 1), "KNOWLEDGE.md: name 'Sample_X' is not kebab-case\nKNOWLEDGE.md: broken body link: missing.md\n"},
		{"bad status", strings.Replace(valid, "keywords", "status: old\nkeywords", 1), "KNOWLEDGE.md: status 'old' is not one of ['deprecated', 'draft', 'stable']\nKNOWLEDGE.md: broken body link: missing.md\n"},
		{"missing scope path", strings.Replace(valid, "scope: src", "scope: nowhere", 1), "KNOWLEDGE.md: scope path does not exist: nowhere\nKNOWLEDGE.md: broken body link: missing.md\n"},
		{"stale verified", strings.Replace(valid, "keywords", "verified:\n  - by: human:y\n    at: 2025-01-01\nkeywords", 1), "KNOWLEDGE.md: verified (2025-01-01) is older than the last change (2026-01-02) — a meaningful change must clear 'verified'\nKNOWLEDGE.md: broken body link: missing.md\n"},
		{"missing generated", strings.Replace(valid, "generated:\n  by: human:x\n  at: 2026-01-02\n", "", 1), "KNOWLEDGE.md: missing 'generated' with 'by' and 'at'\nKNOWLEDGE.md: broken body link: missing.md\n"},
		{"bad date", strings.Replace(valid, "2026-01-02", "26-1-2", 1), "KNOWLEDGE.md: generated.at must be YYYY-MM-DD, got '26-1-2'\nKNOWLEDGE.md: broken body link: missing.md\n"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRepo(t)
			writeFile(t, root, "src/x.go", "package x\n")
			writeFile(t, root, "other.md", "x\n")
			writeFile(t, root, "KNOWLEDGE.md", tt.doc)
			out, failed := runCheck(t, root, "--only", "frontmatter")
			if out != tt.want || !failed {
				t.Fatalf("failed=%v out=%q, want %q", failed, out, tt.want)
			}
		})
	}
	t.Run("duplicate name", func(t *testing.T) {
		root := newRepo(t)
		writeFile(t, root, "src/x.go", "package x\n")
		doc := strings.Replace(valid, "[bad](missing.md)", "", 1)
		writeFile(t, root, "a/KNOWLEDGE.md", doc)
		writeFile(t, root, "b/KNOWLEDGE.md", doc)
		writeFile(t, root, "a/other.md", "x\n")
		writeFile(t, root, "b/other.md", "x\n")
		out, _ := runCheck(t, root, "--only", "frontmatter")
		if out != "b/KNOWLEDGE.md: name 'sample' is already used by a/KNOWLEDGE.md\n" {
			t.Fatalf("out=%q", out)
		}
	})
}

func TestSelectChecks(t *testing.T) {
	if _, err := selectChecks("words,nope"); err == nil {
		t.Fatal("want an error for an unknown check")
	}
	got, err := selectChecks("words,bilingual")
	if err != nil || len(got) != 2 || got[0].name != "words" {
		t.Fatalf("got %v, %v", got, err)
	}
}

func gitIn(t *testing.T, root string, args ...string) {
	t.Helper()
	full := append([]string{"-C", root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"}, args...)
	if out, err := exec.Command("git", full...).CombinedOutput(); err != nil {
		t.Fatalf("git %v: %v: %s", args, err, out)
	}
}

func TestCheckStaged(t *testing.T) {
	const old = "# Old\n\nWe refuse it.\n"
	tests := []struct {
		name     string
		staged   map[string]string
		unstaged map[string]string
		want     string
	}{
		{"old violation is not reported", map[string]string{"old.md": old + "\nFine.\n"}, nil, ""},
		{"added line", map[string]string{"old.md": old + "\nWe refused.\n"}, nil,
			"old.md:5: refuse -> reject: We refused.\n"},
		{"unstaged change is ignored", map[string]string{"old.md": old + "\nFine.\n"},
			map[string]string{"old.md": "We refuse.\n" + old, "new.md": "We refuse.\n"}, ""},
		{"staged content is read", map[string]string{"new.md": "# New\n\nWe refuse.\n"},
			map[string]string{"new.md": "# New\n"}, "new.md:3: refuse -> reject: We refuse.\n"},
		{"one side of a pair", map[string]string{"doc.md": "# A\n\nMore.\n"}, nil,
			"doc.md: changed without doc.ko.md\n"},
		{"unstaged partner does not count", map[string]string{"doc.md": "# A\n\n## B\n"},
			map[string]string{"doc.ko.md": "# 가\n\n## 나\n"},
			"doc.ko.md: headings differ from doc.md: [(1, 1)] and [(1, 1), (2, 1)]\ndoc.md: changed without doc.ko.md\n"},
		{"long AGENTS.md", map[string]string{"AGENTS.md": strings.Repeat("rule\n", 201)},
			map[string]string{"AGENTS.md": "rule\n"}, "AGENTS.md:1: 201 lines, limit 200\n"},
		{"nothing staged", nil, map[string]string{"old.md": "We refuse.\n"}, ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRepo(t)
			writeFile(t, root, "old.md", old)
			writeFile(t, root, "doc.md", "# A\n")
			writeFile(t, root, "doc.ko.md", "# 가\n")
			gitIn(t, root, "add", ".")
			gitIn(t, root, "commit", "-q", "-m", "base")
			for path, content := range tt.staged {
				writeFile(t, root, path, content)
				gitIn(t, root, "add", path)
			}
			for path, content := range tt.unstaged {
				writeFile(t, root, path, content)
			}
			out, failed := runCheck(t, root, "--staged")
			if out != tt.want || failed != (tt.want != "") {
				t.Fatalf("failed=%v out=%q, want %q", failed, out, tt.want)
			}
		})
	}
}

func TestStagedTakesNoBaseOrFiles(t *testing.T) {
	for _, args := range [][]string{{"check", "--staged", "--base", "x"}, {"check", "--staged", "a.md"}} {
		if _, err := run(args, io.Discard); err == nil {
			t.Errorf("run(%v): want an error", args)
		}
	}
}
