// Package dbtest gives a test an isolated PostgreSQL database with the migrations applied.
package dbtest

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io/fs"
	"net/url"
	"os"
	"slices"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/lablup/backend.ai/migrations"
)

const (
	urlEnv  = "TEST_DATABASE_URL"
	timeout = 30 * time.Second
)

// New skips the test under `-short` or without TEST_DATABASE_URL. Otherwise it
// creates a database, applies the migrations, and drops it when the test ends.
// Call it first in a test that needs a database, an external service or real time.
func New(t *testing.T) *pgxpool.Pool {
	t.Helper()
	if testing.Short() {
		t.Skip("skipped by -short")
	}
	adminURL := os.Getenv(urlEnv)
	if adminURL == "" {
		t.Skipf("%s is not set", urlEnv)
	}

	ctx, cancel := context.WithTimeout(t.Context(), timeout)
	defer cancel()

	admin, err := pgx.Connect(ctx, adminURL)
	if err != nil {
		t.Fatalf("connect to %s: %v", urlEnv, err)
	}
	defer func() { _ = admin.Close(context.WithoutCancel(ctx)) }()

	name, err := databaseName()
	if err != nil {
		t.Fatal(err)
	}
	quoted := pgx.Identifier{name}.Sanitize()
	if _, err := admin.Exec(ctx, "CREATE DATABASE "+quoted); err != nil {
		t.Fatalf("create database: %v", err)
	}
	t.Cleanup(func() {
		cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), timeout)
		defer cleanupCancel()
		conn, err := pgx.Connect(cleanupCtx, adminURL)
		if err != nil {
			t.Errorf("connect to drop database %s: %v", name, err)
			return
		}
		defer func() { _ = conn.Close(cleanupCtx) }()
		if _, err := conn.Exec(cleanupCtx, "DROP DATABASE IF EXISTS "+quoted+" WITH (FORCE)"); err != nil {
			t.Errorf("drop database %s: %v", name, err)
		}
	})

	testURL, err := withDatabase(adminURL, name)
	if err != nil {
		t.Fatal(err)
	}
	if err := migrate(ctx, testURL); err != nil {
		t.Fatal(err)
	}
	pool, err := pgxpool.New(ctx, testURL)
	if err != nil {
		t.Fatalf("open pool: %v", err)
	}
	t.Cleanup(pool.Close)
	return pool
}

func databaseName() (string, error) {
	b := make([]byte, 8)
	if _, err := rand.Read(b); err != nil {
		return "", fmt.Errorf("random database name: %w", err)
	}
	return "test_" + hex.EncodeToString(b), nil
}

func withDatabase(rawURL, name string) (string, error) {
	u, err := url.Parse(rawURL)
	if err != nil {
		return "", fmt.Errorf("parse %s: %w", urlEnv, err)
	}
	u.Path = "/" + name
	return u.String(), nil
}

// migrate uses its own connection: the dump sets an empty search_path on the
// session, so the pool must not reuse it.
func migrate(ctx context.Context, testURL string) error {
	conn, err := pgx.Connect(ctx, testURL)
	if err != nil {
		return fmt.Errorf("connect to the test database: %w", err)
	}
	defer func() { _ = conn.Close(context.WithoutCancel(ctx)) }()

	files, err := fs.Glob(migrations.Files, "*.sql")
	if err != nil {
		return fmt.Errorf("list migrations: %w", err)
	}
	slices.Sort(files)
	for _, file := range files {
		sql, err := fs.ReadFile(migrations.Files, file)
		if err != nil {
			return fmt.Errorf("read %s: %w", file, err)
		}
		// Without arguments, Exec runs the file as one simple-protocol query string.
		if _, err := conn.Exec(ctx, string(sql)); err != nil {
			return fmt.Errorf("apply %s: %w", file, err)
		}
	}
	return nil
}
