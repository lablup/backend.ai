package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// scope is what a run checks: the changed documents (base), the given files, or everything.
type scope struct {
	root  string
	base  string
	files []string
}

// report collects the output. A failure makes the run exit 1; a review line does not.
type report struct {
	w        io.Writer
	failures int
}

func (r *report) fail(line string) {
	r.failures++
	_, _ = fmt.Fprintln(r.w, line)
}

func (r *report) review(line string) {
	_, _ = fmt.Fprintln(r.w, "review: "+line)
}

func newScope(root, base string, args []string) (*scope, error) {
	absRoot, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	sc := &scope{root: root, base: base}
	for _, arg := range args {
		path := arg
		if filepath.IsAbs(path) {
			rel, err := filepath.Rel(absRoot, path)
			if err != nil || strings.HasPrefix(rel, "..") {
				return nil, fmt.Errorf("%s is outside the root", arg)
			}
			path = rel
		}
		sc.files = append(sc.files, filepath.ToSlash(filepath.Clean(path)))
	}
	return sc, nil
}

// restricted reports whether the run is limited to some documents.
func (s *scope) restricted() bool {
	return s.base != "" || len(s.files) > 0
}

// selected returns the documents of the run among candidates: those changed since base or
// given as files; every candidate when the run is not restricted.
func (s *scope) selected(candidates []string) ([]string, error) {
	if !s.restricted() {
		return candidates, nil
	}
	chosen := map[string]bool{}
	if s.base != "" {
		changed, err := changedFiles(s.root, s.base)
		if err != nil {
			return nil, err
		}
		for _, path := range changed {
			chosen[path] = true
		}
	}
	for _, path := range s.files {
		chosen[path] = true
	}
	var result []string
	for _, path := range candidates {
		if chosen[path] {
			result = append(result, path)
		}
	}
	return result, nil
}

// changedSet returns the documents changed since base and the given files.
func (s *scope) changedSet() (map[string]bool, error) {
	set := map[string]bool{}
	if s.base != "" {
		changed, err := changedFiles(s.root, s.base)
		if err != nil {
			return nil, err
		}
		for _, path := range changed {
			set[path] = true
		}
	}
	for _, path := range s.files {
		set[path] = true
	}
	return set, nil
}

// allMarkdown returns every tracked or untracked, not ignored, .md file.
func (s *scope) allMarkdown() ([]string, error) {
	return s.listFiles("*.md")
}

func (s *scope) listFiles(pattern string) ([]string, error) {
	paths, err := gitLines(s.root, "ls-files", "--cached", "--others", "--exclude-standard", pattern)
	if err != nil {
		return nil, err
	}
	var existing []string
	for _, path := range paths {
		if info, err := os.Lstat(resolve(s.root, path)); err == nil && info.Mode().IsRegular() {
			existing = append(existing, path)
		}
	}
	sort.Strings(existing)
	return existing, nil
}
