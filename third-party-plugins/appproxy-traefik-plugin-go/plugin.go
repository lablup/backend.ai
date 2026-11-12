package appproxy_traefik_plugin_go

import (
	"context"
	"fmt"
	"html/template"
	"net"
	"net/http"
	"os"
	"strings"
	"time"
)

type ContentEncodingConfig struct {
	RejectedEncodings []string `yaml:"rejectedencodings"`
}

type Config struct {
	LastUsedMarkerPath string                `yaml:"lastusedmarkerpath"`
	Id                 string                `yaml:"id"`
	SessionIds         []string              `yaml:"sessionids"`
	ContentEncoding    ContentEncodingConfig `yaml:"contentencoding"`
}

func CreateConfig() *Config {
	return &Config{
		LastUsedMarkerPath: "",
		Id:                 "",
		SessionIds:         []string{},
		ContentEncoding:    ContentEncodingConfig{RejectedEncodings: []string{}},
	}
}

// Plugin a Plugin plugin.
type Plugin struct {
	config     *Config
	next       http.Handler
	name       string
	template   *template.Template
	httpClient *http.Client
}

// New created a new Plugin plugin.
func New(ctx context.Context, next http.Handler, config *Config, name string) (http.Handler, error) {
	// Create HTTP client with timeout
	httpClient := &http.Client{
		Timeout: 10 * time.Second,
		Transport: &http.Transport{
			DialContext: func(_ context.Context, _, _ string) (net.Conn, error) {
				return net.Dial("unix", config.LastUsedMarkerPath)
			},
			IdleConnTimeout: 10 * time.Second,
		},
	}

	rejectedEncodings := make([]string, 0, len(config.ContentEncoding.RejectedEncodings))
	for _, rejectedEncoding := range config.ContentEncoding.RejectedEncodings {
		rejectedEncodings = append(rejectedEncodings, strings.ToLower(strings.TrimSpace(rejectedEncoding)))
	}
	config.ContentEncoding.RejectedEncodings = rejectedEncodings

	return &Plugin{
		config:     config,
		next:       next,
		name:       name,
		template:   template.New("demo").Delims("[[", "]]"),
		httpClient: httpClient,
	}, nil
}

func (a *Plugin) MarkLastUsed(isWebsocket bool) {
	_, err := a.httpClient.Head(fmt.Sprintf("http://unix/circuit.%s.last_access/mark-last-used-time", a.config.Id))
	if err != nil {
		os.Stderr.WriteString(fmt.Sprintf("Failed to mark last used time of circuit.%s: %v\n", a.config.Id, err))
	}

	for _, sessionId := range a.config.SessionIds {
		_, err := a.httpClient.Head(fmt.Sprintf("http://unix/session.%s.last_access/mark-last-used-time", sessionId))
		if err != nil {
			os.Stderr.WriteString(fmt.Sprintf("Failed to mark last used time of session.%s: %v\n", sessionId, err))
		}
	}

	if isWebsocket {
		_, err := a.httpClient.Head(fmt.Sprintf("http://unix/%s/mark-active", a.config.Id))
		if err != nil {
			os.Stderr.WriteString(fmt.Sprintf("Failed to mark active of %s: %v\n", a.config.Id, err))
		}
	}
}

func (a *Plugin) MarkInactive() {
	_, err := a.httpClient.Head(fmt.Sprintf("http://unix/%s/mark-inactive", a.config.Id))
	if err != nil {
		os.Stderr.WriteString(fmt.Sprintf("Failed to mark inactive of %s: %v\n", a.config.Id, err))
	}
}

func (a *Plugin) findRejectedContentEncoding(contentEncodingHeaders []string) (string, bool) {
	// Each header line may list several codings, e.g. "gzip, br" (RFC 9110 section 8.4).
	// Codings are case-insensitive (RFC 9110 section 8.4.1), and some session apps decode
	// "BR" as brotli, so the header is lowercased like the configured codings.
	for _, headerValue := range contentEncodingHeaders {
		for _, coding := range strings.Split(headerValue, ",") {
			lowercasedCoding := strings.ToLower(strings.TrimSpace(coding))
			for _, rejectedEncoding := range a.config.ContentEncoding.RejectedEncodings {
				if lowercasedCoding == rejectedEncoding {
					return lowercasedCoding, true
				}
			}
		}
	}
	return "", false
}

func (a *Plugin) ServeHTTP(rw http.ResponseWriter, req *http.Request) {
	contentEncodingHeaders := req.Header.Values("Content-Encoding")
	rejectedEncoding, found := a.findRejectedContentEncoding(contentEncodingHeaders)
	if found {
		http.Error(rw, fmt.Sprintf("Request bodies encoded with %s are not accepted", rejectedEncoding), http.StatusUnsupportedMediaType)
		return
	}

	isWebsocket := strings.ToLower(req.Header.Get("Upgrade")) == "websocket"

	go a.MarkLastUsed(isWebsocket)
	a.next.ServeHTTP(rw, req)
	if isWebsocket {
		go a.MarkInactive()
	}
}
