package kdoc

import (
	"errors"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func load(t *testing.T, text string) (Raw, error) {
	t.Helper()
	path := filepath.Join(t.TempDir(), FileName)
	if err := os.WriteFile(path, []byte(text), 0o644); err != nil {
		t.Fatal(err)
	}
	raw, _, err := Load(path)
	return raw, err
}

func TestLoad(t *testing.T) {
	tests := []struct {
		name    string
		text    string
		want    Raw
		wantErr string
	}{
		{"scalars and inline list", "---\nname: 'a b'\nkeywords: [x, \"y\"]\nempty: []\n---\n",
			Raw{"name": "a b", "keywords": []any{"x", "y"}, "empty": []any{}}, ""},
		{"nested mapping", "---\ngenerated:\n  by: human:x\n  at: 2026-01-02\n---\n",
			Raw{"generated": map[string]string{"by": "human:x", "at": "2026-01-02"}}, ""},
		{"block list of mappings", "---\nverified:\n  - by: a\n    at: 2026-01-01\n  - by: b\n    at: 2026-01-02\n---\n",
			Raw{"verified": []any{map[string]string{"by": "a", "at": "2026-01-01"}, map[string]string{"by": "b", "at": "2026-01-02"}}}, ""},
		{"block list of scalars", "---\nsources:\n  - a.go\n  - b.go\n---\n", Raw{"sources": []any{"a.go", "b.go"}}, ""},
		{"comment and blank lines", "---\n# c\n\nname: a\n---\n", Raw{"name": "a"}, ""},
		{"no fence", "name: a\n", nil, "frontmatter line 1: missing or unclosed '---' frontmatter fence"},
		{"unclosed fence", "---\nname: a\n", nil, "frontmatter line 1: missing or unclosed '---' frontmatter fence"},
		{"indentation", "---\n  name: a\n---\n", nil, "frontmatter line 1: unexpected indentation: 'name: a'"},
		{"not key value", "---\njust text\n---\n", nil, "frontmatter line 1: expected 'key: value', got 'just text'"},
		{"mixed block", "---\nk:\n  - a\n  b: c\n---\n", nil, "frontmatter line 3: a block cannot mix list items and mapping entries"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := load(t, tt.text)
			if tt.wantErr != "" {
				var parseErr *ParseError
				if err == nil || !errors.As(err, &parseErr) || err.Error() != tt.wantErr {
					t.Fatalf("err = %v, want %q", err, tt.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(got, tt.want) {
				t.Fatalf("got %#v, want %#v", got, tt.want)
			}
		})
	}
}

func TestBuild(t *testing.T) {
	full := func() Raw {
		return Raw{
			"name": "ok-name", "type": "guide", "description": "d", "scope": "src",
			"generated": map[string]string{"by": "a", "at": "2026-01-02"},
		}
	}
	tests := []struct {
		name   string
		change func(Raw)
		want   []string
	}{
		{"valid", func(Raw) {}, nil},
		{"empty type", func(r Raw) { r["type"] = " " }, []string{"missing or empty required field 'type'"}},
		{"keywords not list", func(r Raw) { r["keywords"] = "x" }, []string{"'keywords' must be a list of strings"}},
		{"updated before generated", func(r Raw) { r["updated"] = map[string]string{"by": "a", "at": "2025-01-01"} },
			[]string{"updated (2025-01-01) is older than generated (2026-01-02)"}},
		{"verified single mapping ok", func(r Raw) { r["verified"] = map[string]string{"by": "a", "at": "2026-01-02"} }, nil},
		{"status deprecated ok", func(r Raw) { r["status"] = "deprecated" }, nil},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			raw := full()
			tt.change(raw)
			_, problems := Build(raw)
			if strings.Join(problems, "|") != strings.Join(tt.want, "|") {
				t.Fatalf("got %q, want %q", problems, tt.want)
			}
		})
	}
}
