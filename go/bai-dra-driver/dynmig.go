package main

// Dynamic MIG on top of the plugin host's devices: each GPU NVML can partition gets a counter
// set, its whole device consumes all of it and one exclusive device per MIG placement consumes
// a part (the NVIDIA DRA driver's DynamicMIG model, package nvmig).

import (
	"errors"
	"fmt"
	"sort"

	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/dynamic-resource-allocation/resourceslice"

	"github.com/lablup/backend.ai/go/bai-dra-driver/nvmig"
)

// counterSetsPerSlice is the API limit of counter sets in one ResourceSlice (Kubernetes 1.35).
const counterSetsPerSlice = 8

// Attributes of a shared device that do not describe its MIG devices.
var wholeOnlyAttributes = []resourceapi.QualifiedName{"memory", "processingUnits"}

// migSlotName is the Backend.AI slot of a MIG profile, as the CUDA plugins name static MIG.
func migSlotName(slotName, profile string) string {
	return fmt.Sprintf("%s.device:%s-mig", slotName, profile)
}

// dynamicGPU is the partitionable GPU of a device, or nil.
func (d *driver) dynamicGPU(info DeviceInfo) *nvmig.GPU {
	if d.mig == nil || info.UUID == "" {
		return nil
	}
	if g := d.mig.GPU(info.UUID); g != nil && g.Dynamic() {
		return g
	}
	return nil
}

// slices turns the plugin host's devices into ResourceSlices, and returns the whole-GPU device
// names of dynamic-MIG GPUs by UUID.
func (d *driver) slices(resp *DevicesResponse) ([]resourceslice.Slice, map[string]string, error) {
	infos := append([]DeviceInfo{}, resp.Devices...)
	if d.mig != nil {
		listed := map[string]bool{}
		for _, info := range infos {
			if d.dynamicGPU(info) != nil {
				listed[info.UUID] = true
				d.migParents[info.UUID] = info
			}
		}
		var missing []string
		for uuid := range d.migParents {
			if !listed[uuid] {
				missing = append(missing, uuid)
			}
		}
		sort.Strings(missing)
		for _, uuid := range missing {
			infos = append(infos, d.migParents[uuid])
		}
	}
	devices, err := toDevices(&DevicesResponse{Devices: infos})
	if err != nil {
		return nil, nil, err
	}
	whole := map[string]string{}
	var rest []resourceapi.Device
	var gpuSlices []resourceslice.Slice
	var sets []resourceapi.CounterSet
	for i, info := range infos {
		g := d.dynamicGPU(info)
		if g == nil {
			rest = append(rest, devices[i])
			continue
		}
		var slice resourceslice.Slice
		if g.WholeAllowed() {
			dev := devices[i]
			dev.ConsumesCounters = g.WholeConsumption()
			slice.Devices = append(slice.Devices, dev)
			whole[dev.Name] = g.UUID
		}
		parent := make(map[resourceapi.QualifiedName]resourceapi.DeviceAttribute, len(devices[i].Attributes))
		for k, v := range devices[i].Attributes {
			parent[k] = v
		}
		for _, k := range wholeOnlyAttributes {
			delete(parent, k)
		}
		for _, p := range g.Placements {
			slice.Devices = append(slice.Devices, g.PlacementDevice(p, migSlotName(resp.SlotName, p.Profile), parent))
		}
		if d.splitCounters {
			sets = append(sets, g.CounterSet())
		} else {
			slice.SharedCounters = []resourceapi.CounterSet{g.CounterSet()}
		}
		gpuSlices = append(gpuSlices, slice)
	}
	var out []resourceslice.Slice
	for start := 0; start < len(sets); start += counterSetsPerSlice {
		out = append(out, resourceslice.Slice{SharedCounters: sets[start:min(start+counterSetsPerSlice, len(sets))]})
	}
	if len(rest) > 0 || len(gpuSlices) == 0 {
		out = append(out, resourceslice.Slice{Devices: rest})
	}
	return append(out, gpuSlices...), whole, nil
}

// migPrepared is what prepareMig hands to the CDI spec: per MIG device its capability device
// nodes and its CDI ids (the parent GPU's toolkit device first).
type migPrepared struct {
	nodes map[string][]cdiDeviceNode
	ids   map[string][]string
}

// prepareMig takes whole GPUs out of MIG mode and creates the claim's MIG devices.
func (d *driver) prepareMig(claimUID string, names, migNames []string) (migPrepared, error) {
	out := migPrepared{nodes: map[string][]cdiDeviceNode{}, ids: map[string][]string{}}
	if d.mig == nil {
		return out, nil
	}
	if !d.published.Load() {
		return out, errors.New("dynamic MIG devices are not published yet")
	}
	d.mu.Lock()
	var uuids []string
	for _, name := range names {
		if uuid, ok := d.wholeGPUs[name]; ok {
			uuids = append(uuids, uuid)
		}
	}
	d.mu.Unlock()
	for _, uuid := range uuids {
		if err := d.mig.PrepareWhole(uuid); err != nil {
			return out, err
		}
	}
	if len(migNames) == 0 {
		return out, nil
	}
	insts, err := d.mig.Prepare(claimUID, migNames)
	if err != nil {
		return out, err
	}
	for _, inst := range insts {
		caps, err := d.mig.DeviceNodes(inst)
		if err != nil {
			return out, d.rollbackMig(claimUID, err)
		}
		nodes := make([]cdiDeviceNode, 0, len(caps))
		for _, c := range caps {
			mode := c.FileMode
			nodes = append(nodes, cdiDeviceNode{Path: c.Path, Type: "c", Major: c.Major, Minor: c.Minor, FileMode: &mode})
		}
		out.nodes[inst.Device] = nodes
		out.ids[inst.Device] = []string{nvmig.ParentCDIDevice(inst)}
	}
	return out, nil
}

// rollbackMig destroys the MIG devices of a claim whose prepare failed after creating them.
func (d *driver) rollbackMig(claimUID string, cause error) error {
	if d.mig == nil {
		return cause
	}
	return errors.Join(cause, d.mig.Unprepare(claimUID))
}
