package main

import (
	"fmt"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"unicode/utf8"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
	"github.com/lablup/backend.ai/tools/internal/spec"
)

var (
	listItem     = regexp.MustCompile(`^(\s*)(?:[-*]|\d+\.) (.*)$`)
	tableRow     = regexp.MustCompile(`^\s*\|`)
	tableDivider = regexp.MustCompile(`^\s*\|[\s:|-]+\|\s*$`)
	imageLine    = regexp.MustCompile(`^\s*!\[`)
	sentenceEnd  = regexp.MustCompile(`[^\d\s.]\.(?:\s|$)`)
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
		if at := slices.Index(lines[1:], "---"); at >= 0 {
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

// bepChecker checks proposals against the limits of the spec.
type bepChecker struct {
	limits       spec.BEP
	translation  string
	abbreviation *regexp.Regexp
}

func newBEPChecker(loaded *spec.Spec) bepChecker {
	quoted := make([]string, len(loaded.BEP.Design.Abbreviations))
	for i, word := range loaded.BEP.Design.Abbreviations {
		quoted[i] = regexp.QuoteMeta(word)
	}
	return bepChecker{
		limits:       loaded.BEP,
		translation:  loaded.Documents.TranslationSuffix,
		abbreviation: regexp.MustCompile(`(?i)\b(?:` + strings.Join(quoted, "|") + `)\.`),
	}
}

func (c bepChecker) check(data []byte, display string) []string {
	lang := spec.English
	if strings.HasSuffix(display, c.translation) {
		lang = spec.Korean
	}
	lines := contentLines(string(data))
	var problems []string
	if limit := c.limits.MaxLines; len(lines) > limit {
		problems = append(problems, fmt.Sprintf("%s:1: %d lines, limit %d", display, len(lines), limit))
	}
	for _, line := range lines {
		match := listItem.FindStringSubmatch(line.text)
		if match == nil {
			continue
		}
		if match[1] != "" {
			problems = append(problems, fmt.Sprintf("%s:%d: nested list item, keep lists one level", display, line.number))
		}
		if length, limit := utf8.RuneCountInString(match[2]), c.limits.MaxItemChars[lang]; length > limit {
			problems = append(problems, fmt.Sprintf("%s:%d: list item of %d chars, limit %d", display, line.number, length, limit))
		}
	}
	limit := c.limits.MaxItems
	for _, sec := range sections(lines, "##") {
		switch {
		case slices.Contains(c.limits.GoalSections, sec.title):
			for _, tbl := range tables(sec.body) {
				if tbl.rows > limit {
					problems = append(problems, fmt.Sprintf("%s:%d: %d goal rows, limit %d", display, tbl.first, tbl.rows, limit))
				}
			}
		case slices.Contains(c.limits.CountedSections, sec.title):
			if count := topItems(sec.body); count > limit {
				problems = append(problems, fmt.Sprintf("%s:%d: %d items in '%s', limit %d", display, sec.line, count, sec.title, limit))
			}
		case slices.Contains(c.limits.Design.Sections, sec.title):
			problems = append(problems, c.design(sec, display)...)
		}
	}
	return problems
}

func (c bepChecker) design(sec section, display string) []string {
	var problems []string
	subsections := sections(sec.body, "###")
	if limit := c.limits.Design.MaxSubsections; len(subsections) > limit {
		problems = append(problems, fmt.Sprintf("%s:%d: %d design subsections, limit %d", display, sec.line, len(subsections), limit))
	}
	var lead []numberedLine
	for _, line := range sec.body {
		if len(subsections) == 0 || line.number < subsections[0].line {
			lead = append(lead, line)
		}
	}
	units := append([]section{{title: sec.title, line: sec.line, body: lead}}, subsections...)
	for _, unit := range units {
		problems = append(problems, c.designUnit(unit, display)...)
	}
	return problems
}

// designUnit checks the table and sentence limits of a design subsection, or of the text
// before the first one.
func (c bepChecker) designUnit(unit section, display string) []string {
	limits := c.limits.Design
	var problems []string
	found := tables(unit.body)
	if len(found) > limits.MaxTables {
		problems = append(problems, fmt.Sprintf("%s:%d: %d tables, limit %d", display, unit.line, len(found), limits.MaxTables))
	}
	for _, tbl := range found {
		if tbl.rows > limits.MaxTableRows {
			problems = append(problems, fmt.Sprintf("%s:%d: %d table rows, limit %d", display, tbl.first, tbl.rows, limits.MaxTableRows))
		}
	}
	sentences := 0
	for _, line := range unit.body {
		text := strings.TrimSpace(line.text)
		if text == "" || tableRow.MatchString(line.text) || imageLine.MatchString(line.text) {
			continue
		}
		if hasAnyPrefix(text, limits.SkippedLinePrefixes) {
			continue
		}
		count := len(sentenceEnd.FindAllString(c.abbreviation.ReplaceAllString(line.text, ""), -1))
		if listItem.MatchString(line.text) {
			count = max(count, 1)
		}
		sentences += count
	}
	if sentences > limits.MaxSentences {
		problems = append(problems, fmt.Sprintf("%s:%d: %d sentences in '%s', limit %d", display, unit.line, sentences, unit.title, limits.MaxSentences))
	}
	return problems
}

func hasAnyPrefix(text string, prefixes []string) bool {
	return slices.ContainsFunc(prefixes, func(prefix string) bool { return strings.HasPrefix(text, prefix) })
}

// bepPaths returns the documents of the proposals the limits apply to.
func bepPaths(sc *scope) ([]string, error) {
	all, err := sc.allDocuments()
	if err != nil {
		return nil, err
	}
	var paths []string
	for _, path := range all {
		match := sc.spec.BEP.Path.FindStringSubmatch(path)
		if match == nil {
			continue
		}
		if number, err := strconv.Atoi(match[1]); err == nil && number >= sc.spec.BEP.FirstNumber {
			paths = append(paths, path)
		}
	}
	return paths, nil
}

func runBEPLength(sc *scope, out *report) error {
	candidates, err := bepPaths(sc)
	if err != nil {
		return err
	}
	paths, err := sc.selected(candidates)
	if err != nil {
		return err
	}
	checker := newBEPChecker(sc.spec)
	for _, path := range paths {
		data, err := sc.read(path)
		if err != nil {
			return err
		}
		for _, problem := range checker.check(data, path) {
			out.fail(problem)
		}
	}
	return nil
}
