package main

import (
	"bytes"
	"cmp"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"maps"
	"net/http"
	"os"
	"slices"
	"strings"
	"time"
	"unicode"
)

const descriptionLimit = 400

var severityColor = map[string]string{"CRITICAL": "Attention", "HIGH": "Attention", "MEDIUM": "Warning"}

// object is one JSON object of an Adaptive Card.
type object = map[string]any

func runNotify(ctx context.Context, args []string, stdout io.Writer) error {
	fs := flag.NewFlagSet("notify", flag.ContinueOnError)
	webhookURL := fs.String("webhook-url", "", "Teams webhook (required)")
	dryRun := fs.Bool("dry-run", false, "print the payload instead of sending it")
	// The report may come before the flags, which flag.Parse alone stops at.
	var files []string
	for rest := args; ; {
		if err := fs.Parse(rest); err != nil {
			return usageError{err}
		}
		if fs.NArg() == 0 {
			break
		}
		files = append(files, fs.Arg(0))
		rest = fs.Args()[1:]
	}
	hasURL := false
	fs.Visit(func(f *flag.Flag) { hasURL = hasURL || f.Name == "webhook-url" })
	// The arguments are not echoed: one of them is the secret URL.
	if len(files) != 1 || !hasURL {
		return usageError{errors.New("usage: cvewatch notify <cves.json> --webhook-url <url> [--dry-run]")}
	}

	raw, err := os.ReadFile(files[0])
	if err != nil {
		return err
	}
	var in report
	if err := json.Unmarshal(raw, &in); err != nil {
		return fmt.Errorf("%s: %w", files[0], err)
	}
	if in.CVEs == nil {
		return fmt.Errorf("%s: no \"cves\" list", files[0])
	}
	count := len(in.CVEs)
	if count == 0 {
		_, err := fmt.Fprintln(stdout, 0)
		return err
	}

	var body bytes.Buffer
	enc := json.NewEncoder(&body)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(payload(in)); err != nil {
		return err
	}
	if *dryRun {
		_, err := stdout.Write(body.Bytes())
		return err
	}
	if err := send(ctx, *webhookURL, body.Bytes()); err != nil {
		return err
	}
	_, err = fmt.Fprintln(stdout, count)
	return err
}

// send posts the payload. Its errors never carry the URL: the run log is public.
func send(ctx context.Context, webhookURL string, body []byte) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, webhookURL, bytes.NewReader(body))
	if err != nil {
		return errors.New("the webhook URL is not valid")
	}
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{Timeout: time.Minute}
	resp, err := client.Do(req)
	if err != nil {
		return errors.New("sending to the webhook failed")
	}
	defer func() { _ = resp.Body.Close() }()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("the webhook answered %d", resp.StatusCode)
	}
	return nil
}

func text(value any, style object) object {
	block := object{"type": "TextBlock", "text": value, "wrap": true}
	maps.Copy(block, style)
	return block
}

func cell(value any, style object) object {
	return object{"type": "TableCell", "items": []object{text(value, style)}}
}

func score(e entry) float64 {
	if e.CVSS == nil {
		return -1
	}
	f, err := e.CVSS.Score.Float64()
	if err != nil {
		return -1
	}
	return f
}

func header(e entry) object {
	severity, color := "No CVSS", "Default"
	if e.CVSS != nil {
		name := "None"
		if e.CVSS.Severity != nil {
			name = *e.CVSS.Severity
		}
		severity = fmt.Sprintf("%s %s", name, e.CVSS.Score)
		color = cmp.Or(severityColor[name], color)
	}
	title := fmt.Sprintf("[%s](%s)", e.ID, e.URL)
	return object{
		"type": "ColumnSet",
		"columns": []object{
			{
				"type":  "Column",
				"width": "stretch",
				"items": []object{text(title, object{"size": "Medium", "weight": "Bolder"})},
			},
			{
				"type":  "Column",
				"width": "auto",
				"items": []object{text(severity, object{"weight": "Bolder", "color": color})},
			},
		},
	}
}

func date(value string) string {
	return value[:min(len(value), 10)]
}

func facts(e entry) object {
	status := "-"
	if e.Status != nil {
		status = cmp.Or(*e.Status, status)
	}
	version := "-"
	if e.CVSS != nil {
		version = fmt.Sprintf("%s %s", e.CVSS.Version, e.CVSS.Score)
	}
	return object{
		"type": "FactSet",
		"facts": []object{
			{"title": "NVD status", "value": status},
			{"title": "Published", "value": date(e.Published)},
			{"title": "Modified", "value": date(e.LastModified)},
			{"title": "CVSS", "value": version},
		},
	}
}

func ranges(e entry) object {
	var header []object
	for _, name := range []string{"Advisory", "Package", "Affected", "Patched"} {
		header = append(header, cell(name, object{"weight": "Bolder"}))
	}
	rows := []object{{"type": "TableRow", "cells": header}}
	for _, a := range e.Advisories {
		for _, r := range a.Ranges {
			patched := "none"
			if r.FirstPatched != nil {
				patched = cmp.Or(*r.FirstPatched, patched)
			}
			rows = append(rows, object{
				"type": "TableRow",
				"cells": []object{
					cell(fmt.Sprintf("[%s](%s)", a.GHSAID, a.URL), nil),
					cell(r.Package, nil),
					cell(r.Vulnerable, nil),
					cell(patched, nil),
				},
			})
		}
	}
	if len(rows) == 1 {
		return text("No affected range in the GitHub Advisory Database", object{"color": "Warning"})
	}
	return object{
		"type":             "Table",
		"columns":          []object{{"width": 3}, {"width": 2}, {"width": 3}, {"width": 2}},
		"firstRowAsHeader": true,
		"showGridLines":    false,
		"rows":             rows,
	}
}

func links(e entry) object {
	actions := []object{{"type": "Action.OpenUrl", "title": "NVD", "url": e.URL}}
	for _, a := range e.Advisories {
		actions = append(actions, object{"type": "Action.OpenUrl", "title": a.GHSAID, "url": a.URL})
	}
	return object{"type": "ActionSet", "actions": actions}
}

func cveSection(e entry) object {
	description := e.Description
	if runes := []rune(description); len(runes) > descriptionLimit {
		description = strings.TrimRightFunc(string(runes[:descriptionLimit]), unicode.IsSpace) + "..."
	}
	return object{
		"type":      "Container",
		"separator": true,
		"spacing":   "Large",
		"items": []object{
			header(e),
			text(description, object{"isSubtle": true}),
			facts(e),
			ranges(e),
			links(e),
		},
	}
}

// payload builds the message: an Adaptive Card, which both Teams Workflows webhooks
// and legacy incoming webhooks accept. The highest score comes first.
func payload(in report) object {
	cves := slices.Clone(in.CVEs)
	slices.SortStableFunc(cves, func(a, b entry) int { return cmp.Compare(score(b), score(a)) })
	period := fmt.Sprintf("%s to %s", date(in.Start), date(in.End))
	body := []object{
		text(fmt.Sprintf("%d Backend.AI CVE(s) on NVD", len(cves)), object{"size": "Large", "weight": "Bolder"}),
		text("Published or modified "+period, object{"isSubtle": true, "spacing": "None"}),
	}
	for _, e := range cves {
		body = append(body, cveSection(e))
	}
	return object{
		"type": "message",
		"attachments": []object{
			{
				"contentType": "application/vnd.microsoft.card.adaptive",
				"content": object{
					"$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
					"type":    "AdaptiveCard",
					"version": "1.5",
					"msteams": object{"width": "Full"},
					"body":    body,
				},
			},
		},
	}
}
