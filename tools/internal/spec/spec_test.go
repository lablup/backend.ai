package spec

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestDecodeRejectsFlowMappings(t *testing.T) {
	type target struct {
		Name  string              `yaml:"name,omitempty" spec:"optional"`
		List  []string            `yaml:"list,omitempty" spec:"optional"`
		Items []map[string]string `yaml:"items,omitempty" spec:"optional"`
		Map   map[string]string   `yaml:"map,omitempty" spec:"optional"`
	}
	tests := []struct {
		name string
		text string
		line string
	}{
		{"block", "name: a\nmap:\n  en: a\nitems:\n  - en: a\n", ""},
		{"flow list", "list: [a, b]\n", ""},
		{"braces in a string", "name: \"{en: a}\"\n", ""},
		{"top level", "{name: a}\n", ":1:"},
		{"value", "name: a\nmap: {en: a}\n", ":2:"},
		{"list item", "items:\n  - en: a\n  - {en: b}\n", ":3:"},
		{"empty", "name: a\n\nmap: {}\n", ":3:"},
		{"over lines", "map: {\n  en: a}\n", ":1:"},
		{"pair in a flow list", "list: [a: b]\n", ":1:"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "spec.yaml")
			if err := os.WriteFile(path, []byte(tt.text), 0o644); err != nil {
				t.Fatal(err)
			}
			var got target
			err := Decode(path, &got)
			if tt.line == "" {
				if err != nil {
					t.Fatal(err)
				}
				return
			}
			want := path + tt.line + " mapping in flow style"
			if err == nil || !strings.Contains(err.Error(), want) {
				t.Fatalf("err = %v, want %q", err, want)
			}
		})
	}
}
