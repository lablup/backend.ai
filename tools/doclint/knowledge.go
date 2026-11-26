package main

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
)

var linkPattern = regexp.MustCompile(`\[[^\]]*\]\(([^)\s]+)\)`)

var externalPrefixes = []string{"http://", "https://", "mailto:", "#"}

// runFrontmatter validates the KNOWLEDGE.md files: frontmatter schema, unique names, existing
// scope and sources paths, and resolvable body links. Names are unique over every document
// even when the run covers a few.
func runFrontmatter(sc *scope, out *report) error {
	paths, err := kdoc.IterFiles(sc.root)
	if err != nil {
		return err
	}
	relative := make([]string, len(paths))
	for i, path := range paths {
		rel, err := filepath.Rel(sc.root, path)
		if err != nil {
			return err
		}
		relative[i] = filepath.ToSlash(rel)
	}
	selected, err := sc.selected(relative)
	if err != nil {
		return err
	}
	inScope := map[string]bool{}
	for _, path := range selected {
		inScope[path] = true
	}
	names := map[string]string{}
	for _, path := range relative {
		for _, problem := range checkKnowledge(sc, path, names, inScope[path]) {
			out.fail(problem)
		}
	}
	return nil
}

func checkKnowledge(sc *scope, relPath string, names map[string]string, report bool) []string {
	root := sc.root
	full := filepath.Join(root, relPath)
	var raw kdoc.Raw
	var body []string
	data, err := sc.read(relPath)
	if err == nil {
		raw, body, err = kdoc.Parse(data)
	}
	if err != nil {
		if report {
			return []string{fmt.Sprintf("%s: %v", relPath, err)}
		}
		return nil
	}
	document, schema := kdoc.Build(raw)
	var problems []string
	for _, problem := range schema {
		problems = append(problems, fmt.Sprintf("%s: %s", relPath, problem))
	}
	if document != nil {
		if first, used := names[document.Name]; used {
			problems = append(problems, fmt.Sprintf("%s: name '%s' is already used by %s", relPath, document.Name, first))
		} else {
			names[document.Name] = relPath
		}
		if !exists(filepath.Join(root, document.Scope)) {
			problems = append(problems, fmt.Sprintf("%s: scope path does not exist: %s", relPath, document.Scope))
		}
		for _, source := range document.Sources {
			if !exists(filepath.Join(root, source)) {
				problems = append(problems, fmt.Sprintf("%s: sources path does not exist: %s", relPath, source))
			}
		}
	}
	for _, target := range bodyLinks(body) {
		resolved := filepath.Join(filepath.Dir(full), target)
		if strings.HasPrefix(target, "/") {
			resolved = filepath.Join(root, strings.TrimLeft(target, "/"))
		}
		if !exists(resolved) {
			problems = append(problems, fmt.Sprintf("%s: broken body link: %s", relPath, target))
		}
	}
	if !report {
		return nil
	}
	return problems
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func bodyLinks(body []string) []string {
	var prose []string
	fenced := false
	for _, line := range body {
		if strings.HasPrefix(strings.TrimLeft(line, " \t"), "```") {
			fenced = !fenced
			continue
		}
		if !fenced {
			prose = append(prose, line)
		}
	}
	var links []string
	for _, match := range linkPattern.FindAllStringSubmatch(strings.Join(prose, "\n"), -1) {
		target := match[1]
		external := false
		for _, prefix := range externalPrefixes {
			if strings.HasPrefix(target, prefix) {
				external = true
			}
		}
		if external {
			continue
		}
		path, _, _ := strings.Cut(target, "#")
		if path != "" {
			links = append(links, path)
		}
	}
	return links
}
