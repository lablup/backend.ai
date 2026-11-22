/*
Copyright The Kubernetes Authors.
Modifications copyright Lablup Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

// Portions derived from the NVIDIA DRA driver for GPUs (cmd/gpu-kubelet-plugin/partitions.go
// and mig.go): the KEP-4815 counter model of a GPU and its MIG devices. See NOTICE.

package nvmig

import (
	"fmt"
	"strings"

	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/api/resource"
)

// One CounterSet per GPU: a counter per capacity dimension and one per memory slice (value 1).
// The whole GPU consumes all of them; a MIG device its profile's share and its slices.

// CounterSetName names the GPU's CounterSet.
func (g *GPU) CounterSetName() string {
	return fmt.Sprintf("gpu-%d-counter-set", g.Minor)
}

// DeviceName is the DRA device name of a placement on this GPU: gpu-<minor>-mig-<profile>-<id>-<start>.
func (g *GPU) DeviceName(p Placement) string {
	profile := rfc1123(strings.ReplaceAll(p.Profile, ".", ""))
	return fmt.Sprintf("gpu-%d-mig-%s-%d-%d", g.Minor, profile, p.ProfileID, p.Start)
}

// CounterSet is the GPU's shared counters.
func (g *GPU) CounterSet() resourceapi.CounterSet {
	return resourceapi.CounterSet{Name: g.CounterSetName(), Counters: counters(g.Max, 0, g.MemSlices)}
}

// WholeConsumption is what the whole GPU consumes: every counter.
func (g *GPU) WholeConsumption() []resourceapi.DeviceCounterConsumption {
	return []resourceapi.DeviceCounterConsumption{{CounterSet: g.CounterSetName(), Counters: counters(g.Max, 0, g.MemSlices)}}
}

// PlacementDevice is the DRA device of a placement. `attributes` are the parent GPU's.
func (g *GPU) PlacementDevice(p Placement, slotName string, attributes map[resourceapi.QualifiedName]resourceapi.DeviceAttribute) resourceapi.Device {
	attrs := make(map[resourceapi.QualifiedName]resourceapi.DeviceAttribute, len(attributes)+6)
	for k, v := range attributes {
		attrs[k] = v
	}
	attrs["slotName"] = stringAttr(slotName)
	attrs["type"] = stringAttr("mig")
	attrs["profile"] = stringAttr(p.Profile)
	attrs["parentUUID"] = stringAttr(g.UUID)
	attrs["deviceId"] = stringAttr(g.DeviceName(p))
	start := int64(p.Start)
	attrs["placementStart"] = resourceapi.DeviceAttribute{IntValue: &start}
	return resourceapi.Device{
		Name:       g.DeviceName(p),
		Attributes: attrs,
		Capacity: map[resourceapi.QualifiedName]resourceapi.DeviceCapacity{
			"memory":          intCapacity(p.Caps.Memory),
			"processingUnits": intCapacity(p.Caps.Multiprocessors),
			"copyEngines":     intCapacity(p.Caps.CopyEngines),
			"decoders":        intCapacity(p.Caps.Decoders),
			"encoders":        intCapacity(p.Caps.Encoders),
			"jpegEngines":     intCapacity(p.Caps.JpegEngines),
			"ofaEngines":      intCapacity(p.Caps.OfaEngines),
		},
		ConsumesCounters: []resourceapi.DeviceCounterConsumption{{
			CounterSet: g.CounterSetName(),
			Counters:   counters(p.Caps, p.Start, p.Size),
		}},
	}
}

func counters(c Capacities, sliceStart, sliceCount int) map[string]resourceapi.Counter {
	out := map[string]resourceapi.Counter{
		"memory":          intCounter(c.Memory),
		"multiprocessors": intCounter(c.Multiprocessors),
		"copy-engines":    intCounter(c.CopyEngines),
		"decoders":        intCounter(c.Decoders),
		"encoders":        intCounter(c.Encoders),
		"jpeg-engines":    intCounter(c.JpegEngines),
		"ofa-engines":     intCounter(c.OfaEngines),
	}
	for i := sliceStart; i < sliceStart+sliceCount; i++ {
		out[MemorySliceCounter(i)] = intCounter(1)
	}
	return out
}

// MemorySliceCounter names the counter of memory slice i.
func MemorySliceCounter(i int) string { return fmt.Sprintf("memory-slice-%d", i) }

func intCounter(v int64) resourceapi.Counter {
	return resourceapi.Counter{Value: *resource.NewQuantity(v, resource.BinarySI)}
}

func intCapacity(v int64) resourceapi.DeviceCapacity {
	return resourceapi.DeviceCapacity{Value: *resource.NewQuantity(v, resource.BinarySI)}
}

func stringAttr(s string) resourceapi.DeviceAttribute {
	return resourceapi.DeviceAttribute{StringValue: &s}
}
