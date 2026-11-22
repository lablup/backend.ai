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
)

// driver turns the plugin host's devices into a ResourceSlice and its prepare answers into CDI.
type driver struct {
	name     string
	nodeName string
	bridge   *bridge
	cdi      *cdiWriter
	helper   *kubeletplugin.Helper

	// mu guards prepared and claimLocks only; bridge calls run under the claim's own lock.
	mu         sync.Mutex
	prepared   map[types.UID][]kubeletplugin.Device
	claimLocks map[types.UID]*claimLock

	// What was last published: the plugin host instance and its device generation.
	publishedHost       string
	publishedGeneration int64
	published           atomic.Bool
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
	d.publishedHost, d.publishedGeneration = resp.HostID, resp.Generation
	d.published.Store(true)
	return nil
}

func (d *driver) publish(ctx context.Context, resp *DevicesResponse) error {
	devices, err := toDevices(resp)
	if err != nil {
		return err
	}
	klog.FromContext(ctx).Info("publishing devices", "count", len(devices), "slot", resp.SlotName, "generation", resp.Generation)
	return d.helper.PublishResources(ctx, resourceslice.DriverResources{
		Pools: map[string]resourceslice.Pool{
			d.nodeName: {Slices: []resourceslice.Slice{{Devices: devices}}},
		},
	})
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
	var names []string
	var ours []resourceapi.DeviceRequestAllocationResult
	consumed := map[string]map[string]string{}
	for _, r := range claim.Status.Allocation.Devices.Results {
		if r.Driver != d.name {
			continue
		}
		names = append(names, r.Device)
		ours = append(ours, r)
		if len(r.ConsumedCapacity) > 0 {
			consumed[r.Device] = map[string]string{}
			for k, q := range r.ConsumedCapacity {
				consumed[r.Device][string(k)] = quantityString(q)
			}
		}
	}
	start := time.Now()
	resp, err := d.bridge.Prepare(ctx, string(claim.UID), names, consumed)
	if err != nil {
		return kubeletplugin.PrepareResult{Err: err}
	}
	// The claim's own spec and the CDI devices no single device owns go to the first device.
	claimIDs := append([]string{}, resp.Edits.CDIDevices...)
	if !resp.Edits.Empty() {
		cdiID, err := d.cdi.Write(string(claim.UID), &resp.Edits)
		if err != nil {
			return kubeletplugin.PrepareResult{Err: err}
		}
		claimIDs = append(claimIDs, cdiID)
	}
	devices = make([]kubeletplugin.Device, 0, len(ours))
	for i, r := range ours {
		ids := append([]string{}, resp.DeviceCDIDevices[r.Device]...)
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
