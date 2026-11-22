package nvmig

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/NVIDIA/go-nvml/pkg/nvml"
)

// The directories, under the driver root, where distributions install libnvidia-ml.
var libraryDirs = []string{
	"usr/lib64",
	"usr/lib/x86_64-linux-gnu",
	"usr/lib/aarch64-linux-gnu",
	"lib64",
	"usr/lib",
}

const libraryName = "libnvidia-ml.so.1"

// Open loads and initializes NVML from the node's driver root (mounted into the container).
func Open(driverRoot string) (nvml.Interface, error) {
	path, err := findLibrary(driverRoot)
	if err != nil {
		return nil, err
	}
	lib := nvml.New(nvml.WithLibraryPath(path))
	if ret := lib.Init(); ret != nvml.SUCCESS {
		return nil, fmt.Errorf("initialize NVML from %s: %w", path, ret)
	}
	return lib, nil
}

func findLibrary(driverRoot string) (string, error) {
	for _, dir := range libraryDirs {
		path := filepath.Join(driverRoot, dir, libraryName)
		if _, err := os.Stat(path); err == nil {
			return path, nil
		}
	}
	return "", fmt.Errorf("%s not found under the driver root %s", libraryName, driverRoot)
}
