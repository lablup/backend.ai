package main

// The bridge API to the Python plugin host. Mirrors src/ai/backend/dra/bridge.py; change both together.

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"time"
)

// bridgeTimeout bounds one plugin host call. It stays below the kubelet's deadline for
// NodePrepareResources (45 s) so that a stuck host fails the claim instead of the kubelet call.
const bridgeTimeout = 30 * time.Second

type CapacityPolicy struct {
	Default string `json:"default"`
	Min     string `json:"min"`
	Max     string `json:"max"`
	Step    string `json:"step"`
}

type DeviceInfo struct {
	Name string `json:"name"`
	// Decoded with UseNumber: whole numbers stay ints, anything else becomes a string.
	Attributes               map[string]any            `json:"attributes"`
	Capacity                 map[string]string         `json:"capacity"`
	AllowMultipleAllocations bool                      `json:"allow_multiple_allocations"`
	RequestPolicies          map[string]CapacityPolicy `json:"request_policies"`
	// The NVML UUID of a GPU (GPU-...); dynamic MIG attaches the GPU's MIG devices by it.
	UUID string `json:"uuid,omitempty"`
}

type DevicesResponse struct {
	SlotName   string       `json:"slot_name"`
	HostID     string       `json:"host_id"`
	Generation int64        `json:"generation"`
	Devices    []DeviceInfo `json:"devices"`
}

type DeviceNode struct {
	Path        string  `json:"path"`
	HostPath    *string `json:"host_path"`
	Permissions *string `json:"permissions"`
}

type Mount struct {
	HostPath      string   `json:"host_path"`
	ContainerPath string   `json:"container_path"`
	Options       []string `json:"options"`
}

type ContainerEdits struct {
	Env         []string     `json:"env"`
	DeviceNodes []DeviceNode `json:"device_nodes"`
	Mounts      []Mount      `json:"mounts"`
	CDIDevices  []string     `json:"cdi_devices"`
}

type PrepareResponse struct {
	Edits ContainerEdits `json:"edits"`
	// Device name → CDI devices of other specs (e.g. nvidia.com/gpu=...) for that device alone.
	DeviceCDIDevices map[string][]string `json:"device_cdi_devices"`
}

// Empty reports whether the edits need no spec of our own.
func (e *ContainerEdits) Empty() bool {
	return len(e.Env) == 0 && len(e.DeviceNodes) == 0 && len(e.Mounts) == 0
}

type bridge struct {
	client  *http.Client
	timeout time.Duration
}

func newBridge(socket string) *bridge {
	transport := &http.Transport{
		DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
			var d net.Dialer
			return d.DialContext(ctx, "unix", socket)
		},
	}
	return &bridge{client: &http.Client{Transport: transport}, timeout: bridgeTimeout}
}

func (b *bridge) call(ctx context.Context, method, path string, in, out any) error {
	ctx, cancel := context.WithTimeout(ctx, b.timeout)
	defer cancel()
	var body bytes.Buffer
	if in != nil {
		if err := json.NewEncoder(&body).Encode(in); err != nil {
			return err
		}
	}
	req, err := http.NewRequestWithContext(ctx, method, "http://bridge/v1/"+path, &body)
	if err != nil {
		return err
	}
	resp, err := b.client.Do(req)
	if err != nil {
		return fmt.Errorf("plugin host %s: %w", path, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		var e struct {
			Error string `json:"error"`
		}
		_ = json.NewDecoder(resp.Body).Decode(&e)
		return fmt.Errorf("plugin host %s: %s: %s", path, resp.Status, e.Error)
	}
	if out == nil {
		return nil
	}
	dec := json.NewDecoder(resp.Body)
	dec.UseNumber()
	return dec.Decode(out)
}

func (b *bridge) Health(ctx context.Context) error {
	return b.call(ctx, http.MethodGet, "health", nil, nil)
}

func (b *bridge) Devices(ctx context.Context) (*DevicesResponse, error) {
	var out DevicesResponse
	return &out, b.call(ctx, http.MethodGet, "devices", nil, &out)
}

func (b *bridge) Prepare(ctx context.Context, claimUID string, devices []string, consumed map[string]map[string]string) (*PrepareResponse, error) {
	var out PrepareResponse
	in := map[string]any{"claim_uid": claimUID, "devices": devices, "consumed": consumed}
	return &out, b.call(ctx, http.MethodPost, "prepare", in, &out)
}

func (b *bridge) Unprepare(ctx context.Context, claimUID string) error {
	return b.call(ctx, http.MethodPost, "unprepare", map[string]any{"claim_uid": claimUID}, nil)
}
