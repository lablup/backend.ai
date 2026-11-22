package main

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/NVIDIA/go-nvml/pkg/nvml"
	"github.com/NVIDIA/go-nvml/pkg/nvml/mock/dgxh100"
	"github.com/NVIDIA/go-nvml/pkg/nvml/mock/server"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/dynamic-resource-allocation/kubeletplugin"

	"github.com/lablup/backend.ai/go/bai-dra-driver/nvmig"
)

// migDriver is a driver with dynamic MIG on over the go-nvml H100 mock (8 GPUs) and a fake
// procfs holding the capability files of GPU 0's first GPU instance.
func migDriver(t *testing.T, h *fakeHost, split bool) (*driver, *server.Server) {
	t.Helper()
	s := dgxh100.New()
	for _, dev := range s.Devices {
		dev.(*server.Device).GetVirtualizationModeFunc = func() (nvml.GpuVirtualizationMode, nvml.Return) {
			return nvml.GPU_VIRTUALIZATION_MODE_NONE, nvml.SUCCESS
		}
	}
	proc := t.TempDir()
	files := map[string]string{
		"devices": "Character devices:\n195 nvidia\n236 nvidia-caps\n\nBlock devices:\n",
		"driver/nvidia/capabilities/gpu0/mig/gi0/access":     "DeviceFileMinor: 3\nDeviceFileMode: 292\n",
		"driver/nvidia/capabilities/gpu0/mig/gi0/ci0/access": "DeviceFileMinor: 4\nDeviceFileMode: 292\n",
	}
	for rel, body := range files {
		path := filepath.Join(proc, rel)
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	m, err := nvmig.NewManager(s, filepath.Join(t.TempDir(), "mig.json"), proc)
	if err != nil {
		t.Fatal(err)
	}
	d := newDriver("x.dra.backend.ai", "n", startFakeHost(t, h), &cdiWriter{root: t.TempDir()})
	d.mig, d.splitCounters = m, split
	return d, s
}

func gpuUUID(s *server.Server, i int) string { return s.Devices[i].(*server.Device).UUID }

func sharedGPU(name, uuid string) DeviceInfo {
	return DeviceInfo{
		Name:                     name,
		UUID:                     uuid,
		Attributes:               map[string]any{"slotName": "cuda.shares", "model": "H100", "memory": json.Number("85899345920")},
		Capacity:                 map[string]string{"shares": "1000"},
		AllowMultipleAllocations: true,
		RequestPolicies:          map[string]CapacityPolicy{"shares": {Default: "1000", Min: "1", Max: "1000", Step: "1"}},
	}
}

func TestDynamicMigSlicesCombined(t *testing.T) {
	d, s := migDriver(t, &fakeHost{release: make(chan struct{})}, false)
	resp := &DevicesResponse{SlotName: "cuda", Devices: []DeviceInfo{sharedGPU("dev-0", gpuUUID(s, 0)), {Name: "dev-x"}}}
	slices, whole, err := d.slices(resp)
	if err != nil {
		t.Fatal(err)
	}
	if len(slices) != 2 || len(slices[0].Devices) != 1 || slices[0].Devices[0].Name != "dev-x" {
		t.Fatalf("other devices go to a slice of their own: %+v", slices)
	}
	gpu := slices[1]
	if len(gpu.SharedCounters) != 1 || gpu.SharedCounters[0].Name != "gpu-0-counter-set" {
		t.Fatalf("before 1.35 the GPU's slice carries its counters: %+v", gpu.SharedCounters)
	}
	first := gpu.Devices[0]
	if first.Name != "dev-0" || len(first.ConsumesCounters) != 1 || first.AllowMultipleAllocations == nil {
		t.Fatalf("the shared whole device consumes every counter: %+v", first)
	}
	if whole["dev-0"] != gpuUUID(s, 0) {
		t.Fatalf("whole devices: %v", whole)
	}
	var mig int
	for _, dev := range gpu.Devices[1:] {
		slot := *dev.Attributes["slotName"].StringValue
		if !strings.HasPrefix(slot, "cuda.device:") || !strings.HasSuffix(slot, "-mig") {
			t.Fatalf("MIG device slot %s", slot)
		}
		if _, ok := dev.Attributes["memory"]; ok {
			t.Fatal("a MIG device does not inherit the whole GPU's size attributes")
		}
		if *dev.Attributes["model"].StringValue != "H100" {
			t.Fatal("a MIG device inherits the parent's other attributes")
		}
		mig++
	}
	if mig == 0 || len(gpu.Devices) > 128 {
		t.Fatalf("MIG devices: %d", mig)
	}
}

func TestDynamicMigSlicesSplitAndStickyParents(t *testing.T) {
	d, s := migDriver(t, &fakeHost{release: make(chan struct{})}, true)
	resp := &DevicesResponse{SlotName: "cuda", Devices: []DeviceInfo{sharedGPU("dev-0", gpuUUID(s, 0)), sharedGPU("dev-1", gpuUUID(s, 1))}}
	if _, _, err := d.slices(resp); err != nil {
		t.Fatal(err)
	}
	// A GPU in MIG mode may drop out of the plugin host's list; it stays published.
	resp.Devices = resp.Devices[1:]
	slices, whole, err := d.slices(resp)
	if err != nil {
		t.Fatal(err)
	}
	if len(slices) != 3 || len(slices[0].SharedCounters) != 2 || len(slices[0].Devices) != 0 {
		t.Fatalf("1.35 and later: one slice of counters, then the GPUs' devices: %d slices", len(slices))
	}
	for _, sl := range slices[1:] {
		if len(sl.SharedCounters) != 0 {
			t.Fatal("device slices carry no counters")
		}
	}
	if len(whole) != 2 {
		t.Fatalf("both whole devices stay: %v", whole)
	}
}

func migDeviceName(t *testing.T, d *driver, uuid, profile string, start int) string {
	t.Helper()
	g := d.mig.GPU(uuid)
	for _, p := range g.Placements {
		if p.Profile == profile && p.Start == start {
			return g.DeviceName(p)
		}
	}
	t.Fatalf("no %s at %d", profile, start)
	return ""
}

func TestPrepareAMigDeviceWithoutThePluginHost(t *testing.T) {
	h := &fakeHost{release: make(chan struct{})}
	d, s := migDriver(t, h, false)
	if _, _, err := d.slices(&DevicesResponse{SlotName: "cuda", Devices: []DeviceInfo{sharedGPU("dev-0", gpuUUID(s, 0))}}); err != nil {
		t.Fatal(err)
	}
	d.wholeGPUs = map[string]string{"dev-0": gpuUUID(s, 0)}
	name := migDeviceName(t, d, gpuUUID(s, 0), "1g.10gb", 0)
	if result := d.prepare(context.Background(), allocatedClaim("uid-m", name)); result.Err == nil {
		t.Fatal("prepare waits for the first publish")
	}
	d.published.Store(true)
	result := d.prepare(context.Background(), allocatedClaim("uid-m", name))
	if result.Err != nil {
		t.Fatal(result.Err)
	}
	ids := result.Devices[0].CDIDeviceIDs
	want := []string{"nvidia.com/gpu=" + gpuUUID(s, 0), "dra.backend.ai/claim=uid-m-" + name}
	if len(ids) != 2 || ids[0] != want[0] || ids[1] != want[1] {
		t.Fatalf("CDI ids %v, want %v", ids, want)
	}
	if h.calls != 0 {
		t.Fatal("a MIG-only claim does not reach the plugin host")
	}
	data, err := os.ReadFile(d.cdi.path("uid-m"))
	if err != nil {
		t.Fatal(err)
	}
	var spec cdiSpec
	if err := json.Unmarshal(data, &spec); err != nil {
		t.Fatal(err)
	}
	nodes := spec.Devices[0].ContainerEdits.DeviceNodes
	if len(spec.Devices) != 1 || len(nodes) != 2 || nodes[0].Path != "/dev/nvidia-caps/nvidia-cap3" || nodes[0].Type != "c" || nodes[0].Major != 236 {
		t.Fatalf("spec %s", data)
	}
	// The whole GPU is blocked while the MIG device lives.
	if r := d.prepare(context.Background(), allocatedClaim("uid-w", "dev-0")); r.Err == nil || !strings.Contains(r.Err.Error(), "MIG devices") {
		t.Fatalf("whole prepare on a GPU with MIG devices: %v", r.Err)
	}
	dev0 := s.Devices[0].(*server.Device)
	if err := d.unprepare(context.Background(), kubeletplugin.NamespacedObject{UID: types.UID("uid-m")}); err != nil {
		t.Fatal(err)
	}
	if len(dev0.GpuInstances) != 0 || dev0.MigMode != nvml.DEVICE_MIG_DISABLE {
		t.Fatalf("unprepare destroys the MIG device and leaves MIG mode: %d GIs", len(dev0.GpuInstances))
	}
	if r := d.prepare(context.Background(), allocatedClaim("uid-w", "dev-0")); r.Err != nil {
		t.Fatalf("whole prepare on an empty GPU: %v", r.Err)
	}
}

func TestSplitCounterSlicesByServerVersion(t *testing.T) {
	for _, c := range []struct {
		major, minor string
		want         bool
	}{{"1", "34", false}, {"1", "35", true}, {"1", "36+", true}, {"1", "33", false}} {
		if got := splitCounterSlices(c.major, c.minor); got != c.want {
			t.Errorf("%s.%s: %v", c.major, c.minor, got)
		}
	}
}
