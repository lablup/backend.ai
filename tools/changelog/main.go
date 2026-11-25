// Command changelog checks the changelog fragments and batches them into a release.
//
// Usage, from the repository root:
//
//	go run ./tools/changelog check [--require --base <ref>]
//	go run ./tools/changelog batch <version> [--date YYYY-MM-DD]
package main

import (
	"flag"
	"fmt"
	"os"
	"time"
)

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "changelog:", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: changelog check|batch")
	}
	switch args[0] {
	case "check":
		fs := flag.NewFlagSet("check", flag.ContinueOnError)
		root := fs.String("root", ".", "repository root")
		require := fs.Bool("require", false, "fail when no fragment was added since --base")
		base := fs.String("base", "", "base ref of --require")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := check(*root); err != nil {
			return err
		}
		if *require {
			if *base == "" {
				return fmt.Errorf("--require needs --base")
			}
			return checkRequire(*root, *base)
		}
		return nil
	case "batch":
		fs := flag.NewFlagSet("batch", flag.ContinueOnError)
		root := fs.String("root", ".", "repository root")
		date := fs.String("date", "", "release date, YYYY-MM-DD (default today, UTC)")
		// The version comes first: flags after it are still parsed.
		if len(args) < 2 {
			return fmt.Errorf("usage: changelog batch <version> [--date YYYY-MM-DD]")
		}
		version := args[1]
		if err := fs.Parse(args[2:]); err != nil {
			return err
		}
		when := time.Now().UTC()
		if *date != "" {
			var err error
			if when, err = time.Parse("2006-01-02", *date); err != nil {
				return fmt.Errorf("invalid --date: %w", err)
			}
		}
		return batch(*root, version, when)
	default:
		return fmt.Errorf("unknown command %q", args[0])
	}
}
