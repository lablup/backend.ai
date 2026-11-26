// Package kdoc parses the frontmatter of knowledge documents and validates it against the
// schema of doclint.yaml.
//
// The parser accepts only the YAML subset the schema uses: scalars, inline lists, block lists
// (of scalars or flat mappings) and one level of nested mapping. Anything else is a parse error.
package kdoc

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"sort"
	"strings"
	"unicode"

	"github.com/lablup/backend.ai/tools/internal/spec"
)

var keyValue = regexp.MustCompile(`^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$`)

// Signature is an actor and the date they acted.
type Signature struct {
	By string
	At string
}

// Document is a frontmatter validated against the schema. A value is a string (kinds string
// and enum), a []string, a Signature or a []Signature, under the name of its field.
type Document map[string]any

// Text returns the value of a string or enum field.
func (d Document) Text(name string) string {
	text, _ := d[name].(string)
	return text
}

// Texts returns the values of a string, enum or strings field.
func (d Document) Texts(name string) []string {
	if list, ok := d[name].([]string); ok {
		return list
	}
	if text := d.Text(name); text != "" {
		return []string{text}
	}
	return nil
}

// ParseError is a frontmatter that cannot be parsed.
type ParseError struct {
	Line    int
	Message string
}

func (e *ParseError) Error() string {
	return fmt.Sprintf("frontmatter line %d: %s", e.Line, e.Message)
}

// Raw is the parsed frontmatter. A value is a string, a []any of strings or
// map[string]string, or a map[string]string.
type Raw map[string]any

// IterFiles returns every knowledge document under root, outside the skipped directories.
func IterFiles(root string, schema *spec.Knowledge) ([]string, error) {
	var found []string
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() {
			name := entry.Name()
			if path != root && skipped(name, schema) {
				return filepath.SkipDir
			}
			return nil
		}
		if entry.Name() == schema.FileName {
			found = append(found, path)
		}
		return nil
	})
	return found, err
}

func skipped(name string, schema *spec.Knowledge) bool {
	return slices.Contains(schema.SkippedDirectoryNames, name) ||
		slices.ContainsFunc(schema.SkippedDirectoryPrefixes, func(prefix string) bool {
			return strings.HasPrefix(name, prefix)
		})
}

// Load returns the raw frontmatter and the body lines of a knowledge document.
func Load(path string) (Raw, []string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, nil, err
	}
	return Parse(data)
}

// Parse returns the raw frontmatter and the body lines of the content of a knowledge document.
func Parse(data []byte) (Raw, []string, error) {
	front, body, ok := splitDocument(string(data))
	if !ok {
		return nil, nil, &ParseError{Line: 1, Message: "missing or unclosed '---' frontmatter fence"}
	}
	raw, err := parseFrontmatter(front)
	if err != nil {
		return nil, nil, err
	}
	return raw, body, nil
}

func splitDocument(text string) (front, body []string, ok bool) {
	lines := SplitLines(text)
	if len(lines) == 0 || strings.TrimSpace(lines[0]) != "---" {
		return nil, nil, false
	}
	for i := 1; i < len(lines); i++ {
		if strings.TrimSpace(lines[i]) == "---" {
			return lines[1:i], lines[i+1:], true
		}
	}
	return nil, nil, false
}

// SplitLines splits text into lines without the line terminators.
func SplitLines(text string) []string {
	if text == "" {
		return nil
	}
	text = strings.ReplaceAll(text, "\r\n", "\n")
	text = strings.TrimSuffix(text, "\n")
	return strings.Split(text, "\n")
}

func isIndented(line string) bool {
	for _, r := range line {
		return unicode.IsSpace(r)
	}
	return false
}

func parseFrontmatter(lines []string) (Raw, error) {
	data := Raw{}
	index := 0
	for index < len(lines) {
		line := lines[index]
		if strings.TrimSpace(line) == "" || strings.HasPrefix(strings.TrimLeftFunc(line, unicode.IsSpace), "#") {
			index++
			continue
		}
		if isIndented(line) {
			return nil, &ParseError{index + 1, fmt.Sprintf("unexpected indentation: %s", pyRepr(strings.TrimSpace(line)))}
		}
		matched := keyValue.FindStringSubmatch(line)
		if matched == nil {
			return nil, &ParseError{index + 1, fmt.Sprintf("expected 'key: value', got %s", pyRepr(strings.TrimSpace(line)))}
		}
		key, rest := matched[1], strings.TrimSpace(matched[2])
		if rest != "" {
			data[key] = parseInline(rest)
			index++
			continue
		}
		value, next, err := parseBlock(lines, index+1)
		if err != nil {
			return nil, err
		}
		data[key] = value
		index = next
	}
	return data, nil
}

func parseInline(raw string) any {
	if strings.HasPrefix(raw, "[") && strings.HasSuffix(raw, "]") {
		inner := strings.TrimSpace(raw[1 : len(raw)-1])
		if inner == "" {
			return []any{}
		}
		items := []any{}
		for item := range strings.SplitSeq(inner, ",") {
			items = append(items, unquote(item))
		}
		return items
	}
	return unquote(raw)
}

func unquote(raw string) string {
	value := strings.TrimSpace(raw)
	if len(value) >= 2 && value[0] == value[len(value)-1] && (value[0] == '\'' || value[0] == '"') {
		value = value[1 : len(value)-1]
	}
	return value
}

// parseBlock parses the indented block after a bare "key:" line.
func parseBlock(lines []string, start int) (any, int, error) {
	items := []any{}
	mapping := map[string]string{}
	index := start
	for index < len(lines) {
		line := lines[index]
		if strings.TrimSpace(line) == "" {
			index++
			continue
		}
		if !isIndented(line) {
			break
		}
		stripped := strings.TrimSpace(line)
		if strings.HasPrefix(stripped, "- ") {
			entry, next, err := parseListItem(lines, index)
			if err != nil {
				return nil, 0, err
			}
			items = append(items, entry)
			index = next
			continue
		}
		matched := keyValue.FindStringSubmatch(stripped)
		if matched == nil || strings.TrimSpace(matched[2]) == "" {
			return nil, 0, &ParseError{index + 1, fmt.Sprintf(
				"expected '- item' or 'key: value' (one nesting level only), got %s", pyRepr(stripped))}
		}
		mapping[matched[1]] = unquote(matched[2])
		index++
	}
	if len(items) > 0 && len(mapping) > 0 {
		return nil, 0, &ParseError{index, "a block cannot mix list items and mapping entries"}
	}
	if len(items) > 0 {
		return items, index, nil
	}
	return mapping, index, nil
}

// parseListItem parses one "- item" entry, consuming the continuation lines of a flat mapping.
func parseListItem(lines []string, start int) (any, int, error) {
	item := strings.TrimSpace(strings.TrimSpace(lines[start])[2:])
	matched := keyValue.FindStringSubmatch(item)
	if matched == nil || strings.TrimSpace(matched[2]) == "" {
		return unquote(item), start + 1, nil
	}
	entry := map[string]string{matched[1]: unquote(matched[2])}
	index := start + 1
	for index < len(lines) {
		line := lines[index]
		if strings.TrimSpace(line) == "" {
			index++
			continue
		}
		stripped := strings.TrimSpace(line)
		if !isIndented(line) || strings.HasPrefix(stripped, "- ") {
			break
		}
		continued := keyValue.FindStringSubmatch(stripped)
		if continued == nil || strings.TrimSpace(continued[2]) == "" {
			return nil, 0, &ParseError{index + 1, fmt.Sprintf(
				"expected 'key: value' inside a list entry, got %s", pyRepr(stripped))}
		}
		entry[continued[1]] = unquote(continued[2])
		index++
	}
	return entry, index, nil
}

// Build validates raw frontmatter against the schema. It returns the document (nil when a
// required field is unusable) and every violation found.
func Build(schema *spec.Knowledge, raw Raw) (Document, []string) {
	b := &builder{schema: schema, raw: raw, document: Document{}}
	usable := true
	for _, field := range schema.Fields {
		b.field(field)
		if _, ok := b.document[field.Name]; field.Required && !ok {
			usable = false
		}
	}
	for _, field := range schema.Fields {
		b.order(field)
	}
	b.signOff()
	if !usable {
		return nil, b.problems
	}
	return b.document, b.problems
}

type builder struct {
	schema   *spec.Knowledge
	raw      Raw
	document Document
	problems []string
}

func (b *builder) problem(format string, args ...any) {
	b.problems = append(b.problems, fmt.Sprintf(format, args...))
}

// field validates one field and keeps its usable value in the document.
func (b *builder) field(field spec.Field) {
	value, present := b.raw[field.Name]
	switch field.Kind {
	case spec.KindString:
		text, ok := value.(string)
		if !ok || strings.TrimSpace(text) == "" {
			if field.Required {
				b.problem("missing or empty required field '%s'", field.Name)
			} else if present {
				b.problem("'%s' must be a non-empty string", field.Name)
			}
			return
		}
		text = strings.TrimSpace(text)
		b.document[field.Name] = text
		if field.Pattern != nil && !field.Pattern.MatchString(text) {
			b.problem("%s %s is not %s", field.Name, pyRepr(text), field.PatternName)
		}
	case spec.KindEnum:
		if !present {
			b.document[field.Name] = field.Default
			return
		}
		text, _ := value.(string)
		if !slices.Contains(field.Values, text) {
			values := slices.Sorted(slices.Values(field.Values))
			b.problem("%s %s is not one of %s", field.Name, pyRepr(value), pyRepr(anyStrings(values)))
			text = field.Default
		}
		b.document[field.Name] = text
	case spec.KindStrings:
		if !present {
			if field.Required {
				b.problem("missing or empty required field '%s'", field.Name)
			}
			return
		}
		if list, ok := stringList(value); ok {
			b.document[field.Name] = list
			return
		}
		b.problem("'%s' must be a list of strings", field.Name)
	case spec.KindSignature:
		if value == nil && !field.Required {
			return
		}
		if sig := b.signature(value, field.Name); sig != nil {
			b.document[field.Name] = *sig
		}
	case spec.KindSignatures:
		if value == nil {
			if field.Required {
				b.signature(value, field.Name)
			}
			return
		}
		if list := b.signatures(value, field.Name); list != nil {
			b.document[field.Name] = list
		}
	}
}

// order checks that the date of a field is not older than the field it must not precede.
func (b *builder) order(field spec.Field) {
	later, ok := b.document[field.Name].(Signature)
	earlier, found := b.document[field.NotBefore].(Signature)
	if ok && found && later.At < earlier.At {
		b.problem("%s (%s) is older than %s (%s)", field.Name, later.At, field.NotBefore, earlier.At)
	}
}

func (b *builder) signOff() {
	name := b.schema.SignOff.Field
	entries, _ := b.document[name].([]Signature)
	if len(entries) == 0 {
		return
	}
	latest := slices.MaxFunc(entries, func(x, y Signature) int { return strings.Compare(x.At, y.At) }).At
	for _, changedName := range b.schema.SignOff.Changed {
		changed, ok := b.document[changedName].(Signature)
		if !ok {
			continue
		}
		if latest < changed.At {
			b.problem("%s (%s) is older than the last change (%s) — a meaningful change must clear '%s'",
				name, latest, changed.At, name)
		}
		return
	}
}

func stringList(value any) ([]string, bool) {
	list, ok := value.([]any)
	if !ok {
		return nil, false
	}
	result := make([]string, 0, len(list))
	for _, item := range list {
		text, ok := item.(string)
		if !ok {
			return nil, false
		}
		result = append(result, text)
	}
	return result, true
}

func (b *builder) signature(value any, key string) *Signature {
	keys := b.schema.Signature
	mapping, ok := value.(map[string]string)
	if !ok || mapping[keys.Actor] == "" || mapping[keys.Date] == "" {
		b.problem("missing '%s' with '%s' and '%s'", key, keys.Actor, keys.Date)
		return nil
	}
	if !keys.DatePattern.MatchString(mapping[keys.Date]) {
		b.problem("%s.%s must be %s, got %s", key, keys.Date, keys.DateFormat, pyRepr(mapping[keys.Date]))
		return nil
	}
	return &Signature{By: mapping[keys.Actor], At: mapping[keys.Date]}
}

func (b *builder) signatures(value any, key string) []Signature {
	entries, ok := value.([]any)
	if !ok {
		entries = []any{value}
	}
	var result []Signature
	for _, entry := range entries {
		sig := b.signature(entry, key)
		if sig == nil {
			return nil
		}
		result = append(result, *sig)
	}
	return result
}

func anyStrings(values []string) []any {
	result := make([]any, len(values))
	for i, value := range values {
		result[i] = value
	}
	return result
}

// pyRepr renders a value the way Python's repr does for strings, lists and dicts.
func pyRepr(value any) string {
	switch v := value.(type) {
	case string:
		quote := "'"
		if strings.Contains(v, "'") && !strings.Contains(v, `"`) {
			quote = `"`
		}
		escaped := strings.ReplaceAll(v, `\`, `\\`)
		if quote == "'" {
			escaped = strings.ReplaceAll(escaped, "'", `\'`)
		}
		escaped = strings.ReplaceAll(escaped, "\n", `\n`)
		escaped = strings.ReplaceAll(escaped, "\t", `\t`)
		return quote + escaped + quote
	case []any:
		parts := make([]string, len(v))
		for i, item := range v {
			parts[i] = pyRepr(item)
		}
		return "[" + strings.Join(parts, ", ") + "]"
	case map[string]string:
		keys := make([]string, 0, len(v))
		for key := range v {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		parts := make([]string, len(keys))
		for i, key := range keys {
			parts[i] = pyRepr(key) + ": " + pyRepr(v[key])
		}
		return "{" + strings.Join(parts, ", ") + "}"
	default:
		return fmt.Sprint(v)
	}
}
