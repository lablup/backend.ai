package appproxy_traefik_plugin_go

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

type contentEncodingCase struct {
	name                   string
	rejectBrotli           bool
	contentEncodings       []string
	expectedStatus         int
	expectedForwardedCount int
}

func TestServeHTTPContentEncoding(t *testing.T) {
	cases := []contentEncodingCase{
		{name: "enabled/br", rejectBrotli: true, contentEncodings: []string{"br"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "enabled/BR", rejectBrotli: true, contentEncodings: []string{"BR"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "enabled/gzip, br", rejectBrotli: true, contentEncodings: []string{"gzip, br"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "enabled/gzip + br", rejectBrotli: true, contentEncodings: []string{"gzip", "br"}, expectedStatus: http.StatusUnsupportedMediaType, expectedForwardedCount: 0},
		{name: "enabled/none", rejectBrotli: true, contentEncodings: nil, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "enabled/gzip", rejectBrotli: true, contentEncodings: []string{"gzip"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "enabled/deflate", rejectBrotli: true, contentEncodings: []string{"deflate"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "enabled/identity", rejectBrotli: true, contentEncodings: []string{"identity"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "disabled/br", rejectBrotli: false, contentEncodings: []string{"br"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "disabled/gzip, br", rejectBrotli: false, contentEncodings: []string{"gzip, br"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "disabled/gzip", rejectBrotli: false, contentEncodings: []string{"gzip"}, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
		{name: "disabled/none", rejectBrotli: false, contentEncodings: nil, expectedStatus: http.StatusOK, expectedForwardedCount: 1},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			forwardedCount := 0
			next := http.HandlerFunc(func(rw http.ResponseWriter, req *http.Request) {
				forwardedCount++
			})
			config := &Config{
				LastUsedMarkerPath: t.TempDir() + "/marker.sock",
				RejectBrotli:       tc.rejectBrotli,
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
