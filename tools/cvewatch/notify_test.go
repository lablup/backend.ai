package main

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const sampleReport = `{"start":"2026-11-18T00:00:00+00:00","end":"2026-11-26T00:00:00+00:00","cves":[
{"id":"CVE-1","url":"u1","published":"2026-11-19T00:00:00.000","last_modified":"2026-11-20T00:00:00.000",
 "status":null,"cvss":null,"description":"d","advisories":[]},
{"id":"CVE-2","url":"u2","published":"2026-11-19T00:00:00.000","last_modified":"2026-11-20T00:00:00.000",
 "status":"Analyzed","cvss":{"version":"3.1","score":10.0,"severity":"CRITICAL"},"description":"d",
 "advisories":[{"ghsa_id":"GHSA-x","url":"g","ranges":[{"package":"pip:p","vulnerable":"< 2","first_patched":null}]}]}
]}`

func sample(t *testing.T) report {
	t.Helper()
	var r report
	if err := json.Unmarshal([]byte(sampleReport), &r); err != nil {
		t.Fatal(err)
	}
	return r
}

func marshal(t *testing.T, v any) string {
	t.Helper()
	var b bytes.Buffer
	enc := json.NewEncoder(&b)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		t.Fatal(err)
	}
	return b.String()
}

func TestPayload(t *testing.T) {
	got := marshal(t, payload(sample(t)))
	for _, want := range []string{
		`"2 Backend.AI CVE(s) on NVD"`,
		`"Published or modified 2026-11-18 to 2026-11-26"`,
		`"CRITICAL 10.0"`, `"Attention"`, `"3.1 10.0"`, `"No CVSS"`, `"Default"`,
		`"[GHSA-x](g)"`, `"< 2"`, `"none"`,
		`"No affected range in the GitHub Advisory Database"`,
	} {
		if !strings.Contains(got, want) {
			t.Errorf("payload lacks %s", want)
		}
	}
	if strings.Index(got, "[CVE-2](u2)") > strings.Index(got, "[CVE-1](u1)") {
		t.Error("the highest score must come first")
	}
}

func TestDescriptionIsCut(t *testing.T) {
	long := strings.Repeat("é", descriptionLimit-1) + " tail"
	got := marshal(t, cveSection(entry{Description: long}))
	want := `"` + strings.Repeat("é", descriptionLimit-1) + `..."`
	if !strings.Contains(got, want) {
		t.Fatalf("got %s", got)
	}
}

func writeReport(t *testing.T, content string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "cves.json")
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestNotify(t *testing.T) {
	full := writeReport(t, sampleReport)
	empty := writeReport(t, `{"start":"s","end":"e","cves":[]}`)
	const secret = "secret-token"
	tests := []struct {
		name    string
		args    []string
		want    string
		wantErr string
	}{
		{name: "dry run", args: []string{full, "--webhook-url", secret, "--dry-run"}, want: `"type":"message"`},
		{name: "flags first", args: []string{"--dry-run", "--webhook-url=" + secret, full}, want: `"type":"message"`},
		{name: "nothing to send", args: []string{empty, "--webhook-url", secret}, want: "0\n"},
		{name: "no URL", args: []string{full}, wantErr: "usage"},
		{name: "extra argument", args: []string{full, secret, "--webhook-url", secret}, wantErr: "usage"},
		{name: "no list", args: []string{writeReport(t, `{}`), "--webhook-url", secret}, wantErr: "cves"},
		{name: "unreachable", args: []string{full, "--webhook-url", "nope://" + secret}, wantErr: "failed"},
		{name: "invalid URL", args: []string{full, "--webhook-url", "://" + secret}, wantErr: "not valid"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var out bytes.Buffer
			err := runNotify(context.Background(), tt.args, &out)
			if tt.wantErr != "" {
				if err == nil || !strings.Contains(err.Error(), tt.wantErr) {
					t.Fatalf("err = %v, want containing %q", err, tt.wantErr)
				}
				if strings.Contains(err.Error(), secret) || out.Len() != 0 {
					t.Fatalf("leaked: err = %v, out = %q", err, out.String())
				}
				return
			}
			if err != nil || !strings.Contains(out.String(), tt.want) {
				t.Fatalf("out = %q, err = %v", out.String(), err)
			}
		})
	}
}
