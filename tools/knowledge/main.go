// Command knowledge searches the KNOWLEDGE.md documents by their frontmatter.
//
// Usage, from the repository root:
//
//	go run ./tools/knowledge search [--root <dir>] [term ...]
//
// Without terms it lists every KNOWLEDGE.md. With terms it prints the documents whose path,
// name, type, keywords or description contain every term (case-insensitive substring match).
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
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
	paths, err := kdoc.IterFiles(*root)
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
		document, problems := kdoc.Build(raw)
		if document == nil {
			fmt.Fprintf(os.Stderr, "%s: skipped, %s\n", rel, problems[0])
			continue
		}
		if !matches(fs.Args(), rel, document) {
			continue
		}
		fmt.Println(rel)
		fmt.Printf("  %s (%s, %s)\n", document.Name, document.Type, document.Status)
		fmt.Printf("  %s\n", document.Description)
	}
	return nil
}

func matches(terms []string, path string, document *kdoc.Document) bool {
	haystack := strings.ToLower(strings.Join([]string{
		path, document.Name, document.Type, strings.Join(document.Keywords, " "), document.Description,
	}, " "))
	for _, term := range terms {
		if !strings.Contains(haystack, strings.ToLower(term)) {
			return false
		}
	}
	return true
}
