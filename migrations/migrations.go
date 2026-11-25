// Package migrations embeds the SQL migration files.
package migrations

import "embed"

// Files holds the migration files, applied in file name order.
//
//go:embed *.sql
var Files embed.FS
