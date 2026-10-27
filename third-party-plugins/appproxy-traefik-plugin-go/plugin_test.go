package appproxy_traefik_plugin_go

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

type contentEncodingCase struct {
	name                   string
	rejectedEncodings      []string
	contentEncodings       []string
	expectedStatus         int
	expectedForwardedCount int
}

func TestServeHTTPContentEncoding(t *testing.T) {
	cases := []contentEncodingCase{
		{name: "br rejected/br", rejectedEncodings: []string{"br"}, contentEncodings: []string{"br"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "br rejected/BR", rejectedEncodings: []string{"br"}, contentEncodings: []string{"BR"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "br rejected/gzip, Br", rejectedEncodings: []string{"br"}, contentEncodings: []string{"gzip, Br"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "br rejected/gzip, br", rejectedEncodings: []string{"br"}, contentEncodings: []string{"gzip, br"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "br rejected/gzip + br", rejectedEncodings: []string{"br"}, contentEncodings: []string{"gzip", "br"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "br rejected/none", rejectedEncodings: []string{"br"}, contentEncodings: nil, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "br rejected/gzip", rejectedEncodings: []string{"br"}, contentEncodings: []string{"gzip"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "br rejected/deflate", rejectedEncodings: []string{"br"}, contentEncodings: []string{"deflate"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "br rejected/identity", rejectedEncodings: []string{"br"}, contentEncodings: []string{"identity"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "none rejected/br", rejectedEncodings: nil, contentEncodings: []string{"br"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "none rejected/gzip, br", rejectedEncodings: nil, contentEncodings: []string{"gzip, br"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "none rejected/gzip", rejectedEncodings: nil, contentEncodings: []string{"gzip"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "none rejected/none", rejectedEncodings: nil, contentEncodings: nil, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "BR rejected/br", rejectedEncodings: []string{"BR"}, contentEncodings: []string{"br"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "br, zstd rejected/zstd", rejectedEncodings: []string{"br", "zstd"}, contentEncodings: []string{"zstd"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "br, zstd rejected/gzip", rejectedEncodings: []string{"br", "zstd"}, contentEncodings: []string{"gzip"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			forwardedCount := 0
			next := http.HandlerFunc(func(rw http.ResponseWriter, req *http.Request) {
				forwardedCount++
			})
			config := &Config{
				LastUsedMarkerPath: t.TempDir() + "/marker.sock",
				ContentEncoding:    ContentEncodingConfig{RejectedEncodings: tc.rejectedEncodings},
			}
			handler, err := New(context.Background(), next, config, "test")
			if err != nil {
				t.Fatal(err)
			}
			req := httptest.NewRequest(http.MethodPost, "http://localhost/", nil)
			for _, contentEncoding := range tc.contentEncodings {
				req.Header.Add("Content-Encoding", contentEncoding)
			}
			recorder := httptest.NewRecorder()

			handler.ServeHTTP(recorder, req)

			if recorder.Code != tc.expectedStatus {
				t.Errorf("status = %d, want %d", recorder.Code, tc.expectedStatus)
			}
			if forwardedCount != tc.expectedForwardedCount {
				t.Errorf("forwarded %d times, want %d", forwardedCount, tc.expectedForwardedCount)
			}
		})
	}
}
