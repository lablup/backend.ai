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

// Portions derived from the NVIDIA DRA driver for GPUs (internal/common/nvcaps.go and
// cmd/gpu-kubelet-plugin/cdi.go: GetDevNodesForMigDevice). See NOTICE.

package nvmig

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
)

// CapNode is a character device a container needs to open one MIG device: the access
// capability of its GPU instance or of its compute instance.
type CapNode struct {
	Path     string
	Major    int64
	Minor    int64
	FileMode uint32
}

// capNodes reads the two capability devices of a MIG device. The container runtime creates
// them in the container from major/minor; the node needs no /dev/nvidia-caps entries.
func capNodes(procRoot string, inst Instance) ([]CapNode, error) {
	major, err := deviceMajor(filepath.Join(procRoot, "devices"), "nvidia-caps")
	if err != nil {
		return nil, err
	}
	base := filepath.Join(procRoot, "driver/nvidia/capabilities", fmt.Sprintf("gpu%d", inst.ParentMinor), "mig", fmt.Sprintf("gi%d", inst.GIID))
	var nodes []CapNode
	for _, path := range []string{filepath.Join(base, "access"), filepath.Join(base, fmt.Sprintf("ci%d", inst.CIID), "access")} {
		node, err := parseCapFile(path, major)
		if err != nil {
			return nil, err
		}
		nodes = append(nodes, node)
	}
	return nodes, nil
}

func parseCapFile(path string, major int64) (CapNode, error) {
	f, err := os.Open(path)
	if err != nil {
		return CapNode{}, fmt.Errorf("MIG capability %s: %w", path, err)
	}
	defer func() { _ = f.Close() }()
	node := CapNode{Major: major, Minor: -1}
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		key, value, ok := strings.Cut(scanner.Text(), ":")
		if !ok {
			continue
		}
		n, err := strconv.ParseInt(strings.TrimSpace(value), 10, 64)
		if err != nil {
			continue
		}
		switch strings.TrimSpace(key) {
		case "DeviceFileMinor":
			node.Minor = n
		case "DeviceFileMode":
			node.FileMode = uint32(n)
		}
	}
	if err := scanner.Err(); err != nil {
		return CapNode{}, fmt.Errorf("MIG capability %s: %w", path, err)
	}
	if node.Minor < 0 {
		return CapNode{}, fmt.Errorf("MIG capability %s: no DeviceFileMinor", path)
	}
	node.Path = fmt.Sprintf("/dev/nvidia-caps/nvidia-cap%d", node.Minor)
	return node, nil
}

var rxCharDevices = regexp.MustCompile(`(?s)Character devices:(.*?)(?:\n\s*\n|Block devices:|$)`)

// deviceMajor is the major number of a character device in /proc/devices.
func deviceMajor(procDevices, name string) (int64, error) {
	data, err := os.ReadFile(procDevices)
	if err != nil {
		return 0, fmt.Errorf("read %s: %w", procDevices, err)
	}
	section := rxCharDevices.FindSubmatch(data)
	if section == nil {
		return 0, fmt.Errorf("%s has no character devices", procDevices)
	}
	for _, line := range strings.Split(string(section[1]), "\n") {
		fields := strings.Fields(line)
		if len(fields) == 2 && fields[1] == name {
			return strconv.ParseInt(fields[0], 10, 32)
		}
	}
	return 0, fmt.Errorf("%s lists no %s device", procDevices, name)
}
