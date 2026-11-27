package main

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/lablup/backend.ai/tools/internal/spec"
)

const testRules = `expressions:
  - lang: en
    word: "refuse"
    instead: "reject"
    reason: "One verb per operation."
  - lang: en
    word: "leave out"
    qualifier: "a flag"
    instead: "omit"
  - lang: en
    word: "bring up, brought up"
    instead: "start"
  - lang: en
    word: "stand for"
    instead: "represent"
    except: ["stand for election"]
  - lang: ko
    word: "지우다"
    instead: "삭제하다"
  - lang: ko
    word: "막다 / 풀다"
    qualifier: "조건"
    instead: "차단하다"
korean:
  particles: [은, 는, 이, 가, 을, 를, 의, 에, 도, 로, 와, 과, 만, 으로, 이다, 입니다]
  verb:
    dictionary_ending: 다
    consonant_endings: [다, 고, 지, 는, 면, 며, 기, 게, 던, 니, 시, 겠]
    vowel_endings: [아, 어, 았, 었, 은, 을, 습]
    open_stem_finals: [ㄴ, ㄹ, ㅂ]
    past_final: ㅆ
    dropped_final:
      final: ㄹ
      endings: [는, 니]
      added: ㄴ
    contracted_syllables:
      하: 해
    contracted_vowels:
      ㅡ: ㅓ
      ㅣ: ㅕ
      ㅜ: ㅝ
      ㅗ: ㅘ
    irregular:
      syllable: 르
      added_final: ㄹ
      endings: [러, 라, 렀, 랐]
english:
  inflections: [s, es, d, ed, ing]
`

const testTerms = `terms:
  - english: "agent heartbeat"
    korean: "에이전트 heartbeat"
    meaning:
      en: "A signal."
      ko: "신호입니다."
    avoid:
      en: ["heartbeat", "bgtask"]
  - english: "app proxy"
    korean: "앱 프록시"
    meaning:
      en: "A proxy."
      ko: "프록시입니다."
    avoid:
      en: ["wsproxy"]
      ko: ["wsproxy"]
    note:
      en: "wsproxy is the old name."
      ko: "wsproxy 는 옛 이름입니다"
  - english: "Agent"
    korean: "컬럼"
    meaning:
      en: "The agent."
      ko: "열입니다."
    avoid:
      en: ["agent"]
      ko: ["컬럼", "칼럼"]
`

// repositorySpec is the doclint.yaml of this repository.
func repositorySpec(t *testing.T) string {
	t.Helper()
	data, err := os.ReadFile("../../doclint.yaml")
	if err != nil {
		t.Fatal(err)
	}
	return string(data)
}

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
	writeFile(t, root, "doclint.yaml", repositorySpec(t))
	writeFile(t, root, "glossary/registry/rules.yaml", testRules)
	writeFile(t, root, "glossary/registry/terms/process.yaml", testTerms)
	return root
}

func TestMatchWords(t *testing.T) {
	root := newRepo(t)
	english, korean, err := loadWords(filepath.Join(root, "glossary/registry"))
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
		{"allowed expression", english, "I stand for election.", "", false},
		{"outside the allowed expression", english, "They stand for it.", "stand for", false},
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
				if tt.words[i].match(tt.line) {
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

func TestProseLinesQuotes(t *testing.T) {
	tests := []struct {
		name string
		text string
		want map[int]string
	}{
		{"quote block", "> quoted\nkeep\n", map[int]string{2: "keep"}},
		{"indented quote block", "  > quoted\nkeep\n", map[int]string{2: "keep"}},
		{"nested quote block", "> > nested\nkeep\n", map[int]string{2: "keep"}},
		{"double quotes", `say "refuse" now`, map[int]string{1: "say   now"}},
		{"curly quotes", "say “refuse” now", map[int]string{1: "say   now"}},
		{"unpaired quote", `say "refuse now`, map[int]string{1: `say "refuse now`}},
		{"unpaired curly quote", "say “refuse now", map[int]string{1: "say “refuse now"}},
		{"quote in a code span", "say `\"` refuse `\"` now", map[int]string{1: "say   refuse   now"}},
		{"two quoted parts", `"a" b "c"`, map[int]string{1: "  b  "}},
		{"quote inside a fence", "```\n> q\n```\nkeep\n", map[int]string{4: "keep"}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := proseLines(tt.text)
			if len(got) != len(tt.want) {
				t.Fatalf("got %v, want %v", got, tt.want)
			}
			for n, line := range tt.want {
				if got[n] != line {
					t.Fatalf("line %d: got %q, want %q", n, got[n], line)
				}
			}
		})
	}
}

func TestCheckWordsSkipsQuotes(t *testing.T) {
	root := newRepo(t)
	writeFile(t, root, "quoted.md", "# Q\n\n> We refuse it.\n> > We refuse it.\nSay \"we refuse\" and “we refuse”.\n")
	writeFile(t, root, "outside.md", "# Q\n\nSay \"ok\" and we refuse it.\n")
	out, failed := runCheck(t, root, "--only", "words", "quoted.md")
	if failed || out != "" {
		t.Fatalf("failed=%v out=%q", failed, out)
	}
	out, failed = runCheck(t, root, "--only", "words", "outside.md")
	if !failed || out != refused("outside.md", 3) {
		t.Fatalf("failed=%v out=%q", failed, out)
	}
}

func TestSkippedPaths(t *testing.T) {
	loaded, err := spec.Load(newRepo(t))
	if err != nil {
		t.Fatal(err)
	}
	for path, want := range map[string]bool{
		"a/report.md": true, "a/report.ko.md": true,
		"CHANGELOG/26.9.md": true, "proposals/BEP-1.md": false, "AGENTS.md": false,
	} {
		if got := matchesAny(loaded.Words.SkippedPaths, path); got != want {
			t.Errorf("skipped(%q) = %v, want %v", path, got, want)
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
		{"bad.md", true, `bad.md:3: "refuse" -> "reject": One verb per operation.` + "\n"},
		{"review.md", false, `review: review.md:3: "heartbeat" -> "agent heartbeat": A signal.` + "\n"},
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

// refused is the output for the expression "refuse" of testRules.
func refused(path string, line int) string {
	return fmt.Sprintf(`%s:%d: "refuse" -> "reject": One verb per operation.`+"\n", path, line)
}

func TestWordsOutput(t *testing.T) {
	tests := []struct {
		name string
		file string
		line string
		want string
	}{
		{"expression with a reason", "doc.md", "We refuse it.",
			`doc.md:1: "refuse" -> "reject": One verb per operation.`},
		{"expression without a reason", "doc.md", "They stand for it.",
			`doc.md:1: "stand for" -> "represent"`},
		{"term variant takes the meaning", "doc.md", "The bgtask ends.",
			`review: doc.md:1: "bgtask" -> "agent heartbeat": A signal.`},
		{"korean expression without a reason", "doc.ko.md", "파일을 지운다",
			`doc.ko.md:1: "지우다" -> "삭제하다"`},
		{"korean term variant takes the korean meaning", "doc.ko.md", "칼럼을 둔다",
			`review: doc.ko.md:1: "칼럼" -> "컬럼": 열입니다.`},
		{"term variant takes the meaning and the note", "doc.md", "The wsproxy ends.",
			`review: doc.md:1: "wsproxy" -> "app proxy": A proxy. wsproxy is the old name.`},
		{"korean term variant takes the korean note", "doc.ko.md", "wsproxy 를 둔다",
			`review: doc.ko.md:1: "wsproxy" -> "앱 프록시": 프록시입니다. wsproxy 는 옛 이름입니다`},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRepo(t)
			writeFile(t, root, tt.file, tt.line+"\n")
			out, _ := runCheck(t, root, "--only", "words", tt.file)
			if out != tt.want+"\n" {
				t.Fatalf("out=%q, want %q", out, tt.want+"\n")
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

	// --allow-one-side leaves the other failures.
	out, failed = runCheck(t, root, "--only", "bilingual", "--base", "base", "--allow-one-side")
	want = "review: doc.md: changed without doc.ko.md\ndoc.md: Korean added, move it to the .ko.md file: New 한글 line.\n"
	if !failed || out != want {
		t.Fatalf("failed=%v out=%q, want %q", failed, out, want)
	}

	writeFile(t, root, "doc.md", "# A\n\nNew line.\n")
	gitRun("commit", "-qam", "english only")
	out, failed = runCheck(t, root, "--only", "bilingual", "--base", "base", "--allow-one-side")
	want = "review: doc.md: changed without doc.ko.md\n"
	if failed || out != want {
		t.Fatalf("failed=%v out=%q, want %q", failed, out, want)
	}

	writeFile(t, root, "doc.md", "# A\n\n## B\n")
	gitRun("commit", "-qam", "new section")
	out, failed = runCheck(t, root, "--only", "bilingual", "--base", "base", "--allow-one-side")
	want = "review: doc.md: changed without doc.ko.md\ndoc.ko.md: headings differ from doc.md: [(1, 1)] and [(1, 1), (2, 1)]\n"
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
			refused("old.md", 5)},
		{"unstaged change is ignored", map[string]string{"old.md": old + "\nFine.\n"},
			map[string]string{"old.md": "We refuse.\n" + old, "new.md": "We refuse.\n"}, ""},
		{"staged content is read", map[string]string{"new.md": "# New\n\nWe refuse.\n"},
			map[string]string{"new.md": "# New\n"}, refused("new.md", 3)},
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

func TestSpecChangesTheCheck(t *testing.T) {
	long := "- " + strings.Repeat("a", 121) + "\n"
	tests := []struct {
		name     string
		check    string
		file     string
		content  string
		old, new string
		before   string
		after    string
	}{
		{"agents limit", "agents-lines", "AGENTS.md", strings.Repeat("rule\n", 11),
			"max_lines: 200", "max_lines: 10", "", "AGENTS.md:1: 11 lines, limit 10\n"},
		{"bep item length", "bep-length", "proposals/BEP-1090-x.md", long,
			"en: 120", "en: 130", "proposals/BEP-1090-x.md:1: list item of 121 chars, limit 120\n", ""},
		{"bep first number", "bep-length", "proposals/BEP-1090-x.md", long,
			"first_number: 1080", "first_number: 1091", "proposals/BEP-1090-x.md:1: list item of 121 chars, limit 120\n", ""},
		{"skipped words path", "words", "notes.md", "We refuse.\n",
			"- '(^|/)CHANGELOG(/|$)'", "- '(^|/)CHANGELOG(/|$)'\n    - '^notes'",
			refused("notes.md", 1), ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRepo(t)
			writeFile(t, root, tt.file, tt.content)
			out, _ := runCheck(t, root, "--only", tt.check, tt.file)
			if out != tt.before {
				t.Fatalf("before: out=%q, want %q", out, tt.before)
			}
			changed := strings.Replace(repositorySpec(t), tt.old, tt.new, 1)
			if changed == repositorySpec(t) {
				t.Fatalf("the spec has no %q", tt.old)
			}
			writeFile(t, root, "doclint.yaml", changed)
			out, _ = runCheck(t, root, "--only", tt.check, tt.file)
			if out != tt.after {
				t.Fatalf("after: out=%q, want %q", out, tt.after)
			}
		})
	}
}

func TestInvalidSpecIsRejected(t *testing.T) {
	const (
		specFile  = "doclint.yaml"
		rulesPath = "glossary/registry/rules.yaml"
		termsPath = "glossary/registry/terms/process.yaml"
	)
	tests := []struct {
		name     string
		file     string
		old, new string
		want     string
	}{
		{"unknown key", specFile, "max_lines: 200", "max_lines: 200\n  max_line: 1", "field max_line not found"},
		{"missing value", specFile, "  max_lines: 200\n", "", "missing value agents.max_lines"},
		{"empty list", specFile, "goal_sections: [Goals, 목표]", "goal_sections: []", "missing value bep.goal_sections"},
		{"missing pattern", specFile, "  path: '(^|/)AGENTS\\.md$'\n", "", "missing value agents.path"},
		{"bad pattern", specFile, "'(^|/)AGENTS\\.md$'", "'('", "error parsing regexp"},
		{"missing language", specFile, "    ko: 80\n", "", "missing value bep.max_item_chars.ko"},
		{"flow mapping in the spec", specFile, "  max_item_chars:\n    en: 120\n    ko: 80\n", "  max_item_chars: {en: 120, ko: 80}\n", "doclint.yaml:17: mapping in flow style"},
		{"unknown kind", specFile, "kind: enum", "kind: choice", "unknown kind"},
		{"unknown field reference", specFile, "title: name", "title: nothing", "unknown field"},
		{"default outside the values", specFile, "default: stable", "default: old", "default must be one of the values"},
		{"unknown rules key", rulesPath, "english:\n", "extra: 1\nenglish:\n", "field extra not found"},
		{"missing rules value", rulesPath, "    past_final: ㅆ\n", "", "missing value korean.verb.past_final"},
		{"missing instead", rulesPath, "    instead: \"reject\"\n", "", "missing value expressions[0].instead"},
		{"unknown language", rulesPath, "lang: en\n    word: \"refuse\"", "lang: fr\n    word: \"refuse\"", "unknown lang"},
		{"flow mapping in the rules", rulesPath, "    contracted_syllables:\n      하: 해\n", "    contracted_syllables: {하: 해}\n", "mapping in flow style"},
		{"not a jamo", rulesPath, "past_final: ㅆ", "past_final: x", "is not a jamo"},
		{"missing meaning", termsPath, "      ko: \"신호입니다.\"\n", "", "terms[0]: missing value meaning.ko"},
		{"flow mapping in a term file", termsPath, "    meaning:\n      en: \"A signal.\"\n      ko: \"신호입니다.\"\n", "    meaning: {en: \"A signal.\", ko: \"신호입니다.\"}\n", "process.yaml:4: mapping in flow style"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRepo(t)
			data, err := os.ReadFile(filepath.Join(root, tt.file))
			if err != nil {
				t.Fatal(err)
			}
			changed := strings.Replace(string(data), tt.old, tt.new, 1)
			if changed == string(data) {
				t.Fatalf("%s has no %q", tt.file, tt.old)
			}
			writeFile(t, root, tt.file, changed)
			_, err = run([]string{"check", "--root", root, "--only", "words"}, io.Discard)
			if err == nil || !strings.Contains(err.Error(), tt.want) {
				t.Fatalf("err = %v, want %q", err, tt.want)
			}
		})
	}
}

func TestRepositoryRegistryLoads(t *testing.T) {
	loaded, err := spec.Load("../..")
	if err != nil {
		t.Fatal(err)
	}
	if _, _, err := loadWords(filepath.Join("../..", loaded.Words.Registry)); err != nil {
		t.Fatal(err)
	}
}
