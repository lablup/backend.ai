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

func TestAttributeTypes(t *testing.T) {
	if a := attribute(float64(3)); a.IntValue == nil || *a.IntValue != 3 {
		t.Fatal("JSON numbers become int attributes")
	}
	if a := attribute(true); a.BoolValue == nil || !*a.BoolValue {
		t.Fatal("bools stay bools")
	}
	if a := attribute("x"); a.StringValue == nil || *a.StringValue != "x" {
		t.Fatal("strings stay strings")
	}
}
