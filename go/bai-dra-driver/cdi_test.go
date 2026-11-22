package main

import (
	"encoding/json"
	"os"
	"testing"
)

func TestCDIWriteAndRemove(t *testing.T) {
	w := &cdiWriter{root: t.TempDir()}
	host := "/dev/x0"
	id, err := w.Write("uid-1", &ContainerEdits{
		Env:         []string{"A=1"},
		DeviceNodes: []DeviceNode{{Path: "/dev/x0", HostPath: &host}},
		Mounts:      []Mount{{HostPath: "/a", ContainerPath: "/b", Options: []string{"bind", "ro"}}},
	})
	if err != nil {
		t.Fatal(err)
	}
	if id != "dra.backend.ai/claim=uid-1" {
		t.Fatalf("unexpected CDI id %q", id)
	}
	data, err := os.ReadFile(w.path("uid-1"))
	if err != nil {
		t.Fatal(err)
	}
	var spec cdiSpec
	if err := json.Unmarshal(data, &spec); err != nil {
		t.Fatal(err)
	}
	edits := spec.Devices[0].ContainerEdits
	if spec.Kind != cdiKind || edits.Env[0] != "A=1" || edits.DeviceNodes[0].HostPath != host || edits.Mounts[0].ContainerPath != "/b" {
		t.Fatalf("unexpected spec %+v", spec)
	}
	if err := w.Remove("uid-1"); err != nil {
		t.Fatal(err)
	}
	if err := w.Remove("uid-1"); err != nil {
		t.Fatalf("removing twice must not fail: %v", err)
	}
}
