// Package kdoc parses the frontmatter of KNOWLEDGE.md files and validates it against the schema.
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
	"sort"
	"strings"
	"unicode"
)

const (
	// FileName is the name of a knowledge document.
	FileName = "KNOWLEDGE.md"

	defaultStatus = "stable"
)

var (
	namePattern  = regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`)
	datePattern  = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}$`)
	keyValue     = regexp.MustCompile(`^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$`)
	statusValues = []string{"deprecated", "draft", "stable"}
)

// Signature is an actor and the date they acted.
type Signature struct {
	By string
	At string
}

// Document is a KNOWLEDGE.md frontmatter validated against the schema.
type Document struct {
	Name        string
	Type        string
	Description string
	Scope       string
	Generated   Signature
	Keywords    []string
	Sources     []string
	Updated     *Signature
	Verified    []Signature
	Status      string
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

// IterFiles returns every KNOWLEDGE.md under root, skipping hidden and build directories.
func IterFiles(root string) ([]string, error) {
	var found []string
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() {
			name := entry.Name()
			if path != root && (strings.HasPrefix(name, ".") || name == "node_modules" || name == "dist" || name == "build") {
				return filepath.SkipDir
			}
			return nil
		}
		if entry.Name() == FileName {
			found = append(found, path)
		}
		return nil
	})
	return found, err
}

// Load returns the raw frontmatter and the body lines of a KNOWLEDGE.md file.
func Load(path string) (Raw, []string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, nil, err
	}
	return Parse(data)
}

// Parse returns the raw frontmatter and the body lines of the content of a KNOWLEDGE.md.
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

// Build validates raw frontmatter. It returns the document (nil when a required field is
// unusable) and every schema violation found.
func Build(raw Raw) (*Document, []string) {
	var problems []string

	name := requiredString(raw, "name", &problems)
	if name != "" && !namePattern.MatchString(name) {
		problems = append(problems, fmt.Sprintf("name %s is not kebab-case", pyRepr(name)))
	}
	docType := requiredString(raw, "type", &problems)
	description := requiredString(raw, "description", &problems)
	scope := requiredString(raw, "scope", &problems)
	generated := signature(raw["generated"], "generated", &problems)

	var rawStatus any = defaultStatus
	if value, ok := raw["status"]; ok {
		rawStatus = value
	}
	status, _ := rawStatus.(string)
	if !contains(statusValues, status) {
		problems = append(problems, fmt.Sprintf("status %s is not one of %s", pyRepr(rawStatus), pyRepr(anyStrings(statusValues))))
		status = defaultStatus
	}

	keywords := stringList(raw, "keywords", &problems)
	sources := stringList(raw, "sources", &problems)
	var updated *Signature
	if value := raw["updated"]; value != nil {
		updated = signature(value, "updated", &problems)
	}
	verified := verifiedList(raw["verified"], &problems)

	if generated != nil && updated != nil && updated.At < generated.At {
		problems = append(problems, fmt.Sprintf("updated (%s) is older than generated (%s)", updated.At, generated.At))
	}
	changed := updated
	if changed == nil {
		changed = generated
	}
	if changed != nil && len(verified) > 0 {
		latest := verified[0].At
		for _, entry := range verified {
			if entry.At > latest {
				latest = entry.At
			}
		}
		if latest < changed.At {
			problems = append(problems, fmt.Sprintf(
				"verified (%s) is older than the last change (%s) — a meaningful change must clear 'verified'",
				latest, changed.At))
		}
	}

	if name == "" || docType == "" || description == "" || scope == "" || generated == nil {
		return nil, problems
	}
	return &Document{
		Name:        name,
		Type:        docType,
		Description: description,
		Scope:       scope,
		Generated:   *generated,
		Keywords:    keywords,
		Sources:     sources,
		Updated:     updated,
		Verified:    verified,
		Status:      status,
	}, problems
}

func requiredString(raw Raw, key string, problems *[]string) string {
	value, ok := raw[key].(string)
	if !ok || strings.TrimSpace(value) == "" {
		*problems = append(*problems, fmt.Sprintf("missing or empty required field '%s'", key))
		return ""
	}
	return strings.TrimSpace(value)
}

func stringList(raw Raw, key string, problems *[]string) []string {
	value, present := raw[key]
	if !present {
		return nil
	}
	list, ok := value.([]any)
	if !ok {
		*problems = append(*problems, fmt.Sprintf("'%s' must be a list of strings", key))
		return nil
	}
	result := make([]string, 0, len(list))
	for _, item := range list {
		text, ok := item.(string)
		if !ok {
			*problems = append(*problems, fmt.Sprintf("'%s' must be a list of strings", key))
			return nil
		}
		result = append(result, text)
	}
	return result
}

func signature(value any, key string, problems *[]string) *Signature {
	mapping, ok := value.(map[string]string)
	if !ok || mapping["by"] == "" || mapping["at"] == "" {
		*problems = append(*problems, fmt.Sprintf("missing '%s' with 'by' and 'at'", key))
		return nil
	}
	if !datePattern.MatchString(mapping["at"]) {
		*problems = append(*problems, fmt.Sprintf("%s.at must be YYYY-MM-DD, got %s", key, pyRepr(mapping["at"])))
		return nil
	}
	return &Signature{By: mapping["by"], At: mapping["at"]}
}

func verifiedList(value any, problems *[]string) []Signature {
	if value == nil {
		return nil
	}
	entries, ok := value.([]any)
	if !ok {
		entries = []any{value}
	}
	var result []Signature
	for _, entry := range entries {
		sig := signature(entry, "verified", problems)
		if sig == nil {
			return nil
		}
		result = append(result, *sig)
	}
	return result
}

func contains(values []string, value string) bool {
	i := sort.SearchStrings(values, value)
	return i < len(values) && values[i] == value
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
