package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const (
	docsSpec = "documents:\n  extension: .md\n  translation_suffix: .ko.md\n"
	// wordsTail ends a spec that checks the words of the registry in glossary/registry.
	wordsTail = "words:\n  registry: glossary/registry\n  skipped_paths:\n    - '^skip/'\n"
)

// newBareRepo is a git repository without a spec, for a test that writes its own.
func newBareRepo(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	gitIn(t, root, "init", "-q")
	return root
}

// newRegistryRepo is a repository with the test registry and the given spec.
func newRegistryRepo(t *testing.T, specText string) string {
	t.Helper()
	root := newBareRepo(t)
	writeFile(t, root, "doclint.yaml", specText)
	writeFile(t, root, "glossary/registry/rules.yaml", testRules)
	writeFile(t, root, "glossary/registry/terms/process.yaml", testTerms)
	return root
}

// runWith runs doclint with the standard input and returns the output, whether it failed and
// the read error.
func runWith(args []string, stdin string) (string, bool, error) {
	var out strings.Builder
	failed, err := run(append([]string{"check"}, args...), strings.NewReader(stdin), &out)
	return out.String(), failed, err
}

func TestPartsOfTheSpecAreOptional(t *testing.T) {
	root := newRegistryRepo(t, docsSpec+"agents:\n  path: '(^|/)AGENTS\\.md$'\n  max_lines: 5\n"+wordsTail)
	writeFile(t, root, "AGENTS.md", strings.Repeat("rule\n", 6))
	writeFile(t, root, "bad.md", "We refuse it.\n")
	writeFile(t, root, "proposals/BEP-1090-x.md", "- "+strings.Repeat("a", 121)+"\n")
	writeFile(t, root, "KNOWLEDGE.md", "no frontmatter\n")
	writeFile(t, root, "orphan.ko.md", "# 가\n")
	out, failed := runCheck(t, root)
	want := refused("bad.md", 1) + "AGENTS.md:1: 6 lines, limit 5\n"
	if !failed || out != want {
		t.Fatalf("failed=%v out=%q, want %q", failed, out, want)
	}
	for only, part := range map[string]string{"bep-length": "bep", "frontmatter": "knowledge", "bilingual": "pairs", "words,bilingual": "pairs"} {
		_, _, err := runWith([]string{"--root", root, "--only", only}, "")
		if err == nil || !strings.Contains(err.Error(), "needs "+part+" in the spec") {
			t.Errorf("--only %s: err = %v", only, err)
		}
	}
}

func TestChecksNeedDocuments(t *testing.T) {
	root := newRegistryRepo(t, "agents:\n  path: '(^|/)AGENTS\\.md$'\n  max_lines: 5\n")
	_, _, err := runWith([]string{"--root", root}, "")
	if err == nil || !strings.Contains(err.Error(), "documents is missing") {
		t.Fatalf("err = %v", err)
	}
	root = newRegistryRepo(t, docsSpec)
	if out, failed, err := runWith([]string{"--root", root}, ""); err != nil || failed || out != "" {
		t.Fatalf("a spec of documents runs no check: out=%q failed=%v err=%v", out, failed, err)
	}
}

func TestInvalidParts(t *testing.T) {
	tests := []struct {
		name string
		spec string
		want string
	}{
		{"part with a missing value", docsSpec + "agents:\n  path: 'a'\n", "missing value agents.max_lines"},
		{"documents without a suffix", "documents:\n  extension: .md\n" + wordsTail, "missing value documents.translation_suffix"},
		{"unknown language", docsSpec + "  language: fr\n" + wordsTail, "unknown language"},
		{"registry with rules", docsSpec + "words:\n  registry: glossary/registry\n  rules: [a.yaml]\n  skipped_paths: ['a']\n", "cannot be used with"},
		{"registry with terms", docsSpec + "words:\n  registry: glossary/registry\n  terms: t\n  skipped_paths: ['a']\n", "cannot be used with"},
		{"terms without rules", docsSpec + "words:\n  terms: t\n  skipped_paths: ['a']\n", "needs registry, or rules"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRegistryRepo(t, tt.spec)
			_, _, err := runWith([]string{"--root", root}, "")
			if err == nil || !strings.Contains(err.Error(), tt.want) {
				t.Fatalf("err = %v, want %q", err, tt.want)
			}
		})
	}
}

func TestDocumentLanguage(t *testing.T) {
	const mixed = "We refuse it.\n파일을 지운다\nrefuse 한글 mix\n"
	english := `doc.md:1: "refuse" -> "reject": One verb per operation.` + "\n"
	englishAll := english + `doc.md:3: "refuse" -> "reject": One verb per operation.` + "\n"
	korean := `doc.md:2: "지우다" -> "삭제하다"` + "\n"
	tests := []struct {
		name     string
		language string
		file     string
		want     string
	}{
		{"default is English", "", "doc.md", englishAll},
		{"en", "  language: en\n", "doc.md", englishAll},
		{"ko", "  language: ko\n", "doc.md", korean},
		{"hangul chooses by line", "  language: hangul\n", "doc.md", english + korean},
		{"the suffix is Korean with en", "  language: en\n", "doc.ko.md", strings.ReplaceAll(korean, "doc.md", "doc.ko.md")},
		{"the suffix is Korean with hangul", "  language: hangul\n", "doc.ko.md", strings.ReplaceAll(korean, "doc.md", "doc.ko.md")},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRegistryRepo(t, docsSpec+tt.language+wordsTail)
			writeFile(t, root, tt.file, mixed)
			out, _ := runCheck(t, root, "--only", "words")
			if out != tt.want {
				t.Fatalf("out=%q, want %q", out, tt.want)
			}
		})
	}
}

const (
	rulesHead = "expressions:\n"
	rulesTail = "korean:\n  particles: [은, 는, 이, 가, 을, 를]\n  verb:\n    dictionary_ending: 다\n" +
		"    consonant_endings: [다, 고]\n    vowel_endings: [아, 어]\n    open_stem_finals: [ㄴ, ㄹ, ㅂ]\n" +
		"    past_final: ㅆ\n    dropped_final:\n      final: ㄹ\n      endings: [는]\n      added: ㄴ\n" +
		"    contracted_syllables:\n      하: 해\n    contracted_vowels:\n      ㅡ: ㅓ\n    irregular:\n" +
		"      syllable: 르\n      added_final: ㄹ\n      endings: [러]\n" +
		"english:\n  inflections: [s, es, d, ed, ing]\n"
	entryRefuse = "  - lang: en\n    word: \"refuse\"\n    instead: \"reject\"\n"
	entryStand  = "  - lang: en\n    word: \"stand for\"\n    instead: \"represent\"\n"
)

// newRulesRepo writes the rule files by name under rules/ and a spec of the words check.
func newRulesRepo(t *testing.T, wordsLines string, rules map[string]string) string {
	t.Helper()
	root := newBareRepo(t)
	writeFile(t, root, "doclint.yaml", docsSpec+"words:\n"+wordsLines+"  skipped_paths:\n    - '^skip/'\n")
	for name, content := range rules {
		writeFile(t, root, "rules/"+name, content)
	}
	return root
}

func TestRuleFiles(t *testing.T) {
	const rules = "  rules: [rules/b.yaml, rules/a.yaml]\n"
	t.Run("both files apply", func(t *testing.T) {
		root := newRulesRepo(t, rules, map[string]string{
			"a.yaml": rulesHead + entryRefuse + rulesTail,
			"b.yaml": rulesHead + entryStand,
		})
		writeFile(t, root, "doc.md", "We refuse it.\nThey stand for it.\n")
		out, failed := runCheck(t, root)
		want := `doc.md:1: "refuse" -> "reject"` + "\n" + `doc.md:2: "stand for" -> "represent"` + "\n"
		if !failed || out != want {
			t.Fatalf("failed=%v out=%q, want %q", failed, out, want)
		}
	})
	errs := []struct {
		name  string
		files map[string]string
		want  []string
	}{
		{"same expression in two files", map[string]string{
			"a.yaml": rulesHead + entryRefuse + rulesTail, "b.yaml": rulesHead + entryRefuse,
		}, []string{`en "refuse"`, "rules/a.yaml", "rules/b.yaml"}},
		{"same pattern in two files", map[string]string{
			"a.yaml": rulesHead + "  - lang: en\n    pattern: 'x+'\n    instead: y\n" + rulesTail,
			"b.yaml": rulesHead + "  - lang: en\n    pattern: 'x+'\n    instead: y\n",
		}, []string{`en "x+"`, "rules/a.yaml", "rules/b.yaml"}},
		{"korean rules in two files", map[string]string{
			"a.yaml": rulesHead + entryRefuse + rulesTail, "b.yaml": rulesTail,
		}, []string{"korean is in more than one rule file", "rules/a.yaml", "rules/b.yaml"}},
		{"no inflection rules", map[string]string{
			"a.yaml": rulesHead + entryRefuse, "b.yaml": rulesHead + entryStand,
		}, []string{"missing value korean"}},
	}
	for _, tt := range errs {
		t.Run(tt.name, func(t *testing.T) {
			root := newRulesRepo(t, rules, tt.files)
			writeFile(t, root, "doc.md", "x\n")
			_, _, err := runWith([]string{"--root", root}, "")
			if err == nil {
				t.Fatal("want an error")
			}
			for _, part := range tt.want {
				if !strings.Contains(err.Error(), part) {
					t.Fatalf("err = %v, want %q", err, part)
				}
			}
		})
	}
}

func TestRuleFilesAreReadInPathOrder(t *testing.T) {
	root := newRulesRepo(t, "  rules: [rules/b.yaml, rules/a.yaml]\n", map[string]string{
		"a.yaml": rulesHead + entryStand + rulesTail,
		"b.yaml": rulesHead + entryRefuse,
	})
	writeFile(t, root, "doc.md", "We refuse and stand for it.\n")
	out, _ := runCheck(t, root)
	want := `doc.md:1: "stand for" -> "represent"` + "\n" + `doc.md:1: "refuse" -> "reject"` + "\n"
	if out != want {
		t.Fatalf("out=%q, want %q", out, want)
	}
}

const setsRules = "sets:\n" +
	"  - name: a\n    description: Set a.\n    skipped_paths:\n      - '^docs/'\n" +
	"  - name: b\n    description: Set b.\n" +
	"expressions:\n" +
	"  - lang: en\n    word: \"refuse\"\n    instead: \"reject\"\n    sets: [a]\n" +
	"  - lang: en\n    word: \"stand for\"\n    instead: \"represent\"\n    sets: [b]\n" +
	"  - lang: en\n    word: \"bring up\"\n    instead: \"start\"\n" +
	"  - lang: en\n    word: \"leave out\"\n    instead: \"omit\"\n    sets: [a, b]\n" +
	rulesTail

func TestRuleSets(t *testing.T) {
	const text = "We refuse it.\nThey stand for it.\nSo bring up the rest.\nAnd leave out the flag.\n"
	const (
		refuse = "%s:1: \"refuse\" -> \"reject\"\n"
		stand  = "%s:2: \"stand for\" -> \"represent\"\n"
		bring  = "%s:3: \"bring up\" -> \"start\"\n"
		leave  = "%s:4: \"leave out\" -> \"omit\"\n"
	)
	tests := []struct {
		name  string
		words string
		path  string
		want  string
	}{
		{"no selection uses every rule", "  rules: [rules/a.yaml]\n", "x.md", refuse + stand + bring + leave},
		{"a selection uses its rules and the rules without a set", "  rules: [rules/a.yaml]\n  sets: [a]\n", "x.md", refuse + bring + leave},
		{"another selection", "  rules: [rules/a.yaml]\n  sets: [b]\n", "x.md", stand + bring + leave},
		{"both sets", "  rules: [rules/a.yaml]\n  sets: [a, b]\n", "x.md", refuse + stand + bring + leave},
		{"a set skips its path", "  rules: [rules/a.yaml]\n  sets: [a]\n", "docs/x.md", bring},
		{"a rule of two sets is checked while one does not skip", "  rules: [rules/a.yaml]\n  sets: [a, b]\n", "docs/x.md", stand + bring + leave},
		{"the skip applies without a selection", "  rules: [rules/a.yaml]\n", "docs/x.md", stand + bring + leave},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRulesRepo(t, tt.words, map[string]string{"a.yaml": setsRules})
			writeFile(t, root, tt.path, text)
			out, _ := runCheck(t, root)
			want := strings.ReplaceAll(tt.want, "%s", tt.path)
			if out != want {
				t.Fatalf("out=%q, want %q", out, want)
			}
		})
	}
}

func TestRuleSetErrors(t *testing.T) {
	tests := []struct {
		name  string
		words string
		files map[string]string
		want  []string
	}{
		{"unknown set in an expression", "  rules: [rules/a.yaml]\n", map[string]string{
			"a.yaml": strings.Replace(setsRules, "sets: [b]", "sets: [c]", 1)}, []string{`unknown set "c"`}},
		{"unknown set in the selection", "  rules: [rules/a.yaml]\n  sets: [c]\n", map[string]string{
			"a.yaml": setsRules}, []string{`words.sets: unknown set "c"`}},
		{"set declared twice in a file", "  rules: [rules/a.yaml]\n", map[string]string{
			"a.yaml": strings.Replace(setsRules, "name: b", "name: a", 1)}, []string{`set "a" is declared in`}},
		{"set declared in two files", "  rules: [rules/a.yaml, rules/b.yaml]\n", map[string]string{
			"a.yaml": setsRules, "b.yaml": "sets:\n  - name: a\n    description: Again.\n"}, []string{`set "a" is declared in`, "rules/a.yaml", "rules/b.yaml"}},
		{"set without a description", "  rules: [rules/a.yaml]\n", map[string]string{
			"a.yaml": strings.Replace(setsRules, "    description: Set b.\n", "", 1)}, []string{"missing value sets[1].description"}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRulesRepo(t, tt.words, tt.files)
			writeFile(t, root, "x.md", "x\n")
			_, _, err := runWith([]string{"--root", root}, "")
			if err == nil {
				t.Fatal("want an error")
			}
			for _, part := range tt.want {
				if !strings.Contains(err.Error(), part) {
					t.Fatalf("err = %v, want %q", err, part)
				}
			}
		})
	}
	t.Run("a set of another file is declared", func(t *testing.T) {
		root := newRulesRepo(t, "  rules: [rules/a.yaml, rules/b.yaml]\n", map[string]string{
			"a.yaml": setsRules,
			"b.yaml": "expressions:\n  - lang: en\n    word: x\n    instead: y\n    sets: [b]\n",
		})
		writeFile(t, root, "x.md", "x\n")
		if _, _, err := runWith([]string{"--root", root}, ""); err != nil {
			t.Fatal(err)
		}
	})
}

func TestPatternExpressions(t *testing.T) {
	const entry = "  - lang: en\n    pattern: '\\bfoo[0-9]+\\b'\n    instead: \"a name\"\n    reason: \"Names have no digits.\"\n"
	root := newRulesRepo(t, "  rules: [rules/a.yaml]\n", map[string]string{"a.yaml": rulesHead + entry + rulesTail})
	writeFile(t, root, "doc.md", "A foo12 here.\nA foo here.\nA `foo1` span.\nxfoo3\n")
	out, failed := runCheck(t, root)
	want := `doc.md:1: "\bfoo[0-9]+\b" -> "a name": Names have no digits.` + "\n"
	if !failed || out != want {
		t.Fatalf("failed=%v out=%q, want %q", failed, out, want)
	}
	tests := []struct {
		name  string
		entry string
		want  string
	}{
		{"word and pattern", "  - lang: en\n    word: a\n    pattern: b\n    instead: c\n", "exactly one of word and pattern"},
		{"neither", "  - lang: en\n    instead: c\n", "exactly one of word and pattern"},
		{"bad pattern", "  - lang: en\n    pattern: '('\n    instead: c\n", "error parsing regexp"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := newRulesRepo(t, "  rules: [rules/a.yaml]\n", map[string]string{"a.yaml": rulesHead + tt.entry + rulesTail})
			_, _, err := runWith([]string{"--root", root}, "")
			if err == nil || !strings.Contains(err.Error(), tt.want) {
				t.Fatalf("err = %v, want %q", err, tt.want)
			}
		})
	}
}

func TestRulesAndTermsListTheRegistryFiles(t *testing.T) {
	root := newRegistryRepo(t, docsSpec+"words:\n  rules: [glossary/registry/rules.yaml]\n  terms: glossary/registry/terms\n  skipped_paths: ['^skip/']\n")
	writeFile(t, root, "doc.md", "We refuse it.\nThe heartbeat arrives.\n")
	out, _ := runCheck(t, root)
	want := `review: doc.md:2: "heartbeat" -> "agent heartbeat": A signal.` + "\n" + refused("doc.md", 1)
	if out != want {
		t.Fatalf("out=%q, want %q", out, want)
	}
}

func TestSpecFile(t *testing.T) {
	tmp := t.TempDir()
	root := filepath.Join(tmp, "repo")
	if err := os.MkdirAll(root, 0o755); err != nil {
		t.Fatal(err)
	}
	gitIn(t, root, "init", "-q")
	writeFile(t, tmp, "cfg/spec.yaml", docsSpec+"words:\n  rules: [reg/rules.yaml]\n  terms: reg/terms\n  skipped_paths:\n    - '^skip/'\n")
	writeFile(t, tmp, "cfg/reg/rules.yaml", testRules)
	writeFile(t, tmp, "cfg/reg/terms/process.yaml", testTerms)
	writeFile(t, root, "doc.md", "We refuse it.\n")
	writeFile(t, root, "skip/doc.md", "We refuse it.\n")
	t.Chdir(tmp)
	for _, specPath := range []string{"cfg/spec.yaml", filepath.Join(tmp, "cfg/spec.yaml")} {
		out, failed, err := runWith([]string{"--root", root, "--spec", specPath}, "")
		if err != nil || !failed || out != refused("doc.md", 1) {
			t.Fatalf("--spec %s: out=%q failed=%v err=%v", specPath, out, failed, err)
		}
	}
	if _, _, err := runWith([]string{"--root", root}, ""); err == nil {
		t.Fatal("without --spec the spec of the root is read")
	}
	if _, _, err := runWith([]string{"--root", root, "--spec", "cfg/none.yaml"}, ""); err == nil {
		t.Fatal("want an error for a missing spec file")
	}
}

func TestStdin(t *testing.T) {
	root := newRegistryRepo(t, docsSpec+"  language: hangul\nwords:\n  registry: glossary/registry\n  skipped_paths:\n    - '^<stdin>$'\n")
	args := []string{"--root", root, "--stdin"}
	tests := []struct {
		name       string
		input      string
		wantFailed bool
		want       string
	}{
		{"hits with the input line numbers", "fine\nWe refuse it.\n파일을 지운다\n", true,
			`<stdin>:2: "refuse" -> "reject": One verb per operation.` + "\n" + `<stdin>:3: "지우다" -> "삭제하다"` + "\n"},
		{"a review does not fail", "The heartbeat arrives.\n", false, `review: <stdin>:1: "heartbeat" -> "agent heartbeat": A signal.` + "\n"},
		{"nothing to report", "Fine.\n", false, ""},
		{"code is skipped", "```\nWe refuse it.\n```\n", false, ""},
		{"empty input", "", false, ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			out, failed, err := runWith(args, tt.input)
			if err != nil || failed != tt.wantFailed || out != tt.want {
				t.Fatalf("out=%q failed=%v err=%v, want %q failed=%v", out, failed, err, tt.want, tt.wantFailed)
			}
		})
	}
	t.Run("only the words check runs", func(t *testing.T) {
		out, failed, err := runWith(append(append([]string{}, args...), "--only", "words"), "We refuse it.\n")
		if err != nil || !failed || out == "" {
			t.Fatalf("out=%q failed=%v err=%v", out, failed, err)
		}
		if _, _, err := runWith(append(append([]string{}, args...), "--only", "agents-lines"), ""); err == nil {
			t.Fatal("want an error for another check")
		}
	})
	for _, rest := range [][]string{{"a.md"}, {"--base", "HEAD"}, {"--staged"}} {
		if _, _, err := runWith(append(append([]string{}, args...), rest...), ""); err == nil {
			t.Errorf("--stdin %v: want an error", rest)
		}
	}
}

func TestStdinWithoutDocuments(t *testing.T) {
	root := newRegistryRepo(t, "words:\n  registry: glossary/registry\n  skipped_paths: ['^skip/']\n")
	out, failed, err := runWith([]string{"--root", root, "--stdin"}, "We refuse it.\n")
	if err != nil || !failed || out != `<stdin>:1: "refuse" -> "reject": One verb per operation.`+"\n" {
		t.Fatalf("out=%q failed=%v err=%v", out, failed, err)
	}
	root = newRegistryRepo(t, docsSpec+"agents:\n  path: 'AGENTS'\n  max_lines: 5\n")
	if _, _, err = runWith([]string{"--root", root, "--stdin"}, "x\n"); err == nil {
		t.Fatal("want an error for a spec without words")
	}
}

func TestStdinSkipsNoPath(t *testing.T) {
	root := newRulesRepo(t, "  rules: [rules/a.yaml]\n", map[string]string{
		"a.yaml": strings.Replace(setsRules, "'^docs/'", "'^<stdin>$'", 1)})
	out, _, err := runWith([]string{"--root", root, "--stdin"}, "We refuse it.\n")
	if err != nil || out != "<stdin>:1: \"refuse\" -> \"reject\"\n" {
		t.Fatalf("out=%q err=%v", out, err)
	}
}
