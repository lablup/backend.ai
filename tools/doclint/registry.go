package main

import (
	"fmt"
	"os"
	"path/filepath"
	"slices"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/spec"
)

// The files of the glossary registry.
const (
	rulesFile     = "rules.yaml"
	termsDir      = "terms"
	yamlExtension = ".yaml"
	// topicPlaceholder stands for the topic in a path or a text of the registry.
	topicPlaceholder = "{topic}"
)

// registry is the source of the glossary documents.
type registry struct {
	rules  rulesDocument
	topics map[string]topicDocument
}

type rulesDocument struct {
	Topics      []string                  `yaml:"topics"`
	Documents   map[string]glossaryPage   `yaml:"documents"`
	Style       map[string][]styleSection `yaml:"style"`
	Expressions []expression              `yaml:"expressions"`
	Korean      koreanRules               `yaml:"korean"`
	English     englishRules              `yaml:"english"`
}

// glossaryPage is the fixed text of the glossary documents of one language.
type glossaryPage struct {
	Path          string     `yaml:"path"`
	TermPath      string     `yaml:"term_path"`
	GeneratedNote string     `yaml:"generated_note"`
	Title         string     `yaml:"title"`
	Intro         [][]string `yaml:"intro"`
	Index         struct {
		Heading string `yaml:"heading"`
		Lead    string `yaml:"lead"`
	} `yaml:"index"`
	Expressions struct {
		Heading string   `yaml:"heading"`
		Lead    string   `yaml:"lead"`
		Columns []string `yaml:"columns"`
	} `yaml:"expressions"`
	Terms struct {
		TitlePrefix string   `yaml:"title_prefix"`
		Lead        string   `yaml:"lead"`
		Columns     []string `yaml:"columns"`
	} `yaml:"terms"`
}

type styleSection struct {
	Heading string   `yaml:"heading"`
	Rules   []string `yaml:"rules"`
}

// expression is a rejected expression. A qualifier names the sense that is rejected; except
// lists longer expressions in which the word is allowed.
type expression struct {
	Lang      string   `yaml:"lang"`
	Word      string   `yaml:"word"`
	Qualifier string   `yaml:"qualifier,omitempty" spec:"optional"`
	Instead   string   `yaml:"instead"`
	Except    []string `yaml:"except,omitempty" spec:"optional"`
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
	Title map[string]topicTitle `yaml:"title"`
	Terms []term                `yaml:"terms"`
}

type topicTitle struct {
	Page        string `yaml:"page"`
	Link        string `yaml:"link"`
	Description string `yaml:"description"`
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

func loadRegistry(directory string) (*registry, error) {
	reg := &registry{topics: map[string]topicDocument{}}
	rulesPath := filepath.Join(directory, rulesFile)
	if err := spec.Decode(rulesPath, &reg.rules); err != nil {
		return nil, err
	}
	entries, err := os.ReadDir(filepath.Join(directory, termsDir))
	if err != nil {
		return nil, err
	}
	for _, entry := range entries {
		name, ok := strings.CutSuffix(entry.Name(), yamlExtension)
		path := filepath.Join(directory, termsDir, entry.Name())
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
	if err := reg.validate(); err != nil {
		return nil, fmt.Errorf("%s: %w", rulesPath, err)
	}
	return reg, nil
}

func (r *registry) validate() error {
	for _, lang := range languages {
		if _, ok := r.rules.Documents[lang]; !ok {
			return fmt.Errorf("missing value documents.%s", lang)
		}
		if len(r.rules.Style[lang]) == 0 {
			return fmt.Errorf("missing value style.%s", lang)
		}
	}
	if len(r.rules.Documents) != len(languages) || len(r.rules.Style) != len(languages) {
		return fmt.Errorf("documents and style take the languages %s", strings.Join(languages, ", "))
	}
	for i, entry := range r.rules.Expressions {
		if !slices.Contains(languages, entry.Lang) {
			return fmt.Errorf("expressions[%d]: unknown lang %q", i, entry.Lang)
		}
	}
	if len(r.rules.Topics) != len(r.topics) {
		return fmt.Errorf("topics lists %d topics, %s/ has %d files", len(r.rules.Topics), termsDir, len(r.topics))
	}
	seen := map[string]bool{}
	for _, name := range r.rules.Topics {
		if _, ok := r.topics[name]; !ok || seen[name] {
			return fmt.Errorf("topics: %q is repeated or has no term file", name)
		}
		seen[name] = true
	}
	return nil
}

func (t topicDocument) validate() error {
	for _, lang := range languages {
		if _, ok := t.Title[lang]; !ok {
			return fmt.Errorf("missing value title.%s", lang)
		}
	}
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
