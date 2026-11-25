// Package dbtest gives a test an isolated PostgreSQL database with the migrations applied.
package dbtest

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io/fs"
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
	ciEnv   = "CI"
	timeout = 30 * time.Second

	// lockKey serializes template creation and CREATE DATABASE across the test processes.
	lockKey = 0x62616931313133
)

// New returns a pool on a new database with the migrations applied. The test is skipped
// under `-short` or without TEST_DATABASE_URL (a failure when CI is set). The pool is
// closed and the database dropped on test cleanup; it can be called from a t.Parallel test.
func New(t *testing.T) *pgxpool.Pool {
	t.Helper()
	if testing.Short() {
		t.Skip("skipped by -short")
	}
	adminURL := os.Getenv(urlEnv)
	if adminURL == "" {
		if os.Getenv(ciEnv) != "" {
			t.Fatalf("%s is not set while %s is set", urlEnv, ciEnv)
		}
		t.Skipf("%s is not set", urlEnv)
	}

	ctx, cancel := context.WithTimeout(t.Context(), timeout)
	defer cancel()

	name, err := createDatabase(ctx, adminURL)
	if err != nil {
		t.Fatal(err)
	}
	quoted := pgx.Identifier{name}.Sanitize()
	t.Cleanup(func() {
		if err := dropDatabase(adminURL, quoted); err != nil {
			t.Errorf("drop database %s: %v", name, err)
		}
	})

	poolCfg, err := pgxpool.ParseConfig(adminURL)
	if err != nil {
		t.Fatalf("parse %s: %v", urlEnv, err)
	}
	poolCfg.ConnConfig.Database = name
	pool, err := pgxpool.NewWithConfig(ctx, poolCfg)
	if err != nil {
		t.Fatalf("open pool: %v", err)
	}
	t.Cleanup(pool.Close)
	if err := pool.Ping(ctx); err != nil {
		t.Fatalf("ping the test database: %v", err)
	}
	return pool
}

// createDatabase creates a random database from the template of the current migrations.
func createDatabase(ctx context.Context, adminURL string) (string, error) {
	cfg, err := pgx.ParseConfig(adminURL)
	if err != nil {
		return "", fmt.Errorf("parse %s: %w", urlEnv, err)
	}
	b := make([]byte, 8)
	if _, err := rand.Read(b); err != nil {
		return "", fmt.Errorf("random database name: %w", err)
	}
	name := "test_" + hex.EncodeToString(b)

	files, err := readMigrations()
	if err != nil {
		return "", err
	}
	template := templateName(files)

	admin, err := pgx.ConnectConfig(ctx, cfg)
	if err != nil {
		return "", fmt.Errorf("connect to %s: %w", urlEnv, err)
	}
	defer closeConn(admin)
	if _, err := admin.Exec(ctx, "SELECT pg_advisory_lock($1)", int64(lockKey)); err != nil {
		return "", fmt.Errorf("lock: %w", err)
	}
	if err := ensureTemplate(ctx, admin, cfg, template, files); err != nil {
		return "", err
	}
	query := "CREATE DATABASE " + pgx.Identifier{name}.Sanitize() + " TEMPLATE " + pgx.Identifier{template}.Sanitize()
	if _, err := admin.Exec(ctx, query); err != nil {
		return "", fmt.Errorf("create database: %w", err)
	}
	return name, nil
}

// ensureTemplate builds the template database when it does not exist. The caller holds the lock.
func ensureTemplate(ctx context.Context, admin *pgx.Conn, cfg *pgx.ConnConfig, template string, files []file) error {
	var isTemplate bool
	err := admin.QueryRow(ctx, "SELECT datistemplate FROM pg_database WHERE datname = $1", template).Scan(&isTemplate)
	if err == nil && isTemplate {
		return nil
	}
	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		return fmt.Errorf("look up the template: %w", err)
	}
	quoted := pgx.Identifier{template}.Sanitize()
	if err == nil {
		// A previous run stopped before it marked the database as a template.
		if _, err := admin.Exec(ctx, "DROP DATABASE "+quoted+" WITH (FORCE)"); err != nil {
			return fmt.Errorf("drop the unfinished template: %w", err)
		}
	}
	if _, err := admin.Exec(ctx, "CREATE DATABASE "+quoted); err != nil {
		return fmt.Errorf("create the template: %w", err)
	}
	if err := migrate(ctx, cfg, template, files); err != nil {
		return err
	}
	if _, err := admin.Exec(ctx, "ALTER DATABASE "+quoted+" IS_TEMPLATE true"); err != nil {
		return fmt.Errorf("mark the template: %w", err)
	}
	return nil
}

// migrate uses its own connection: the dump sets an empty search_path on the session.
func migrate(ctx context.Context, cfg *pgx.ConnConfig, database string, files []file) error {
	cfg = cfg.Copy()
	cfg.Database = database
	conn, err := pgx.ConnectConfig(ctx, cfg)
	if err != nil {
		return fmt.Errorf("connect to the template: %w", err)
	}
	defer closeConn(conn)
	for _, f := range files {
		// Without arguments, Exec runs the file as one simple-protocol query string.
		if _, err := conn.Exec(ctx, string(f.sql)); err != nil {
			return fmt.Errorf("apply %s: %w", f.name, err)
		}
	}
	return nil
}

func dropDatabase(adminURL, quoted string) error {
	cfg, err := pgx.ParseConfig(adminURL)
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	conn, err := pgx.ConnectConfig(ctx, cfg)
	if err != nil {
		return err
	}
	defer closeConn(conn)
	_, err = conn.Exec(ctx, "DROP DATABASE IF EXISTS "+quoted+" WITH (FORCE)")
	return err
}

func closeConn(conn *pgx.Conn) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	_ = conn.Close(ctx)
}

type file struct {
	name string
	sql  []byte
}

func readMigrations() ([]file, error) {
	names, err := fs.Glob(migrations.Files, "*.sql")
	if err != nil {
		return nil, fmt.Errorf("list migrations: %w", err)
	}
	slices.Sort(names)
	files := make([]file, 0, len(names))
	for _, name := range names {
		sql, err := fs.ReadFile(migrations.Files, name)
		if err != nil {
			return nil, fmt.Errorf("read %s: %w", name, err)
		}
		files = append(files, file{name: name, sql: sql})
	}
	return files, nil
}

// templateName changes with the names and contents of the migration files.
func templateName(files []file) string {
	h := sha256.New()
	for _, f := range files {
		h.Write([]byte(f.name))
		h.Write([]byte{0})
		h.Write(f.sql)
		h.Write([]byte{0})
	}
	return "tmpl_" + hex.EncodeToString(h.Sum(nil))[:16]
}
