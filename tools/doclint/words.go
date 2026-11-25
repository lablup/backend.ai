package main

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"unicode/utf8"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
)

const (
	koSuffix  = ".ko.md"
	hangul    = "가-힣"
	particles = "은는이가을를의에도로와과만"

	syllableBase = 0xAC00
	vowelCount   = 21
	finalCount   = 28
	finalN       = 4
	finalL       = 8
	finalB       = 17
	finalSS      = 20

	consonantEndings = "다고지는면며기게던니시겠"
	vowelEndings     = "아어았었은을습"

	// beforeWord and afterWord stand for the lookarounds of the Python version, which RE2 lacks.
	// They consume a character, which does not matter when only a match is looked for.
	wordBoundaryBefore = `(?:^|[^\p{L}\p{N}_-])`
	wordBoundaryAfter  = `(?:$|[^\p{L}\p{N}_-])`
	hangulBefore       = `(?:^|[^` + hangul + `])`
	hangulAfter        = `(?:$|[^` + hangul + `])`
	space              = `[\s\p{Z}]`
)

var (
	expressionHeaders = []string{"사용하지 않는 표현", "Do not write"}
	termHeaders       = []string{"사용하지 않는 어휘", "Do not write"}
	skippedNames      = []string{"report.md", "report.ko.md", "GLOSSARY.md", "GLOSSARY.ko.md", "CHANGELOG.md"}
	skippedParts      = []string{"glossary", "CHANGELOG"}

	qualifier  = regexp.MustCompile(`\s*\([^)]*\)\s*$`)
	fence      = regexp.MustCompile("^\\s*(```|~~~)")
	codeSpan   = regexp.MustCompile("`[^`]*`")
	hangulText = regexp.MustCompile("[" + hangul + "]")
	altSplit   = regexp.MustCompile(`\s*/\s*|,\s+`)
	commaSplit = regexp.MustCompile(`,\s+`)

	// The vowel index of the stem to the vowel index after adding 아/어.
	contractedVowels = map[int]int{18: 4, 20: 6, 13: 14, 8: 9}
)

type word struct {
	text        string
	replacement string
	pattern     *regexp.Regexp
	advisory    bool
}

func floorDiv(a, b int) int {
	q := a / b
	if a%b != 0 && (a < 0) != (b < 0) {
		q--
	}
	return q
}

func floorMod(a, b int) int {
	return a - floorDiv(a, b)*b
}

func withFinal(syllable rune, final int) rune {
	return syllable + rune(final)
}

func split(syllable rune) (initial, vowel, final int) {
	offset := int(syllable) - syllableBase
	return floorDiv(offset, vowelCount*finalCount), floorMod(floorDiv(offset, finalCount), vowelCount), floorMod(offset, finalCount)
}

func join(initial, vowel, final int) rune {
	return rune(syllableBase + (initial*vowelCount+vowel)*finalCount + final)
}

// verbForms returns the regex alternatives of the inflected forms of a verb stem.
func verbForms(stem string) []string {
	runes := []rune(stem)
	head, last := string(runes[:len(runes)-1]), runes[len(runes)-1]
	initial, vowel, final := split(last)
	consonant := fmt.Sprintf("%s[%s]", stem, consonantEndings)
	if final == finalL {
		dropped := head + string(join(initial, vowel, 0))
		return []string{
			consonant,
			fmt.Sprintf("%s[%s]", stem, vowelEndings),
			fmt.Sprintf("%s[는니]", dropped),
			head + string(withFinal(join(initial, vowel, 0), finalN)),
		}
	}
	if final != 0 {
		return []string{consonant, fmt.Sprintf("%s[%s]", stem, vowelEndings)}
	}
	forms := []string{
		consonant,
		head + string(withFinal(last, finalN)),
		head + string(withFinal(last, finalL)),
		head + string(withFinal(last, finalB)),
	}
	var contracted rune
	switch {
	case last == '하':
		contracted = '해'
	case last == '르' && head != "":
		headRunes := []rune(head)
		priorInitial, priorVowel, _ := split(headRunes[len(headRunes)-1])
		return append(forms, string(headRunes[:len(headRunes)-1])+string(join(priorInitial, priorVowel, finalL))+"[러라렀랐]")
	default:
		replaced, ok := contractedVowels[vowel]
		if !ok {
			replaced = vowel
		}
		contracted = join(initial, replaced, 0)
	}
	return append(forms, head+string(contracted), head+string(withFinal(contracted, finalSS)))
}

func koreanPattern(text string) (string, error) {
	clean := strings.TrimSpace(strings.ReplaceAll(text, "~", " "))
	tokens := strings.Fields(clean)
	if len(tokens) == 0 {
		return "", fmt.Errorf("empty word %q", text)
	}
	last := tokens[len(tokens)-1]
	quoted := func(items []string, sep string) string {
		parts := make([]string, len(items))
		for i, item := range items {
			parts[i] = regexp.QuoteMeta(item)
		}
		return strings.Join(parts, sep)
	}
	prefix := quoted(tokens[:len(tokens)-1], space+"+")
	if len(tokens) > 1 && strings.Contains(text, "~") && strings.Index(text, "~") > 0 {
		prefix = regexp.QuoteMeta(tokens[0]) + space + "+.*?" + quoted(tokens[1:len(tokens)-1], space+"*")
	}
	var ending string
	if strings.HasSuffix(last, "다") && utf8.RuneCountInString(last) > 1 {
		ending = "(?:" + strings.Join(verbForms(strings.TrimSuffix(last, "다")), "|") + ")"
	} else {
		quotedLast := regexp.QuoteMeta(last)
		ending = "(?:" + quotedLast + "(?:[" + particles + "]|으로|이다|입니다)" + hangulAfter +
			"|" + quotedLast + hangulAfter + ")"
	}
	body := ending
	if prefix != "" {
		body = prefix + space + "+" + ending
	}
	if strings.HasPrefix(text, "~") {
		return body, nil
	}
	return hangulBefore + body, nil
}

func englishPattern(text string) string {
	fields := strings.Fields(text)
	for i, field := range fields {
		fields[i] = regexp.QuoteMeta(field)
	}
	words := strings.Join(fields, space+"+")
	return wordBoundaryBefore + words + "(?:s|es|d|ed|ing)?" + wordBoundaryAfter
}

func newWord(text, replacement string, advisory bool) (word, error) {
	var source string
	if hangulText.MatchString(text) {
		var err error
		if source, err = koreanPattern(text); err != nil {
			return word{}, err
		}
	} else {
		source = englishPattern(text)
	}
	pattern, err := regexp.Compile(source)
	if err != nil {
		return word{}, fmt.Errorf("word %q: %w", text, err)
	}
	return word{text: text, replacement: replacement, pattern: pattern, advisory: advisory}, nil
}

// alternatives splits a cell, carrying a shared leading word into the alternatives after it.
func alternatives(cell string) []string {
	var parts []string
	for _, part := range altSplit.Split(cell, -1) {
		if part = strings.TrimSpace(part); part != "" {
			parts = append(parts, part)
		}
	}
	if len(parts) == 0 {
		return nil
	}
	fields := strings.Fields(parts[0])
	leading := fields[:len(fields)-1]
	result := []string{parts[0]}
	for _, part := range parts[1:] {
		if len(leading) > 0 && len(strings.Fields(part)) == 1 && strings.HasSuffix(part, "다") {
			part = strings.Join(append(append([]string{}, leading...), part), " ")
		}
		result = append(result, part)
	}
	return result
}

func tableRows(path string) ([][]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var rows [][]string
	for _, line := range kdoc.SplitLines(string(data)) {
		if strings.HasPrefix(line, "|") && !strings.HasPrefix(line, "|---") {
			cells := strings.Split(strings.Trim(strings.TrimSpace(line), "|"), "|")
			for i := range cells {
				cells[i] = strings.TrimSpace(cells[i])
			}
			rows = append(rows, cells)
		}
	}
	return rows, nil
}

func indexOf(values []string, value string) int {
	for i, candidate := range values {
		if candidate == value {
			return i
		}
	}
	return -1
}

func expressions(path string) ([]word, error) {
	rows, err := tableRows(path)
	if err != nil {
		return nil, err
	}
	var words []word
	inTable := false
	for _, row := range rows {
		if indexOf(expressionHeaders, row[0]) >= 0 && len(row) == 2 {
			inTable = true
			continue
		}
		if !inTable || len(row) != 2 {
			inTable = false
			continue
		}
		cell, replacement := row[0], row[1]
		advisory := qualifier.MatchString(cell)
		for _, text := range alternatives(qualifier.ReplaceAllString(cell, "")) {
			if !strings.Contains(strings.ToLower(replacement), strings.ToLower(text)) {
				built, err := newWord(text, replacement, advisory)
				if err != nil {
					return nil, err
				}
				words = append(words, built)
			}
		}
	}
	return words, nil
}

func terms(path string) ([]word, error) {
	rows, err := tableRows(path)
	if err != nil {
		return nil, err
	}
	headerAt := -1
	for i, row := range rows {
		if indexOf(row, termHeaders[0]) >= 0 || indexOf(row, termHeaders[1]) >= 0 {
			headerAt = i
			break
		}
	}
	if headerAt < 0 {
		return nil, nil
	}
	header := rows[headerAt]
	variantAt := indexOf(header, termHeaders[0])
	if variantAt < 0 {
		variantAt = indexOf(header, termHeaders[1])
	}
	var words []word
	for i, row := range rows {
		if i == headerAt || len(row) != len(header) {
			continue
		}
		term := row[0]
		for _, text := range commaSplit.Split(row[variantAt], -1) {
			if text != "" && !strings.EqualFold(text, term) {
				built, err := newWord(text, term, true)
				if err != nil {
					return nil, err
				}
				words = append(words, built)
			}
		}
	}
	return words, nil
}

// loadWords returns the rejected words of the English documents and of the Korean documents.
func loadWords(root string) (english, korean []word, err error) {
	if english, err = expressions(filepath.Join(root, "GLOSSARY.md")); err != nil {
		return nil, nil, err
	}
	if korean, err = expressions(filepath.Join(root, "GLOSSARY.ko.md")); err != nil {
		return nil, nil, err
	}
	paths, err := filepath.Glob(filepath.Join(root, "glossary", "*.md"))
	if err != nil {
		return nil, nil, err
	}
	sort.Strings(paths)
	for _, path := range paths {
		found, err := terms(path)
		if err != nil {
			return nil, nil, err
		}
		if strings.HasSuffix(path, koSuffix) {
			korean = append(korean, found...)
		} else {
			english = append(english, found...)
		}
	}
	return english, korean, nil
}

func isSkipped(path string) bool {
	parts := strings.Split(path, "/")
	if indexOf(skippedNames, parts[len(parts)-1]) >= 0 {
		return true
	}
	for _, part := range parts {
		if indexOf(skippedParts, part) >= 0 {
			return true
		}
	}
	return false
}

// proseLines returns line number to text, without frontmatter, fenced blocks and code spans.
func proseLines(text string) map[int]string {
	lines := kdoc.SplitLines(text)
	start := 0
	if len(lines) > 0 && lines[0] == "---" {
		if at := indexOf(lines[1:], "---"); at >= 0 {
			start = at + 2
		}
	}
	prose := map[int]string{}
	fenced := false
	for i := start; i < len(lines); i++ {
		if fence.MatchString(lines[i]) {
			fenced = !fenced
		} else if !fenced {
			prose[i+1] = codeSpan.ReplaceAllString(lines[i], " ")
		}
	}
	return prose
}

// checkWords returns the failures and the review lines of one file. numbers limits the lines.
func checkWords(root, path string, numbers map[int]bool, english, korean []word) (problems, reviews []string, err error) {
	words := english
	if strings.HasSuffix(path, koSuffix) {
		words = korean
	}
	data, err := os.ReadFile(resolve(root, path))
	if err != nil {
		return nil, nil, err
	}
	prose := proseLines(string(data))
	numbersSorted := make([]int, 0, len(prose))
	for number := range prose {
		numbersSorted = append(numbersSorted, number)
	}
	sort.Ints(numbersSorted)
	for _, number := range numbersSorted {
		if numbers != nil && !numbers[number] {
			continue
		}
		line := prose[number]
		for _, w := range words {
			if w.pattern.MatchString(line) {
				message := fmt.Sprintf("%s:%d: %s -> %s: %s", path, number, w.text, w.replacement, strings.TrimSpace(line))
				if w.advisory {
					reviews = append(reviews, message)
				} else {
					problems = append(problems, message)
				}
			}
		}
	}
	return problems, reviews, nil
}

func resolve(root, path string) string {
	if filepath.IsAbs(path) {
		return path
	}
	return filepath.Join(root, path)
}

// wordsTargets maps each file to check to the lines of it to check (nil for every line).
func wordsTargets(sc *scope) (map[string]map[int]bool, error) {
	targets := map[string]map[int]bool{}
	switch {
	case sc.base != "" || len(sc.files) > 0:
		if sc.base != "" {
			added, err := addedLines(sc.root, sc.base)
			if err != nil {
				return nil, err
			}
			for path, numbers := range added {
				targets[path] = numbers
			}
		}
		for _, path := range sc.files {
			if strings.HasSuffix(path, ".md") {
				targets[path] = nil
			}
		}
	default:
		all, err := sc.allMarkdown()
		if err != nil {
			return nil, err
		}
		for _, path := range all {
			targets[path] = nil
		}
	}
	return targets, nil
}

func runWords(sc *scope, out *report) error {
	english, korean, err := loadWords(sc.root)
	if err != nil {
		return err
	}
	targets, err := wordsTargets(sc)
	if err != nil {
		return err
	}
	paths := make([]string, 0, len(targets))
	for path := range targets {
		paths = append(paths, path)
	}
	sort.Strings(paths)
	var problems, reviews []string
	for _, path := range paths {
		if isSkipped(path) {
			continue
		}
		fileProblems, fileReviews, err := checkWords(sc.root, path, targets[path], english, korean)
		if err != nil {
			return err
		}
		problems = append(problems, fileProblems...)
		reviews = append(reviews, fileReviews...)
	}
	for _, review := range reviews {
		out.review(review)
	}
	for _, problem := range problems {
		out.fail(problem)
	}
	return nil
}
