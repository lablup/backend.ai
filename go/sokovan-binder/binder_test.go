package main

import (
	"context"
	"testing"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/fake"
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
	b := &binder{client: client}
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
	b := &binder{client: fake.NewClientset(taken)}
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
	b := &binder{client: client}
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
