package example_test

import (
	"testing"

	"github.com/lablup/backend.ai/internal/dbtest"
	"github.com/lablup/backend.ai/internal/example"
)

func TestNormalizeName(t *testing.T) {
	const in, want = "  Default ", "default"
	if got := example.NormalizeName(in); got != want {
		t.Errorf("NormalizeName(%q) = %q, want %q", in, got, want)
	}
}

func TestCountDomains(t *testing.T) {
	pool := dbtest.New(t)

	got, err := example.CountDomains(t.Context(), pool)
	if err != nil {
		t.Fatal(err)
	}
	if want := 0; got != want {
		t.Errorf("CountDomains() = %d, want %d", got, want)
	}
}
