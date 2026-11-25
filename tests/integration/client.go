//go:build integration

// Package integration holds the integration tests that run against a live
// Backend.AI server. They are built only with the `integration` tag; without
// INTEGRATION_ENDPOINT they skip.
//
// Run: INTEGRATION_ENDPOINT=http://127.0.0.1:8091 go test -tags integration -count=1 -v ./tests/integration/...
package integration

import (
	"os"
	"testing"
)

const envEndpoint = "INTEGRATION_ENDPOINT"

// Endpoint returns the address of the server under test and skips the test
// when INTEGRATION_ENDPOINT is not set.
func Endpoint(t *testing.T) string {
	t.Helper()
	endpoint := os.Getenv(envEndpoint)
	if endpoint == "" {
		t.Skipf("%s is not set", envEndpoint)
	}
	return endpoint
}
