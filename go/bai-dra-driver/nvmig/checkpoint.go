package nvmig

// The MIG devices bai-dra created, per claim, on the node's disk: a restarted driver reuses the
// devices of prepared claims and destroys the rest.

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

const checkpointVersion = 1

type claimState string

const (
	// stateStarted: the claim's devices are being created; a restart destroys them.
	stateStarted claimState = "started"
	// stateCompleted: the claim is prepared; its devices stay until it is unprepared.
	stateCompleted claimState = "completed"
)

// Instance is a MIG device bai-dra created: the placement and the NVML instance IDs.
type Instance struct {
	Device      string `json:"device"`
	ParentUUID  string `json:"parentUUID"`
	ParentMinor int    `json:"parentMinor"`
	ProfileID   int    `json:"profileID"`
	Start       int    `json:"placementStart"`
	GIID        int    `json:"giID"`
	CIID        int    `json:"ciID"`
}

type claimRecord struct {
	State     claimState `json:"state"`
	Devices   []string   `json:"devices"`
	Instances []Instance `json:"instances"`
}

type checkpoint struct {
	Version int                     `json:"version"`
	Claims  map[string]*claimRecord `json:"claims"`
}

type checkpointStore struct {
	path string
}

func (s *checkpointStore) load() (*checkpoint, error) {
	cp := &checkpoint{Version: checkpointVersion, Claims: map[string]*claimRecord{}}
	data, err := os.ReadFile(s.path)
	if errors.Is(err, os.ErrNotExist) {
		return cp, nil
	}
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal(data, cp); err != nil {
		return nil, fmt.Errorf("MIG checkpoint %s: %w", s.path, err)
	}
	if cp.Version != checkpointVersion {
		return nil, fmt.Errorf("MIG checkpoint %s: version %d, want %d", s.path, cp.Version, checkpointVersion)
	}
	if cp.Claims == nil {
		cp.Claims = map[string]*claimRecord{}
	}
	return cp, nil
}

// save writes atomically: a crash leaves the old or the new checkpoint.
func (s *checkpointStore) save(cp *checkpoint) error {
	data, err := json.Marshal(cp)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(s.path), 0o750); err != nil {
		return err
	}
	tmp := s.path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o600); err != nil {
		return err
	}
	return os.Rename(tmp, s.path)
}
