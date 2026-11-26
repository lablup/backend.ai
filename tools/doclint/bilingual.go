package main

import (
	"fmt"
	"regexp"
	"slices"
	"sort"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
	"github.com/lablup/backend.ai/tools/internal/spec"
)

var headingStart = regexp.MustCompile(`^(#{1,6}) `)

func englishPath(sc *scope, koPath string) string {
	return strings.TrimSuffix(koPath, sc.spec.Documents.TranslationSuffix) + sc.spec.Documents.Extension
}

func headingCounts(sc *scope, path string) (map[int]int, error) {
	data, err := sc.read(path)
	if err != nil {
		return nil, err
	}
	lines := kdoc.SplitLines(string(data))
	if len(lines) > 0 && lines[0] == "---" {
		if at := slices.Index(lines[1:], "---"); at >= 0 {
			lines = lines[at+2:]
		}
	}
	counts := map[int]int{}
	fenced := false
	for _, line := range lines {
		if fence.MatchString(line) {
			fenced = !fenced
		} else if !fenced {
			if match := headingStart.FindStringSubmatch(line); match != nil {
				counts[len(match[1])]++
			}
		}
	}
	return counts, nil
}

func formatCounts(counts map[int]int) string {
	levels := make([]int, 0, len(counts))
	for level := range counts {
		levels = append(levels, level)
	}
	sort.Ints(levels)
	parts := make([]string, len(levels))
	for i, level := range levels {
		parts[i] = fmt.Sprintf("(%d, %d)", level, counts[level])
	}
	return "[" + strings.Join(parts, ", ") + "]"
}

func sameCounts(a, b map[int]int) bool {
	if len(a) != len(b) {
		return false
	}
	for level, count := range a {
		if b[level] != count {
			return false
		}
	}
	return true
}

// checkPairs validates the translations: an English file beside each, with the same number of
// headings at each level. A restricted run checks the pairs with a file among the changed.
func checkPairs(sc *scope, changed map[string]bool) ([]string, error) {
	koFiles, err := sc.listFiles(sc.pathspec(sc.spec.Documents.TranslationSuffix))
	if err != nil {
		return nil, err
	}
	var problems []string
	for _, koPath := range koFiles {
		enPath := englishPath(sc, koPath)
		if sc.restricted() && !changed[koPath] && !changed[enPath] {
			continue
		}
		if !sc.has(enPath) {
			problems = append(problems, fmt.Sprintf("%s: %s is missing", koPath, enPath))
			continue
		}
		koCounts, err := headingCounts(sc, koPath)
		if err != nil {
			return nil, err
		}
		enCounts, err := headingCounts(sc, enPath)
		if err != nil {
			return nil, err
		}
		if !sameCounts(koCounts, enCounts) {
			problems = append(problems, fmt.Sprintf("%s: headings differ from %s: %s and %s",
				koPath, enPath, formatCounts(koCounts), formatCounts(enCounts)))
		}
	}
	return problems, nil
}

// checkAddedKorean rejects Korean added to a document that is not a translation.
func checkAddedKorean(sc *scope) ([]string, error) {
	diff, err := git(sc.root, "diff", "--unified=0", "--no-color", sc.diffRange(),
		"--", sc.pathspec(sc.spec.Documents.Extension))
	suffix := sc.spec.Documents.TranslationSuffix
	if err != nil {
		return nil, err
	}
	var problems []string
	current := ""
	for _, line := range strings.Split(diff, "\n") {
		if match := diffFilePattern.FindStringSubmatch(line); match != nil {
			current = match[1]
		} else if strings.HasPrefix(line, "+") && !strings.HasPrefix(line, "+++") &&
			!strings.HasSuffix(current, suffix) && sc.spec.Pairs.TranslationCharacters.MatchString(line) {
			problems = append(problems, fmt.Sprintf("%s: Korean added, move it to the %s file: %s",
				current, suffix, strings.TrimSpace(line[1:])))
		}
	}
	return problems, nil
}

// checkPairUpdates requires both files of a pair to change together. A newly added .ko.md is
// exempt, since it translates an English file that does not change.
func checkPairUpdates(sc *scope) ([]string, error) {
	pathspec := sc.pathspec(sc.spec.Documents.Extension)
	changedList, err := gitLines(sc.root, "diff", "--name-only", sc.diffRange(), "--", pathspec)
	if err != nil {
		return nil, err
	}
	addedList, err := gitLines(sc.root, "diff", "--name-only", "--diff-filter=A", sc.diffRange(), "--", pathspec)
	if err != nil {
		return nil, err
	}
	changed := map[string]bool{}
	for _, path := range changedList {
		changed[path] = true
	}
	added := map[string]bool{}
	for _, path := range addedList {
		added[path] = true
	}
	sort.Strings(changedList)
	var problems []string
	for _, path := range changedList {
		if matchesAny(sc.spec.Pairs.OneSideChangeAllowed, path) {
			continue
		}
		var partner string
		if strings.HasSuffix(path, sc.spec.Documents.TranslationSuffix) {
			if added[path] {
				continue
			}
			partner = englishPath(sc, path)
		} else {
			partner = strings.TrimSuffix(path, sc.spec.Documents.Extension) + sc.spec.Documents.TranslationSuffix
			if !sc.has(partner) {
				continue
			}
		}
		if !changed[partner] {
			problems = append(problems, fmt.Sprintf("%s: changed without %s", path, partner))
		}
	}
	return problems, nil
}

func matchesAny(patterns []spec.Pattern, text string) bool {
	return slices.ContainsFunc(patterns, func(p spec.Pattern) bool { return p.MatchString(text) })
}

func runBilingual(sc *scope, out *report) error {
	changed, err := sc.changedSet()
	if err != nil {
		return err
	}
	problems, err := checkPairs(sc, changed)
	if err != nil {
		return err
	}
	if sc.diffing() {
		added, err := checkAddedKorean(sc)
		if err != nil {
			return err
		}
		updates, err := checkPairUpdates(sc)
		if err != nil {
			return err
		}
		problems = append(problems, added...)
		problems = append(problems, updates...)
	}
	for _, problem := range problems {
		out.fail(problem)
	}
	return nil
}
