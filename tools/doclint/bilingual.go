package main

import (
	"fmt"
	"regexp"
	"sort"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
)

var (
	hangulAny    = regexp.MustCompile(`[\x{1100}-\x{11ff}\x{3130}-\x{318f}\x{ac00}-\x{d7a3}]`)
	headingStart = regexp.MustCompile(`^(#{1,6}) `)
)

// oneSideChangeAllowed is the glossary: a wording fix can change only one language.
const oneSideChangeAllowed = "glossary/"

func englishPath(koPath string) string {
	return strings.TrimSuffix(koPath, koSuffix) + ".md"
}

func headingCounts(sc *scope, path string) (map[int]int, error) {
	data, err := sc.read(path)
	if err != nil {
		return nil, err
	}
	lines := kdoc.SplitLines(string(data))
	if len(lines) > 0 && lines[0] == "---" {
		if at := indexOf(lines[1:], "---"); at >= 0 {
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

// checkPairs validates the .ko.md files: an English file beside each, with the same number of
// headings at each level. A restricted run checks the pairs with a file among the changed.
func checkPairs(sc *scope, changed map[string]bool) ([]string, error) {
	koFiles, err := sc.listFiles("*" + koSuffix)
	if err != nil {
		return nil, err
	}
	var problems []string
	for _, koPath := range koFiles {
		enPath := englishPath(koPath)
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

// checkAddedKorean rejects Korean added to a .md file.
func checkAddedKorean(sc *scope) ([]string, error) {
	diff, err := git(sc.root, "diff", "--unified=0", "--no-color", sc.diffRange(), "--", "*.md")
	if err != nil {
		return nil, err
	}
	var problems []string
	current := ""
	for _, line := range strings.Split(diff, "\n") {
		if match := diffFilePattern.FindStringSubmatch(line); match != nil {
			current = match[1]
		} else if strings.HasPrefix(line, "+") && !strings.HasPrefix(line, "+++") &&
			!strings.HasSuffix(current, koSuffix) && hangulAny.MatchString(line) {
			problems = append(problems, fmt.Sprintf("%s: Korean added, move it to the .ko.md file: %s",
				current, strings.TrimSpace(line[1:])))
		}
	}
	return problems, nil
}

// checkPairUpdates requires both files of a pair to change together. A newly added .ko.md is
// exempt, since it translates an English file that does not change.
func checkPairUpdates(sc *scope) ([]string, error) {
	changedList, err := gitLines(sc.root, "diff", "--name-only", sc.diffRange(), "--", "*.md")
	if err != nil {
		return nil, err
	}
	addedList, err := gitLines(sc.root, "diff", "--name-only", "--diff-filter=A", sc.diffRange(), "--", "*.md")
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
		if strings.HasPrefix(path, oneSideChangeAllowed) {
			continue
		}
		var partner string
		if strings.HasSuffix(path, koSuffix) {
			if added[path] {
				continue
			}
			partner = englishPath(path)
		} else {
			partner = strings.TrimSuffix(path, ".md") + koSuffix
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
