package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestSearchNeedsTheKnowledgePart(t *testing.T) {
	root := t.TempDir()
	spec := "documents:\n  extension: .md\n  translation_suffix: .ko.md\n"
	if err := os.WriteFile(filepath.Join(root, "doclint.yaml"), []byte(spec), 0o644); err != nil {
		t.Fatal(err)
	}
	err := run([]string{"search", "--root", root})
	if err == nil || !strings.Contains(err.Error(), "no knowledge part") {
		t.Fatalf("err = %v", err)
	}
}
