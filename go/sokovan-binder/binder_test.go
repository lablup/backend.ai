package main

import (
	"context"
	"errors"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	dynamicfake "k8s.io/client-go/dynamic/fake"
	"k8s.io/client-go/kubernetes/fake"
	resourcelisters "k8s.io/client-go/listers/resource/v1"
	"k8s.io/client-go/tools/cache"
)

func allocationOf(devices ...string) resourceapi.AllocationResult {
	var results []resourceapi.DeviceRequestAllocationResult
	for _, d := range devices {
		results = append(results, resourceapi.DeviceRequestAllocationResult{Request: "gpu", Driver: testDriver, Pool: "n1", Device: d})
	}
	return resourceapi.AllocationResult{Devices: resourceapi.DeviceAllocationResult{Results: results}}
}

func testPod() *corev1.Pod {
	return &corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: "p", Namespace: "ns", UID: "uid-p"}}
}

func TestAllocateClaimRecordsAllocationAndReservation(t *testing.T) {
	client := fake.NewClientset(claim("a"))
	b := newBinder(client, nil)
	ca := ClaimAllocation{Name: "a", Allocation: allocationOf("dev-0")}
	if err := b.allocateClaim(context.Background(), "ns", testPod(), ca); err != nil {
		t.Fatal(err)
	}
	if err := b.allocateClaim(context.Background(), "ns", testPod(), ca); err != nil {
		t.Fatalf("a retry must be accepted: %v", err)
	}
	got, _ := client.ResourceV1().ResourceClaims("ns").Get(context.Background(), "a", metav1.GetOptions{})
	if got.Status.Allocation == nil || got.Status.Allocation.Devices.Results[0].Device != "dev-0" {
		t.Fatalf("allocation not recorded: %+v", got.Status)
	}
	if len(got.Status.ReservedFor) != 1 || got.Status.ReservedFor[0].UID != "uid-p" {
		t.Fatalf("reservation not recorded once: %+v", got.Status.ReservedFor)
	}
}

func TestAllocateClaimRefusesOtherDevices(t *testing.T) {
	taken := claim("a")
	alloc := allocationOf("dev-1")
	taken.Status.Allocation = &alloc
	b := newBinder(fake.NewClientset(taken), nil)
	err := b.allocateClaim(context.Background(), "ns", testPod(), ClaimAllocation{Name: "a", Allocation: allocationOf("dev-0")})
	if err == nil {
		t.Fatal("expected a conflict")
	}
}

func TestRollbackFreesOnlyItsOwnAllocation(t *testing.T) {
	mine, theirs := claim("a"), claim("b")
	a, other := allocationOf("dev-0"), allocationOf("dev-1")
	mine.Status.Allocation, theirs.Status.Allocation = &a, &other
	client := fake.NewClientset(mine, theirs)
	b := newBinder(client, nil)
	br := &bindRequest{ObjectMeta: metav1.ObjectMeta{Namespace: "ns"}, Spec: bindRequestSpec{
		ResourceClaimAllocations: []ClaimAllocation{
			{Name: "a", Allocation: allocationOf("dev-0")},
			{Name: "b", Allocation: allocationOf("dev-0")},
		},
	}}
	b.rollback(context.Background(), br)
	gotA, _ := client.ResourceV1().ResourceClaims("ns").Get(context.Background(), "a", metav1.GetOptions{})
	gotB, _ := client.ResourceV1().ResourceClaims("ns").Get(context.Background(), "b", metav1.GetOptions{})
	if gotA.Status.Allocation != nil {
		t.Fatal("own allocation was not freed")
	}
	if gotB.Status.Allocation == nil {
		t.Fatal("an allocation written by someone else was freed")
	}
}

func TestAllocateClaimRefusesADeviceAnotherClaimHolds(t *testing.T) {
	client := fake.NewClientset(claim("a"), claim("b"))
	b := newBinder(client, nil)
	if err := b.allocateClaim(context.Background(), "ns", testPod(), ClaimAllocation{Name: "a", Allocation: allocationOf("dev-0")}); err != nil {
		t.Fatal(err)
	}
	other := &corev1.Pod{ObjectMeta: metav1.ObjectMeta{Name: "q", Namespace: "ns", UID: "uid-q"}}
	err := b.allocateClaim(context.Background(), "ns", other, ClaimAllocation{Name: "b", Allocation: allocationOf("dev-0")})
	if err == nil {
		t.Fatal("expected a device conflict")
	}
}

func TestRollbackRemovesOnlyItsPodFromTheReservation(t *testing.T) {
	shared := claim("a")
	alloc := allocationOf("dev-0")
	shared.Status.Allocation = &alloc
	shared.Status.ReservedFor = []resourceapi.ResourceClaimConsumerReference{
		{Resource: "pods", Name: "p", UID: "uid-p"},
		{Resource: "pods", Name: "q", UID: "uid-q"},
	}
	client := fake.NewClientset(shared)
	b := newBinder(client, nil)
	br := &bindRequest{ObjectMeta: metav1.ObjectMeta{Namespace: "ns"}, Spec: bindRequestSpec{
		PodName: "p", PodUID: "uid-p", SelectedNode: "n1",
		ResourceClaimAllocations: []ClaimAllocation{{Name: "a", Allocation: allocationOf("dev-0")}},
	}}
	b.rollback(context.Background(), br)
	got, _ := client.ResourceV1().ResourceClaims("ns").Get(context.Background(), "a", metav1.GetOptions{})
	if got.Status.Allocation == nil || len(got.Status.ReservedFor) != 1 || got.Status.ReservedFor[0].UID != "uid-q" {
		t.Fatalf("only p must leave the reservation: %+v", got.Status)
	}
}

func TestRollbackKeepsTheClaimsOfABoundPod(t *testing.T) {
	mine := claim("a")
	alloc := allocationOf("dev-0")
	mine.Status.Allocation = &alloc
	bound := testPod()
	bound.Spec.NodeName = "n1"
	client := fake.NewClientset(mine, bound)
	b := newBinder(client, nil)
	br := &bindRequest{ObjectMeta: metav1.ObjectMeta{Namespace: "ns"}, Spec: bindRequestSpec{
		PodName: "p", PodUID: "uid-p", SelectedNode: "n1",
		ResourceClaimAllocations: []ClaimAllocation{{Name: "a", Allocation: allocationOf("dev-0")}},
	}}
	b.rollback(context.Background(), br)
	got, _ := client.ResourceV1().ResourceClaims("ns").Get(context.Background(), "a", metav1.GetOptions{})
	if got.Status.Allocation == nil {
		t.Fatal("the claim of a bound pod was freed")
	}
}

func TestSameDevicesIgnoresOrderButNotShares(t *testing.T) {
	ab, ba := allocationOf("dev-0", "dev-1"), allocationOf("dev-1", "dev-0")
	if !sameDevices(&ab, &ba) {
		t.Fatal("order must not matter")
	}
	shared := allocationOf("dev-0", "dev-1")
	share := types.UID("s1")
	shared.Devices.Results[0].ShareID = &share
	if sameDevices(&ab, &shared) {
		t.Fatal("a share differs from the whole device")
	}
}

func claimLister(t *testing.T, claims ...*resourceapi.ResourceClaim) resourcelisters.ResourceClaimLister {
	t.Helper()
	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{cache.NamespaceIndex: cache.MetaNamespaceIndexFunc})
	for _, c := range claims {
		if err := indexer.Add(c); err != nil {
			t.Fatal(err)
		}
	}
	return resourcelisters.NewResourceClaimLister(indexer)
}

func TestAWrittenAllocationHoldsItsDeviceOnlyUntilTheInformerCatchesUp(t *testing.T) {
	written := writtenAllocation{allocation: allocationOf("dev-0"), uid: "uid-a", resourceVersion: "10", at: time.Now()}
	at := func(rv string) *resourceapi.ResourceClaim {
		c := claim("a")
		c.UID, c.ResourceVersion = "uid-a", rv
		return c
	}
	recreated := at("12")
	recreated.UID = "uid-a2"
	cases := []struct {
		name     string
		informer []*resourceapi.ResourceClaim
		synced   string
		conflict bool
	}{
		{"informer behind the write", []*resourceapi.ResourceClaim{at("9")}, "9", true},
		{"informer shows the claim freed", []*resourceapi.ResourceClaim{at("11")}, "11", false},
		{"claim deleted after the write", nil, "11", false},
		{"claim absent before the informer reached the write", nil, "9", true},
		{"claim recreated", []*resourceapi.ResourceClaim{recreated}, "12", false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			b := newBinder(fake.NewClientset(claim("b")), nil)
			b.claims = claimLister(t, tc.informer...)
			b.claimsVersion = func() string { return tc.synced }
			b.written["ns/a"] = written
			err := b.allocateClaim(context.Background(), "ns", testPod(), ClaimAllocation{Name: "b", Allocation: allocationOf("dev-0")})
			if (err != nil) != tc.conflict {
				t.Fatalf("conflict = %v, want %v", err, tc.conflict)
			}
		})
	}
}

func sliceLister(t *testing.T, devices ...resourceapi.Device) resourcelisters.ResourceSliceLister {
	t.Helper()
	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{})
	rs := &resourceapi.ResourceSlice{
		ObjectMeta: metav1.ObjectMeta{Name: "n1-slice"},
		Spec:       resourceapi.ResourceSliceSpec{Driver: testDriver, Pool: resourceapi.ResourcePool{Name: "n1"}, Devices: devices},
	}
	if err := indexer.Add(rs); err != nil {
		t.Fatal(err)
	}
	return resourcelisters.NewResourceSliceLister(indexer)
}

func shareOf(device, share string, shares int64) resourceapi.AllocationResult {
	id := types.UID(share)
	return resourceapi.AllocationResult{Devices: resourceapi.DeviceAllocationResult{Results: []resourceapi.DeviceRequestAllocationResult{{
		Request: "gpu", Driver: testDriver, Pool: "n1", Device: device, ShareID: &id,
		ConsumedCapacity: map[resourceapi.QualifiedName]resource.Quantity{"shares": *resource.NewQuantity(shares, resource.DecimalSI)},
	}}}}
}

func sharedDevice(multiple bool) resourceapi.Device {
	return resourceapi.Device{
		Name:                     "dev-0",
		AllowMultipleAllocations: &multiple,
		Capacity:                 map[resourceapi.QualifiedName]resourceapi.DeviceCapacity{"shares": {Value: resource.MustParse("100")}},
	}
}

func TestSharesOfADeviceAreSummedOverEveryHolder(t *testing.T) {
	cases := []struct {
		name     string
		multiple bool
		mine     int64
		conflict bool
	}{
		{"within the capacity", true, 40, false},
		{"over the capacity", true, 50, true},
		{"a device that takes one allocation", false, 10, true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			held := claim("a")
			alloc := shareOf("dev-0", "s1", 60)
			held.Status.Allocation = &alloc
			b := newBinder(fake.NewClientset(claim("b")), nil)
			b.claims = claimLister(t, held)
			b.slices = sliceLister(t, sharedDevice(tc.multiple))
			err := b.allocateClaim(context.Background(), "ns", testPod(), ClaimAllocation{Name: "b", Allocation: shareOf("dev-0", "s2", tc.mine)})
			if (err != nil) != tc.conflict {
				t.Fatalf("conflict = %v, want %v", err, tc.conflict)
			}
		})
	}
}

func TestAnAdminAccessAllocationHoldsNoDevice(t *testing.T) {
	held := claim("a")
	alloc := allocationOf("dev-0")
	alloc.Devices.Results[0].AdminAccess = ptr(true)
	held.Status.Allocation = &alloc
	b := newBinder(fake.NewClientset(claim("b")), nil)
	b.claims = claimLister(t, held)
	if err := b.allocateClaim(context.Background(), "ns", testPod(), ClaimAllocation{Name: "b", Allocation: allocationOf("dev-0")}); err != nil {
		t.Fatalf("an admin access allocation must not conflict: %v", err)
	}
}

func podWithClaims() *corev1.Pod {
	p := testPod()
	p.Spec.ResourceClaims = []corev1.PodResourceClaim{
		{Name: "named", ResourceClaimName: ptr("a")},
		{Name: "templated", ResourceClaimTemplateName: ptr("t")},
	}
	p.Status.ResourceClaimStatuses = []corev1.PodResourceClaimStatus{{Name: "templated", ResourceClaimName: ptr("b")}}
	return p
}

func allocatedFor(name string, uid types.UID) *resourceapi.ResourceClaim {
	c := claim(name)
	alloc := allocationOf("dev-0")
	c.Status.Allocation = &alloc
	c.Status.ReservedFor = []resourceapi.ResourceClaimConsumerReference{{Resource: "pods", Name: "p", UID: uid}}
	return c
}

func TestEveryClaimOfThePodMustBeAllocatedForItBeforeTheBind(t *testing.T) {
	ready := newBinder(fake.NewClientset(allocatedFor("a", "uid-p"), allocatedFor("b", "uid-p")), nil)
	if err := ready.checkPodClaims(context.Background(), podWithClaims()); err != nil {
		t.Fatalf("allocated claims must pass: %v", err)
	}
	cases := map[string]*binder{
		"not reserved for the pod": newBinder(fake.NewClientset(allocatedFor("a", "uid-p"), allocatedFor("b", "uid-q")), nil),
		"not allocated":            newBinder(fake.NewClientset(allocatedFor("a", "uid-p"), claim("b")), nil),
		"missing":                  newBinder(fake.NewClientset(allocatedFor("a", "uid-p")), nil),
	}
	for name, b := range cases {
		t.Run(name, func(t *testing.T) {
			var notReady errClaimsNotReady
			if err := b.checkPodClaims(context.Background(), podWithClaims()); !errors.As(err, &notReady) {
				t.Fatalf("got %v, want a not-ready claim", err)
			}
		})
	}
	uncreated := podWithClaims()
	uncreated.Status.ResourceClaimStatuses = nil
	var notReady errClaimsNotReady
	if err := ready.checkPodClaims(context.Background(), uncreated); !errors.As(err, &notReady) {
		t.Fatalf("a claim not generated yet must fail the bind: %v", err)
	}
}

func succeededRequest() (*bindRequest, *unstructured.Unstructured) {
	br := &bindRequest{
		ObjectMeta: metav1.ObjectMeta{Name: "p-1", Namespace: "ns", UID: "br-uid"},
		Spec: bindRequestSpec{
			PodName: "p", PodUID: "uid-p", SelectedNode: "n1",
			ResourceClaimAllocations: []ClaimAllocation{{Name: "a", Allocation: allocationOf("dev-0")}},
		},
	}
	obj := &unstructured.Unstructured{}
	obj.SetAPIVersion("scheduling.backend.ai/v1alpha1")
	obj.SetKind("BindRequest")
	obj.SetName(br.Name)
	obj.SetNamespace(br.Namespace)
	obj.SetUID(br.UID)
	return br, obj
}

func requestExists(t *testing.T, b *binder) bool {
	t.Helper()
	_, err := b.dynamic.Resource(bindRequestGVR).Namespace("ns").Get(context.Background(), "p-1", metav1.GetOptions{})
	return err == nil
}

func dynamicWith(obj runtime.Object) *dynamicfake.FakeDynamicClient {
	return dynamicfake.NewSimpleDynamicClientWithCustomListKinds(
		runtime.NewScheme(), map[schema.GroupVersionResource]string{bindRequestGVR: "BindRequestList"}, obj)
}

func TestASucceededRequestStaysUntilTheClaimInformerShowsItsAllocation(t *testing.T) {
	br, obj := succeededRequest()
	b := newBinder(nil, dynamicWith(obj))
	now := time.Now()
	b.now = func() time.Time { return now }
	b.claims = claimLister(t, claim("a"))
	b.deleteSucceeded(context.Background(), br, "ns/p-1")
	now = now.Add(time.Minute)
	b.deleteSucceeded(context.Background(), br, "ns/p-1")
	if !requestExists(t, b) {
		t.Fatal("deleted before the informer showed the allocation")
	}
	b.claims = claimLister(t, allocatedFor("a", "uid-p"))
	b.deleteSucceeded(context.Background(), br, "ns/p-1")
	if requestExists(t, b) {
		t.Fatal("kept after the informer showed the allocation")
	}
}

func TestASucceededRequestGoesAfterTheSafetyAge(t *testing.T) {
	br, obj := succeededRequest()
	b := newBinder(nil, dynamicWith(obj))
	now := time.Now()
	b.now = func() time.Time { return now }
	b.claims = claimLister(t)
	b.deleteSucceeded(context.Background(), br, "ns/p-1")
	now = now.Add(succeededMaxAge + time.Second)
	b.deleteSucceeded(context.Background(), br, "ns/p-1")
	if requestExists(t, b) {
		t.Fatal("kept past the safety age")
	}
}
