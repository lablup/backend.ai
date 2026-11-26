package main

import (
	"errors"
	"fmt"
	"maps"
	"path/filepath"
	"regexp"
	"slices"
	"sort"
	"strings"
	"unicode/utf8"

	"github.com/lablup/backend.ai/tools/internal/kdoc"
	"github.com/lablup/backend.ai/tools/internal/spec"
)

// Unicode composition of the Hangul syllables: initial, vowel and final jamo in the order of
// the compatibility jamo below.
const (
	syllableBase = '가'
	syllableLast = '힣'
	vowelCount   = 21
	finalCount   = 28
	vowelJamo    = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
	finalJamo    = "ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
	hangulClass  = string(syllableBase) + "-" + string(syllableLast)
)

// The notation of a registry word: "a, b / c" lists alternatives and "~" stands for any text.
const (
	gapMarker = "~"

	// The boundaries stand for lookarounds, which RE2 lacks. They consume a character, which
	// does not matter when only a match is looked for.
	wordBoundaryBefore = `(?:^|[^\p{L}\p{N}_-])`
	wordBoundaryAfter  = `(?:$|[^\p{L}\p{N}_-])`
	hangulBefore       = `(?:^|[^` + hangulClass + `])`
	hangulAfter        = `(?:$|[^` + hangulClass + `])`
	space              = `[\s\p{Z}]`
)

var (
	fence      = regexp.MustCompile("^\\s*(```|~~~)")
	codeSpan   = regexp.MustCompile("`[^`]*`")
	hangulText = regexp.MustCompile("[" + hangulClass + "]")
	altSplit   = regexp.MustCompile(`\s*/\s*|,\s+`)
)

type word struct {
	text        string
	replacement string
	reason      string
	pattern     *regexp.Regexp
	advisory    bool
	// allowed are longer expressions in which the word is not reported.
	allowed []string
}

// message reports the word found at the line.
func (w word) message(path string, line int) string {
	message := fmt.Sprintf(`%s:%d: "%s" -> "%s"`, path, line, w.text, w.replacement)
	if w.reason != "" {
		message += ": " + w.reason
	}
	return message
}

// match reports whether the line uses the word outside the allowed expressions.
func (w word) match(line string) bool {
	for _, expression := range w.allowed {
		line = strings.ReplaceAll(line, expression, " ")
	}
	return w.pattern.MatchString(line)
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

func split(syllable rune) (initial, vowel, final int) {
	offset := int(syllable - syllableBase)
	return floorDiv(offset, vowelCount*finalCount), floorMod(floorDiv(offset, finalCount), vowelCount), floorMod(offset, finalCount)
}

func join(initial, vowel, final int) rune {
	return syllableBase + rune((initial*vowelCount+vowel)*finalCount+final)
}

// jamoIndex returns the position of a jamo among the finals (from 1) or the vowels (from 0).
func jamoIndex(jamo, set string, first int) (int, error) {
	i := slices.Index([]rune(set), []rune(jamo)[0])
	if i < 0 || utf8.RuneCountInString(jamo) != 1 {
		return 0, fmt.Errorf("%q is not a jamo of %q", jamo, set)
	}
	return i + first, nil
}

// matcher builds the patterns of the words from the inflections of the registry.
type matcher struct {
	particles        []string
	verb             verbRules
	openStemFinals   []int
	pastFinal        int
	droppedFinal     int
	droppedAdded     int
	contractedVowels map[int]int
	irregularFinal   int
	inflections      []string
}

func newMatcher(korean koreanRules, english englishRules) (*matcher, error) {
	m := &matcher{
		particles:        korean.Particles,
		verb:             korean.Verb,
		contractedVowels: map[int]int{},
		inflections:      english.Inflections,
	}
	var errs []error
	final := func(jamo string) int {
		i, err := jamoIndex(jamo, finalJamo, 1)
		errs = append(errs, err)
		return i
	}
	vowel := func(jamo string) int {
		i, err := jamoIndex(jamo, vowelJamo, 0)
		errs = append(errs, err)
		return i
	}
	for _, jamo := range korean.Verb.OpenStemFinals {
		m.openStemFinals = append(m.openStemFinals, final(jamo))
	}
	m.pastFinal = final(korean.Verb.PastFinal)
	m.droppedFinal = final(korean.Verb.DroppedFinal.Final)
	m.droppedAdded = final(korean.Verb.DroppedFinal.Added)
	m.irregularFinal = final(korean.Verb.Irregular.AddedFinal)
	for from, to := range korean.Verb.ContractedVowels {
		m.contractedVowels[vowel(from)] = vowel(to)
	}
	return m, errors.Join(errs...)
}

// class returns the character class of single syllables.
func class(syllables []string) string {
	return "[" + regexp.QuoteMeta(strings.Join(syllables, "")) + "]"
}

func alternation(items []string) string {
	quoted := make([]string, len(items))
	for i, item := range items {
		quoted[i] = regexp.QuoteMeta(item)
	}
	return "(?:" + strings.Join(quoted, "|") + ")"
}

// verbForms returns the regex alternatives of the inflected forms of a verb stem.
func (m *matcher) verbForms(stem string) []string {
	runes := []rune(stem)
	head, last := string(runes[:len(runes)-1]), runes[len(runes)-1]
	initial, vowel, final := split(last)
	consonant := stem + class(m.verb.ConsonantEndings)
	if final == m.droppedFinal {
		dropped := head + string(join(initial, vowel, 0))
		return []string{
			consonant,
			stem + class(m.verb.VowelEndings),
			dropped + class(m.verb.DroppedFinal.Endings),
			head + string(join(initial, vowel, m.droppedAdded)),
		}
	}
	if final != 0 {
		return []string{consonant, stem + class(m.verb.VowelEndings)}
	}
	forms := []string{consonant}
	for _, added := range m.openStemFinals {
		forms = append(forms, head+string(last+rune(added)))
	}
	var contracted rune
	switch replacement, ok := m.verb.ContractedSyllables[string(last)]; {
	case ok:
		contracted = []rune(replacement)[0]
	case string(last) == m.verb.Irregular.Syllable && head != "":
		headRunes := []rune(head)
		priorInitial, priorVowel, _ := split(headRunes[len(headRunes)-1])
		return append(forms, string(headRunes[:len(headRunes)-1])+
			string(join(priorInitial, priorVowel, m.irregularFinal))+class(m.verb.Irregular.Endings))
	default:
		replaced, ok := m.contractedVowels[vowel]
		if !ok {
			replaced = vowel
		}
		contracted = join(initial, replaced, 0)
	}
	return append(forms, head+string(contracted), head+string(contracted+rune(m.pastFinal)))
}

func (m *matcher) koreanPattern(text string) (string, error) {
	tokens := strings.Fields(strings.ReplaceAll(text, gapMarker, " "))
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
	if len(tokens) > 1 && strings.Index(text, gapMarker) > 0 {
		prefix = regexp.QuoteMeta(tokens[0]) + space + "+.*?" + quoted(tokens[1:len(tokens)-1], space+"*")
	}
	var ending string
	if stem, ok := strings.CutSuffix(last, m.verb.DictionaryEnding); ok && stem != "" {
		ending = "(?:" + strings.Join(m.verbForms(stem), "|") + ")"
	} else {
		quotedLast := regexp.QuoteMeta(last)
		ending = "(?:" + quotedLast + alternation(m.particles) + hangulAfter + "|" + quotedLast + hangulAfter + ")"
	}
	body := ending
	if prefix != "" {
		body = prefix + space + "+" + ending
	}
	if strings.HasPrefix(text, gapMarker) {
		return body, nil
	}
	return hangulBefore + body, nil
}

func (m *matcher) englishPattern(text string) string {
	fields := strings.Fields(text)
	for i, field := range fields {
		fields[i] = regexp.QuoteMeta(field)
	}
	return wordBoundaryBefore + strings.Join(fields, space+"+") + alternation(m.inflections) + "?" + wordBoundaryAfter
}

// build sets the pattern of the word.
func (m *matcher) build(w word) (word, error) {
	text := w.text
	var source string
	if hangulText.MatchString(text) {
		var err error
		if source, err = m.koreanPattern(text); err != nil {
			return word{}, err
		}
	} else {
		source = m.englishPattern(text)
	}
	pattern, err := regexp.Compile(source)
	if err != nil {
		return word{}, fmt.Errorf("word %q: %w", text, err)
	}
	w.pattern = pattern
	return w, nil
}

// alternatives splits an expression, carrying a shared leading word into the verbs after it.
func (m *matcher) alternatives(expression string) []string {
	var parts []string
	for _, part := range altSplit.Split(expression, -1) {
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
		if len(leading) > 0 && len(strings.Fields(part)) == 1 && strings.HasSuffix(part, m.verb.DictionaryEnding) {
			part = strings.Join(append(append([]string{}, leading...), part), " ")
		}
		result = append(result, part)
	}
	return result
}

// loadWords returns the rejected words of the English documents and of the Korean documents:
// the expressions, then the term variants by topic file. A term variant, and an expression
// with a qualifier, have other valid meanings, so they are advisory.
func loadWords(directory string) (english, korean []word, err error) {
	reg, err := loadRegistry(directory)
	if err != nil {
		return nil, nil, err
	}
	m, err := newMatcher(reg.rules.Korean, reg.rules.English)
	if err != nil {
		return nil, nil, fmt.Errorf("%s: %w", directory, err)
	}
	words := map[string][]word{}
	add := func(lang string, w word) error {
		built, err := m.build(w)
		words[lang] = append(words[lang], built)
		return err
	}
	for _, entry := range reg.rules.Expressions {
		for _, text := range m.alternatives(entry.Word) {
			if strings.Contains(strings.ToLower(entry.Instead), strings.ToLower(text)) {
				continue
			}
			if err := add(entry.Lang, word{
				text:        text,
				replacement: entry.Instead,
				reason:      entry.Reason,
				advisory:    entry.Qualifier != "",
				allowed:     entry.Except,
			}); err != nil {
				return nil, nil, err
			}
		}
	}
	for _, name := range slices.Sorted(maps.Keys(reg.topics)) {
		for _, term := range reg.topics[name].Terms {
			for _, lang := range []string{spec.English, spec.Korean} {
				own := term.name(lang)
				for _, text := range term.Avoid[lang] {
					if strings.EqualFold(text, own) {
						continue
					}
					variant := word{text: text, replacement: own, reason: term.Meaning[lang], advisory: true}
					if err := add(lang, variant); err != nil {
						return nil, nil, err
					}
				}
			}
		}
	}
	return words[spec.English], words[spec.Korean], nil
}

// proseLines returns line number to text, without frontmatter, fenced blocks and code spans.
func proseLines(text string) map[int]string {
	lines := kdoc.SplitLines(text)
	start := 0
	if len(lines) > 0 && lines[0] == "---" {
		if at := slices.Index(lines[1:], "---"); at >= 0 {
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
func checkWords(sc *scope, path string, numbers map[int]bool, english, korean []word) (problems, reviews []string, err error) {
	words := english
	if strings.HasSuffix(path, sc.spec.Documents.TranslationSuffix) {
		words = korean
	}
	data, err := sc.read(path)
	if err != nil {
		return nil, nil, err
	}
	prose := proseLines(string(data))
	for _, number := range slices.Sorted(maps.Keys(prose)) {
		if numbers != nil && !numbers[number] {
			continue
		}
		line := prose[number]
		for _, w := range words {
			if w.match(line) {
				message := w.message(path, number)
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

func matchesAny(patterns []spec.Pattern, text string) bool {
	return slices.ContainsFunc(patterns, func(p spec.Pattern) bool { return p.MatchString(text) })
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
	case sc.restricted():
		if sc.diffing() {
			added, err := addedLines(sc)
			if err != nil {
				return nil, err
			}
			for path, numbers := range added {
				targets[path] = numbers
			}
		}
		for _, path := range sc.files {
			if strings.HasSuffix(path, sc.spec.Documents.Extension) {
				targets[path] = nil
			}
		}
	default:
		all, err := sc.allDocuments()
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
	english, korean, err := loadWords(filepath.Join(sc.root, sc.spec.Words.Registry))
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
		if matchesAny(sc.spec.Words.SkippedPaths, path) {
			continue
		}
		fileProblems, fileReviews, err := checkWords(sc, path, targets[path], english, korean)
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
