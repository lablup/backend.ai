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

// Portions derived from the NVIDIA DRA driver for GPUs (cmd/gpu-kubelet-plugin/nvlib.go:
// createMigDevice, selectCIProfile, deleteMigDevice, maybeDisableMigMode; device_state.go and
// cleanup.go: DestroyUnknownMIGDevices, unprepare of partially prepared claims). See NOTICE.

// Package nvmig creates NVIDIA MIG devices on demand for bai-dra (dynamic MIG). It is used
// only by driver entries with dynamic MIG on; the rest of the driver stays vendor-neutral.
package nvmig

import (
	"errors"
	"fmt"
	"sort"
	"sync"

	"github.com/NVIDIA/go-nvml/pkg/nvml"
	"k8s.io/klog/v2"
)

// ParentCDIKind names the NVIDIA toolkit's CDI devices; a MIG device adds its parent GPU's.
const ParentCDIKind = "nvidia.com/gpu"

type placementRef struct {
	gpu *GPU
	p   Placement
}

type liveInstance struct {
	profileID int
	start     int
	giID      int
	gi        nvml.GpuInstance
}

// Manager owns the MIG layout of the node's GPUs. All NVML calls run under one lock.
type Manager struct {
	lib      nvml.Interface
	procRoot string
	store    checkpointStore

	mu         sync.Mutex
	cp         *checkpoint
	gpus       map[string]*GPU
	placements map[string]placementRef
}

// NewManager inspects every GPU of an initialized NVML library and loads the checkpoint.
func NewManager(lib nvml.Interface, checkpointPath, procRoot string) (*Manager, error) {
	m := &Manager{
		lib:        lib,
		procRoot:   procRoot,
		store:      checkpointStore{path: checkpointPath},
		gpus:       map[string]*GPU{},
		placements: map[string]placementRef{},
	}
	cp, err := m.store.load()
	if err != nil {
		return nil, err
	}
	m.cp = cp
	count, ret := lib.DeviceGetCount()
	if ret != nvml.SUCCESS {
		return nil, fmt.Errorf("count GPUs: %w", ret)
	}
	for i := 0; i < count; i++ {
		dev, ret := lib.DeviceGetHandleByIndex(i)
		if ret != nvml.SUCCESS {
			return nil, fmt.Errorf("get GPU %d: %w", i, ret)
		}
		gpu, err := Inspect(dev)
		if err != nil {
			return nil, err
		}
		m.gpus[gpu.UUID] = gpu
		for _, p := range gpu.Placements {
			m.placements[gpu.DeviceName(p)] = placementRef{gpu: gpu, p: p}
		}
		klog.V(1).Info("GPU inspected for dynamic MIG", "uuid", gpu.UUID, "minor", gpu.Minor, "placements", len(gpu.Placements), "toggle", gpu.Toggle)
	}
	return m, nil
}

// GPU is the inspected GPU of a UUID, or nil when NVML does not list it.
func (m *Manager) GPU(uuid string) *GPU {
	return m.gpus[uuid]
}

// IsPartition reports whether a device name is a MIG placement of this node.
func (m *Manager) IsPartition(name string) bool {
	_, ok := m.placements[name]
	return ok
}

// ParentCDIDevice is the toolkit's CDI device of an instance's parent GPU (by UUID, as the
// CUDA plugin names whole GPUs).
func ParentCDIDevice(inst Instance) string {
	return ParentCDIKind + "=" + inst.ParentUUID
}

// DeviceNodes are the capability devices a container needs for the instance.
func (m *Manager) DeviceNodes(inst Instance) ([]CapNode, error) {
	return capNodes(m.procRoot, inst)
}

// Prepare creates the MIG devices of a claim, or returns those a prepared claim already holds.
func (m *Manager) Prepare(claimUID string, names []string) ([]Instance, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if rec, ok := m.cp.Claims[claimUID]; ok {
		if rec.State == stateCompleted {
			return rec.Instances, nil
		}
		if err := m.destroyClaim(rec); err != nil {
			return nil, err
		}
	}
	rec := &claimRecord{State: stateStarted, Devices: append([]string{}, names...)}
	m.cp.Claims[claimUID] = rec
	if err := m.store.save(m.cp); err != nil {
		delete(m.cp.Claims, claimUID)
		return nil, err
	}
	for _, name := range names {
		inst, err := m.create(name)
		if err == nil {
			rec.Instances = append(rec.Instances, inst)
			err = m.store.save(m.cp)
		}
		if err != nil {
			if cleanup := m.destroyClaim(rec); cleanup != nil {
				// The record stays "started": the next start destroys what is left.
				return nil, errors.Join(err, cleanup)
			}
			delete(m.cp.Claims, claimUID)
			return nil, errors.Join(err, m.store.save(m.cp))
		}
	}
	rec.State = stateCompleted
	if err := m.store.save(m.cp); err != nil {
		return nil, err
	}
	return rec.Instances, nil
}

// Unprepare destroys the MIG devices of a claim. Unknown claims are a no-op.
func (m *Manager) Unprepare(claimUID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	rec, ok := m.cp.Claims[claimUID]
	if !ok {
		return nil
	}
	if err := m.destroyClaim(rec); err != nil {
		return err
	}
	delete(m.cp.Claims, claimUID)
	return m.store.save(m.cp)
}

// PrepareWhole makes a GPU usable as a whole (or by shares): it leaves MIG mode when no MIG
// device is left. A GPU with MIG devices, or one that cannot leave MIG mode, fails.
func (m *Manager) PrepareWhole(uuid string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	gpu := m.gpus[uuid]
	if gpu == nil || !gpu.Dynamic() {
		return nil
	}
	dev, ret := m.lib.DeviceGetHandleByUUID(uuid)
	if ret != nvml.SUCCESS {
		return fmt.Errorf("get GPU %s: %w", uuid, ret)
	}
	enabled, err := migEnabled(dev)
	if err != nil || !enabled {
		return err
	}
	live, err := m.live(gpu, dev)
	if err != nil {
		return err
	}
	if len(live) > 0 {
		return fmt.Errorf("GPU %s holds %d MIG devices: a whole or shared allocation cannot use it", uuid, len(live))
	}
	if !gpu.Toggle {
		return fmt.Errorf("GPU %s is in MIG mode and cannot leave it without a GPU reset", uuid)
	}
	if ret, activation := dev.SetMigMode(nvml.DEVICE_MIG_DISABLE); ret != nvml.SUCCESS {
		return fmt.Errorf("disable MIG mode of GPU %s: %w (activation: %v)", uuid, ret, activation)
	}
	klog.V(1).Info("MIG mode disabled for a whole allocation", "uuid", uuid)
	return nil
}

// Reconcile runs at start: it destroys the devices of claims whose prepare did not finish and
// every MIG device on a dynamic-MIG GPU that no prepared claim holds.
func (m *Manager) Reconcile() error {
	m.mu.Lock()
	defer m.mu.Unlock()
	var errs []error
	for uid, rec := range m.cp.Claims {
		if rec.State == stateCompleted {
			continue
		}
		if err := m.destroyClaim(rec); err != nil {
			errs = append(errs, fmt.Errorf("claim %s: %w", uid, err))
			continue
		}
		delete(m.cp.Claims, uid)
	}
	held := map[string]bool{}
	for _, rec := range m.cp.Claims {
		for _, inst := range rec.Instances {
			held[instanceKey(inst.ParentUUID, inst.ProfileID, inst.Start)] = true
		}
	}
	for _, uuid := range m.sortedGPUs() {
		gpu := m.gpus[uuid]
		dev, ret := m.lib.DeviceGetHandleByUUID(uuid)
		if ret != nvml.SUCCESS {
			errs = append(errs, fmt.Errorf("get GPU %s: %w", uuid, ret))
			continue
		}
		live, err := m.live(gpu, dev)
		if err != nil {
			errs = append(errs, err)
			continue
		}
		for _, l := range live {
			if held[instanceKey(uuid, l.profileID, l.start)] {
				continue
			}
			klog.Info("destroying a MIG device no prepared claim holds", "uuid", uuid, "profileID", l.profileID, "start", l.start)
			if err := destroyGI(l.gi); err != nil {
				errs = append(errs, fmt.Errorf("GPU %s: %w", uuid, err))
			}
		}
		if err := m.maybeDisableMigMode(gpu, dev); err != nil {
			errs = append(errs, err)
		}
	}
	errs = append(errs, m.store.save(m.cp))
	return errors.Join(errs...)
}

func (m *Manager) sortedGPUs() []string {
	var uuids []string
	for uuid, gpu := range m.gpus {
		if gpu.Dynamic() {
			uuids = append(uuids, uuid)
		}
	}
	sort.Strings(uuids)
	return uuids
}

func instanceKey(uuid string, profileID, start int) string {
	return fmt.Sprintf("%s/%d/%d", uuid, profileID, start)
}

// create makes one MIG device: MIG mode on, GPU instance at the placement, one compute
// instance over all its slices.
func (m *Manager) create(name string) (Instance, error) {
	ref, ok := m.placements[name]
	if !ok {
		return Instance{}, fmt.Errorf("device %s is not a MIG placement of this node", name)
	}
	gpu, p := ref.gpu, ref.p
	dev, ret := m.lib.DeviceGetHandleByUUID(gpu.UUID)
	if ret != nvml.SUCCESS {
		return Instance{}, fmt.Errorf("get GPU %s: %w", gpu.UUID, ret)
	}
	enabled, err := migEnabled(dev)
	if err != nil {
		return Instance{}, err
	}
	if !enabled {
		if !gpu.Toggle {
			return Instance{}, fmt.Errorf("GPU %s cannot enter MIG mode without a GPU reset", gpu.UUID)
		}
		if ret, activation := dev.SetMigMode(nvml.DEVICE_MIG_ENABLE); ret != nvml.SUCCESS {
			return Instance{}, fmt.Errorf("enable MIG mode of GPU %s: %w (activation: %v)", gpu.UUID, ret, activation)
		}
		klog.V(1).Info("MIG mode enabled", "uuid", gpu.UUID)
	}
	info, ret := dev.GetGpuInstanceProfileInfo(p.ProfileID)
	if ret != nvml.SUCCESS {
		return Instance{}, fmt.Errorf("get MIG profile %s of GPU %s: %w", p.Profile, gpu.UUID, ret)
	}
	// NVML reports an occupied placement as INSUFFICIENT_RESOURCES, not ALREADY_EXISTS.
	gi, ret := dev.CreateGpuInstanceWithPlacement(&info, &nvml.GpuInstancePlacement{Start: uint32(p.Start), Size: uint32(p.Size)})
	if ret != nvml.SUCCESS {
		return Instance{}, fmt.Errorf("create GPU instance %s: %w", name, ret)
	}
	giInfo, ret := gi.GetInfo()
	if ret != nvml.SUCCESS {
		return Instance{}, errors.Join(fmt.Errorf("get GPU instance %s: %w", name, ret), destroyGI(gi))
	}
	ciProfile, err := selectCIProfile(gi, info.SliceCount)
	if err != nil {
		return Instance{}, errors.Join(fmt.Errorf("%s: %w", name, err), destroyGI(gi))
	}
	ci, ret := gi.CreateComputeInstance(&ciProfile)
	if ret != nvml.SUCCESS {
		return Instance{}, errors.Join(fmt.Errorf("create compute instance %s: %w", name, ret), destroyGI(gi))
	}
	ciInfo, ret := ci.GetInfo()
	if ret != nvml.SUCCESS {
		return Instance{}, errors.Join(fmt.Errorf("get compute instance %s: %w", name, ret), destroyGI(gi))
	}
	klog.V(1).Info("MIG device created", "device", name, "uuid", gpu.UUID, "gi", giInfo.Id, "ci", ciInfo.Id)
	return Instance{
		Device: name, ParentUUID: gpu.UUID, ParentMinor: gpu.Minor,
		ProfileID: p.ProfileID, Start: p.Start, GIID: int(giInfo.Id), CIID: int(ciInfo.Id),
	}, nil
}

// destroyClaim destroys a claim's recorded devices and, for a claim whose prepare did not
// finish, the live devices at its placements; then leaves MIG mode where nothing is left.
func (m *Manager) destroyClaim(rec *claimRecord) error {
	targets := map[string]map[string]bool{} // GPU UUID → instance keys
	add := func(uuid string, profileID, start int) {
		if targets[uuid] == nil {
			targets[uuid] = map[string]bool{}
		}
		targets[uuid][instanceKey(uuid, profileID, start)] = true
	}
	for _, inst := range rec.Instances {
		add(inst.ParentUUID, inst.ProfileID, inst.Start)
	}
	if rec.State != stateCompleted {
		for _, name := range rec.Devices {
			if ref, ok := m.placements[name]; ok {
				add(ref.gpu.UUID, ref.p.ProfileID, ref.p.Start)
			}
		}
	}
	var errs []error
	for _, uuid := range m.sortedGPUs() {
		keys := targets[uuid]
		if keys == nil {
			continue
		}
		gpu := m.gpus[uuid]
		dev, ret := m.lib.DeviceGetHandleByUUID(uuid)
		if ret != nvml.SUCCESS {
			errs = append(errs, fmt.Errorf("get GPU %s: %w", uuid, ret))
			continue
		}
		live, err := m.live(gpu, dev)
		if err != nil {
			errs = append(errs, err)
			continue
		}
		for _, l := range live {
			// Can fail with "in use by another client" while a process still runs on it.
			if keys[instanceKey(uuid, l.profileID, l.start)] {
				if err := destroyGI(l.gi); err != nil {
					errs = append(errs, fmt.Errorf("GPU %s: %w", uuid, err))
				}
			}
		}
		// Leaving MIG mode is best effort: a whole allocation does it again (PrepareWhole).
		if err := m.maybeDisableMigMode(gpu, dev); err != nil {
			klog.ErrorS(err, "MIG mode stays on", "uuid", uuid)
		}
	}
	return errors.Join(errs...)
}

// live lists the GPU instances of a GPU, by the profiles it can place.
func (m *Manager) live(gpu *GPU, dev nvml.Device) ([]liveInstance, error) {
	enabled, err := migEnabled(dev)
	if err != nil || !enabled {
		return nil, err
	}
	seen := map[int]bool{}
	var out []liveInstance
	for _, p := range gpu.Placements {
		if seen[p.ProfileID] {
			continue
		}
		seen[p.ProfileID] = true
		info, ret := dev.GetGpuInstanceProfileInfo(p.ProfileID)
		if ret != nvml.SUCCESS {
			return nil, fmt.Errorf("get MIG profile %s of GPU %s: %w", p.Profile, gpu.UUID, ret)
		}
		gis, ret := dev.GetGpuInstances(&info)
		if ret == nvml.ERROR_NOT_FOUND {
			continue
		}
		if ret != nvml.SUCCESS {
			return nil, fmt.Errorf("list GPU instances %s of GPU %s: %w", p.Profile, gpu.UUID, ret)
		}
		for _, gi := range gis {
			giInfo, ret := gi.GetInfo()
			if ret != nvml.SUCCESS {
				return nil, fmt.Errorf("get GPU instance of GPU %s: %w", gpu.UUID, ret)
			}
			out = append(out, liveInstance{profileID: p.ProfileID, start: int(giInfo.Placement.Start), giID: int(giInfo.Id), gi: gi})
		}
	}
	return out, nil
}

// maybeDisableMigMode leaves MIG mode when no MIG device is left (Hopper and later only).
func (m *Manager) maybeDisableMigMode(gpu *GPU, dev nvml.Device) error {
	if !gpu.Toggle {
		return nil
	}
	live, err := m.live(gpu, dev)
	if err != nil || len(live) > 0 {
		return err
	}
	enabled, err := migEnabled(dev)
	if err != nil || !enabled {
		return err
	}
	if ret, activation := dev.SetMigMode(nvml.DEVICE_MIG_DISABLE); ret != nvml.SUCCESS {
		return fmt.Errorf("disable MIG mode of GPU %s: %w (activation: %v)", gpu.UUID, ret, activation)
	}
	klog.V(1).Info("MIG mode disabled", "uuid", gpu.UUID)
	return nil
}

func migEnabled(dev nvml.Device) (bool, error) {
	current, _, ret := dev.GetMigMode()
	if ret == nvml.ERROR_NOT_SUPPORTED {
		return false, nil
	}
	if ret != nvml.SUCCESS {
		return false, fmt.Errorf("get MIG mode: %w", ret)
	}
	return current == nvml.DEVICE_MIG_ENABLE, nil
}

// selectCIProfile picks the compute instance profile spanning the GPU instance; of several
// (e.g. a `rev1` variant), the one with the most multiprocessors.
func selectCIProfile(gi nvml.GpuInstance, slices uint32) (nvml.ComputeInstanceProfileInfo, error) {
	var best *nvml.ComputeInstanceProfileInfo
	for id := 0; id < nvml.COMPUTE_INSTANCE_PROFILE_COUNT; id++ {
		info, ret := gi.GetComputeInstanceProfileInfo(id, nvml.COMPUTE_INSTANCE_ENGINE_PROFILE_SHARED)
		if ret != nvml.SUCCESS || info.SliceCount != slices {
			continue
		}
		if best == nil || info.MultiprocessorCount > best.MultiprocessorCount {
			best = &info
		}
	}
	if best == nil {
		return nvml.ComputeInstanceProfileInfo{}, fmt.Errorf("no compute instance profile of %d slices", slices)
	}
	return *best, nil
}

// destroyGI destroys a GPU instance with its compute instances (children first).
func destroyGI(gi nvml.GpuInstance) error {
	for id := 0; id < nvml.COMPUTE_INSTANCE_PROFILE_COUNT; id++ {
		info, ret := gi.GetComputeInstanceProfileInfo(id, nvml.COMPUTE_INSTANCE_ENGINE_PROFILE_SHARED)
		if ret != nvml.SUCCESS {
			continue
		}
		cis, ret := gi.GetComputeInstances(&info)
		if ret != nvml.SUCCESS {
			continue
		}
		for _, ci := range cis {
			if ret := ci.Destroy(); ret != nvml.SUCCESS && ret != nvml.ERROR_NOT_FOUND {
				return fmt.Errorf("destroy compute instance: %w", ret)
			}
		}
	}
	if ret := gi.Destroy(); ret != nvml.SUCCESS && ret != nvml.ERROR_NOT_FOUND {
		return fmt.Errorf("destroy GPU instance: %w", ret)
	}
	return nil
}
