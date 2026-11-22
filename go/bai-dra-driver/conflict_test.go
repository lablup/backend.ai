package main

import (
	"context"
	"strings"
	"sync"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/fake"
	"k8s.io/dynamic-resource-allocation/resourceslice"
)

// fakePublisher keeps the last published resources.
type fakePublisher struct {
	mu   sync.Mutex
	last *resourceslice.DriverResources
}

func (p *fakePublisher) PublishResources(_ context.Context, r resourceslice.DriverResources) error {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.last = &r
	return nil
}

func (p *fakePublisher) devices(node string) int {
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.last == nil {
		return -1
	}
	n := 0
	for _, s := range p.last.Pools[node].Slices {
		n += len(s.Devices)
	}
	return n
}

const testNode = "gpu-1"

// publishedDriver has published two devices of the plugin host.
func publishedDriver(t *testing.T, gpu bool) (*driver, *fakePublisher) {
	t.Helper()
	p := &fakePublisher{}
	d := newDriver("cuda.dra.backend.ai", testNode, nil, nil)
	d.publisher, d.gpu = p, gpu
	resp := &DevicesResponse{SlotName: "cuda", Devices: []DeviceInfo{{Name: "dev-0"}, {Name: "dev-1"}}}
	d.publishMu.Lock()
	err := d.publish(context.Background(), resp)
	d.lastDevices = resp
	d.publishMu.Unlock()
	if err != nil {
		t.Fatal(err)
	}
	return d, p
}

func testNodeObject(gpus int64) *corev1.Node {
	node := &corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: testNode}}
	if gpus > 0 {
		node.Status.Allocatable = corev1.ResourceList{nvidiaExtendedResource: *resource.NewQuantity(gpus, resource.DecimalSI)}
	}
	return node
}

func nvidiaSlice(name, driver, node string, devices int) *resourceapi.ResourceSlice {
	s := &resourceapi.ResourceSlice{ObjectMeta: metav1.ObjectMeta{Name: name}}
	s.Spec.Driver, s.Spec.NodeName = driver, &node
	s.Spec.Pool = resourceapi.ResourcePool{Name: node, ResourceSliceCount: 1}
	for i := range devices {
		s.Spec.Devices = append(s.Spec.Devices, resourceapi.Device{Name: "gpu-" + string(rune('0'+i))})
	}
	return s
}

func condition(t *testing.T, client *fake.Clientset) *corev1.NodeCondition {
	t.Helper()
	node, err := client.CoreV1().Nodes().Get(context.Background(), testNode, metav1.GetOptions{})
	if err != nil {
		t.Fatal(err)
	}
	for i := range node.Status.Conditions {
		if node.Status.Conditions[i].Type == conflictCondition {
			return &node.Status.Conditions[i]
		}
	}
	return nil
}

func events(t *testing.T, client *fake.Clientset) []corev1.Event {
	t.Helper()
	list, err := client.CoreV1().Events(metav1.NamespaceDefault).List(context.Background(), metav1.ListOptions{})
	if err != nil {
		t.Fatal(err)
	}
	return list.Items
}

func TestOtherAllocators(t *testing.T) {
	cases := []struct {
		name   string
		node   *corev1.Node
		slices []*resourceapi.ResourceSlice
		want   []string
	}{
		{"none", testNodeObject(0), nil, nil},
		{"NVIDIA DRA GPUs", testNodeObject(0), []*resourceapi.ResourceSlice{nvidiaSlice("s", nvidiaDRADriver, testNode, 2)}, []string{"gpu.nvidia.com (2 devices)"}},
		{"device plugin", testNodeObject(4), nil, []string{"device plugin (nvidia.com/gpu: 4)"}},
		{"ComputeDomain only", testNodeObject(0), []*resourceapi.ResourceSlice{nvidiaSlice("s", "compute-domain.nvidia.com", testNode, 2)}, nil},
		{"an empty NVIDIA slice", testNodeObject(0), []*resourceapi.ResourceSlice{nvidiaSlice("s", nvidiaDRADriver, testNode, 0)}, nil},
		{"another node's GPUs", testNodeObject(0), []*resourceapi.ResourceSlice{nvidiaSlice("s", nvidiaDRADriver, "gpu-2", 2)}, nil},
	}
	for _, c := range cases {
		got := otherAllocators(c.node, c.slices)
		if strings.Join(got, ";") != strings.Join(c.want, ";") {
			t.Errorf("%s: got %v, want %v", c.name, got, c.want)
		}
	}
}

func TestConflictWithdrawsTheGPUsAndRecoveryPublishesThemAgain(t *testing.T) {
	d, p := publishedDriver(t, true)
	node := testNodeObject(0)
	client := fake.NewClientset(node)
	w, _ := newConflictWatch(client, d, testNode)
	ctx := context.Background()

	if err := w.evaluate(ctx, node, []*resourceapi.ResourceSlice{nvidiaSlice("s", nvidiaDRADriver, testNode, 8)}); err != nil {
		t.Fatal(err)
	}
	if n := p.devices(testNode); n != 0 {
		t.Fatalf("a conflict publishes no device, got %d", n)
	}
	c := condition(t, client)
	if c == nil || c.Status != corev1.ConditionTrue || c.Reason != conflictReason || !strings.Contains(c.Message, "gpu.nvidia.com (8 devices)") {
		t.Fatalf("condition on conflict: %+v", c)
	}
	evs := events(t, client)
	if len(evs) != 1 || evs[0].Type != corev1.EventTypeWarning || evs[0].Reason != conflictReason || evs[0].InvolvedObject.Name != testNode {
		t.Fatalf("one Warning event on the node: %+v", evs)
	}

	// The same conflict again: no new event.
	node, _ = client.CoreV1().Nodes().Get(ctx, testNode, metav1.GetOptions{})
	if err := w.evaluate(ctx, node, []*resourceapi.ResourceSlice{nvidiaSlice("s", nvidiaDRADriver, testNode, 8)}); err != nil {
		t.Fatal(err)
	}
	if len(events(t, client)) != 1 {
		t.Fatal("an unchanged conflict records no new event")
	}

	if err := w.evaluate(ctx, node, nil); err != nil {
		t.Fatal(err)
	}
	if n := p.devices(testNode); n != 2 {
		t.Fatalf("recovery publishes the devices again, got %d", n)
	}
	c = condition(t, client)
	if c == nil || c.Status != corev1.ConditionFalse || c.Reason != noConflictReason {
		t.Fatalf("condition after recovery: %+v", c)
	}
	if evs := events(t, client); len(evs) != 2 || evs[1].Type != corev1.EventTypeNormal {
		t.Fatalf("recovery records a Normal event: %+v", evs)
	}
}

func TestDevicePluginGPUsAreAConflict(t *testing.T) {
	d, p := publishedDriver(t, true)
	node := testNodeObject(8)
	client := fake.NewClientset(node)
	w, _ := newConflictWatch(client, d, testNode)
	if err := w.evaluate(context.Background(), node, nil); err != nil {
		t.Fatal(err)
	}
	if n := p.devices(testNode); n != 0 {
		t.Fatalf("device plugin GPUs withdraw the devices, got %d", n)
	}
	if c := condition(t, client); c == nil || !strings.Contains(c.Message, "device plugin (nvidia.com/gpu: 8)") {
		t.Fatalf("the message names the device plugin: %+v", c)
	}
}

func TestComputeDomainSlicesAreNoConflict(t *testing.T) {
	d, p := publishedDriver(t, true)
	node := testNodeObject(0)
	client := fake.NewClientset(node)
	w, _ := newConflictWatch(client, d, testNode)
	slices := []*resourceapi.ResourceSlice{nvidiaSlice("cd", "compute-domain.nvidia.com", testNode, 4)}
	if err := w.evaluate(context.Background(), node, slices); err != nil {
		t.Fatal(err)
	}
	if n := p.devices(testNode); n != 2 {
		t.Fatalf("ComputeDomain devices keep the GPUs published, got %d", n)
	}
	if c := condition(t, client); c != nil {
		t.Fatalf("no condition is written on a node that never had a conflict: %+v", c)
	}
}

func TestAnNPUEntryIgnoresNVIDIAGPUs(t *testing.T) {
	d, p := publishedDriver(t, false)
	node := testNodeObject(8)
	client := fake.NewClientset(node)
	w, _ := newConflictWatch(client, d, testNode)
	if err := w.evaluate(context.Background(), node, []*resourceapi.ResourceSlice{nvidiaSlice("s", nvidiaDRADriver, testNode, 8)}); err != nil {
		t.Fatal(err)
	}
	if n := p.devices(testNode); n != 2 {
		t.Fatalf("an NPU entry keeps its devices, got %d", n)
	}
	if c := condition(t, client); c != nil || len(events(t, client)) != 0 {
		t.Fatalf("an NPU entry reports nothing: %+v", c)
	}
}

func TestAConflictBeforeTheFirstPublishWithdrawsIt(t *testing.T) {
	p := &fakePublisher{}
	d := newDriver("cuda.dra.backend.ai", testNode, nil, nil)
	d.publisher, d.gpu = p, true
	changed, err := d.withdraw(context.Background(), true)
	if err != nil || !changed || p.devices(testNode) != -1 {
		t.Fatalf("nothing to publish yet: changed=%v err=%v", changed, err)
	}
	d.publishMu.Lock()
	err = d.publish(context.Background(), &DevicesResponse{Devices: []DeviceInfo{{Name: "dev-0"}}})
	d.publishMu.Unlock()
	if err != nil || p.devices(testNode) != 0 {
		t.Fatalf("the first publish lists no device: %v", err)
	}
}

func TestWithdrawnSlicesKeepTheirSharedCounters(t *testing.T) {
	d, s := migDriver(t, &fakeHost{release: make(chan struct{})}, false)
	resp := &DevicesResponse{SlotName: "cuda", Devices: []DeviceInfo{sharedGPU("dev-0", gpuUUID(s, 0))}}
	slices, _, err := d.slices(resp)
	if err != nil {
		t.Fatal(err)
	}
	counters := 0
	for _, s := range withoutDevices(slices) {
		if len(s.Devices) != 0 {
			t.Fatalf("a withdrawn slice lists devices: %+v", s.Devices)
		}
		counters += len(s.SharedCounters)
	}
	if counters != 1 {
		t.Fatalf("the GPU's counter set stays: %d", counters)
	}
}

func TestTheWatchFollowsTheNodeAndItsSlices(t *testing.T) {
	d, p := publishedDriver(t, true)
	node := testNodeObject(0)
	client := fake.NewClientset(node)
	w, start := newConflictWatch(client, d, testNode)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	start(ctx.Done())
	if err := w.sync(ctx); err != nil {
		t.Fatal(err)
	}
	go w.run(ctx, time.Hour)

	slice := nvidiaSlice("nv", nvidiaDRADriver, testNode, 4)
	if _, err := client.ResourceV1().ResourceSlices().Create(ctx, slice, metav1.CreateOptions{}); err != nil {
		t.Fatal(err)
	}
	waitFor(t, "the GPUs are withdrawn", func() bool { return p.devices(testNode) == 0 })
	if err := client.ResourceV1().ResourceSlices().Delete(ctx, "nv", metav1.DeleteOptions{}); err != nil {
		t.Fatal(err)
	}
	waitFor(t, "the GPUs are published again", func() bool { return p.devices(testNode) == 2 })
	waitFor(t, "the condition is False", func() bool {
		c := condition(t, client)
		return c != nil && c.Status == corev1.ConditionFalse
	})
}

func waitFor(t *testing.T, what string, ok func() bool) {
	t.Helper()
	deadline := time.Now().Add(5 * time.Second)
	for !ok() {
		if time.Now().After(deadline) {
			t.Fatalf("timed out: %s", what)
		}
		time.Sleep(10 * time.Millisecond)
	}
}
