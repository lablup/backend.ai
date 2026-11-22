package nvmig

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/NVIDIA/go-nvml/pkg/nvml"
	"github.com/NVIDIA/go-nvml/pkg/nvml/mock/dgxa100"
	"github.com/NVIDIA/go-nvml/pkg/nvml/mock/dgxh100"
	"github.com/NVIDIA/go-nvml/pkg/nvml/mock/server"
)

// fakeNVML is a go-nvml mock server with what the mocks leave out: bare-metal virtualization,
// and MIG mode changes refused while instances exist (as NVML does).
func fakeNVML(t *testing.T, s *server.Server) *server.Server {
	t.Helper()
	for _, d := range s.Devices {
		dev := d.(*server.Device)
		dev.GetVirtualizationModeFunc = func() (nvml.GpuVirtualizationMode, nvml.Return) {
			return nvml.GPU_VIRTUALIZATION_MODE_NONE, nvml.SUCCESS
		}
		set := dev.SetMigModeFunc
		dev.SetMigModeFunc = func(mode int) (nvml.Return, nvml.Return) {
			dev.RLock()
			busy := len(dev.GpuInstances) > 0
			dev.RUnlock()
			if busy {
				return nvml.ERROR_IN_USE, nvml.ERROR_IN_USE
			}
			return set(mode)
		}
		create := dev.CreateGpuInstanceWithPlacementFunc
		dev.CreateGpuInstanceWithPlacementFunc = func(info *nvml.GpuInstanceProfileInfo, p *nvml.GpuInstancePlacement) (nvml.GpuInstance, nvml.Return) {
			dev.RLock()
			enabled := dev.MigMode == nvml.DEVICE_MIG_ENABLE
			var overlap bool
			for gi := range dev.GpuInstances {
				q := gi.Info.Placement
				overlap = overlap || (p.Start < q.Start+q.Size && q.Start < p.Start+p.Size)
			}
			dev.RUnlock()
			if !enabled {
				return nil, nvml.ERROR_NOT_SUPPORTED
			}
			if overlap {
				return nil, nvml.ERROR_INSUFFICIENT_RESOURCES
			}
			return create(info, p)
		}
	}
	return s
}

func newTestManager(t *testing.T, s *server.Server) (*Manager, string) {
	t.Helper()
	cp := filepath.Join(t.TempDir(), "mig.json")
	m, err := NewManager(fakeNVML(t, s), cp, t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	return m, cp
}

func h100(t *testing.T) (*Manager, *server.Server, string) {
	t.Helper()
	s := dgxh100.New()
	m, cp := newTestManager(t, s)
	return m, s, cp
}

func device(s *server.Server, i int) *server.Device { return s.Devices[i].(*server.Device) }

func placementName(t *testing.T, g *GPU, profile string, start int) string {
	t.Helper()
	for _, p := range g.Placements {
		if p.Profile == profile && p.Start == start {
			return g.DeviceName(p)
		}
	}
	t.Fatalf("no %s placement at %d", profile, start)
	return ""
}

func TestInspectH100(t *testing.T) {
	m, s, _ := h100(t)
	g := m.GPU(device(s, 0).UUID)
	if !g.Dynamic() || !g.Toggle || !g.WholeAllowed() {
		t.Fatalf("an H100 serves whole GPUs and dynamic MIG: %+v", g)
	}
	if g.MemSlices != 7 { // the go-nvml H100 mock's placements
		t.Fatalf("memory slices: %d", g.MemSlices)
	}
	counts := map[string]int{}
	for _, p := range g.Placements {
		counts[p.Profile]++
	}
	if counts["1g.10gb"] != 7 || counts["7g.80gb"] != 1 || counts["1g.10gb+me"] != 7 {
		t.Fatalf("placements per profile: %v", counts)
	}
	if name := placementName(t, g, "1g.10gb", 3); name != "gpu-0-mig-1g10gb-0-3" {
		t.Fatalf("device name %s", name)
	}
}

func TestInspectA100WithoutMIGModeIsNotDynamic(t *testing.T) {
	s := dgxa100.New()
	m, _ := newTestManager(t, s)
	g := m.GPU(device(s, 0).UUID)
	if g.Dynamic() || !g.WholeAllowed() {
		t.Fatalf("an A100 outside MIG mode cannot enter it without a reset: %+v", g)
	}
}

func TestInspectA100InMIGModeServesMIGOnly(t *testing.T) {
	s := dgxa100.New()
	device(s, 0).MigMode = nvml.DEVICE_MIG_ENABLE
	m, _ := newTestManager(t, s)
	g := m.GPU(device(s, 0).UUID)
	if !g.Dynamic() || g.WholeAllowed() {
		t.Fatalf("an A100 in MIG mode serves MIG devices only: %+v", g)
	}
}

func TestPrepareCreatesAndUnprepareDestroys(t *testing.T) {
	m, s, cp := h100(t)
	dev := device(s, 0)
	g := m.GPU(dev.UUID)
	a, b := placementName(t, g, "1g.10gb", 0), placementName(t, g, "3g.40gb", 4)
	insts, err := m.Prepare("claim-1", []string{a, b})
	if err != nil {
		t.Fatal(err)
	}
	if len(insts) != 2 || dev.MigMode != nvml.DEVICE_MIG_ENABLE || len(dev.GpuInstances) != 2 {
		t.Fatalf("instances %+v, MIG mode %d, GIs %d", insts, dev.MigMode, len(dev.GpuInstances))
	}
	if insts[0].ParentUUID != dev.UUID || insts[1].Start != 4 {
		t.Fatalf("instances %+v", insts)
	}
	for gi := range dev.GpuInstances {
		if len(gi.ComputeInstances) != 1 {
			t.Fatal("each GPU instance gets one compute instance")
		}
	}
	again, err := m.Prepare("claim-1", []string{a, b})
	if err != nil || len(again) != 2 || len(dev.GpuInstances) != 2 {
		t.Fatalf("a prepared claim reuses its devices: %v %+v", err, again)
	}
	data, _ := os.ReadFile(cp)
	if !strings.Contains(string(data), `"completed"`) {
		t.Fatalf("checkpoint: %s", data)
	}
	if err := m.Unprepare("claim-1"); err != nil {
		t.Fatal(err)
	}
	if len(dev.GpuInstances) != 0 || dev.MigMode != nvml.DEVICE_MIG_DISABLE {
		t.Fatalf("GIs %d, MIG mode %d after unprepare", len(dev.GpuInstances), dev.MigMode)
	}
	if err := m.Unprepare("claim-1"); err != nil {
		t.Fatalf("unpreparing twice: %v", err)
	}
}

func TestAFailedPrepareRollsBack(t *testing.T) {
	m, s, _ := h100(t)
	dev := device(s, 0)
	g := m.GPU(dev.UUID)
	a, overlapping := placementName(t, g, "1g.10gb", 0), placementName(t, g, "2g.20gb", 0)
	if _, err := m.Prepare("claim-1", []string{a, overlapping}); err == nil {
		t.Fatal("overlapping placements cannot both be created")
	}
	if len(dev.GpuInstances) != 0 || len(m.cp.Claims) != 0 {
		t.Fatalf("a failed prepare leaves nothing: GIs %d, claims %d", len(dev.GpuInstances), len(m.cp.Claims))
	}
}

func TestPrepareWholeLeavesMIGModeOnlyWhenEmpty(t *testing.T) {
	m, s, _ := h100(t)
	dev := device(s, 0)
	g := m.GPU(dev.UUID)
	if _, err := m.Prepare("mig", []string{placementName(t, g, "1g.10gb", 0)}); err != nil {
		t.Fatal(err)
	}
	if err := m.PrepareWhole(dev.UUID); err == nil || !strings.Contains(err.Error(), "MIG devices") {
		t.Fatalf("a GPU with MIG devices cannot be used whole: %v", err)
	}
	if err := m.Unprepare("mig"); err != nil {
		t.Fatal(err)
	}
	dev.MigMode = nvml.DEVICE_MIG_ENABLE // left on, e.g. by an older driver
	if err := m.PrepareWhole(dev.UUID); err != nil || dev.MigMode != nvml.DEVICE_MIG_DISABLE {
		t.Fatalf("an empty GPU leaves MIG mode: %v, mode %d", err, dev.MigMode)
	}
}

func TestPrepareWholeOnAnA100InMIGModeFails(t *testing.T) {
	s := dgxa100.New()
	device(s, 0).MigMode = nvml.DEVICE_MIG_ENABLE
	m, _ := newTestManager(t, s)
	if err := m.PrepareWhole(device(s, 0).UUID); err == nil || !strings.Contains(err.Error(), "reset") {
		t.Fatalf("an A100 cannot leave MIG mode: %v", err)
	}
}

func TestReconcileKeepsPreparedAndDestroysTheRest(t *testing.T) {
	s := dgxh100.New()
	cp := filepath.Join(t.TempDir(), "mig.json")
	m, err := NewManager(fakeNVML(t, s), cp, t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	dev := device(s, 0)
	g := m.GPU(dev.UUID)
	kept, crashed := placementName(t, g, "1g.10gb", 0), placementName(t, g, "1g.10gb", 1)
	if _, err := m.Prepare("kept", []string{kept}); err != nil {
		t.Fatal(err)
	}
	if _, err := m.Prepare("crashed", []string{crashed}); err != nil {
		t.Fatal(err)
	}
	// A crash in the middle of "crashed"'s prepare, and a device nobody recorded.
	m.cp.Claims["crashed"].State = stateStarted
	if err := m.store.save(m.cp); err != nil {
		t.Fatal(err)
	}
	if _, err := m.create(placementName(t, g, "1g.10gb", 2)); err != nil {
		t.Fatal(err)
	}
	restarted, err := NewManager(s, cp, t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if err := restarted.Reconcile(); err != nil {
		t.Fatal(err)
	}
	if len(dev.GpuInstances) != 1 {
		t.Fatalf("only the prepared claim's device stays: %d", len(dev.GpuInstances))
	}
	for gi := range dev.GpuInstances {
		if gi.Info.Placement.Start != 0 {
			t.Fatalf("kept the wrong device: %+v", gi.Info.Placement)
		}
	}
	if _, ok := restarted.cp.Claims["crashed"]; ok {
		t.Fatal("an unfinished claim leaves the checkpoint")
	}
	if insts, err := restarted.Prepare("kept", []string{kept}); err != nil || len(insts) != 1 {
		t.Fatalf("a prepared claim survives the restart: %v", err)
	}
}

func TestCapNodes(t *testing.T) {
	root := t.TempDir()
	write := func(rel, body string) {
		path := filepath.Join(root, rel)
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	write("devices", "Character devices:\n  1 mem\n195 nvidia\n236 nvidia-caps\n\nBlock devices:\n  8 sd\n")
	write("driver/nvidia/capabilities/gpu1/mig/gi3/access", "DeviceFileMinor: 30\nDeviceFileMode: 292\nDeviceFileModify: 1\n")
	write("driver/nvidia/capabilities/gpu1/mig/gi3/ci0/access", "DeviceFileMinor: 31\nDeviceFileMode: 292\n")
	nodes, err := capNodes(root, Instance{ParentMinor: 1, GIID: 3, CIID: 0})
	if err != nil {
		t.Fatal(err)
	}
	if len(nodes) != 2 || nodes[0] != (CapNode{Path: "/dev/nvidia-caps/nvidia-cap30", Major: 236, Minor: 30, FileMode: 292}) || nodes[1].Minor != 31 {
		t.Fatalf("nodes %+v", nodes)
	}
	if _, err := deviceMajor(filepath.Join(root, "devices"), "nvidia-cap"); err == nil {
		t.Fatal("a device name matches whole")
	}
}

func TestProfileNames(t *testing.T) {
	const gib = 1 << 30
	for _, c := range []struct {
		id, slices int
		total      uint64
		mb         uint64
		want       string
	}{
		{nvml.GPU_INSTANCE_PROFILE_1_SLICE, 1, 80 * gib, 9856, "1g.10gb"},
		{nvml.GPU_INSTANCE_PROFILE_1_SLICE_REV1, 1, 80 * gib, 9856, "1g.10gb+me"},
		{nvml.GPU_INSTANCE_PROFILE_7_SLICE, 7, 80 * gib, 80 * 1024, "7g.80gb"},
		{nvml.GPU_INSTANCE_PROFILE_1_SLICE, 1, 40 * gib, 4864, "1g.5gb"},
	} {
		if got := profileName(c.id, c.slices, c.total, c.mb); got != c.want {
			t.Errorf("%d/%d: got %s, want %s", c.id, c.mb, got, c.want)
		}
	}
}
