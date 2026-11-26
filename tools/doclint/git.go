package main

import (
	"bytes"
	"fmt"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
)

var (
	hunkPattern     = regexp.MustCompile(`^@@ -\S+ \+(\d+)(?:,(\d+))? @@`)
	diffFilePattern = regexp.MustCompile(`^\+\+\+ b/(.+)$`)
)

func git(root string, args ...string) (string, error) {
	cmd := exec.Command("git", append([]string{"-C", root, "-c", "core.quotePath=false"}, args...)...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("git %s: %w: %s", strings.Join(args, " "), err, strings.TrimSpace(stderr.String()))
	}
	return stdout.String(), nil
}

func gitLines(root string, args ...string) ([]string, error) {
	out, err := git(root, args...)
	if err != nil {
		return nil, err
	}
	var lines []string
	for _, line := range strings.Split(out, "\n") {
		if line != "" {
			lines = append(lines, line)
		}
	}
	return lines, nil
}

// changedFiles returns the changed documents, without the deleted ones.
func changedFiles(sc *scope) ([]string, error) {
	return gitLines(sc.root, "diff", "--name-only", "--diff-filter=d", sc.diffRange(), "--", sc.pathspec(sc.spec.Documents.Extension))
}

// addedLines returns the line numbers added to each changed document.
func addedLines(sc *scope) (map[string]map[int]bool, error) {
	diff, err := git(sc.root, "diff", "--unified=0", "--no-color", "--diff-filter=d", sc.diffRange(),
		"--", sc.pathspec(sc.spec.Documents.Extension))
	if err != nil {
		return nil, err
	}
	added := map[string]map[int]bool{}
	current := ""
	for _, line := range strings.Split(diff, "\n") {
		if match := diffFilePattern.FindStringSubmatch(line); match != nil {
			current = match[1]
		} else if match := hunkPattern.FindStringSubmatch(line); match != nil {
			first, _ := strconv.Atoi(match[1])
			count := 1
			if match[2] != "" {
				count, _ = strconv.Atoi(match[2])
			}
			if added[current] == nil {
				added[current] = map[int]bool{}
			}
			for n := first; n < first+count; n++ {
				added[current][n] = true
			}
		}
	}
	return added, nil
}
