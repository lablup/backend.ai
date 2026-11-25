// Package example is a minimal package that exercises the test tooling.
package example

import (
	"context"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
)

// NormalizeName trims and lower-cases a name.
func NormalizeName(name string) string {
	return strings.ToLower(strings.TrimSpace(name))
}

// CountDomains returns the number of rows in the domains table.
func CountDomains(ctx context.Context, pool *pgxpool.Pool) (int, error) {
	var n int
	if err := pool.QueryRow(ctx, "SELECT count(*) FROM domains").Scan(&n); err != nil {
		return 0, fmt.Errorf("count domains: %w", err)
	}
	return n, nil
}
