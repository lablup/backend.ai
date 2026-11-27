package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/spec"
)

// scope is what a run checks: the documents changed since base or staged, the given files,
// or everything. A staged run reads the documents from the index.
type scope struct {
	spec   *spec.Spec
	root   string
	base   string
	staged bool
	files  []string
	// allowOneSide turns a change to one document of a pair into a review line.
	allowOneSide bool
	// specFile is the spec file, for the messages.
	specFile string
	// stdin is the text of the standard input: the only document of a --stdin run.
	stdin *string
}

// stdinName is the path of the standard input in a result.
const stdinName = "<stdin>"

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

// newScope reads the spec: the file named by specPath, else doclint.yaml at the root.
func newScope(root, specPath, base string, args []string) (*scope, error) {
	absRoot, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	if specPath == "" {
		specPath = filepath.Join(root, spec.FileName)
	}
	loaded, err := spec.LoadFile(specPath)
	if err != nil {
		return nil, err
	}
	sc := &scope{spec: loaded, root: root, base: base, specFile: specPath}
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

// diffing reports whether the run compares two versions: base with HEAD, or HEAD with the index.
func (s *scope) diffing() bool {
	return s.staged || s.base != ""
}

// diffRange is the git diff argument naming the two versions.
func (s *scope) diffRange() string {
	if s.staged {
		return "--cached"
	}
	return s.base + "...HEAD"
}

// read returns a document: the staged content in a staged run when the index has it.
func (s *scope) read(rel string) ([]byte, error) {
	if s.stdin != nil && rel == stdinName {
		return []byte(*s.stdin), nil
	}
	if s.staged && s.inIndex(rel) {
		out, err := git(s.root, "show", ":./"+rel)
		return []byte(out), err
	}
	return os.ReadFile(resolve(s.root, rel))
}

// has reports whether the checked version holds the file.
func (s *scope) has(rel string) bool {
	if s.staged {
		return s.inIndex(rel)
	}
	return exists(resolve(s.root, rel))
}

func (s *scope) inIndex(rel string) bool {
	_, err := git(s.root, "cat-file", "-e", ":./"+rel)
	return err == nil
}

// restricted reports whether the run is limited to some documents.
func (s *scope) restricted() bool {
	return s.diffing() || len(s.files) > 0
}

// selected returns the documents of the run among candidates: those changed or given as
// files; every candidate when the run is not restricted.
func (s *scope) selected(candidates []string) ([]string, error) {
	if !s.restricted() {
		return candidates, nil
	}
	chosen, err := s.changedSet()
	if err != nil {
		return nil, err
	}
	var result []string
	for _, path := range candidates {
		if chosen[path] {
			result = append(result, path)
		}
	}
	return result, nil
}

// changedSet returns the changed documents and the given files.
func (s *scope) changedSet() (map[string]bool, error) {
	set := map[string]bool{}
	if s.diffing() {
		changed, err := changedFiles(s)
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

// pathspec is the git pathspec of the documents with the suffix.
func (s *scope) pathspec(suffix string) string {
	return "*" + suffix
}

// allDocuments returns every tracked or untracked, not ignored, document; in a staged run,
// every document of the index.
func (s *scope) allDocuments() ([]string, error) {
	return s.listFiles(s.pathspec(s.spec.Documents.Extension))
}

func (s *scope) listFiles(pattern string) ([]string, error) {
	if s.staged {
		return s.listIndex(pattern)
	}
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

// listIndex returns the regular files of the index matching pattern.
func (s *scope) listIndex(pattern string) ([]string, error) {
	entries, err := gitLines(s.root, "ls-files", "--stage", pattern)
	if err != nil {
		return nil, err
	}
	var paths []string
	for _, entry := range entries {
		meta, path, ok := strings.Cut(entry, "\t")
		if ok && strings.HasPrefix(meta, "100") {
			paths = append(paths, path)
		}
	}
	sort.Strings(paths)
	return paths, nil
}
