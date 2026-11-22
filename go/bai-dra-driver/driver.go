package main

import (
	"context"
	"fmt"
	"sync"
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

	mu       sync.Mutex
	prepared map[types.UID][]kubeletplugin.Device
}

func (d *driver) publish(ctx context.Context) error {
	resp, err := d.bridge.Devices(ctx)
	if err != nil {
		return err
	}
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
				return fmt.Errorf("device %s capacity %s: %w", info.Name, k, err)
			}
			capacity := resourceapi.DeviceCapacity{Value: q}
			if p, ok := info.RequestPolicies[k]; ok {
				if capacity.RequestPolicy, err = requestPolicy(p); err != nil {
					return fmt.Errorf("device %s capacity %s policy: %w", info.Name, k, err)
				}
			}
			device.Capacity[resourceapi.QualifiedName(k)] = capacity
		}
		if info.AllowMultipleAllocations {
			device.AllowMultipleAllocations = ptr(true)
		}
		devices = append(devices, device)
	}
	klog.FromContext(ctx).Info("publishing devices", "count", len(devices), "slot", resp.SlotName)
	return d.helper.PublishResources(ctx, resourceslice.DriverResources{
		Pools: map[string]resourceslice.Pool{
			d.nodeName: {Slices: []resourceslice.Slice{{Devices: devices}}},
		},
	})
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

func attribute(v any) resourceapi.DeviceAttribute {
	switch t := v.(type) {
	case bool:
		return resourceapi.DeviceAttribute{BoolValue: &t}
	case float64: // JSON numbers
		i := int64(t)
		return resourceapi.DeviceAttribute{IntValue: &i}
	case string:
		return resourceapi.DeviceAttribute{StringValue: &t}
	default:
		s := fmt.Sprint(t)
		return resourceapi.DeviceAttribute{StringValue: &s}
	}
}

func (d *driver) PrepareResourceClaims(ctx context.Context, claims []*resourceapi.ResourceClaim) (map[types.UID]kubeletplugin.PrepareResult, error) {
	results := make(map[types.UID]kubeletplugin.PrepareResult, len(claims))
	for _, claim := range claims {
		results[claim.UID] = d.prepare(ctx, claim)
	}
	return results, nil
}

func (d *driver) prepare(ctx context.Context, claim *resourceapi.ResourceClaim) kubeletplugin.PrepareResult {
	d.mu.Lock()
	defer d.mu.Unlock()
	if devices, ok := d.prepared[claim.UID]; ok {
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
				consumed[r.Device][string(k)] = q.String()
			}
		}
	}
	start := time.Now()
	edits, err := d.bridge.Prepare(ctx, string(claim.UID), names, consumed)
	if err != nil {
		return kubeletplugin.PrepareResult{Err: err}
	}
	// Devices of other CDI specs (e.g. nvidia.com/gpu) go to the runtime as they are.
	cdiIDs := append([]string{}, edits.CDIDevices...)
	if !edits.Empty() {
		cdiID, err := d.cdi.Write(string(claim.UID), edits)
		if err != nil {
			return kubeletplugin.PrepareResult{Err: err}
		}
		cdiIDs = append(cdiIDs, cdiID)
	}
	devices := make([]kubeletplugin.Device, 0, len(ours))
	for _, r := range ours {
		devices = append(devices, kubeletplugin.Device{
			Requests:     []string{r.Request},
			PoolName:     r.Pool,
			DeviceName:   r.Device,
			CDIDeviceIDs: cdiIDs,
		})
	}
	d.prepared[claim.UID] = devices
	klog.FromContext(ctx).Info("claim prepared", "claim", klog.KObj(claim), "devices", names, "elapsed", time.Since(start))
	return kubeletplugin.PrepareResult{Devices: devices}
}

func (d *driver) UnprepareResourceClaims(ctx context.Context, claims []kubeletplugin.NamespacedObject) (map[types.UID]error, error) {
	results := make(map[types.UID]error, len(claims))
	d.mu.Lock()
	defer d.mu.Unlock()
	for _, claim := range claims {
		err := d.bridge.Unprepare(ctx, string(claim.UID))
		if err == nil {
			err = d.cdi.Remove(string(claim.UID))
		}
		if err == nil {
			delete(d.prepared, claim.UID)
			klog.FromContext(ctx).Info("claim unprepared", "claim", claim.NamespacedName)
		}
		results[claim.UID] = err
	}
	return results, nil
}

func (d *driver) HandleError(ctx context.Context, err error, msg string) {
	klog.FromContext(ctx).Error(err, msg)
}
