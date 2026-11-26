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

// runFrontmatter validates the knowledge documents: frontmatter schema, unique values,
// existing paths and resolvable body links. Values are unique over every document even when
// the run covers a few.
func runFrontmatter(sc *scope, out *report) error {
	paths, err := kdoc.IterFiles(sc.root, &sc.spec.Knowledge)
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
	used := map[string]string{}
	for _, path := range relative {
		for _, problem := range checkKnowledge(sc, path, used, inScope[path]) {
			out.fail(problem)
		}
	}
	return nil
}

func checkKnowledge(sc *scope, relPath string, used map[string]string, report bool) []string {
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
	document, violations := kdoc.Build(&sc.spec.Knowledge, raw)
	var problems []string
	for _, problem := range violations {
		problems = append(problems, fmt.Sprintf("%s: %s", relPath, problem))
	}
	if document != nil {
		for _, problem := range checkEnvironment(sc, relPath, document, used) {
			problems = append(problems, fmt.Sprintf("%s: %s", relPath, problem))
		}
	}
	for _, target := range bodyLinks(body, sc.spec.Knowledge.ExternalLinkPrefixes) {
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

// checkEnvironment checks the unique values, against those of the documents before, and the
// existence of the paths.
func checkEnvironment(sc *scope, relPath string, document kdoc.Document, used map[string]string) []string {
	var problems []string
	for _, field := range sc.spec.Knowledge.Fields {
		if value := document.Text(field.Name); field.Unique && value != "" {
			key := field.Name + "\x00" + value
			if first, ok := used[key]; ok {
				problems = append(problems, fmt.Sprintf("%s '%s' is already used by %s", field.Name, value, first))
			} else {
				used[key] = relPath
			}
		}
		if !field.Path {
			continue
		}
		for _, path := range document.Texts(field.Name) {
			if !exists(filepath.Join(sc.root, path)) {
				problems = append(problems, fmt.Sprintf("%s path does not exist: %s", field.Name, path))
			}
		}
	}
	return problems
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func bodyLinks(body, externalPrefixes []string) []string {
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
