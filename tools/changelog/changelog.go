package main

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

const (
	unreleasedDir = "changes/unreleased"
	changesDir    = "changes"
	changelogFile = "CHANGELOG.md"
)

// kinds lists the fragment kinds in the order batch prints them.
var kinds = []struct{ name, title string }{
	{"breaking", "Breaking Changes"},
	{"feature", "Features"},
	{"deprecation", "Deprecations"},
	{"fix", "Fixes"},
	{"doc", "Documentation"},
	{"misc", "Miscellaneous"},
}

var (
	issueKeyRe = regexp.MustCompile(`^([A-Z][A-Z0-9]*)-([0-9]+)$`)
	versionRe  = regexp.MustCompile(`^[0-9A-Za-z][0-9A-Za-z._+-]*$`)
)

type fragment struct {
	key     string
	kind    string
	content string
	prefix  string
	number  int
}

func kindTitle(kind string) (string, bool) {
	for _, k := range kinds {
		if k.name == kind {
			return k.title, true
		}
	}
	return "", false
}

// parseName splits `<issue key>.<kind>.md`.
func parseName(name string) (key, kind string, err error) {
	stem, ok := strings.CutSuffix(name, ".md")
	if !ok {
		return "", "", fmt.Errorf("%s: the name must be <issue key>.<kind>.md", name)
	}
	i := strings.LastIndex(stem, ".")
	if i < 0 {
		return "", "", fmt.Errorf("%s: the name must be <issue key>.<kind>.md", name)
	}
	key, kind = stem[:i], stem[i+1:]
	if !issueKeyRe.MatchString(key) {
		return "", "", fmt.Errorf("%s: %q is not an issue key such as BAI-123", name, key)
	}
	if _, ok := kindTitle(kind); !ok {
		names := make([]string, len(kinds))
		for j, k := range kinds {
			names[j] = k.name
		}
		return "", "", fmt.Errorf("%s: unknown kind %q (one of %s)", name, kind, strings.Join(names, ", "))
	}
	return key, kind, nil
}

// readFragments reads and validates every fragment under root. It returns the
// valid ones together with one error per invalid file.
func readFragments(root string) ([]fragment, []error) {
	dir := filepath.Join(root, unreleasedDir)
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, []error{err}
	}
	var frags []fragment
	var errs []error
	for _, e := range entries {
		name := e.Name()
		if name == ".gitkeep" {
			continue
		}
		if e.IsDir() {
			errs = append(errs, fmt.Errorf("%s: a directory is not a fragment", name))
			continue
		}
		key, kind, err := parseName(name)
		if err != nil {
			errs = append(errs, err)
			continue
		}
		b, err := os.ReadFile(filepath.Join(dir, name))
		if err != nil {
			errs = append(errs, err)
			continue
		}
		content := strings.TrimSpace(string(b))
		if content == "" {
			errs = append(errs, fmt.Errorf("%s: the content is empty", name))
			continue
		}
		m := issueKeyRe.FindStringSubmatch(key)
		n, _ := strconv.Atoi(m[2])
		frags = append(frags, fragment{key: key, kind: kind, content: content, prefix: m[1], number: n})
	}
	return frags, errs
}

func check(root string) error {
	_, errs := readFragments(root)
	return errors.Join(errs...)
}

// addedFragments lists the fragments added after base, as files in unreleasedDir.
func addedFragments(root, base string) ([]string, error) {
	cmd := exec.Command("git", "-C", root, "diff", "--name-only", "--diff-filter=A", base+"...HEAD", "--", unreleasedDir)
	out, err := cmd.Output()
	if err != nil {
		var ee *exec.ExitError
		if errors.As(err, &ee) {
			return nil, fmt.Errorf("git diff against %s: %s", base, strings.TrimSpace(string(ee.Stderr)))
		}
		return nil, err
	}
	var added []string
	for _, line := range strings.Split(string(out), "\n") {
		if line != "" && filepath.Base(line) != ".gitkeep" {
			added = append(added, line)
		}
	}
	return added, nil
}

func checkRequire(root, base string) error {
	added, err := addedFragments(root, base)
	if err != nil {
		return err
	}
	if len(added) == 0 {
		return fmt.Errorf("no fragment added under %s since %s", unreleasedDir, base)
	}
	return nil
}

func render(version, date string, frags []fragment) string {
	var b strings.Builder
	fmt.Fprintf(&b, "## %s (%s)\n", version, date)
	if len(frags) == 0 {
		b.WriteString("\nNo user-facing changes.\n")
		return b.String()
	}
	for _, k := range kinds {
		var group []fragment
		for _, f := range frags {
			if f.kind == k.name {
				group = append(group, f)
			}
		}
		if len(group) == 0 {
			continue
		}
		sort.Slice(group, func(i, j int) bool {
			if group[i].prefix != group[j].prefix {
				return group[i].prefix < group[j].prefix
			}
			return group[i].number < group[j].number
		})
		fmt.Fprintf(&b, "\n### %s\n\n", k.title)
		for _, f := range group {
			lines := strings.Split(f.content, "\n")
			lines[0] = "- " + lines[0]
			for i := 1; i < len(lines); i++ {
				if lines[i] != "" {
					lines[i] = "  " + lines[i]
				}
			}
			lines[len(lines)-1] += fmt.Sprintf(" (%s)", f.key)
			b.WriteString(strings.Join(lines, "\n") + "\n")
		}
	}
	return b.String()
}

// insertAfterTitle puts section below the first title of the changelog.
func insertAfterTitle(changelog, section string) string {
	lines := strings.Split(changelog, "\n")
	title := 0
	switch {
	case len(lines) > 1 && strings.Trim(lines[1], "=") == "" && lines[1] != "":
		title = 2
	case len(lines) > 0 && strings.HasPrefix(lines[0], "#"):
		title = 1
	}
	head := strings.Join(lines[:title], "\n")
	rest := strings.TrimLeft(strings.Join(lines[title:], "\n"), "\n")
	if head != "" {
		head += "\n\n"
	}
	return head + section + "\n" + rest
}

func batch(root, version string, date time.Time, allowEmpty bool) error {
	if !versionRe.MatchString(version) {
		return fmt.Errorf("invalid version %q", version)
	}
	versionFile := filepath.Join(root, changesDir, version+".md")
	if _, err := os.Stat(versionFile); err == nil {
		return fmt.Errorf("%s already exists", filepath.Join(changesDir, version+".md"))
	} else if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	frags, errs := readFragments(root)
	if err := errors.Join(errs...); err != nil {
		return err
	}
	if len(frags) == 0 && !allowEmpty {
		return fmt.Errorf("no fragment under %s", unreleasedDir)
	}
	section := render(version, date.Format("2006-01-02"), frags)

	path := filepath.Join(root, changelogFile)
	old, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	if err := os.WriteFile(versionFile, []byte(section), 0o644); err != nil {
		return err
	}
	if err := os.WriteFile(path, []byte(insertAfterTitle(string(old), section)), 0o644); err != nil {
		return err
	}
	for _, f := range frags {
		if err := os.Remove(filepath.Join(root, unreleasedDir, f.key+"."+f.kind+".md")); err != nil {
			return err
		}
	}
	return nil
}
