// Command doclint checks the documents of the repository.
//
// Usage, from the repository root:
//
//	go run ./tools/doclint check [--only <check>[,<check>...]] [--base <ref> | --staged] [--allow-one-side]
//	    [--root <dir>] [--spec <file>] [file ...]
//	<text> | go run ./tools/doclint check --spec <file> --stdin
//
// The checks are frontmatter (knowledge document schema, names, paths, links), bilingual
// (document pairs), words (words the registry rejects), bep-length (proposal limits) and
// agents-lines (rule document length). Their criteria are in doclint.yaml and in the glossary
// registry. A check runs when the spec has its part: knowledge for frontmatter, pairs for
// bilingual, words, bep for bep-length and agents for agents-lines. --only with a check whose
// part is missing is an error.
//
// --spec reads the criteria from the file instead of doclint.yaml at the root. The paths of
// files in it are relative to the file. --stdin checks the words of the standard input as one
// Markdown document named <stdin>; it takes no files, --base or --staged.
//
// With --base, a check covers the documents changed since the ref, and the words check the
// lines added since it. --staged does the same for the staged changes. With files, a check
// covers those files. With none of these, it covers all.
// --allow-one-side reports a change to one document of a pair for review instead of failing.
// A failure exits 1. A line starting with "review:" is printed and does not fail.
package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/lablup/backend.ai/tools/internal/spec"
)

// check is one check of the tool. part names the part of the spec it reads and has reports
// whether the spec has it.
type check struct {
	name string
	part string
	has  func(*spec.Spec) bool
	run  func(*scope, *report) error
}

var checks = []check{
	{"frontmatter", "knowledge", func(s *spec.Spec) bool { return s.Knowledge != nil }, runFrontmatter},
	{"bilingual", "pairs", func(s *spec.Spec) bool { return s.Pairs != nil }, runBilingual},
	{"words", "words", func(s *spec.Spec) bool { return s.Words != nil }, runWords},
	{"bep-length", "bep", func(s *spec.Spec) bool { return s.BEP != nil }, runBEPLength},
	{"agents-lines", "agents", func(s *spec.Spec) bool { return s.Agents != nil }, runAgentsLines},
}

func main() {
	failed, err := run(os.Args[1:], os.Stdin, os.Stdout)
	if err != nil {
		fmt.Fprintln(os.Stderr, "doclint:", err)
		os.Exit(2)
	}
	if failed {
		os.Exit(1)
	}
}

func run(args []string, stdin io.Reader, stdout io.Writer) (failed bool, err error) {
	if len(args) == 0 || args[0] != "check" {
		return false, fmt.Errorf("usage: doclint check [--only <check>] [--base <ref> | --staged] [--allow-one-side] [--spec <file>] [--stdin] [file ...]")
	}
	fs := flag.NewFlagSet("check", flag.ContinueOnError)
	root := fs.String("root", ".", "repository root")
	specPath := fs.String("spec", "", "spec file, instead of "+spec.FileName+" at the root")
	base := fs.String("base", "", "check the documents changed since this git ref")
	staged := fs.Bool("staged", false, "check the staged changes")
	allowOneSide := fs.Bool("allow-one-side", false, "report a change to one document of a pair for review")
	fromStdin := fs.Bool("stdin", false, "check the words of the standard input")
	only := fs.String("only", "", "comma-separated checks to run: "+checkNames())
	if err := fs.Parse(args[1:]); err != nil {
		return false, err
	}
	if *staged && (*base != "" || fs.NArg() > 0) {
		return false, fmt.Errorf("--staged takes neither --base nor files")
	}
	if *fromStdin && (*staged || *base != "" || fs.NArg() > 0) {
		return false, fmt.Errorf("--stdin takes no files, --base or --staged")
	}
	sc, err := newScope(*root, *specPath, *base, fs.Args())
	if err != nil {
		return false, err
	}
	sc.staged = *staged
	sc.allowOneSide = *allowOneSide
	var selected []check
	if *fromStdin {
		if selected, err = stdinChecks(*only, sc.spec); err != nil {
			return false, err
		}
		data, err := io.ReadAll(stdin)
		if err != nil {
			return false, err
		}
		text := string(data)
		sc.stdin = &text
	} else {
		if selected, err = selectChecks(*only, sc.spec); err != nil {
			return false, err
		}
		if sc.spec.Documents == nil && len(selected) > 0 {
			return false, fmt.Errorf("%s: documents is missing, which the %s check reads", sc.specFile, selected[0].name)
		}
	}
	out := &report{w: stdout}
	for _, c := range selected {
		if err := c.run(sc, out); err != nil {
			return false, fmt.Errorf("%s: %w", c.name, err)
		}
	}
	return out.failures > 0, nil
}

// stdinChecks returns the words check, the only one a --stdin run executes.
func stdinChecks(only string, loaded *spec.Spec) ([]check, error) {
	if only != "" && only != "words" {
		return nil, fmt.Errorf("--stdin runs the words check only")
	}
	return selectChecks("words", loaded)
}

func checkNames() string {
	names := make([]string, len(checks))
	for i, c := range checks {
		names[i] = c.name
	}
	return strings.Join(names, ", ")
}

// selectChecks returns the checks named by only, or those whose part the spec has. A check
// named by only whose part is missing is an error.
func selectChecks(only string, loaded *spec.Spec) ([]check, error) {
	if only == "" {
		var selected []check
		for _, c := range checks {
			if c.has(loaded) {
				selected = append(selected, c)
			}
		}
		return selected, nil
	}
	var selected []check
	for name := range strings.SplitSeq(only, ",") {
		found := false
		for _, c := range checks {
			if c.name != strings.TrimSpace(name) {
				continue
			}
			if !c.has(loaded) {
				return nil, fmt.Errorf("the %s check needs %s in the spec", c.name, c.part)
			}
			selected = append(selected, c)
			found = true
		}
		if !found {
			return nil, fmt.Errorf("unknown check %q, want one of: %s", name, checkNames())
		}
	}
	return selected, nil
}
