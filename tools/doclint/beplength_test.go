package main

import (
	"strings"
	"testing"

	"github.com/lablup/backend.ai/tools/internal/spec"
)

func TestCheckBEPLength(t *testing.T) {
	items := func(n int) string { return strings.Repeat("- item\n", n) }
	tests := []struct {
		name string
		path string
		doc  string
		want []string
	}{
		{"ok", "BEP-1090-x.md", "# T\n\n## Goals\n\n" + items(3), nil},
		{"too many lines", "BEP-1090-x.md", strings.Repeat("text\n", 301), []string{"BEP-1090-x.md:1: 301 lines, limit 300"}},
		{"nested item", "BEP-1090-x.md", "- a\n  - b\n", []string{"BEP-1090-x.md:2: nested list item, keep lists one level"}},
		{"long item en", "BEP-1090-x.md", "- " + strings.Repeat("a", 121) + "\n", []string{"BEP-1090-x.md:1: list item of 121 chars, limit 120"}},
		{"long item ko", "BEP-1090-x.ko.md", "- " + strings.Repeat("가", 81) + "\n", []string{"BEP-1090-x.ko.md:1: list item of 81 chars, limit 80"}},
		{"ko limit passes en", "BEP-1090-x.ko.md", "- " + strings.Repeat("가", 80) + "\n", nil},
		{"counted list", "BEP-1090-x.md", "## Impact\n\n" + items(8), []string{"BEP-1090-x.md:1: 8 items in 'Impact', limit 7"}},
		{"counted list ko", "BEP-1090-x.ko.md", "## 구현 순서\n\n" + items(7), nil},
		{"goal rows", "BEP-1090-x.md", "## Goals\n\n| a | b |\n|---|---|\n" + strings.Repeat("| 1 | 2 |\n", 8), []string{"BEP-1090-x.md:3: 8 goal rows, limit 7"}},
		{"frontmatter and fences skipped", "BEP-1090-x.md", "---\nk: v\n---\n```\n" + strings.Repeat("text\n", 400) + "```\n", nil},
		{"comments skipped", "BEP-1090-x.md", "<!--\n" + strings.Repeat("text\n", 400) + "-->\n", nil},
		{"design subsections", "BEP-1090-x.md", "## Design\n\n### a\n\n### b\n\n### c\n\n### d\n\n### e\n", []string{"BEP-1090-x.md:1: 5 design subsections, limit 4"}},
		{"design sentences", "BEP-1090-x.md", "## Design\n\n### a\n\nOne. Two. Three. Four.\n", []string{"BEP-1090-x.md:3: 4 sentences in 'a', limit 3"}},
		{"design sentences abbreviation", "BEP-1090-x.md", "## Design\n\n### a\n\nOne e.g. two. Three. Four.\n", nil},
		{"rejected line skipped", "BEP-1090-x.md", "## Design\n\n### a\n\nRejected: One. Two. Three. Four.\n", nil},
		{"design tables", "BEP-1090-x.md", "## Design\n\n### a\n\n| a |\n|---|\n| 1 |\n\n| b |\n|---|\n| 1 |\n\n| c |\n|---|\n| 1 |\n", []string{"BEP-1090-x.md:3: 3 tables, limit 2"}},
		{"design table rows", "BEP-1090-x.md", "## Design\n\n### a\n\n| a |\n|---|\n" + strings.Repeat("| 1 |\n", 8), []string{"BEP-1090-x.md:5: 8 table rows, limit 7"}},
		{"design lead text", "BEP-1090-x.md", "## Design\n\nOne. Two. Three. Four.\n\n### a\n", []string{"BEP-1090-x.md:1: 4 sentences in 'Design', limit 3"}},
	}
	loaded, err := spec.Load("../..")
	if err != nil {
		t.Fatal(err)
	}
	checker := newBEPChecker(loaded)
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := checker.check([]byte(tt.doc), tt.path)
			if strings.Join(got, "\n") != strings.Join(tt.want, "\n") {
				t.Fatalf("got %q, want %q", got, tt.want)
			}
		})
	}
}

func TestBEPPaths(t *testing.T) {
	root := newRepo(t)
	for _, rel := range []string{
		"proposals/BEP-1079-old.md", "proposals/BEP-1080-new.md", "proposals/BEP-1080-new.ko.md",
		"proposals/BEP-1081/a.md", "proposals/BEP-1070/a.md", "proposals/AGENTS.md",
	} {
		writeFile(t, root, rel, "x\n")
	}
	sc, err := newScope(root, "", nil)
	if err != nil {
		t.Fatal(err)
	}
	got, err := bepPaths(sc)
	if err != nil {
		t.Fatal(err)
	}
	want := "proposals/BEP-1080-new.ko.md proposals/BEP-1080-new.md proposals/BEP-1081/a.md"
	if strings.Join(got, " ") != want {
		t.Fatalf("got %v, want %s", got, want)
	}
}
