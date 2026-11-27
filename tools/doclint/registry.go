package main

import (
	"fmt"
	"os"
	"path/filepath"
	"slices"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/spec"
)

const yamlExtension = ".yaml"

// registry is the rules of the words check.
type registry struct {
	// rules are the rule files by path, in the order they are read.
	rules  []rulesFile
	topics map[string]topicDocument
}

type rulesFile struct {
	path string
	rulesDocument
}

type rulesDocument struct {
	Sets        []ruleSet     `yaml:"sets,omitempty" spec:"part"`
	Expressions []expression  `yaml:"expressions,omitempty" spec:"part"`
	Korean      *koreanRules  `yaml:"korean,omitempty" spec:"part"`
	English     *englishRules `yaml:"english,omitempty" spec:"part"`
}

// ruleSet is a named group of expressions. A path matching skipped_paths is not checked with
// the expressions of the set.
type ruleSet struct {
	Name         string         `yaml:"name"`
	Description  string         `yaml:"description"`
	SkippedPaths []spec.Pattern `yaml:"skipped_paths,omitempty" spec:"optional"`
}

// expression is a rejected expression, a word or a pattern. A qualifier names the sense that is
// rejected; except lists longer expressions in which the word is allowed. Sets names the sets
// the expression belongs to; without it the expression applies everywhere.
type expression struct {
	Lang      string        `yaml:"lang"`
	Word      string        `yaml:"word,omitempty" spec:"optional"`
	Pattern   *spec.Pattern `yaml:"pattern,omitempty" spec:"optional"`
	Qualifier string        `yaml:"qualifier,omitempty" spec:"optional"`
	Instead   string        `yaml:"instead"`
	Reason    string        `yaml:"reason,omitempty" spec:"optional"`
	Except    []string      `yaml:"except,omitempty" spec:"optional"`
	Sets      []string      `yaml:"sets,omitempty" spec:"optional"`
}

// text is the expression as the output names it.
func (e expression) text() string {
	if e.Pattern != nil {
		return e.Pattern.String()
	}
	return e.Word
}

type koreanRules struct {
	Particles []string  `yaml:"particles"`
	Verb      verbRules `yaml:"verb"`
}

// verbRules are the endings and the stem changes of a Korean verb.
type verbRules struct {
	DictionaryEnding string   `yaml:"dictionary_ending"`
	ConsonantEndings []string `yaml:"consonant_endings"`
	VowelEndings     []string `yaml:"vowel_endings"`
	OpenStemFinals   []string `yaml:"open_stem_finals"`
	PastFinal        string   `yaml:"past_final"`
	DroppedFinal     struct {
		Final   string   `yaml:"final"`
		Endings []string `yaml:"endings"`
		Added   string   `yaml:"added"`
	} `yaml:"dropped_final"`
	ContractedSyllables map[string]string `yaml:"contracted_syllables"`
	ContractedVowels    map[string]string `yaml:"contracted_vowels"`
	Irregular           struct {
		Syllable   string   `yaml:"syllable"`
		AddedFinal string   `yaml:"added_final"`
		Endings    []string `yaml:"endings"`
	} `yaml:"irregular"`
}

type englishRules struct {
	Inflections []string `yaml:"inflections"`
}

// topicDocument is one term file.
type topicDocument struct {
	Terms []term `yaml:"terms"`
}

type term struct {
	English string              `yaml:"english"`
	Korean  string              `yaml:"korean"`
	Meaning map[string]string   `yaml:"meaning"`
	Avoid   map[string][]string `yaml:"avoid,omitempty" spec:"optional"`
	Note    map[string]string   `yaml:"note,omitempty" spec:"optional"`
}

// name returns the term in the language.
func (t term) name(lang string) string {
	if lang == spec.Korean {
		return t.Korean
	}
	return t.English
}

var languages = []string{spec.English, spec.Korean}

// loadRegistry reads the rule files, in path order, and the term files of the directory.
func loadRegistry(rulePaths []string, termsDirectory string) (*registry, error) {
	reg := &registry{topics: map[string]topicDocument{}}
	for _, path := range slices.Sorted(slices.Values(rulePaths)) {
		var document rulesDocument
		if err := spec.Decode(path, &document); err != nil {
			return nil, err
		}
		if err := document.validate(); err != nil {
			return nil, fmt.Errorf("%s: %w", path, err)
		}
		reg.rules = append(reg.rules, rulesFile{path: path, rulesDocument: document})
	}
	if err := reg.validate(); err != nil {
		return nil, err
	}
	if termsDirectory == "" {
		return reg, nil
	}
	entries, err := os.ReadDir(termsDirectory)
	if err != nil {
		return nil, err
	}
	for _, entry := range entries {
		name, ok := strings.CutSuffix(entry.Name(), yamlExtension)
		path := filepath.Join(termsDirectory, entry.Name())
		if !ok {
			return nil, fmt.Errorf("%s: not a %s file", path, yamlExtension)
		}
		var topic topicDocument
		if err := spec.Decode(path, &topic); err != nil {
			return nil, err
		}
		if err := topic.validate(); err != nil {
			return nil, fmt.Errorf("%s: %w", path, err)
		}
		reg.topics[name] = topic
	}
	return reg, nil
}

func (d rulesDocument) validate() error {
	for i, entry := range d.Expressions {
		if !slices.Contains(languages, entry.Lang) {
			return fmt.Errorf("expressions[%d]: unknown lang %q", i, entry.Lang)
		}
		if (entry.Word == "") == (entry.Pattern == nil) {
			return fmt.Errorf("expressions[%d]: write exactly one of word and pattern", i)
		}
	}
	return nil
}

// validate checks what spans the rule files: the inflection rules are in exactly one file, an
// expression is in one file, and a set is declared once and referred to by its name.
func (r *registry) validate() error {
	for _, kind := range []struct {
		name    string
		present func(rulesDocument) bool
	}{
		{"korean", func(d rulesDocument) bool { return d.Korean != nil }},
		{"english", func(d rulesDocument) bool { return d.English != nil }},
	} {
		var holders []string
		for _, file := range r.rules {
			if kind.present(file.rulesDocument) {
				holders = append(holders, file.path)
			}
		}
		switch len(holders) {
		case 0:
			return fmt.Errorf("missing value %s in the rule files", kind.name)
		case 1:
		default:
			return fmt.Errorf("%s is in more than one rule file: %s", kind.name, strings.Join(holders, ", "))
		}
	}
	declared := map[string]string{}
	type key struct{ lang, text string }
	expressions := map[key]string{}
	for _, file := range r.rules {
		for _, set := range file.Sets {
			if first, ok := declared[set.Name]; ok {
				return fmt.Errorf("set %q is declared in %s and %s", set.Name, first, file.path)
			}
			declared[set.Name] = file.path
		}
		for _, entry := range file.Expressions {
			k := key{entry.Lang, entry.text()}
			if first, ok := expressions[k]; ok && first != file.path {
				return fmt.Errorf("%s %q is in %s and %s", entry.Lang, k.text, first, file.path)
			}
			expressions[k] = file.path
		}
	}
	for _, file := range r.rules {
		for i, entry := range file.Expressions {
			for _, name := range entry.Sets {
				if _, ok := declared[name]; !ok {
					return fmt.Errorf("%s: expressions[%d]: unknown set %q", file.path, i, name)
				}
			}
		}
	}
	return nil
}

func (t topicDocument) validate() error {
	for i, entry := range t.Terms {
		for _, lang := range languages {
			if entry.Meaning[lang] == "" {
				return fmt.Errorf("terms[%d]: missing value meaning.%s", i, lang)
			}
		}
		for _, keys := range []map[string]bool{keySet(entry.Meaning), keySet(entry.Avoid), keySet(entry.Note)} {
			for lang := range keys {
				if !slices.Contains(languages, lang) {
					return fmt.Errorf("terms[%d]: unknown lang %q", i, lang)
				}
			}
		}
	}
	return nil
}

func keySet[V any](values map[string]V) map[string]bool {
	keys := map[string]bool{}
	for key := range values {
		keys[key] = true
	}
	return keys
}
