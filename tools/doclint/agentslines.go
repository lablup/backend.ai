package main

import (
	"fmt"
	"os"
	"path"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
)

const (
	agentsFile     = "AGENTS.md"
	maxAgentsLines = 200
)

func checkAgentsLines(root, rel string) (string, error) {
	data, err := os.ReadFile(resolve(root, rel))
	if err != nil {
		return "", err
	}
	if count := len(kdoc.SplitLines(string(data))); count > maxAgentsLines {
		return fmt.Sprintf("%s:1: %d lines, limit %d", rel, count, maxAgentsLines), nil
	}
	return "", nil
}

func runAgentsLines(sc *scope, out *report) error {
	all, err := sc.allMarkdown()
	if err != nil {
		return err
	}
	var candidates []string
	for _, rel := range all {
		if path.Base(rel) == agentsFile {
			candidates = append(candidates, rel)
		}
	}
	selected, err := sc.selected(candidates)
	if err != nil {
		return err
	}
	for _, rel := range selected {
		problem, err := checkAgentsLines(sc.root, rel)
		if err != nil {
			return err
		}
		if problem != "" {
			out.fail(problem)
		}
	}
	return nil
}
