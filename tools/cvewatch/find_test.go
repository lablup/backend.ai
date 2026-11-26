package main

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"reflect"
	"strings"
	"testing"
	"time"
)

func TestWindow(t *testing.T) {
	now := time.Date(2026, 11, 26, 6, 0, 0, 123456789, time.UTC)
	tests := []struct {
		name      string
		start     string
		end       string
		wantStart string
		wantEnd   string
		wantErr   string
	}{
		{name: "defaults", wantStart: "2026-11-18T06:00:00.123456+00:00", wantEnd: "2026-11-26T06:00:00.123456+00:00"},
		{name: "start from end", end: "2026-11-20", wantStart: "2026-11-12T00:00:00+00:00", wantEnd: "2026-11-20T00:00:00+00:00"},
		{name: "offset", start: "2026-11-01T09:00:00+09:00", end: "2026-11-02T12:30Z", wantStart: "2026-11-01T00:00:00+00:00", wantEnd: "2026-11-02T12:30:00+00:00"},
		{name: "naive is UTC", start: "2026-11-01 01:02:03.5", end: "20261102", wantStart: "2026-11-01T01:02:03.500000+00:00", wantEnd: "2026-11-02T00:00:00+00:00"},
		{name: "not before", start: "2026-11-02", end: "2026-11-02", wantErr: "is not before"},
		{name: "bad start", start: "yesterday", wantErr: "--start"},
		{name: "bad end", end: "2026-13-01", wantErr: "--end"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			start, end, err := window(tt.start, tt.end, now)
			if tt.wantErr != "" {
				if err == nil || !strings.Contains(err.Error(), tt.wantErr) {
					t.Fatalf("err = %v, want containing %q", err, tt.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if got := isoTime(start); got != tt.wantStart {
				t.Errorf("start = %s, want %s", got, tt.wantStart)
			}
			if got := isoTime(end); got != tt.wantEnd {
				t.Errorf("end = %s, want %s", got, tt.wantEnd)
			}
		})
	}
}

func decodePage(t *testing.T, body string) nvdPage {
	t.Helper()
	var page nvdPage
	if err := json.Unmarshal([]byte(body), &page); err != nil {
		t.Fatal(err)
	}
	return page
}

func TestSearchAllMergesByID(t *testing.T) {
	pages := map[string]string{
		"Lablup/0":     `{"resultsPerPage":1,"totalResults":2,"vulnerabilities":[{"cve":{"id":"CVE-2","published":"first"}}]}`,
		"Lablup/1":     `{"resultsPerPage":1,"totalResults":2,"vulnerabilities":[{"cve":{"id":"CVE-1"}}]}`,
		"BackendAI/0":  `{"resultsPerPage":1,"totalResults":1,"vulnerabilities":[{"cve":{"id":"CVE-2","published":"second"}}]}`,
		"Backend.AI/0": `{"resultsPerPage":0,"totalResults":0,"vulnerabilities":[]}`,
	}
	get := func(_ context.Context, p url.Values) (nvdPage, error) {
		return decodePage(t, pages[p.Get("keywordSearch")+"/"+p.Get("startIndex")]), nil
	}
	start := time.Date(2026, 11, 1, 0, 0, 0, 0, time.UTC)
	got, err := searchAll(context.Background(), get, start, start.Add(time.Hour))
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 2 || got["CVE-2"].Published != "first" || got["CVE-1"].ID != "CVE-1" {
		t.Fatalf("got %+v", got)
	}
}

func TestSearchChunksTheRange(t *testing.T) {
	var ranges []string
	get := func(_ context.Context, p url.Values) (nvdPage, error) {
		ranges = append(ranges, p.Get("lastModStartDate")+"~"+p.Get("lastModEndDate"))
		return decodePage(t, `{"resultsPerPage":0,"totalResults":0,"vulnerabilities":[]}`), nil
	}
	start := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
	if _, err := search(context.Background(), get, "Lablup", start, start.Add(150*24*time.Hour)); err != nil {
		t.Fatal(err)
	}
	want := []string{
		"2026-01-01T00:00:00.000Z~2026-05-01T00:00:00.000Z",
		"2026-05-01T00:00:00.000Z~2026-05-31T00:00:00.000Z",
	}
	if !reflect.DeepEqual(ranges, want) {
		t.Fatalf("ranges = %v, want %v", ranges, want)
	}
}

func TestSearchRejectsAnUnexpectedBody(t *testing.T) {
	get := func(context.Context, url.Values) (nvdPage, error) { return decodePage(t, `{}`), nil }
	start := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
	if _, err := search(context.Background(), get, "Lablup", start, start.Add(time.Hour)); err == nil {
		t.Fatal("want an error")
	}
}

type roundTrip func(*http.Request) (*http.Response, error)

func (f roundTrip) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestGetRetries(t *testing.T) {
	tests := []struct {
		name      string
		status    []int
		wantCalls int
		wantErr   bool
	}{
		{"succeeds after rate limits", []int{403, 429, 503, 200}, 4, false},
		{"gives up", []int{503, 503, 503, 503}, 4, true},
		{"does not retry", []int{404}, 1, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			calls := 0
			client := &nvdClient{
				sleep: func(time.Duration) {},
				http: &http.Client{Transport: roundTrip(func(*http.Request) (*http.Response, error) {
					status := tt.status[calls]
					calls++
					return &http.Response{StatusCode: status, Body: io.NopCloser(strings.NewReader(`{}`))}, nil
				})},
			}
			_, err := client.get(context.Background(), url.Values{})
			if (err != nil) != tt.wantErr || calls != tt.wantCalls {
				t.Fatalf("calls = %d, err = %v", calls, err)
			}
		})
	}
}

func TestNewEntry(t *testing.T) {
	var cve nvdCVE
	err := json.Unmarshal([]byte(`{
		"id": "CVE-2026-1",
		"published": "2026-11-01T00:00:00.000",
		"lastModified": "2026-11-02T00:00:00.000",
		"descriptions": [{"lang": "es", "value": "no"}, {"lang": "en", "value": "yes"}],
		"metrics": {
			"cvssMetricV2": [{"type": "Primary", "cvssData": {"version": "2.0", "baseScore": 5.0}}],
			"cvssMetricV31": [
				{"type": "Secondary", "cvssData": {"version": "3.1", "baseScore": 1.0}},
				{"type": "Primary", "baseSeverity": "HIGH", "cvssData": {"version": "3.1", "baseScore": 8.0}}
			]
		}
	}`), &cve)
	if err != nil {
		t.Fatal(err)
	}
	got, err := json.Marshal(newEntry(cve, []advisory{}))
	if err != nil {
		t.Fatal(err)
	}
	want := `{"id":"CVE-2026-1","url":"https://nvd.nist.gov/vuln/detail/CVE-2026-1",` +
		`"published":"2026-11-01T00:00:00.000","last_modified":"2026-11-02T00:00:00.000","status":null,` +
		`"cvss":{"version":"3.1","score":8.0,"severity":"HIGH"},"description":"yes","advisories":[]}`
	if string(got) != want {
		t.Fatalf("got %s\nwant %s", got, want)
	}
}

func TestParseAdvisories(t *testing.T) {
	got, err := parseAdvisories([]byte(`[{"ghsa_id":"GHSA-x","html_url":"https://example.com/x","vulnerabilities":[
		{"package":{"ecosystem":"pip","name":"p"},"vulnerable_version_range":"< 2","first_patched_version":null}]}]`))
	if err != nil {
		t.Fatal(err)
	}
	want := `[{"ghsa_id":"GHSA-x","url":"https://example.com/x","ranges":[{"package":"pip:p","vulnerable":"< 2","first_patched":null}]}]`
	if b := marshal(t, got); b != want+"\n" {
		t.Fatalf("got %s", b)
	}
	empty, err := parseAdvisories([]byte(`[]`))
	if err != nil || empty == nil || len(empty) != 0 {
		t.Fatalf("empty = %#v, %v", empty, err)
	}
}
