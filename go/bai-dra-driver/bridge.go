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

type CapacityPolicy struct {
	Default string `json:"default"`
	Min     string `json:"min"`
	Max     string `json:"max"`
	Step    string `json:"step"`
}

type DeviceInfo struct {
	Name                     string                    `json:"name"`
	Attributes               map[string]any            `json:"attributes"`
	Capacity                 map[string]string         `json:"capacity"`
	AllowMultipleAllocations bool                      `json:"allow_multiple_allocations"`
	RequestPolicies          map[string]CapacityPolicy `json:"request_policies"`
}

type DevicesResponse struct {
	SlotName string       `json:"slot_name"`
	Devices  []DeviceInfo `json:"devices"`
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

// Empty reports whether the edits need no spec of our own.
func (e *ContainerEdits) Empty() bool {
	return len(e.Env) == 0 && len(e.DeviceNodes) == 0 && len(e.Mounts) == 0
}

type bridge struct {
	client *http.Client
}

func newBridge(socket string) *bridge {
	transport := &http.Transport{
		DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
			var d net.Dialer
			return d.DialContext(ctx, "unix", socket)
		},
	}
	return &bridge{client: &http.Client{Transport: transport, Timeout: 60 * time.Second}}
}

func (b *bridge) call(ctx context.Context, method, path string, in, out any) error {
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
	return json.NewDecoder(resp.Body).Decode(out)
}

func (b *bridge) Devices(ctx context.Context) (*DevicesResponse, error) {
	var out DevicesResponse
	return &out, b.call(ctx, http.MethodGet, "devices", nil, &out)
}

func (b *bridge) Prepare(ctx context.Context, claimUID string, devices []string, consumed map[string]map[string]string) (*ContainerEdits, error) {
	var out struct {
		Edits ContainerEdits `json:"edits"`
	}
	in := map[string]any{"claim_uid": claimUID, "devices": devices, "consumed": consumed}
	return &out.Edits, b.call(ctx, http.MethodPost, "prepare", in, &out)
}

func (b *bridge) Unprepare(ctx context.Context, claimUID string) error {
	return b.call(ctx, http.MethodPost, "unprepare", map[string]any{"claim_uid": claimUID}, nil)
}
