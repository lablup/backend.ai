package main

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"unicode/utf8"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
)

const (
	firstCheckedBEP      = 1080
	maxLines             = 300
	maxItems             = 7
	maxDesignSubsections = 4
	maxDesignTables      = 2
	maxTableRows         = 7
	maxDesignSentences   = 3
)

var (
	bepFile = regexp.MustCompile(`^BEP-(\d{4})-.+\.md$`)
	bepDir  = regexp.MustCompile(`^BEP-(\d{4})$`)

	maxItemChars = map[string]int{"ko": 80, "en": 120}

	goalTitles     = []string{"목표", "Goals"}
	countedLists   = []string{"목표가 아닌 것", "Non-goals", "영향", "Impact", "구현 순서", "Implementation Order"}
	designTitles   = []string{"설계", "Design"}
	rejectedPrefix = []string{"기각한 대안:", "Rejected:"}

	listItem     = regexp.MustCompile(`^(\s*)(?:[-*]|\d+\.) (.*)$`)
	tableRow     = regexp.MustCompile(`^\s*\|`)
	tableDivider = regexp.MustCompile(`^\s*\|[\s:|-]+\|\s*$`)
	imageLine    = regexp.MustCompile(`^\s*!\[`)
	sentenceEnd  = regexp.MustCompile(`[^\d\s.]\.(?:\s|$)`)
	abbreviation = regexp.MustCompile(`(?i)\b(?:e\.g|i\.e|etc|vs|cf)\.`)
)

type numberedLine struct {
	number int
	text   string
}

type section struct {
	title string
	line  int
	body  []numberedLine
}

// contentLines returns the lines outside frontmatter, code fences and HTML comments.
func contentLines(text string) []numberedLine {
	lines := kdoc.SplitLines(text)
	start := 0
	if len(lines) > 0 && lines[0] == "---" {
		if at := indexOf(lines[1:], "---"); at >= 0 {
			start = at + 2
		}
	}
	var result []numberedLine
	fenced, commented := false, false
	for i := start; i < len(lines); i++ {
		line := lines[i]
		if fence.MatchString(line) {
			fenced = !fenced
			continue
		}
		if fenced {
			continue
		}
		if commented || strings.HasPrefix(strings.TrimLeft(line, " \t"), "<!--") {
			commented = !strings.Contains(line, "-->")
			continue
		}
		result = append(result, numberedLine{i + 1, line})
	}
	return result
}

func sections(lines []numberedLine, level string) []section {
	var result []section
	for _, line := range lines {
		if strings.HasPrefix(line.text, level+" ") {
			result = append(result, section{title: strings.TrimSpace(line.text[len(level)+1:]), line: line.number})
		} else if len(result) > 0 {
			last := &result[len(result)-1]
			last.body = append(last.body, line)
		}
	}
	return result
}

type table struct {
	first int
	rows  int
}

func tables(body []numberedLine) []table {
	var result []table
	inTable := false
	for _, line := range body {
		if tableRow.MatchString(line.text) {
			if !inTable {
				result = append(result, table{first: line.number})
				inTable = true
			} else if !tableDivider.MatchString(line.text) {
				result[len(result)-1].rows++
			}
		} else {
			inTable = false
		}
	}
	return result
}

func topItems(body []numberedLine) int {
	count := 0
	for _, line := range body {
		if match := listItem.FindStringSubmatch(line.text); match != nil && match[1] == "" {
			count++
		}
	}
	return count
}

func checkBEPLength(data []byte, display string) []string {
	lang := "en"
	if strings.HasSuffix(display, koSuffix) {
		lang = "ko"
	}
	lines := contentLines(string(data))
	var problems []string
	if len(lines) > maxLines {
		problems = append(problems, fmt.Sprintf("%s:1: %d lines, limit %d", display, len(lines), maxLines))
	}
	for _, line := range lines {
		match := listItem.FindStringSubmatch(line.text)
		if match == nil {
			continue
		}
		if match[1] != "" {
			problems = append(problems, fmt.Sprintf("%s:%d: nested list item, keep lists one level", display, line.number))
		}
		if length := utf8.RuneCountInString(match[2]); length > maxItemChars[lang] {
			problems = append(problems, fmt.Sprintf("%s:%d: list item of %d chars, limit %d", display, line.number, length, maxItemChars[lang]))
		}
	}
	for _, sec := range sections(lines, "##") {
		switch {
		case indexOf(goalTitles, sec.title) >= 0:
			for _, tbl := range tables(sec.body) {
				if tbl.rows > maxItems {
					problems = append(problems, fmt.Sprintf("%s:%d: %d goal rows, limit %d", display, tbl.first, tbl.rows, maxItems))
				}
			}
		case indexOf(countedLists, sec.title) >= 0:
			if count := topItems(sec.body); count > maxItems {
				problems = append(problems, fmt.Sprintf("%s:%d: %d items in '%s', limit %d", display, sec.line, count, sec.title, maxItems))
			}
		case indexOf(designTitles, sec.title) >= 0:
			problems = append(problems, checkDesign(sec, display)...)
		}
	}
	return problems
}

func checkDesign(sec section, display string) []string {
	var problems []string
	subsections := sections(sec.body, "###")
	if len(subsections) > maxDesignSubsections {
		problems = append(problems, fmt.Sprintf("%s:%d: %d design subsections, limit %d", display, sec.line, len(subsections), maxDesignSubsections))
	}
	var lead []numberedLine
	for _, line := range sec.body {
		if len(subsections) == 0 || line.number < subsections[0].line {
			lead = append(lead, line)
		}
	}
	units := append([]section{{title: sec.title, line: sec.line, body: lead}}, subsections...)
	for _, unit := range units {
		problems = append(problems, checkDesignUnit(unit, display)...)
	}
	return problems
}

// checkDesignUnit checks the table and sentence limits of a design subsection, or of the text
// before the first one.
func checkDesignUnit(unit section, display string) []string {
	var problems []string
	found := tables(unit.body)
	if len(found) > maxDesignTables {
		problems = append(problems, fmt.Sprintf("%s:%d: %d tables, limit %d", display, unit.line, len(found), maxDesignTables))
	}
	for _, tbl := range found {
		if tbl.rows > maxTableRows {
			problems = append(problems, fmt.Sprintf("%s:%d: %d table rows, limit %d", display, tbl.first, tbl.rows, maxTableRows))
		}
	}
	sentences := 0
	for _, line := range unit.body {
		text := strings.TrimSpace(line.text)
		if text == "" || tableRow.MatchString(line.text) || imageLine.MatchString(line.text) {
			continue
		}
		if hasAnyPrefix(text, rejectedPrefix) {
			continue
		}
		count := len(sentenceEnd.FindAllString(abbreviation.ReplaceAllString(line.text, ""), -1))
		if listItem.MatchString(line.text) {
			count = max(count, 1)
		}
		sentences += count
	}
	if sentences > maxDesignSentences {
		problems = append(problems, fmt.Sprintf("%s:%d: %d sentences in '%s', limit %d", display, unit.line, sentences, unit.title, maxDesignSentences))
	}
	return problems
}

func hasAnyPrefix(text string, prefixes []string) bool {
	for _, prefix := range prefixes {
		if strings.HasPrefix(text, prefix) {
			return true
		}
	}
	return false
}

// bepPaths returns the BEP documents from BEP-1080 on: proposals/BEP-<number>-*.md and the
// .md files in proposals/BEP-<number>/.
func bepPaths(root string) ([]string, error) {
	entries, err := os.ReadDir(filepath.Join(root, "proposals"))
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var paths []string
	for _, entry := range entries {
		if entry.IsDir() {
			match := bepDir.FindStringSubmatch(entry.Name())
			if match == nil || bepNumber(match[1]) < firstCheckedBEP {
				continue
			}
			sub, err := filepath.Glob(filepath.Join(root, "proposals", entry.Name(), "*.md"))
			if err != nil {
				return nil, err
			}
			sort.Strings(sub)
			for _, path := range sub {
				rel, _ := filepath.Rel(root, path)
				paths = append(paths, filepath.ToSlash(rel))
			}
		} else if match := bepFile.FindStringSubmatch(entry.Name()); match != nil && bepNumber(match[1]) >= firstCheckedBEP {
			paths = append(paths, "proposals/"+entry.Name())
		}
	}
	return paths, nil
}

func bepNumber(text string) int {
	number, _ := strconv.Atoi(text)
	return number
}

func runBEPLength(sc *scope, out *report) error {
	candidates, err := bepPaths(sc.root)
	if err != nil {
		return err
	}
	paths, err := sc.selected(candidates)
	if err != nil {
		return err
	}
	for _, path := range paths {
		data, err := sc.read(path)
		if err != nil {
			return err
		}
		for _, problem := range checkBEPLength(data, path) {
			out.fail(problem)
		}
	}
	return nil
}
