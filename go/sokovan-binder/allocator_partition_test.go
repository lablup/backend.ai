package main

import (
	"context"
	"fmt"
	"testing"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes/fake"
)

// A dynamic-MIG GPU as bai-dra publishes it on Kubernetes 1.35+: a slice with the GPU's counter
// set (4 memory slices here) and a slice with the whole shared device (all counters) and its
// MIG placements: 1g at slices 0..3 and 2g at 0 and 2.
const counterSet = "gpu-0-counter-set"

func counterMap(slices []int, sms int64) map[string]resourceapi.Counter {
	out := map[string]resourceapi.Counter{"multiprocessors": {Value: *resource.NewQuantity(sms, resource.DecimalSI)}}
	for _, i := range slices {
		out[fmt.Sprintf("memory-slice-%d", i)] = resourceapi.Counter{Value: resource.MustParse("1")}
	}
	return out
}

func migDevice(profile string, start, size int, sms int64) resourceapi.Device {
	var slices []int
	for i := start; i < start+size; i++ {
		slices = append(slices, i)
	}
	slot := fmt.Sprintf("cuda.device:%s-mig", profile)
	return resourceapi.Device{
		Name:             fmt.Sprintf("gpu-0-mig-%s-%d", profile, start),
		Attributes:       map[resourceapi.QualifiedName]resourceapi.DeviceAttribute{"slotName": {StringValue: &slot}},
		ConsumesCounters: []resourceapi.DeviceCounterConsumption{{CounterSet: counterSet, Counters: counterMap(slices, sms)}},
	}
}

func partitionAllocator(t *testing.T, claims ...*resourceapi.ResourceClaim) *allocator {
	t.Helper()
	full, one := resource.MustParse("100"), resource.MustParse("1")
	shares := "cuda.shares"
	whole := resourceapi.Device{
		Name:                     "dev-0",
		AllowMultipleAllocations: ptr(true),
		Attributes:               map[resourceapi.QualifiedName]resourceapi.DeviceAttribute{"slotName": {StringValue: &shares}},
		Capacity: map[resourceapi.QualifiedName]resourceapi.DeviceCapacity{"shares": {
			Value:         full,
			RequestPolicy: &resourceapi.CapacityRequestPolicy{Default: &full, ValidRange: &resourceapi.CapacityRequestPolicyRange{Min: &one, Max: &full, Step: &one}},
		}},
		ConsumesCounters: []resourceapi.DeviceCounterConsumption{{CounterSet: counterSet, Counters: counterMap([]int{0, 1, 2, 3}, 4)}},
	}
	devices := []resourceapi.Device{whole}
	for start := 0; start < 4; start++ {
		devices = append(devices, migDevice("1g", start, 1, 1))
	}
	devices = append(devices, migDevice("2g", 0, 2, 2), migDevice("2g", 2, 2, 2))
	objects := []runtime.Object{
		&corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: "n1"}},
		&resourceapi.DeviceClass{
			ObjectMeta: metav1.ObjectMeta{Name: testDriver},
			Spec:       resourceapi.DeviceClassSpec{Selectors: []resourceapi.DeviceSelector{{CEL: &resourceapi.CELDeviceSelector{Expression: `device.driver == "` + testDriver + `"`}}}},
		},
		&resourceapi.ResourceSlice{
			ObjectMeta: metav1.ObjectMeta{Name: "n1-counters"},
			Spec: resourceapi.ResourceSliceSpec{
				Driver: testDriver, NodeName: ptr("n1"),
				Pool:           resourceapi.ResourcePool{Name: "n1", ResourceSliceCount: 2},
				SharedCounters: []resourceapi.CounterSet{{Name: counterSet, Counters: counterMap([]int{0, 1, 2, 3}, 4)}},
			},
		},
		&resourceapi.ResourceSlice{
			ObjectMeta: metav1.ObjectMeta{Name: "n1-gpu-0"},
			Spec: resourceapi.ResourceSliceSpec{
				Driver: testDriver, NodeName: ptr("n1"),
				Pool:    resourceapi.ResourcePool{Name: "n1", ResourceSliceCount: 2},
				Devices: devices,
			},
		},
	}
	for _, c := range claims {
		objects = append(objects, c)
	}
	return allocatorFor(t, fake.NewClientset(objects...))
}

// slotClaim requests one device of a Backend.AI slot, as the session controller does.
func slotClaim(name, slot string, shares int64) *resourceapi.ResourceClaim {
	c := claim(name)
	req := c.Spec.Devices.Requests[0].Exactly
	req.Selectors = []resourceapi.DeviceSelector{{CEL: &resourceapi.CELDeviceSelector{
		Expression: fmt.Sprintf(`device.attributes[%q].slotName == %q`, testDriver, slot),
	}}}
	if shares > 0 {
		req.Capacity = sharesOf(shares)
	}
	return c
}

func allocatedOn(t *testing.T, a *allocator, name string) *resourceapi.ResourceClaim {
	t.Helper()
	resp, err := a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p-"+name, name)}})
	if err != nil || !resp.Fits {
		t.Fatalf("%s must fit: %+v %v", name, resp, err)
	}
	c, err := a.claims.ResourceClaims("ns").Get(name)
	if err != nil {
		t.Fatal(err)
	}
	c = c.DeepCopy()
	c.Status.Allocation = &resp.Pods[0].Allocations[0].Allocation
	return c
}

func fits(t *testing.T, a *allocator, reserved []*resourceapi.ResourceClaim, names ...string) bool {
	t.Helper()
	req := &AllocateRequest{}
	for _, c := range reserved {
		req.Reserved = append(req.Reserved, ReservedClaim{Namespace: c.Namespace, Name: c.Name, Allocation: *c.Status.Allocation})
	}
	for _, n := range names {
		req.Pods = append(req.Pods, pod("p-"+n, n))
	}
	resp, err := a.allocate(context.Background(), req)
	if err != nil {
		t.Fatal(err)
	}
	return resp.Fits
}

func TestAWholeGPUBlocksEveryMIGPlacement(t *testing.T) {
	a := partitionAllocator(t, slotClaim("whole", "cuda.shares", 0), slotClaim("mig", "cuda.device:1g-mig", 0))
	whole := allocatedOn(t, a, "whole")
	if fits(t, a, []*resourceapi.ResourceClaim{whole}, "mig") {
		t.Fatal("a MIG placement fits next to a whole GPU")
	}
}

func TestAFractionOfTheGPUBlocksMIGAndLetsMoreFractionsIn(t *testing.T) {
	a := partitionAllocator(t, slotClaim("half", "cuda.shares", 50), slotClaim("other", "cuda.shares", 50), slotClaim("mig", "cuda.device:1g-mig", 0))
	half := allocatedOn(t, a, "half")
	if fits(t, a, []*resourceapi.ResourceClaim{half}, "mig") {
		t.Fatal("a MIG placement fits next to a fraction of the GPU")
	}
	// The counters of a shared device are reserved on its first allocation only.
	if !fits(t, a, []*resourceapi.ResourceClaim{half}, "other") {
		t.Fatal("a second fraction must fit on the shared device")
	}
}

func TestAMIGPlacementBlocksTheWholeGPU(t *testing.T) {
	a := partitionAllocator(t, slotClaim("mig", "cuda.device:1g-mig", 0), slotClaim("whole", "cuda.shares", 0), slotClaim("part", "cuda.shares", 10))
	mig := allocatedOn(t, a, "mig")
	if fits(t, a, []*resourceapi.ResourceClaim{mig}, "whole") || fits(t, a, []*resourceapi.ResourceClaim{mig}, "part") {
		t.Fatal("the shared device fits next to a MIG placement")
	}
}

func TestDisjointMIGPlacementsFitAndOverlappingOnesDoNot(t *testing.T) {
	a := partitionAllocator(t,
		slotClaim("a", "cuda.device:2g-mig", 0), slotClaim("b", "cuda.device:2g-mig", 0),
		slotClaim("c", "cuda.device:1g-mig", 0))
	if !fits(t, a, nil, "a", "b") {
		t.Fatal("two disjoint 2g placements must fit")
	}
	if fits(t, a, nil, "a", "b", "c") {
		t.Fatal("a 1g placement fits on slices both 2g placements hold")
	}
	first := allocatedOn(t, a, "a")
	if got := first.Status.Allocation.Devices.Results[0].Device; got != "gpu-0-mig-2g-0" {
		t.Fatalf("first 2g at %s", got)
	}
	if !fits(t, a, []*resourceapi.ResourceClaim{first}, "c") {
		t.Fatal("a 1g placement fits on the free slices")
	}
}
