// Command knowledge searches the knowledge documents by their frontmatter.
//
// Usage, from the repository root:
//
//	go run ./tools/knowledge search [--root <dir>] [term ...]
//
// Without terms it lists every document. With terms it prints the documents whose path or
// search fields (doclint.yaml) contain every term (case-insensitive substring match).
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
	"github.com/lablup/backend.ai/tools/internal/spec"
)

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "knowledge:", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 0 || args[0] != "search" {
		return fmt.Errorf("usage: knowledge search [--root <dir>] [term ...]")
	}
	fs := flag.NewFlagSet("search", flag.ContinueOnError)
	root := fs.String("root", ".", "repository root")
	if err := fs.Parse(args[1:]); err != nil {
		return err
	}
	loaded, err := spec.Load(*root)
	if err != nil {
		return err
	}
	schema := loaded.Knowledge
	if schema == nil {
		return fmt.Errorf("%s has no knowledge part", filepath.Join(*root, spec.FileName))
	}
	paths, err := kdoc.IterFiles(*root, schema)
	if err != nil {
		return err
	}
	for _, path := range paths {
		rel, err := filepath.Rel(*root, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		raw, _, err := kdoc.Load(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s: skipped, %v\n", rel, err)
			continue
		}
		document, problems := kdoc.Build(schema, raw)
		if document == nil {
			fmt.Fprintf(os.Stderr, "%s: skipped, %s\n", rel, problems[0])
			continue
		}
		if !matches(fs.Args(), rel, schema.Search.Fields, document) {
			continue
		}
		fmt.Println(rel)
		tags := make([]string, len(schema.Search.Tags))
		for i, name := range schema.Search.Tags {
			tags[i] = document.Text(name)
		}
		fmt.Printf("  %s (%s)\n", document.Text(schema.Search.Title), strings.Join(tags, ", "))
		fmt.Printf("  %s\n", document.Text(schema.Search.Summary))
	}
	return nil
}

func matches(terms []string, path string, fields []string, document kdoc.Document) bool {
	parts := []string{path}
	for _, name := range fields {
		parts = append(parts, strings.Join(document.Texts(name), " "))
	}
	haystack := strings.ToLower(strings.Join(parts, " "))
	for _, term := range terms {
		if !strings.Contains(haystack, strings.ToLower(term)) {
			return false
		}
	}
	return true
}
