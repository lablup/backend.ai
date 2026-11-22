package main

// One CDI spec file per prepared claim; the container runtime applies its edits.

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

const cdiKind = "dra.backend.ai/claim"

type cdiSpec struct {
	Version string      `json:"cdiVersion"`
	Kind    string      `json:"kind"`
	Devices []cdiDevice `json:"devices"`
}

type cdiDevice struct {
	Name           string         `json:"name"`
	ContainerEdits cdiEditsFields `json:"containerEdits"`
}

type cdiEditsFields struct {
	Env         []string        `json:"env,omitempty"`
	DeviceNodes []cdiDeviceNode `json:"deviceNodes,omitempty"`
	Mounts      []cdiMount      `json:"mounts,omitempty"`
}

type cdiDeviceNode struct {
	Path        string `json:"path"`
	HostPath    string `json:"hostPath,omitempty"`
	Permissions string `json:"permissions,omitempty"`
	// A character device the runtime creates in the container (a MIG capability).
	Type     string  `json:"type,omitempty"`
	Major    int64   `json:"major,omitempty"`
	Minor    int64   `json:"minor,omitempty"`
	FileMode *uint32 `json:"fileMode,omitempty"`
}

type cdiMount struct {
	HostPath      string   `json:"hostPath"`
	ContainerPath string   `json:"containerPath"`
	Options       []string `json:"options,omitempty"`
}

type cdiWriter struct {
	root string
}

func (w *cdiWriter) path(claimUID string) string {
	return filepath.Join(w.root, fmt.Sprintf("bai-dra-%s.json", claimUID))
}

// Write the spec atomically and return the CDI device id the kubelet hands to the runtime.
func (w *cdiWriter) Write(claimUID string, edits *ContainerEdits) (string, error) {
	id, _, err := w.WriteSpec(claimUID, edits, nil)
	return id, err
}

// WriteSpec writes the claim's edits (nil: none) and one CDI device per entry of `devices`
// (device name → its device nodes). It returns the claim's CDI id ("" without edits) and the
// devices' ids.
func (w *cdiWriter) WriteSpec(claimUID string, edits *ContainerEdits, devices map[string][]cdiDeviceNode) (string, map[string]string, error) {
	var specDevices []cdiDevice
	claimID := ""
	if edits != nil {
		specDevices = append(specDevices, cdiDevice{Name: claimUID, ContainerEdits: claimFields(edits)})
		claimID = fmt.Sprintf("%s=%s", cdiKind, claimUID)
	}
	ids := make(map[string]string, len(devices))
	names := make([]string, 0, len(devices))
	for name := range devices {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		specName := claimUID + "-" + name
		specDevices = append(specDevices, cdiDevice{Name: specName, ContainerEdits: cdiEditsFields{DeviceNodes: devices[name]}})
		ids[name] = fmt.Sprintf("%s=%s", cdiKind, specName)
	}
	spec := cdiSpec{Version: "0.6.0", Kind: cdiKind, Devices: specDevices}
	data, err := json.MarshalIndent(spec, "", "  ")
	if err != nil {
		return "", nil, err
	}
	if err := os.MkdirAll(w.root, 0o755); err != nil {
		return "", nil, err
	}
	tmp := w.path(claimUID) + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return "", nil, err
	}
	if err := os.Rename(tmp, w.path(claimUID)); err != nil {
		return "", nil, err
	}
	return claimID, ids, nil
}

func claimFields(edits *ContainerEdits) cdiEditsFields {
	fields := cdiEditsFields{Env: edits.Env}
	for _, n := range edits.DeviceNodes {
		node := cdiDeviceNode{Path: n.Path}
		if n.HostPath != nil {
			node.HostPath = *n.HostPath
		}
		if n.Permissions != nil {
			node.Permissions = *n.Permissions
		}
		fields.DeviceNodes = append(fields.DeviceNodes, node)
	}
	for _, m := range edits.Mounts {
		fields.Mounts = append(fields.Mounts, cdiMount(m))
	}
	return fields
}

func (w *cdiWriter) Remove(claimUID string) error {
	err := os.Remove(w.path(claimUID))
	if os.IsNotExist(err) {
		return nil
	}
	return err
}
