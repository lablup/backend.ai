package main

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/dynamic-resource-allocation/kubeletplugin"
	"k8s.io/dynamic-resource-allocation/resourceslice"
	"k8s.io/klog/v2"

	"github.com/lablup/backend.ai/go/bai-dra-driver/nvmig"
)

// publisher publishes the node's ResourceSlices: the kubelet plugin helper.
type publisher interface {
	PublishResources(ctx context.Context, resources resourceslice.DriverResources) error
}

// driver turns the plugin host's devices into a ResourceSlice and its prepare answers into CDI.
type driver struct {
	name      string
	nodeName  string
	bridge    *bridge
	cdi       *cdiWriter
	publisher publisher
	// gpu: the driver publishes NVIDIA GPUs and withdraws them while another allocator has some.
	gpu bool

	// publishMu serializes publishing; it guards lastDevices, withdrawn and migParents.
	publishMu   sync.Mutex
	lastDevices *DevicesResponse
	// withdrawn: another GPU allocator is on the node, so the slices list no devices.
	withdrawn bool

	// mu guards prepared and claimLocks only; bridge calls run under the claim's own lock.
	mu         sync.Mutex
	prepared   map[types.UID][]kubeletplugin.Device
	claimLocks map[types.UID]*claimLock

	// What was last published: the plugin host instance and its device generation.
	publishedHost       string
	publishedGeneration int64
	published           atomic.Bool

	// Dynamic MIG, nil when off: MIG devices are created at prepare (dynmig.go).
	mig *nvmig.Manager
	// Kubernetes 1.35 and later take shared counters in ResourceSlices without devices.
	splitCounters bool
	// The last listed device of each dynamic-MIG GPU, by UUID (publish only): the plugin host
	// may not list a GPU while it is in MIG mode.
	migParents map[string]DeviceInfo
	// Whole-GPU device name → UUID of the dynamic-MIG GPUs last published; under mu.
	wholeGPUs map[string]string
}

type claimLock struct {
	mu   sync.Mutex
	refs int
}

func newDriver(name, nodeName string, b *bridge, cdi *cdiWriter) *driver {
	return &driver{
		name:       name,
		nodeName:   nodeName,
		bridge:     b,
		cdi:        cdi,
		prepared:   map[types.UID][]kubeletplugin.Device{},
		claimLocks: map[types.UID]*claimLock{},
		migParents: map[string]DeviceInfo{},
		wholeGPUs:  map[string]string{},
	}
}

// lockClaim serializes the work on one claim; different claims proceed in parallel.
func (d *driver) lockClaim(uid types.UID) func() {
	d.mu.Lock()
	l, ok := d.claimLocks[uid]
	if !ok {
		l = &claimLock{}
		d.claimLocks[uid] = l
	}
	l.refs++
	d.mu.Unlock()
	l.mu.Lock()
	return func() {
		l.mu.Unlock()
		d.mu.Lock()
		l.refs--
		if l.refs == 0 {
			delete(d.claimLocks, uid)
		}
		d.mu.Unlock()
	}
}

// syncDevices publishes the plugin host's devices when the host or its device list changed.
func (d *driver) syncDevices(ctx context.Context) error {
	d.publishMu.Lock()
	defer d.publishMu.Unlock()
	resp, err := d.bridge.Devices(ctx)
	if err != nil {
		return err
	}
	if d.published.Load() && resp.HostID == d.publishedHost && resp.Generation == d.publishedGeneration {
		return nil
	}
	if err := d.publish(ctx, resp); err != nil {
		return err
	}
	d.lastDevices = resp
	d.publishedHost, d.publishedGeneration = resp.HostID, resp.Generation
	d.published.Store(true)
	return nil
}

// withdraw takes the GPUs out of the slices while another allocator is on the node
// (conflict.go) and publishes them again once it is gone. It reports whether the state changed.
func (d *driver) withdraw(ctx context.Context, conflict bool) (bool, error) {
	d.publishMu.Lock()
	defer d.publishMu.Unlock()
	if conflict == d.withdrawn {
		return false, nil
	}
	d.withdrawn = conflict
	if d.lastDevices != nil {
		if err := d.publish(ctx, d.lastDevices); err != nil {
			d.withdrawn = !conflict
			return false, err
		}
	}
	return true, nil
}

// publish runs under publishMu.
func (d *driver) publish(ctx context.Context, resp *DevicesResponse) error {
	slices, wholeGPUs, err := d.slices(resp)
	if err != nil {
		return err
	}
	if d.withdrawn {
		slices = withoutDevices(slices)
	}
	count := 0
	for _, s := range slices {
		count += len(s.Devices)
	}
	d.mu.Lock()
	d.wholeGPUs = wholeGPUs
	d.mu.Unlock()
	klog.FromContext(ctx).Info("publishing devices", "count", count, "slices", len(slices), "slot", resp.SlotName, "generation", resp.Generation, "withdrawn", d.withdrawn)
	return d.publisher.PublishResources(ctx, resourceslice.DriverResources{
		Pools: map[string]resourceslice.Pool{d.nodeName: {Slices: slices}},
	})
}

// withoutDevices keeps the slices and their shared counters but lists no device: no new claim
// is allocated, and the claims allocated before stay prepared.
func withoutDevices(slices []resourceslice.Slice) []resourceslice.Slice {
	out := make([]resourceslice.Slice, 0, len(slices))
	for _, s := range slices {
		s.Devices = nil
		out = append(out, s)
	}
	return out
}

func toDevices(resp *DevicesResponse) ([]resourceapi.Device, error) {
	devices := make([]resourceapi.Device, 0, len(resp.Devices))
	for _, info := range resp.Devices {
		device := resourceapi.Device{
			Name:       info.Name,
			Attributes: map[resourceapi.QualifiedName]resourceapi.DeviceAttribute{},
			Capacity:   map[resourceapi.QualifiedName]resourceapi.DeviceCapacity{},
		}
		for k, v := range info.Attributes {
			device.Attributes[resourceapi.QualifiedName(k)] = attribute(v)
		}
		for k, v := range info.Capacity {
			q, err := resource.ParseQuantity(v)
			if err != nil {
				return nil, fmt.Errorf("device %s capacity %s: %w", info.Name, k, err)
			}
			capacity := resourceapi.DeviceCapacity{Value: q}
			if p, ok := info.RequestPolicies[k]; ok {
				if capacity.RequestPolicy, err = requestPolicy(p); err != nil {
					return nil, fmt.Errorf("device %s capacity %s policy: %w", info.Name, k, err)
				}
			}
			device.Capacity[resourceapi.QualifiedName(k)] = capacity
		}
		if info.AllowMultipleAllocations {
			device.AllowMultipleAllocations = ptr(true)
		}
		devices = append(devices, device)
	}
	return devices, nil
}

func requestPolicy(p CapacityPolicy) (*resourceapi.CapacityRequestPolicy, error) {
	var q [4]resource.Quantity
	for i, s := range []string{p.Default, p.Min, p.Max, p.Step} {
		v, err := resource.ParseQuantity(s)
		if err != nil {
			return nil, err
		}
		q[i] = v
	}
	return &resourceapi.CapacityRequestPolicy{
		Default:    &q[0],
		ValidRange: &resourceapi.CapacityRequestPolicyRange{Min: &q[1], Max: &q[2], Step: &q[3]},
	}, nil
}

func ptr[T any](v T) *T { return &v }

// attribute keeps whole numbers as ints; a fractional number becomes its decimal string.
func attribute(v any) resourceapi.DeviceAttribute {
	switch t := v.(type) {
	case bool:
		return resourceapi.DeviceAttribute{BoolValue: &t}
	case json.Number:
		if i, err := t.Int64(); err == nil {
			return resourceapi.DeviceAttribute{IntValue: &i}
		}
		s := t.String()
		return resourceapi.DeviceAttribute{StringValue: &s}
	case float64:
		if t == math.Trunc(t) && math.Abs(t) < 1<<53 {
			i := int64(t)
			return resourceapi.DeviceAttribute{IntValue: &i}
		}
		s := strconv.FormatFloat(t, 'f', -1, 64)
		return resourceapi.DeviceAttribute{StringValue: &s}
	case string:
		return resourceapi.DeviceAttribute{StringValue: &t}
	default:
		s := fmt.Sprint(t)
		return resourceapi.DeviceAttribute{StringValue: &s}
	}
}

func (d *driver) PrepareResourceClaims(ctx context.Context, claims []*resourceapi.ResourceClaim) (map[types.UID]kubeletplugin.PrepareResult, error) {
	results := make(map[types.UID]kubeletplugin.PrepareResult, len(claims))
	var mu sync.Mutex
	var wg sync.WaitGroup
	for _, claim := range claims {
		wg.Add(1)
		go func() {
			defer wg.Done()
			result := d.prepare(ctx, claim)
			mu.Lock()
			results[claim.UID] = result
			mu.Unlock()
		}()
	}
	wg.Wait()
	return results, nil
}

func (d *driver) prepare(ctx context.Context, claim *resourceapi.ResourceClaim) kubeletplugin.PrepareResult {
	unlock := d.lockClaim(claim.UID)
	defer unlock()
	d.mu.Lock()
	devices, ok := d.prepared[claim.UID]
	d.mu.Unlock()
	if ok {
		return kubeletplugin.PrepareResult{Devices: devices}
	}
	if claim.Status.Allocation == nil {
		return kubeletplugin.PrepareResult{Err: fmt.Errorf("claim %s is not allocated", claim.Name)}
	}
	var names, migNames []string
	var ours []resourceapi.DeviceRequestAllocationResult
	consumed := map[string]map[string]string{}
	for _, r := range claim.Status.Allocation.Devices.Results {
		if r.Driver != d.name {
			continue
		}
		ours = append(ours, r)
		if d.mig != nil && d.mig.IsPartition(r.Device) {
			migNames = append(migNames, r.Device)
			continue
		}
		names = append(names, r.Device)
		if len(r.ConsumedCapacity) > 0 {
			consumed[r.Device] = map[string]string{}
			for k, q := range r.ConsumedCapacity {
				consumed[r.Device][string(k)] = quantityString(q)
			}
		}
	}
	start := time.Now()
	migIDs, err := d.prepareMig(string(claim.UID), names, migNames)
	if err != nil {
		return kubeletplugin.PrepareResult{Err: err}
	}
	resp := &PrepareResponse{}
	if len(names) > 0 {
		if resp, err = d.bridge.Prepare(ctx, string(claim.UID), names, consumed); err != nil {
			return kubeletplugin.PrepareResult{Err: d.rollbackMig(string(claim.UID), err)}
		}
	}
	// The claim's own spec and the CDI devices no single device owns go to the first device.
	claimIDs := append([]string{}, resp.Edits.CDIDevices...)
	if !resp.Edits.Empty() || len(migIDs.nodes) > 0 {
		var edits *ContainerEdits
		if !resp.Edits.Empty() {
			edits = &resp.Edits
		}
		cdiID, deviceIDs, err := d.cdi.WriteSpec(string(claim.UID), edits, migIDs.nodes)
		if err != nil {
			return kubeletplugin.PrepareResult{Err: d.rollbackMig(string(claim.UID), err)}
		}
		if cdiID != "" {
			claimIDs = append(claimIDs, cdiID)
		}
		for name, id := range deviceIDs {
			migIDs.ids[name] = append(migIDs.ids[name], id)
		}
	}
	devices = make([]kubeletplugin.Device, 0, len(ours))
	for i, r := range ours {
		ids := append([]string{}, resp.DeviceCDIDevices[r.Device]...)
		ids = append(ids, migIDs.ids[r.Device]...)
		if i == 0 {
			ids = append(ids, claimIDs...)
		}
		devices = append(devices, kubeletplugin.Device{
			Requests:     []string{r.Request},
			PoolName:     r.Pool,
			DeviceName:   r.Device,
			CDIDeviceIDs: ids,
		})
	}
	d.mu.Lock()
	d.prepared[claim.UID] = devices
	d.mu.Unlock()
	klog.FromContext(ctx).Info("claim prepared", "claim", klog.KObj(claim), "devices", names, "elapsed", time.Since(start))
	return kubeletplugin.PrepareResult{Devices: devices}
}

// quantityString is the plain decimal of a quantity ("2000", not "2k"; "0.5", not "500m").
func quantityString(q resource.Quantity) string {
	return q.AsDec().String()
}

func (d *driver) UnprepareResourceClaims(ctx context.Context, claims []kubeletplugin.NamespacedObject) (map[types.UID]error, error) {
	results := make(map[types.UID]error, len(claims))
	for _, claim := range claims {
		results[claim.UID] = d.unprepare(ctx, claim)
	}
	return results, nil
}

func (d *driver) unprepare(ctx context.Context, claim kubeletplugin.NamespacedObject) error {
	unlock := d.lockClaim(claim.UID)
	defer unlock()
	err := d.bridge.Unprepare(ctx, string(claim.UID))
	if err == nil && d.mig != nil {
		err = d.mig.Unprepare(string(claim.UID))
	}
	if err == nil {
		err = d.cdi.Remove(string(claim.UID))
	}
	if err == nil {
		d.mu.Lock()
		delete(d.prepared, claim.UID)
		d.mu.Unlock()
		klog.FromContext(ctx).Info("claim unprepared", "claim", claim.NamespacedName)
	}
	return err
}

func (d *driver) HandleError(ctx context.Context, err error, msg string) {
	klog.FromContext(ctx).Error(err, msg)
}
