//go:build integration

// Package integration holds the integration tests that run against a live
// Backend.AI server over its REST v2 and GraphQL APIs. They are built only
// with the `integration` tag; without the connection variables they skip.
//
// Run:
//
//	INTEGRATION_ENDPOINT=http://127.0.0.1:8091 INTEGRATION_ACCESS_KEY=... INTEGRATION_SECRET_KEY=... \
//	  go test -tags integration -count=1 -v ./tests/integration/...
package integration

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"testing"
	"time"
)

const (
	envEndpoint  = "INTEGRATION_ENDPOINT"
	envAccessKey = "INTEGRATION_ACCESS_KEY"
	envSecretKey = "INTEGRATION_SECRET_KEY"

	// apiVersion is the value of the X-BackendAI-Version header, the same as
	// the Python client SDK v2 sends.
	apiVersion = "v9.20250722"

	requestTimeout = 30 * time.Second
)

// client sends requests signed with a keypair, the way the Python client SDK
// v2 does (HMAC-SHA256 over the method, path, date, host, content type and
// API version; the body is not signed).
type client struct {
	endpoint  *url.URL
	accessKey string
	secretKey string
	http      *http.Client
}

// apiError is a response with a status of 400 or more.
type apiError struct {
	Method string
	Path   string
	Status int
	Body   string
}

func (e *apiError) Error() string {
	return fmt.Sprintf("%s %s: status %d: %s", e.Method, e.Path, e.Status, e.Body)
}

// newClient reads the connection from the environment and skips the test
// when any of it is missing.
func newClient(t *testing.T) *client {
	t.Helper()
	values := make(map[string]string, 3)
	for _, name := range []string{envEndpoint, envAccessKey, envSecretKey} {
		values[name] = os.Getenv(name)
		if values[name] == "" {
			t.Skipf("%s is not set", name)
		}
	}
	endpoint, err := url.Parse(values[envEndpoint])
	if err != nil || endpoint.Host == "" {
		t.Fatalf("%s is not a URL with a host: %q", envEndpoint, values[envEndpoint])
	}
	return &client{
		endpoint:  endpoint,
		accessKey: values[envAccessKey],
		secretKey: values[envSecretKey],
		http:      &http.Client{Timeout: requestTimeout},
	}
}

// host is the authority the server sees: a default port is left out.
func (c *client) host() string {
	host := c.endpoint.Host
	switch {
	case c.endpoint.Scheme == "http" && strings.HasSuffix(host, ":80"):
		return strings.TrimSuffix(host, ":80")
	case c.endpoint.Scheme == "https" && strings.HasSuffix(host, ":443"):
		return strings.TrimSuffix(host, ":443")
	}
	return host
}

func hmacSHA256(key []byte, data string) []byte {
	mac := hmac.New(sha256.New, key)
	mac.Write([]byte(data))
	return mac.Sum(nil)
}

// sign returns the Authorization header value.
func (c *client) sign(method, relURL, date string, when time.Time) string {
	host := c.host()
	bodyHash := sha256.Sum256(nil)
	signString := fmt.Sprintf(
		"%s\n%s\n%s\nhost:%s\ncontent-type:application/json\nx-backendai-version:%s\n%s",
		method, relURL, date, host, apiVersion, hex.EncodeToString(bodyHash[:]),
	)
	key := hmacSHA256([]byte(c.secretKey), when.Format("20060102"))
	key = hmacSHA256(key, host)
	signature := hex.EncodeToString(hmacSHA256(key, signString))
	return fmt.Sprintf(
		"BackendAI signMethod=HMAC-SHA256, credential=%s:%s", c.accessKey, signature,
	)
}

// do sends one request. A JSON body is sent when body is not nil; a response
// body is decoded into out when out is not nil. A status of 400 or more is
// returned as an *apiError.
func (c *client) do(ctx context.Context, method, path string, body, out any) error {
	var payload io.Reader
	if body != nil {
		raw, err := json.Marshal(body)
		if err != nil {
			return fmt.Errorf("encode request body: %w", err)
		}
		payload = bytes.NewReader(raw)
	}
	target := *c.endpoint
	target.Path = strings.TrimRight(c.endpoint.Path, "/") + path
	req, err := http.NewRequestWithContext(ctx, method, target.String(), payload)
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	// The date has no fraction, so the string the server rebuilds from the
	// header is the string signed here.
	when := time.Now().UTC().Truncate(time.Second)
	date := when.Format("2006-01-02T15:04:05") + "+00:00"
	req.Header.Set("Date", date)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-BackendAI-Version", apiVersion)
	req.Header.Set("Authorization", c.sign(method, path, date, when))

	resp, err := c.http.Do(req)
	if err != nil {
		return fmt.Errorf("%s %s: %w", method, path, err)
	}
	defer func() { _ = resp.Body.Close() }()
	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("%s %s: read response: %w", method, path, err)
	}
	if resp.StatusCode >= http.StatusBadRequest {
		return &apiError{Method: method, Path: path, Status: resp.StatusCode, Body: string(raw)}
	}
	if out != nil {
		if err := json.Unmarshal(raw, out); err != nil {
			return fmt.Errorf("%s %s: decode response %q: %w", method, path, raw, err)
		}
	}
	return nil
}

// graphQL sends a query to the manager's Strawberry schema and returns its
// data. A response with errors fails.
func (c *client) graphQL(ctx context.Context, query string, variables map[string]any) (json.RawMessage, error) {
	var result struct {
		Data   json.RawMessage `json:"data"`
		Errors []struct {
			Message string `json:"message"`
		} `json:"errors"`
	}
	body := map[string]any{"query": query, "variables": variables}
	if err := c.do(ctx, http.MethodPost, "/admin/gql/strawberry", body, &result); err != nil {
		return nil, err
	}
	if len(result.Errors) > 0 {
		return nil, fmt.Errorf("graphql: %s", result.Errors[0].Message)
	}
	return result.Data, nil
}

// newPrefix returns the name prefix of the objects one test creates: `it-`
// and a random part that differs for each call.
func newPrefix(t *testing.T) string {
	t.Helper()
	raw := make([]byte, 4)
	if _, err := rand.Read(raw); err != nil {
		t.Fatalf("random prefix: %v", err)
	}
	return "it-" + hex.EncodeToString(raw) + "-"
}
