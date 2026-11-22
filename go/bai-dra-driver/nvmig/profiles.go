/*
Copyright The Kubernetes Authors.
Copyright (c) NVIDIA CORPORATION. All rights reserved.
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

// Portions derived from the NVIDIA DRA driver for GPUs (cmd/gpu-kubelet-plugin/nvlib.go:
// inspectMigProfilesAndPlacements, supportsMIGModeToggle, isDynamicMIGCapable) and go-nvlib
// (pkg/nvlib/device/mig_profile.go: profile names). See NOTICE.

package nvmig

import (
	"fmt"
	"math"
	"sort"
	"strings"

	"github.com/NVIDIA/go-nvml/pkg/nvml"
)

// Capacities of one MIG profile, or the per-dimension maxima over all profiles of a GPU.
type Capacities struct {
	Memory          int64 // bytes
	Multiprocessors int64
	CopyEngines     int64
	Decoders        int64
	Encoders        int64
	JpegEngines     int64
	OfaEngines      int64
}

func profileCapacities(p *nvml.GpuInstanceProfileInfo) Capacities {
	return Capacities{
		// NVML documents MemorySizeMB in MiB (nvml.h).
		Memory:          int64(p.MemorySizeMB) * 1024 * 1024,
		Multiprocessors: int64(p.MultiprocessorCount),
		CopyEngines:     int64(p.CopyEngineCount),
		Decoders:        int64(p.DecoderCount),
		Encoders:        int64(p.EncoderCount),
		JpegEngines:     int64(p.JpegCount),
		OfaEngines:      int64(p.OfaCount),
	}
}

func (c Capacities) max(o Capacities) Capacities {
	return Capacities{
		Memory:          max(c.Memory, o.Memory),
		Multiprocessors: max(c.Multiprocessors, o.Multiprocessors),
		CopyEngines:     max(c.CopyEngines, o.CopyEngines),
		Decoders:        max(c.Decoders, o.Decoders),
		Encoders:        max(c.Encoders, o.Encoders),
		JpegEngines:     max(c.JpegEngines, o.JpegEngines),
		OfaEngines:      max(c.OfaEngines, o.OfaEngines),
	}
}

// Placement is one MIG device a GPU can hold: a GPU instance profile at a memory slice range.
type Placement struct {
	ProfileID  int    // GPU instance profile ID (nvmlDeviceCreateGpuInstanceWithPlacement)
	Profile    string // e.g. 1g.10gb, as nvidia-smi names it
	Start      int    // first memory slice
	Size       int    // memory slices
	SliceCount int    // compute slices
	Caps       Capacities
}

// GPU is what dynamic MIG knows of one physical GPU, read once from NVML.
type GPU struct {
	UUID  string
	Minor int
	// Toggle: MIG mode changes without a GPU reset (Hopper and later).
	Toggle bool
	// MigEnabledAtStart: on a GPU without Toggle this decides whether it serves MIG or whole.
	MigEnabledAtStart bool
	Placements        []Placement
	Max               Capacities
	MemSlices         int
}

// Dynamic reports whether the GPU's MIG devices can be created on demand.
func (g *GPU) Dynamic() bool { return len(g.Placements) > 0 }

// WholeAllowed reports whether the whole GPU may be allocated: an Ampere GPU in MIG mode cannot
// leave it without a reset, so it serves MIG devices only.
func (g *GPU) WholeAllowed() bool { return g.Toggle || !g.MigEnabledAtStart }

// Inspect reads the MIG profiles and placements of a GPU. A GPU that cannot change its MIG
// layout on demand comes back without placements.
func Inspect(dev nvml.Device) (*GPU, error) {
	uuid, ret := dev.GetUUID()
	if ret != nvml.SUCCESS {
		return nil, fmt.Errorf("get UUID: %w", ret)
	}
	minor, ret := dev.GetMinorNumber()
	if ret != nvml.SUCCESS {
		return nil, fmt.Errorf("get minor number of %s: %w", uuid, ret)
	}
	gpu := &GPU{UUID: uuid, Minor: minor, Toggle: supportsMIGModeToggle(dev)}
	current, _, ret := dev.GetMigMode()
	if ret == nvml.ERROR_NOT_SUPPORTED {
		return gpu, nil
	}
	if ret != nvml.SUCCESS {
		return nil, fmt.Errorf("get MIG mode of %s: %w", uuid, ret)
	}
	gpu.MigEnabledAtStart = current == nvml.DEVICE_MIG_ENABLE
	mode, ret := dev.GetVirtualizationMode()
	if ret != nvml.SUCCESS {
		return nil, fmt.Errorf("get virtualization mode of %s: %w", uuid, ret)
	}
	// A vGPU guest has its partition fixed by the vGPU profile; an Ampere GPU needs a reset to
	// enter MIG mode.
	if mode == nvml.GPU_VIRTUALIZATION_MODE_VGPU || (!gpu.Toggle && !gpu.MigEnabledAtStart) {
		return gpu, nil
	}
	memory, ret := dev.GetMemoryInfo()
	if ret != nvml.SUCCESS {
		return nil, fmt.Errorf("get memory of %s: %w", uuid, ret)
	}
	for id := 0; id < nvml.GPU_INSTANCE_PROFILE_COUNT; id++ {
		info, ret := dev.GetGpuInstanceProfileInfo(id)
		if ret == nvml.ERROR_NOT_SUPPORTED || ret == nvml.ERROR_INVALID_ARGUMENT {
			continue
		}
		if ret != nvml.SUCCESS {
			return nil, fmt.Errorf("get GPU instance profile %d of %s: %w", id, uuid, ret)
		}
		placements, ret := dev.GetGpuInstancePossiblePlacements(&info)
		if ret == nvml.ERROR_NOT_SUPPORTED || ret == nvml.ERROR_INVALID_ARGUMENT {
			continue
		}
		if ret != nvml.SUCCESS {
			return nil, fmt.Errorf("get placements of GPU instance profile %d of %s: %w", id, uuid, ret)
		}
		caps := profileCapacities(&info)
		name := profileName(id, int(info.SliceCount), memory.Total, info.MemorySizeMB)
		for _, p := range placements {
			gpu.Placements = append(gpu.Placements, Placement{
				ProfileID: id, Profile: name, Start: int(p.Start), Size: int(p.Size),
				SliceCount: int(info.SliceCount), Caps: caps,
			})
			// The largest profile spans every memory slice.
			gpu.MemSlices = max(gpu.MemSlices, int(p.Start+p.Size))
			gpu.Max = gpu.Max.max(caps)
		}
	}
	sort.Slice(gpu.Placements, func(i, j int) bool {
		a, b := gpu.Placements[i], gpu.Placements[j]
		if a.Profile != b.Profile {
			return a.Profile < b.Profile
		}
		if a.ProfileID != b.ProfileID {
			return a.ProfileID < b.ProfileID
		}
		return a.Start < b.Start
	})
	return gpu, nil
}

// supportsMIGModeToggle: Hopper and later change MIG mode without a GPU reset; Ampere does not.
func supportsMIGModeToggle(dev nvml.Device) bool {
	arch, ret := dev.GetArchitecture()
	if ret != nvml.SUCCESS {
		return false
	}
	return arch >= nvml.DEVICE_ARCH_HOPPER && arch != nvml.DEVICE_ARCH_UNKNOWN
}

// profileName follows nvidia-smi (go-nvlib MigProfileInfo.String for C == G): `1g.10gb+me`.
func profileName(profileID, slices int, deviceMemory, migMemoryMB uint64) string {
	var suffix string
	switch profileID {
	case nvml.GPU_INSTANCE_PROFILE_1_SLICE_REV1, nvml.GPU_INSTANCE_PROFILE_2_SLICE_REV1:
		suffix = "+me"
	case nvml.GPU_INSTANCE_PROFILE_1_SLICE_ALL_ME, nvml.GPU_INSTANCE_PROFILE_2_SLICE_ALL_ME:
		suffix = "+me.all"
	case nvml.GPU_INSTANCE_PROFILE_1_SLICE_GFX, nvml.GPU_INSTANCE_PROFILE_2_SLICE_GFX,
		nvml.GPU_INSTANCE_PROFILE_3_SLICE_GFX, nvml.GPU_INSTANCE_PROFILE_4_SLICE_GFX:
		suffix = "+gfx"
	case nvml.GPU_INSTANCE_PROFILE_1_SLICE_NO_ME, nvml.GPU_INSTANCE_PROFILE_2_SLICE_NO_ME:
		suffix = "-me"
	}
	return fmt.Sprintf("%dg.%dgb%s", slices, migMemoryGB(deviceMemory, migMemoryMB), suffix)
}

// migMemoryGB rounds a profile's memory to the GB figure nvidia-smi prints (go-nvlib).
func migMemoryGB(totalDeviceMemory, migMemorySizeMB uint64) uint64 {
	const fracDenominator = 8
	const oneMB = 1024 * 1024
	const oneGB = 1024 * 1024 * 1024
	if totalDeviceMemory == 0 {
		return 0
	}
	fractional := (float64(migMemorySizeMB) * oneMB) / float64(totalDeviceMemory)
	fractional = math.Ceil(fractional*fracDenominator) / fracDenominator
	totalGB := float64((totalDeviceMemory + oneGB - 1) / oneGB)
	return uint64(math.Round(fractional * totalGB))
}

// rfc1123 lowers a name and replaces what a DNS label does not allow with hyphens.
func rfc1123(name string) string {
	var b strings.Builder
	for _, r := range strings.ToLower(name) {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' {
			b.WriteRune(r)
		} else {
			b.WriteRune('-')
		}
	}
	return strings.Trim(b.String(), "-")
}
