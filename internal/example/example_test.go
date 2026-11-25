package example_test

import (
	"testing"

	"github.com/lablup/backend.ai/internal/dbtest"
	"github.com/lablup/backend.ai/internal/example"
)

func TestNormalizeName(t *testing.T) {
	if got := example.NormalizeName("  Default "); got != "default" {
		t.Fatalf("got %q", got)
	}
}

func TestCountDomains(t *testing.T) {
	pool := dbtest.New(t)

	n, err := example.CountDomains(t.Context(), pool)
	if err != nil {
		t.Fatal(err)
	}
	if n != 0 {
		t.Fatalf("got %d domains in a fresh database", n)
	}
}
