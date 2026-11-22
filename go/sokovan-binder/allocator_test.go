package main

import (
	"context"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes/fake"
	"k8s.io/dynamic-resource-allocation/cel"
)

const testDriver = "cuda.dra.backend.ai"

func claim(name string) *resourceapi.ResourceClaim {
	return &resourceapi.ResourceClaim{
		ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: "ns"},
		Spec: resourceapi.ResourceClaimSpec{Devices: resourceapi.DeviceClaim{Requests: []resourceapi.DeviceRequest{{
			Name:    "gpu",
			Exactly: &resourceapi.ExactDeviceRequest{DeviceClassName: testDriver, AllocationMode: resourceapi.DeviceAllocationModeExactCount, Count: 1},
		}}}},
	}
}

func newTestAllocator(t *testing.T) *allocator {
	t.Helper()
	client := fake.NewClientset(
		&corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: "n1"}},
		&resourceapi.DeviceClass{
			ObjectMeta: metav1.ObjectMeta{Name: testDriver},
			Spec:       resourceapi.DeviceClassSpec{Selectors: []resourceapi.DeviceSelector{{CEL: &resourceapi.CELDeviceSelector{Expression: `device.driver == "` + testDriver + `"`}}}},
		},
		&resourceapi.ResourceSlice{
			ObjectMeta: metav1.ObjectMeta{Name: "n1-slice"},
			Spec: resourceapi.ResourceSliceSpec{
				Driver: testDriver, NodeName: ptr("n1"),
				Pool:    resourceapi.ResourcePool{Name: "n1", ResourceSliceCount: 1},
				Devices: []resourceapi.Device{{Name: "dev-0"}, {Name: "dev-1"}},
			},
		},
		claim("a"), claim("b"), claim("c"),
	)
	return allocatorFor(t, client)
}

func ptr[T any](v T) *T { return &v }

func pod(name string, claims ...string) PodPlacement {
	p := PodPlacement{Name: name, Node: "n1"}
	for _, c := range claims {
		p.Claims = append(p.Claims, ClaimRef{Namespace: "ns", Name: c})
	}
	return p
}

func TestGangGetsDistinctDevices(t *testing.T) {
	a := newTestAllocator(t)
	resp, err := a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p0", "a"), pod("p1", "b")}})
	if err != nil || !resp.Fits {
		t.Fatalf("expected a fit, got %+v %v", resp, err)
	}
	first := resp.Pods[0].Allocations[0].Allocation.Devices.Results[0].Device
	second := resp.Pods[1].Allocations[0].Allocation.Devices.Results[0].Device
	if first == second {
		t.Fatalf("both pods got %s", first)
	}
}

func TestGangThatOutgrowsTheNodeDoesNotFit(t *testing.T) {
	a := newTestAllocator(t)
	resp, err := a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p0", "a"), pod("p1", "b"), pod("p2", "c")}})
	if err != nil || resp.Fits {
		t.Fatalf("expected no fit, got %+v %v", resp, err)
	}
}

func TestReservedDevicesAreNotHandedOut(t *testing.T) {
	a := newTestAllocator(t)
	reserved := []resourceapi.DeviceRequestAllocationResult{{Request: "gpu", Driver: testDriver, Pool: "n1", Device: "dev-0"}}
	resp, err := a.allocate(context.Background(), &AllocateRequest{Reserved: reserved, Pods: []PodPlacement{pod("p0", "a")}})
	if err != nil || !resp.Fits {
		t.Fatalf("expected a fit, got %+v %v", resp, err)
	}
	if got := resp.Pods[0].Allocations[0].Allocation.Devices.Results[0].Device; got != "dev-1" {
		t.Fatalf("got %s, want dev-1", got)
	}
}

func shareClaim(name string, shares int64) *resourceapi.ResourceClaim {
	c := claim(name)
	c.Spec.Devices.Requests[0].Exactly.Capacity = &resourceapi.CapacityRequirements{
		Requests: map[resourceapi.QualifiedName]resource.Quantity{"shares": *resource.NewQuantity(shares, resource.DecimalSI)},
	}
	return c
}

func TestSharedDeviceIsSplitByShares(t *testing.T) {
	hundred, one := resource.MustParse("100"), resource.MustParse("1")
	client := fake.NewClientset(
		&corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: "n1"}},
		&resourceapi.DeviceClass{
			ObjectMeta: metav1.ObjectMeta{Name: testDriver},
			Spec:       resourceapi.DeviceClassSpec{Selectors: []resourceapi.DeviceSelector{{CEL: &resourceapi.CELDeviceSelector{Expression: `device.driver == "` + testDriver + `"`}}}},
		},
		&resourceapi.ResourceSlice{
			ObjectMeta: metav1.ObjectMeta{Name: "n1-slice"},
			Spec: resourceapi.ResourceSliceSpec{
				Driver: testDriver, NodeName: ptr("n1"),
				Pool: resourceapi.ResourcePool{Name: "n1", ResourceSliceCount: 1},
				Devices: []resourceapi.Device{{
					Name:                     "dev-0",
					AllowMultipleAllocations: ptr(true),
					Capacity: map[resourceapi.QualifiedName]resourceapi.DeviceCapacity{"shares": {
						Value:         hundred,
						RequestPolicy: &resourceapi.CapacityRequestPolicy{Default: &hundred, ValidRange: &resourceapi.CapacityRequestPolicyRange{Min: &one, Max: &hundred, Step: &one}},
					}},
				}},
			},
		},
		shareClaim("a", 50), shareClaim("b", 50), shareClaim("c", 50),
	)
	a := allocatorFor(t, client)
	resp, err := a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p0", "a"), pod("p1", "b")}})
	if err != nil || !resp.Fits {
		t.Fatalf("two halves must fit: %+v %v", resp, err)
	}
	first := resp.Pods[0].Allocations[0].Allocation.Devices.Results[0]
	consumed := first.ConsumedCapacity["shares"]
	if first.ShareID == nil || consumed.Value() != 50 {
		t.Fatalf("expected a share of 50, got %+v", first)
	}
	resp, err = a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p0", "a"), pod("p1", "b"), pod("p2", "c")}})
	if err != nil || resp.Fits {
		t.Fatalf("a third half must not fit: %+v %v", resp, err)
	}
}

func allocatorFor(t *testing.T, client *fake.Clientset) *allocator {
	t.Helper()
	factory := informers.NewSharedInformerFactory(client, time.Minute)
	a := &allocator{
		nodes:   factory.Core().V1().Nodes().Lister(),
		slices:  factory.Resource().V1().ResourceSlices().Lister(),
		claims:  factory.Resource().V1().ResourceClaims().Lister(),
		classes: classLister{factory.Resource().V1().DeviceClasses().Lister()},
		cel:     cel.NewCache(10, cel.Features{EnableConsumableCapacity: true}),
	}
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(cancel)
	factory.Start(ctx.Done())
	factory.WaitForCacheSync(ctx.Done())
	return a
}
