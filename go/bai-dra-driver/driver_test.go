package main

import (
	"context"
	"encoding/json"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
)

func TestAttributeTypes(t *testing.T) {
	if a := attribute(json.Number("3")); a.IntValue == nil || *a.IntValue != 3 {
		t.Fatal("whole JSON numbers become int attributes")
	}
	if a := attribute(json.Number("1.5")); a.StringValue == nil || *a.StringValue != "1.5" {
		t.Fatal("fractional JSON numbers become strings, not truncated ints")
	}
	if a := attribute(float64(2.25)); a.StringValue == nil || *a.StringValue != "2.25" {
		t.Fatal("fractional floats become strings")
	}
	if a := attribute(true); a.BoolValue == nil || !*a.BoolValue {
		t.Fatal("bools stay bools")
	}
	if a := attribute("x"); a.StringValue == nil || *a.StringValue != "x" {
		t.Fatal("strings stay strings")
	}
}

func TestQuantityStringIsPlainDecimal(t *testing.T) {
	for in, want := range map[string]string{"2k": "2000", "150": "150", "500m": "0.500"} {
		if got := quantityString(resource.MustParse(in)); got != want {
			t.Fatalf("%s: got %s, want %s", in, got, want)
		}
	}
}

// fakeHost serves the bridge API on a Unix socket; prepare blocks until release is closed.
type fakeHost struct {
	release chan struct{}
	mu      sync.Mutex
	calls   int
}

func startFakeHost(t *testing.T, h *fakeHost) *bridge {
	t.Helper()
	// macOS limits a Unix socket path to 104 bytes; t.TempDir() is longer.
	dir, err := os.MkdirTemp("/tmp", "bai-dra-")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.RemoveAll(dir) })
	socket := filepath.Join(dir, "b.sock")
	ln, err := net.Listen("unix", socket)
	if err != nil {
		t.Fatal(err)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/prepare", func(w http.ResponseWriter, r *http.Request) {
		var in struct {
			ClaimUID string   `json:"claim_uid"`
			Devices  []string `json:"devices"`
		}
		_ = json.NewDecoder(r.Body).Decode(&in)
		h.mu.Lock()
		h.calls++
		h.mu.Unlock()
		if strings.HasPrefix(in.ClaimUID, "slow") {
			<-h.release
		}
		perDevice := map[string][]string{}
		for _, d := range in.Devices {
			perDevice[d] = []string{"nvidia.com/gpu=" + d}
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"edits":              map[string]any{"env": []string{"A=1"}},
			"device_cdi_devices": perDevice,
		})
	})
	mux.HandleFunc("/v1/unprepare", func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write([]byte("{}"))
	})
	server := &http.Server{Handler: mux}
	go func() { _ = server.Serve(ln) }()
	t.Cleanup(func() { _ = server.Close() })
	return newBridge(socket)
}

func allocatedClaim(uid string, devices ...string) *resourceapi.ResourceClaim {
	claim := &resourceapi.ResourceClaim{ObjectMeta: metav1.ObjectMeta{Name: uid, UID: types.UID(uid)}}
	results := []resourceapi.DeviceRequestAllocationResult{}
	for _, d := range devices {
		results = append(results, resourceapi.DeviceRequestAllocationResult{Request: "r", Driver: "x.dra.backend.ai", Pool: "n", Device: d})
	}
	claim.Status.Allocation = &resourceapi.AllocationResult{Devices: resourceapi.DeviceAllocationResult{Results: results}}
	return claim
}

func TestPrepareAttachesCDIDevicesPerDevice(t *testing.T) {
	h := &fakeHost{release: make(chan struct{})}
	d := newDriver("x.dra.backend.ai", "n", startFakeHost(t, h), &cdiWriter{root: t.TempDir()})
	result := d.prepare(context.Background(), allocatedClaim("uid-1", "dev-a", "dev-b"))
	if result.Err != nil {
		t.Fatal(result.Err)
	}
	a, b := result.Devices[0].CDIDeviceIDs, result.Devices[1].CDIDeviceIDs
	if len(a) != 2 || a[0] != "nvidia.com/gpu=dev-a" || a[1] != "dra.backend.ai/claim=uid-1" {
		t.Fatalf("first device: %v", a)
	}
	if len(b) != 1 || b[0] != "nvidia.com/gpu=dev-b" {
		t.Fatalf("second device gets only its own CDI device: %v", b)
	}
}

func TestASlowClaimDoesNotBlockOthers(t *testing.T) {
	h := &fakeHost{release: make(chan struct{})}
	d := newDriver("x.dra.backend.ai", "n", startFakeHost(t, h), &cdiWriter{root: t.TempDir()})
	slowDone := make(chan struct{})
	go func() {
		d.prepare(context.Background(), allocatedClaim("slow-1", "dev-a"))
		close(slowDone)
	}()
	done := make(chan struct{})
	go func() {
		d.prepare(context.Background(), allocatedClaim("fast-1", "dev-b"))
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Fatal("a claim waited for another claim's bridge call")
	}
	close(h.release)
	<-slowDone
}

func TestBridgeCallsTimeOut(t *testing.T) {
	h := &fakeHost{release: make(chan struct{})}
	defer close(h.release)
	b := startFakeHost(t, h)
	b.timeout = 100 * time.Millisecond
	if _, err := b.Prepare(context.Background(), "slow-2", nil, nil); err == nil {
		t.Fatal("a stuck plugin host must fail the call")
	}
	if bridgeTimeout >= 45*time.Second {
		t.Fatal("the bridge timeout must stay below the kubelet's deadline")
	}
}
