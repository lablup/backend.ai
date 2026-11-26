package main

import (
	"fmt"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
)

func checkAgentsLines(sc *scope, rel string) (string, error) {
	data, err := sc.read(rel)
	if err != nil {
		return "", err
	}
	if limit, count := sc.spec.Agents.MaxLines, len(kdoc.SplitLines(string(data))); count > limit {
		return fmt.Sprintf("%s:1: %d lines, limit %d", rel, count, limit), nil
	}
	return "", nil
}

func runAgentsLines(sc *scope, out *report) error {
	all, err := sc.allDocuments()
	if err != nil {
		return err
	}
	var candidates []string
	for _, rel := range all {
		if sc.spec.Agents.Path.MatchString(rel) {
			candidates = append(candidates, rel)
		}
	}
	selected, err := sc.selected(candidates)
	if err != nil {
		return err
	}
	for _, rel := range selected {
		problem, err := checkAgentsLines(sc, rel)
		if err != nil {
			return err
		}
		if problem != "" {
			out.fail(problem)
		}
	}
	return nil
}
