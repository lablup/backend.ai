package nvmig

import (
	"testing"

	resourceapi "k8s.io/api/resource/v1"
)

func TestCountersOfWholeGPUAndPlacements(t *testing.T) {
	m, s, _ := h100(t)
	g := m.GPU(device(s, 0).UUID)
	set := g.CounterSet()
	if set.Name != "gpu-0-counter-set" {
		t.Fatalf("counter set %s", set.Name)
	}
	// The go-nvml H100 mock places its profiles on 7 memory slices.
	for i := 0; i < g.MemSlices; i++ {
		if c, ok := set.Counters[MemorySliceCounter(i)]; !ok || c.Value.Value() != 1 {
			t.Fatalf("memory slice %d: %v", i, c)
		}
	}
	if mp := set.Counters["multiprocessors"]; mp.Value.Value() != g.Max.Multiprocessors {
		t.Fatal("the set holds the per-dimension maxima")
	}
	whole := g.WholeConsumption()
	if len(whole) != 1 || len(whole[0].Counters) != len(set.Counters) {
		t.Fatal("the whole GPU consumes every counter")
	}
	if g.MemSlices != 7 {
		t.Fatalf("memory slices %d", g.MemSlices)
	}
	var p Placement
	for _, q := range g.Placements {
		if q.Profile == "3g.40gb" && q.Start == 4 {
			p = q
		}
	}
	parent := map[resourceapi.QualifiedName]resourceapi.DeviceAttribute{"model": stringAttr("H100"), "slotName": stringAttr("cuda.shares")}
	dev := g.PlacementDevice(p, "cuda.device:3g.40gb-mig", parent)
	if *dev.Attributes["slotName"].StringValue != "cuda.device:3g.40gb-mig" || *dev.Attributes["model"].StringValue != "H100" {
		t.Fatalf("attributes %v", dev.Attributes)
	}
	if *parent["slotName"].StringValue != "cuda.shares" {
		t.Fatal("the parent's attributes stay unchanged")
	}
	consumed := dev.ConsumesCounters[0].Counters
	for i := 0; i < g.MemSlices; i++ {
		_, ok := consumed[MemorySliceCounter(i)]
		if ok != (i >= p.Start && i < p.Start+p.Size) {
			t.Fatalf("slice %d consumed: %v", i, ok)
		}
	}
	if dev.AllowMultipleAllocations != nil {
		t.Fatal("a MIG device is exclusive")
	}
}
