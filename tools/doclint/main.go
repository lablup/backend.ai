// Command doclint checks the documents of the repository.
//
// Usage, from the repository root:
//
//	go run ./tools/doclint check [--only <check>[,<check>...]] [--base <ref> | --staged] [--root <dir>] [file ...]
//	go run ./tools/doclint generate [--root <dir>]
//
// The checks are frontmatter (knowledge document schema, names, paths, links), bilingual
// (document pairs), words (words the glossary rejects), bep-length (proposal limits) and
// agents-lines (rule document length). Their criteria are in doclint.yaml and in the glossary
// registry. generate writes the glossary documents from the registry.
//
// With --base, a check covers the documents changed since the ref, and the words check the
// lines added since it. --staged does the same for the staged changes. With files, a check
// covers those files. With none of these, it covers all.
// A failure exits 1. A line starting with "review:" is printed and does not fail.
//
//go:generate go run . generate --root ../..
package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"strings"
)

type check struct {
	name string
	run  func(*scope, *report) error
}

var checks = []check{
	{"frontmatter", runFrontmatter},
	{"bilingual", runBilingual},
	{"words", runWords},
	{"bep-length", runBEPLength},
	{"agents-lines", runAgentsLines},
}

func main() {
	failed, err := run(os.Args[1:], os.Stdout)
	if err != nil {
		fmt.Fprintln(os.Stderr, "doclint:", err)
		os.Exit(2)
	}
	if failed {
		os.Exit(1)
	}
}

func run(args []string, stdout io.Writer) (failed bool, err error) {
	if len(args) > 0 && args[0] == "generate" {
		return false, runGenerate(args[1:])
	}
	if len(args) == 0 || args[0] != "check" {
		return false, fmt.Errorf("usage: doclint check [--only <check>] [--base <ref> | --staged] [file ...]")
	}
	fs := flag.NewFlagSet("check", flag.ContinueOnError)
	root := fs.String("root", ".", "repository root")
	base := fs.String("base", "", "check the documents changed since this git ref")
	staged := fs.Bool("staged", false, "check the staged changes")
	only := fs.String("only", "", "comma-separated checks to run: "+checkNames())
	if err := fs.Parse(args[1:]); err != nil {
		return false, err
	}
	selected, err := selectChecks(*only)
	if err != nil {
		return false, err
	}
	if *staged && (*base != "" || fs.NArg() > 0) {
		return false, fmt.Errorf("--staged takes neither --base nor files")
	}
	sc, err := newScope(*root, *base, fs.Args())
	if err != nil {
		return false, err
	}
	sc.staged = *staged
	out := &report{w: stdout}
	for _, c := range selected {
		if err := c.run(sc, out); err != nil {
			return false, fmt.Errorf("%s: %w", c.name, err)
		}
	}
	return out.failures > 0, nil
}

func checkNames() string {
	names := make([]string, len(checks))
	for i, c := range checks {
		names[i] = c.name
	}
	return strings.Join(names, ", ")
}

func selectChecks(only string) ([]check, error) {
	if only == "" {
		return checks, nil
	}
	var selected []check
	for name := range strings.SplitSeq(only, ",") {
		found := false
		for _, c := range checks {
			if c.name == strings.TrimSpace(name) {
				selected = append(selected, c)
				found = true
			}
		}
		if !found {
			return nil, fmt.Errorf("unknown check %q, want one of: %s", name, checkNames())
		}
	}
	return selected, nil
}
