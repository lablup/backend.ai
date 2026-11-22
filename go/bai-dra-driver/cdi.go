package main

// One CDI spec file per prepared claim; the container runtime applies its edits.

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
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
		fields.Mounts = append(fields.Mounts, cdiMount{HostPath: m.HostPath, ContainerPath: m.ContainerPath, Options: m.Options})
	}
	spec := cdiSpec{Version: "0.6.0", Kind: cdiKind, Devices: []cdiDevice{{Name: claimUID, ContainerEdits: fields}}}
	data, err := json.MarshalIndent(spec, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(w.root, 0o755); err != nil {
		return "", err
	}
	tmp := w.path(claimUID) + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return "", err
	}
	if err := os.Rename(tmp, w.path(claimUID)); err != nil {
		return "", err
	}
	return fmt.Sprintf("%s=%s", cdiKind, claimUID), nil
}

func (w *cdiWriter) Remove(claimUID string) error {
	err := os.Remove(w.path(claimUID))
	if os.IsNotExist(err) {
		return nil
	}
	return err
}
