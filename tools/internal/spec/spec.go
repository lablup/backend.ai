// Package spec reads doclint.yaml, the criteria of the document checks.
package spec

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"regexp"
	"slices"
	"strings"

	"go.yaml.in/yaml/v3"
)

// FileName is the name of the spec at the repository root.
const FileName = "doclint.yaml"

// The languages of the documents, the keys of a value that differs between them.
const (
	English = "en"
	Korean  = "ko"
)

// The kinds of a frontmatter field.
const (
	KindString     = "string"
	KindStrings    = "strings"
	KindEnum       = "enum"
	KindSignature  = "signature"
	KindSignatures = "signatures"
)

// Pattern is a regular expression of the spec.
type Pattern struct{ *regexp.Regexp }

// UnmarshalYAML compiles the expression.
func (p *Pattern) UnmarshalYAML(node *yaml.Node) error {
	var source string
	if err := node.Decode(&source); err != nil {
		return err
	}
	compiled, err := regexp.Compile(source)
	if err != nil {
		return fmt.Errorf("line %d: %w", node.Line, err)
	}
	p.Regexp = compiled
	return nil
}

// Spec is doclint.yaml. A field without the `optional` tag must have a value.
type Spec struct {
	Documents Documents `yaml:"documents"`
	Agents    Agents    `yaml:"agents"`
	BEP       BEP       `yaml:"bep"`
	Knowledge Knowledge `yaml:"knowledge"`
	Pairs     Pairs     `yaml:"pairs"`
	Words     Words     `yaml:"words"`
}

// Documents names the document files.
type Documents struct {
	Extension         string `yaml:"extension"`
	TranslationSuffix string `yaml:"translation_suffix"`
}

// Agents is the criteria of the rule documents.
type Agents struct {
	Path     Pattern `yaml:"path"`
	MaxLines int     `yaml:"max_lines"`
}

// BEP is the length limits of the proposals.
type BEP struct {
	Path            Pattern        `yaml:"path"`
	FirstNumber     int            `yaml:"first_number"`
	MaxLines        int            `yaml:"max_lines"`
	MaxItems        int            `yaml:"max_items"`
	MaxItemChars    map[string]int `yaml:"max_item_chars"`
	GoalSections    []string       `yaml:"goal_sections"`
	CountedSections []string       `yaml:"counted_sections"`
	Design          Design         `yaml:"design"`
}

// Design is the limits of the design section of a proposal.
type Design struct {
	Sections            []string `yaml:"sections"`
	MaxSubsections      int      `yaml:"max_subsections"`
	MaxTables           int      `yaml:"max_tables"`
	MaxTableRows        int      `yaml:"max_table_rows"`
	MaxSentences        int      `yaml:"max_sentences"`
	SkippedLinePrefixes []string `yaml:"skipped_line_prefixes"`
	Abbreviations       []string `yaml:"abbreviations"`
}

// Knowledge is the schema of the knowledge documents.
type Knowledge struct {
	FileName                 string    `yaml:"file_name"`
	SkippedDirectoryPrefixes []string  `yaml:"skipped_directory_prefixes"`
	SkippedDirectoryNames    []string  `yaml:"skipped_directory_names"`
	ExternalLinkPrefixes     []string  `yaml:"external_link_prefixes"`
	Signature                Signature `yaml:"signature"`
	Fields                   []Field   `yaml:"fields"`
	SignOff                  SignOff   `yaml:"sign_off"`
	Search                   Search    `yaml:"search"`
}

// Signature names the keys of an actor and the date they acted.
type Signature struct {
	Actor       string  `yaml:"actor"`
	Date        string  `yaml:"date"`
	DatePattern Pattern `yaml:"date_pattern"`
	DateFormat  string  `yaml:"date_format"`
}

// Field is one frontmatter field.
type Field struct {
	Name        string   `yaml:"name"`
	Kind        string   `yaml:"kind"`
	Required    bool     `yaml:"required,omitempty" spec:"optional"`
	Unique      bool     `yaml:"unique,omitempty" spec:"optional"`
	Path        bool     `yaml:"path,omitempty" spec:"optional"`
	Pattern     *Pattern `yaml:"pattern,omitempty" spec:"optional"`
	PatternName string   `yaml:"pattern_name,omitempty" spec:"optional"`
	Values      []string `yaml:"values,omitempty" spec:"optional"`
	Default     string   `yaml:"default,omitempty" spec:"optional"`
	NotBefore   string   `yaml:"not_before,omitempty" spec:"optional"`
}

// SignOff requires the sign-off to be newer than the last change.
type SignOff struct {
	Field   string   `yaml:"field"`
	Changed []string `yaml:"changed"`
}

// Search names the fields the search matches and prints.
type Search struct {
	Fields  []string `yaml:"fields"`
	Title   string   `yaml:"title"`
	Tags    []string `yaml:"tags"`
	Summary string   `yaml:"summary"`
}

// Pairs is the criteria of the document pairs.
type Pairs struct {
	TranslationCharacters Pattern `yaml:"translation_characters"`
}

// Words is the criteria of the words check.
type Words struct {
	Registry     string    `yaml:"registry"`
	SkippedPaths []Pattern `yaml:"skipped_paths"`
}

// Load reads and validates the spec at the root.
func Load(root string) (*Spec, error) {
	path := filepath.Join(root, FileName)
	var loaded Spec
	if err := Decode(path, &loaded); err != nil {
		return nil, err
	}
	if err := loaded.validate(); err != nil {
		return nil, fmt.Errorf("%s: %w", path, err)
	}
	return &loaded, nil
}

// Decode reads one YAML document into target. A mapping in flow style and an unknown key are
// errors, and so is a missing or empty value of a field without the `spec:"optional"` tag.
func Decode(path string, target any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var document yaml.Node
	if err := yaml.Unmarshal(data, &document); err != nil {
		return fmt.Errorf("%s: %w", path, err)
	}
	if line := flowMapping(&document); line > 0 {
		return fmt.Errorf("%s:%d: mapping in flow style, write one key per line", path, line)
	}
	decoder := yaml.NewDecoder(bytes.NewReader(data))
	decoder.KnownFields(true)
	if err := decoder.Decode(target); err != nil {
		return fmt.Errorf("%s: %w", path, err)
	}
	var extra any
	if err := decoder.Decode(&extra); err != io.EOF {
		return fmt.Errorf("%s: more than one YAML document", path)
	}
	if err := required(reflect.ValueOf(target), ""); err != nil {
		return fmt.Errorf("%s: %w", path, err)
	}
	return nil
}

// flowMapping returns the line of the first mapping in flow style, or 0.
func flowMapping(node *yaml.Node) int {
	if node.Kind == yaml.MappingNode && node.Style&yaml.FlowStyle != 0 {
		return node.Line
	}
	for _, child := range node.Content {
		if line := flowMapping(child); line > 0 {
			return line
		}
	}
	return 0
}

func required(value reflect.Value, at string) error {
	if value.Type() == reflect.TypeFor[Pattern]() {
		if value.Field(0).IsNil() {
			return fmt.Errorf("missing value %s", at)
		}
		return nil
	}
	switch value.Kind() {
	case reflect.Pointer:
		if value.IsNil() {
			return fmt.Errorf("missing value %s", at)
		}
		return required(value.Elem(), at)
	case reflect.Struct:
		for i := range value.NumField() {
			field := value.Type().Field(i)
			name, _, _ := strings.Cut(field.Tag.Get("yaml"), ",")
			path := strings.TrimPrefix(at+"."+name, ".")
			if field.Tag.Get("spec") == "optional" {
				continue
			}
			if err := required(value.Field(i), path); err != nil {
				return err
			}
		}
	case reflect.Slice, reflect.Map:
		if value.Len() == 0 {
			return fmt.Errorf("missing value %s", at)
		}
		if value.Kind() == reflect.Slice {
			for i := range value.Len() {
				if err := required(value.Index(i), fmt.Sprintf("%s[%d]", at, i)); err != nil {
					return err
				}
			}
			return nil
		}
		for _, key := range value.MapKeys() {
			if err := required(value.MapIndex(key), fmt.Sprintf("%s.%v", at, key)); err != nil {
				return err
			}
		}
	case reflect.String, reflect.Int:
		if value.IsZero() {
			return fmt.Errorf("missing value %s", at)
		}
	}
	return nil
}

// Field returns the frontmatter field of the name.
func (k *Knowledge) Field(name string) (Field, bool) {
	i := slices.IndexFunc(k.Fields, func(f Field) bool { return f.Name == name })
	if i < 0 {
		return Field{}, false
	}
	return k.Fields[i], true
}

func (s *Spec) validate() error {
	for _, lang := range []string{English, Korean} {
		if s.BEP.MaxItemChars[lang] <= 0 {
			return fmt.Errorf("missing value bep.max_item_chars.%s", lang)
		}
	}
	if s.BEP.Path.NumSubexp() < 1 {
		return fmt.Errorf("bep.path needs a group for the number")
	}
	return s.Knowledge.validate()
}

func (k *Knowledge) validate() error {
	seen := map[string]bool{}
	for _, field := range k.Fields {
		if seen[field.Name] {
			return fmt.Errorf("knowledge.fields: %s is repeated", field.Name)
		}
		seen[field.Name] = true
		kinds := []string{KindString, KindStrings, KindEnum, KindSignature, KindSignatures}
		if !slices.Contains(kinds, field.Kind) {
			return fmt.Errorf("knowledge.fields.%s: unknown kind %q", field.Name, field.Kind)
		}
		if field.Kind == KindEnum && !slices.Contains(field.Values, field.Default) {
			return fmt.Errorf("knowledge.fields.%s: the default must be one of the values", field.Name)
		}
		if (field.Pattern == nil) != (field.PatternName == "") {
			return fmt.Errorf("knowledge.fields.%s: pattern and pattern_name go together", field.Name)
		}
		if (field.Unique || field.Pattern != nil) && field.Kind != KindString {
			return fmt.Errorf("knowledge.fields.%s: unique and pattern need the kind %s", field.Name, KindString)
		}
		if field.Path && field.Kind != KindString && field.Kind != KindStrings {
			return fmt.Errorf("knowledge.fields.%s: path needs the kind %s or %s", field.Name, KindString, KindStrings)
		}
	}
	reference := func(at, name string, kind ...string) error {
		field, ok := k.Field(name)
		if !ok {
			return fmt.Errorf("knowledge.%s: unknown field %q", at, name)
		}
		if len(kind) > 0 && !slices.Contains(kind, field.Kind) {
			return fmt.Errorf("knowledge.%s: field %q must be of the kind %s", at, name, strings.Join(kind, " or "))
		}
		return nil
	}
	for _, field := range k.Fields {
		if field.NotBefore == "" {
			continue
		}
		if field.Kind != KindSignature {
			return fmt.Errorf("knowledge.fields.%s: not_before needs the kind %s", field.Name, KindSignature)
		}
		if err := reference("fields.not_before", field.NotBefore, KindSignature); err != nil {
			return err
		}
	}
	if err := reference("sign_off.field", k.SignOff.Field, KindSignatures); err != nil {
		return err
	}
	for _, name := range k.SignOff.Changed {
		if err := reference("sign_off.changed", name, KindSignature); err != nil {
			return err
		}
	}
	printed := append([]string{k.Search.Title, k.Search.Summary}, k.Search.Tags...)
	for _, name := range printed {
		if err := reference("search", name, KindString, KindEnum); err != nil {
			return err
		}
	}
	for _, name := range k.Search.Fields {
		if err := reference("search.fields", name, KindString, KindEnum, KindStrings); err != nil {
			return err
		}
	}
	return nil
}
