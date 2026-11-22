package main

import (
	"context"
	"fmt"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
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

func newTestAllocator(t *testing.T, extra ...runtime.Object) *allocator {
	t.Helper()
	objects := []runtime.Object{
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
		&corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: "n2"}},
	}
	for _, name := range []string{"a", "b", "c"} {
		if !hasObject(extra, name) {
			objects = append(objects, claim(name))
		}
	}
	return allocatorFor(t, fake.NewClientset(append(objects, extra...)...))
}

func hasObject(objects []runtime.Object, name string) bool {
	for _, o := range objects {
		if c, ok := o.(*resourceapi.ResourceClaim); ok && c.Name == name {
			return true
		}
	}
	return false
}

func onNode(node string) *corev1.NodeSelector {
	return &corev1.NodeSelector{NodeSelectorTerms: []corev1.NodeSelectorTerm{{
		MatchFields: []corev1.NodeSelectorRequirement{{Key: "metadata.name", Operator: corev1.NodeSelectorOpIn, Values: []string{node}}},
	}}}
}

func TestAllocatedRequestedClaimStaysCountedAndTiesThePodToItsNode(t *testing.T) {
	taken := claim("a")
	alloc := allocationOf("dev-0")
	alloc.NodeSelector = onNode("n1")
	taken.Status.Allocation = &alloc
	a := newTestAllocator(t, taken)
	// The claim of p0 is allocated on n1 already; p1 must not get dev-0.
	resp, err := a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p0", "a"), pod("p1", "b")}})
	if err != nil || !resp.Fits {
		t.Fatalf("expected a fit, got %+v %v", resp, err)
	}
	if got := resp.Pods[1].Allocations[0].Allocation.Devices.Results[0].Device; got != "dev-1" {
		t.Fatalf("got %s, want dev-1", got)
	}
	elsewhere := pod("p0", "a")
	elsewhere.Node = "n2"
	resp, err = a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{elsewhere}})
	if err != nil || resp.Fits {
		t.Fatalf("a claim allocated on n1 must not fit n2: %+v %v", resp, err)
	}
}

func TestReservedAndInformerAllocationsCountOnce(t *testing.T) {
	taken := claim("a")
	alloc := allocationOf("dev-0")
	taken.Status.Allocation = &alloc
	a := newTestAllocator(t, taken)
	// The same allocation arrives from the informer and as reserved: dev-1 stays free.
	reserved := []ReservedClaim{{Namespace: "ns", Name: "a", Allocation: allocationOf("dev-0")}}
	resp, err := a.allocate(context.Background(), &AllocateRequest{Reserved: reserved, Pods: []PodPlacement{pod("p1", "b")}})
	if err != nil || !resp.Fits {
		t.Fatalf("expected a fit, got %+v %v", resp, err)
	}
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
	reserved := []ReservedClaim{{Namespace: "ns", Name: "in-flight", Allocation: allocationOf("dev-0")}}
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
		cel:     cel.NewCache(10, celFeatures),
	}
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(cancel)
	factory.Start(ctx.Done())
	factory.WaitForCacheSync(ctx.Done())
	return a
}

func sharedSlice(capacities ...int64) *resourceapi.ResourceSlice {
	var devices []resourceapi.Device
	one := resource.MustParse("1")
	for i, c := range capacities {
		value := *resource.NewQuantity(c, resource.DecimalSI)
		devices = append(devices, resourceapi.Device{
			Name:                     fmt.Sprintf("dev-%d", i),
			AllowMultipleAllocations: ptr(true),
			Attributes: map[resourceapi.QualifiedName]resourceapi.DeviceAttribute{
				"resource.kubernetes.io/pciBusID": {StringValue: ptr(fmt.Sprintf("0000:0%d:00.0", i))},
			},
			Capacity: map[resourceapi.QualifiedName]resourceapi.DeviceCapacity{"shares": {
				Value:         value,
				RequestPolicy: &resourceapi.CapacityRequestPolicy{Default: &value, ValidRange: &resourceapi.CapacityRequestPolicyRange{Min: &one, Max: &value, Step: &one}},
			}},
		})
	}
	return &resourceapi.ResourceSlice{
		ObjectMeta: metav1.ObjectMeta{Name: "n1-slice"},
		Spec: resourceapi.ResourceSliceSpec{
			Driver: testDriver, NodeName: ptr("n1"),
			Pool:    resourceapi.ResourcePool{Name: "n1", ResourceSliceCount: 1},
			Devices: devices,
		},
	}
}

func sharesOf(n int64) *resourceapi.CapacityRequirements {
	return &resourceapi.CapacityRequirements{
		Requests: map[resourceapi.QualifiedName]resource.Quantity{"shares": *resource.NewQuantity(n, resource.DecimalSI)},
	}
}

func sharedAllocator(t *testing.T, claims ...*resourceapi.ResourceClaim) *allocator {
	t.Helper()
	objects := []runtime.Object{
		&corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: "n1"}},
		&resourceapi.DeviceClass{
			ObjectMeta: metav1.ObjectMeta{Name: testDriver},
			Spec:       resourceapi.DeviceClassSpec{Selectors: []resourceapi.DeviceSelector{{CEL: &resourceapi.CELDeviceSelector{Expression: `device.driver == "` + testDriver + `"`}}}},
		},
		sharedSlice(100, 100),
	}
	for _, c := range claims {
		objects = append(objects, c)
	}
	return allocatorFor(t, fake.NewClientset(objects...))
}

func TestSplitSharesLandOnDistinctDevices(t *testing.T) {
	split := claim("split")
	part := func(name string) resourceapi.DeviceRequest {
		return resourceapi.DeviceRequest{Name: name, Exactly: &resourceapi.ExactDeviceRequest{
			DeviceClassName: testDriver, AllocationMode: resourceapi.DeviceAllocationModeExactCount, Count: 1, Capacity: sharesOf(40),
		}}
	}
	split.Spec.Devices.Requests = []resourceapi.DeviceRequest{part("p0"), part("p1")}
	attr := resourceapi.FullyQualifiedName("resource.kubernetes.io/pciBusID")
	split.Spec.Devices.Constraints = []resourceapi.DeviceConstraint{{Requests: []string{"p0", "p1"}, DistinctAttribute: &attr}}
	a := sharedAllocator(t, split)
	resp, err := a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p", "split")}})
	if err != nil || !resp.Fits {
		t.Fatalf("expected a fit, got %+v %v", resp, err)
	}
	results := resp.Pods[0].Allocations[0].Allocation.Devices.Results
	if len(results) != 2 || results[0].Device == results[1].Device {
		t.Fatalf("parts must land on distinct devices: %+v", results)
	}
}

func TestFirstAvailableFallsBackToASubrequestThatFits(t *testing.T) {
	pick := claim("pick")
	pick.Spec.Devices.Requests = []resourceapi.DeviceRequest{{Name: "gpu", FirstAvailable: []resourceapi.DeviceSubRequest{
		{Name: "big", DeviceClassName: testDriver, AllocationMode: resourceapi.DeviceAllocationModeExactCount, Count: 1, Capacity: sharesOf(150)},
		{Name: "small", DeviceClassName: testDriver, AllocationMode: resourceapi.DeviceAllocationModeExactCount, Count: 1, Capacity: sharesOf(80)},
	}}}
	a := sharedAllocator(t, pick)
	resp, err := a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p", "pick")}})
	if err != nil || !resp.Fits {
		t.Fatalf("expected a fit, got %+v %v", resp, err)
	}
	if got := resp.Pods[0].Allocations[0].Allocation.Devices.Results[0].Request; got != "gpu/small" {
		t.Fatalf("got request %s, want gpu/small", got)
	}
}

func TestAnAdminAccessAllocationLeavesItsDeviceFree(t *testing.T) {
	admin := claim("x")
	alloc := allocationOf("dev-0")
	alloc.Devices.Results[0].AdminAccess = ptr(true)
	admin.Status.Allocation = &alloc
	a := newTestAllocator(t, admin)
	resp, err := a.allocate(context.Background(), &AllocateRequest{Pods: []PodPlacement{pod("p0", "a"), pod("p1", "b")}})
	if err != nil || !resp.Fits {
		t.Fatalf("both devices must stay usable: %+v %v", resp, err)
	}
}
