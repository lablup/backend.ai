// Command cvewatch finds the NVD CVEs about Backend.AI and posts them to a Teams webhook.
//
// Usage, from the repository root:
//
//	go run ./tools/cvewatch find [--start <time>] [--end <time>]
//	go run ./tools/cvewatch notify <cves.json> --webhook-url <url> [--dry-run]
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"time"
)

const usage = "usage: cvewatch find|notify"

// usageError marks a wrong invocation: the exit status is 2.
type usageError struct{ err error }

func (e usageError) Error() string { return e.err.Error() }

func main() {
	if err := run(context.Background(), os.Args[1:], os.Stdout); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return
		}
		fmt.Fprintln(os.Stderr, "cvewatch:", err)
		if errors.As(err, &usageError{}) {
			os.Exit(2)
		}
		os.Exit(1)
	}
}

func run(ctx context.Context, args []string, stdout io.Writer) error {
	if len(args) == 0 {
		return usageError{errors.New(usage)}
	}
	switch args[0] {
	case "find":
		return runFind(ctx, args[1:], stdout, time.Now())
	case "notify":
		return runNotify(ctx, args[1:], stdout)
	default:
		return usageError{fmt.Errorf("unknown command %q: %s", args[0], usage)}
	}
}
