package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"maps"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"slices"
	"strconv"
	"time"
)

const (
	nvdAPI = "https://services.nvd.nist.gov/rest/json/cves/2.0"

	defaultWindow = 8 * 24 * time.Hour
	// NVD rejects a lastMod range longer than 120 days.
	maxRange = 120 * 24 * time.Hour
	// Without an API key NVD allows 5 requests in a rolling 30 seconds.
	requestInterval = 6500 * time.Millisecond
	retries         = 3
)

// The CNA writes the product as "BackendAI"; "Backend.AI" alone finds none of them.
var keywords = []string{"Lablup", "BackendAI", "Backend.AI"}

// report is the output of find and the input of notify.
type report struct {
	Start string  `json:"start"`
	End   string  `json:"end"`
	CVEs  []entry `json:"cves"`
}

type entry struct {
	ID           string     `json:"id"`
	URL          string     `json:"url"`
	Published    string     `json:"published"`
	LastModified string     `json:"last_modified"`
	Status       *string    `json:"status"`
	CVSS         *cvss      `json:"cvss"`
	Description  string     `json:"description"`
	Advisories   []advisory `json:"advisories"`
}

type cvss struct {
	Version  string      `json:"version"`
	Score    json.Number `json:"score"`
	Severity *string     `json:"severity"`
}

type advisory struct {
	GHSAID string          `json:"ghsa_id"`
	URL    string          `json:"url"`
	Ranges []affectedRange `json:"ranges"`
}

type affectedRange struct {
	Package      string  `json:"package"`
	Vulnerable   *string `json:"vulnerable"`
	FirstPatched *string `json:"first_patched"`
}

type nvdCVE struct {
	ID           string  `json:"id"`
	Published    string  `json:"published"`
	LastModified string  `json:"lastModified"`
	VulnStatus   *string `json:"vulnStatus"`
	Descriptions []struct {
		Lang  string `json:"lang"`
		Value string `json:"value"`
	} `json:"descriptions"`
	Metrics map[string][]nvdMetric `json:"metrics"`
}

type nvdMetric struct {
	Type         string  `json:"type"`
	BaseSeverity *string `json:"baseSeverity"`
	CVSSData     struct {
		Version      string      `json:"version"`
		BaseScore    json.Number `json:"baseScore"`
		BaseSeverity *string     `json:"baseSeverity"`
	} `json:"cvssData"`
}

type nvdPage struct {
	ResultsPerPage  *int `json:"resultsPerPage"`
	TotalResults    *int `json:"totalResults"`
	Vulnerabilities []struct {
		CVE nvdCVE `json:"cve"`
	} `json:"vulnerabilities"`
}

func runFind(ctx context.Context, args []string, stdout io.Writer, now time.Time) error {
	fs := flag.NewFlagSet("find", flag.ContinueOnError)
	startArg := fs.String("start", "", "window start, ISO date or datetime (default --end minus 8 days)")
	endArg := fs.String("end", "", "window end, ISO date or datetime (default now)")
	if err := fs.Parse(args); err != nil {
		return usageError{err}
	}
	if fs.NArg() > 0 {
		return usageError{fmt.Errorf("find takes no argument: %q", fs.Args())}
	}
	start, end, err := window(*startArg, *endArg, now)
	if err != nil {
		return usageError{err}
	}

	client := newNVDClient()
	cves, err := searchAll(ctx, client.get, start, end)
	if err != nil {
		return err
	}
	out := report{Start: isoTime(start), End: isoTime(end), CVEs: []entry{}}
	for _, id := range slices.Sorted(maps.Keys(cves)) {
		advisories, err := findAdvisories(ctx, id)
		if err != nil {
			return err
		}
		out.CVEs = append(out.CVEs, newEntry(cves[id], advisories))
	}
	enc := json.NewEncoder(stdout)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	return enc.Encode(out)
}

// window resolves --start and --end; an empty value takes its default.
func window(startArg, endArg string, now time.Time) (start, end time.Time, err error) {
	end, err = parseTime(endArg, now.UTC().Truncate(time.Microsecond))
	if err != nil {
		return start, end, fmt.Errorf("--end: %w", err)
	}
	start, err = parseTime(startArg, end.Add(-defaultWindow))
	if err != nil {
		return start, end, fmt.Errorf("--start: %w", err)
	}
	if !start.Before(end) {
		return start, end, fmt.Errorf("--start %s is not before --end %s", isoTime(start), isoTime(end))
	}
	return start, end, nil
}

// parseTime reads an ISO date or datetime, as UTC when it carries no offset.
func parseTime(value string, fallback time.Time) (time.Time, error) {
	if value == "" {
		return fallback, nil
	}
	for _, date := range []string{"2006-01-02", "20060102"} {
		if t, err := time.Parse(date, value); err == nil {
			return t, nil
		}
		for _, sep := range []string{"T", " "} {
			for _, clock := range []string{"15", "15:04", "15:04:05", "1504", "150405"} {
				for _, zone := range []string{"", "Z07:00", "Z0700", "Z07"} {
					if t, err := time.Parse(date+sep+clock+zone, value); err == nil {
						return t.UTC().Truncate(time.Microsecond), nil
					}
				}
			}
		}
	}
	return time.Time{}, fmt.Errorf("%q is not an ISO date or datetime", value)
}

// isoTime formats a UTC time as the report writes it: "+00:00", microseconds only when set.
func isoTime(t time.Time) string {
	if t.Nanosecond()/1000 != 0 {
		return t.UTC().Format("2006-01-02T15:04:05.000000-07:00")
	}
	return t.UTC().Format("2006-01-02T15:04:05-07:00")
}

func nvdTime(t time.Time) string {
	return t.UTC().Format("2006-01-02T15:04:05") + ".000Z"
}

type getPage func(ctx context.Context, params url.Values) (nvdPage, error)

// searchAll searches each keyword and merges the hits by CVE id; the first hit wins.
func searchAll(ctx context.Context, get getPage, start, end time.Time) (map[string]nvdCVE, error) {
	cves := map[string]nvdCVE{}
	for _, keyword := range keywords {
		found, err := search(ctx, get, keyword, start, end)
		if err != nil {
			return nil, err
		}
		for _, cve := range found {
			if _, ok := cves[cve.ID]; !ok {
				cves[cve.ID] = cve
			}
		}
	}
	return cves, nil
}

// search reads every page of one keyword, in chunks of at most maxRange.
func search(ctx context.Context, get getPage, keyword string, start, end time.Time) ([]nvdCVE, error) {
	var found []nvdCVE
	for chunkStart := start; chunkStart.Before(end); {
		chunkEnd := chunkStart.Add(maxRange)
		if chunkEnd.After(end) {
			chunkEnd = end
		}
		for index := 0; ; {
			page, err := get(ctx, url.Values{
				"keywordSearch":    {keyword},
				"lastModStartDate": {nvdTime(chunkStart)},
				"lastModEndDate":   {nvdTime(chunkEnd)},
				"startIndex":       {strconv.Itoa(index)},
			})
			if err != nil {
				return nil, err
			}
			// A body without these is not a result page; reading it as empty would hide CVEs.
			if page.ResultsPerPage == nil || page.TotalResults == nil || page.Vulnerabilities == nil {
				return nil, errors.New("NVD response lacks resultsPerPage, totalResults or vulnerabilities")
			}
			for _, item := range page.Vulnerabilities {
				found = append(found, item.CVE)
			}
			index += *page.ResultsPerPage
			if *page.ResultsPerPage == 0 || index >= *page.TotalResults {
				break
			}
		}
		chunkStart = chunkEnd
	}
	return found, nil
}

type nvdClient struct {
	http        *http.Client
	sleep       func(time.Duration)
	lastRequest time.Time
}

func newNVDClient() *nvdClient {
	return &nvdClient{http: &http.Client{Timeout: time.Minute}, sleep: time.Sleep}
}

// get requests one page, pacing the requests and retrying rate limits and network errors.
func (c *nvdClient) get(ctx context.Context, params url.Values) (nvdPage, error) {
	target := nvdAPI + "?" + params.Encode()
	for attempt := 0; ; attempt++ {
		if wait := time.Until(c.lastRequest.Add(requestInterval)); wait > 0 {
			c.sleep(wait)
		}
		c.lastRequest = time.Now()
		page, retryable, err := c.fetch(ctx, target)
		if err == nil || !retryable || attempt == retries {
			return page, err
		}
		c.sleep(requestInterval * time.Duration(attempt+1))
	}
}

func (c *nvdClient) fetch(ctx context.Context, target string) (page nvdPage, retryable bool, err error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		return page, false, err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return page, true, err
	}
	defer func() { _ = resp.Body.Close() }()
	if resp.StatusCode != http.StatusOK {
		// 403 and 503 are how NVD reports rate limiting and overload.
		switch resp.StatusCode {
		case http.StatusForbidden, http.StatusTooManyRequests, http.StatusServiceUnavailable:
			retryable = true
		}
		return page, retryable, fmt.Errorf("GET %s: %s", target, resp.Status)
	}
	if err := json.NewDecoder(resp.Body).Decode(&page); err != nil {
		return page, false, fmt.Errorf("GET %s: %w", target, err)
	}
	return page, false, nil
}

func newEntry(cve nvdCVE, advisories []advisory) entry {
	return entry{
		ID:           cve.ID,
		URL:          "https://nvd.nist.gov/vuln/detail/" + cve.ID,
		Published:    cve.Published,
		LastModified: cve.LastModified,
		Status:       cve.VulnStatus,
		CVSS:         pickCVSS(cve),
		Description:  englishDescription(cve),
		Advisories:   advisories,
	}
}

func englishDescription(cve nvdCVE) string {
	for _, d := range cve.Descriptions {
		if d.Lang == "en" {
			return d.Value
		}
	}
	return ""
}

// pickCVSS takes the newest CVSS version present, and its primary metric when there is one.
func pickCVSS(cve nvdCVE) *cvss {
	for _, key := range []string{"cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"} {
		entries := cve.Metrics[key]
		if len(entries) == 0 {
			continue
		}
		primary := entries[0]
		if i := slices.IndexFunc(entries, func(m nvdMetric) bool { return m.Type == "Primary" }); i >= 0 {
			primary = entries[i]
		}
		data := primary.CVSSData
		severity := data.BaseSeverity
		if severity == nil || *severity == "" {
			severity = primary.BaseSeverity
		}
		return &cvss{Version: data.Version, Score: data.BaseScore, Severity: severity}
	}
	return nil
}

// findAdvisories reads the GitHub Advisory Database entries of a CVE with `gh api`.
func findAdvisories(ctx context.Context, cveID string) ([]advisory, error) {
	cmd := exec.CommandContext(ctx, "gh", "api", "--method", "GET", "/advisories", "-f", "cve_id="+cveID)
	cmd.Stderr = os.Stderr
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("gh api /advisories: %w", err)
	}
	return parseAdvisories(out)
}

func parseAdvisories(body []byte) ([]advisory, error) {
	var raw []struct {
		GHSAID          string `json:"ghsa_id"`
		HTMLURL         string `json:"html_url"`
		Vulnerabilities []struct {
			Package struct {
				Ecosystem string `json:"ecosystem"`
				Name      string `json:"name"`
			} `json:"package"`
			VulnerableVersionRange *string `json:"vulnerable_version_range"`
			FirstPatchedVersion    *string `json:"first_patched_version"`
		} `json:"vulnerabilities"`
	}
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("gh api /advisories: %w", err)
	}
	advisories := []advisory{}
	for _, a := range raw {
		ranges := []affectedRange{}
		for _, v := range a.Vulnerabilities {
			ranges = append(ranges, affectedRange{
				Package:      v.Package.Ecosystem + ":" + v.Package.Name,
				Vulnerable:   v.VulnerableVersionRange,
				FirstPatched: v.FirstPatchedVersion,
			})
		}
		advisories = append(advisories, advisory{GHSAID: a.GHSAID, URL: a.HTMLURL, Ranges: ranges})
	}
	return advisories, nil
}
