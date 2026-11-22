// bai-dra-driver: the node part of bai-dra (suggestion-1122 4.5). It registers with the kubelet,
// publishes the devices of the Python plugin host as a ResourceSlice and prepares claims as CDI.
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"

	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/dynamic-resource-allocation/kubeletplugin"
	"k8s.io/klog/v2"

	"github.com/lablup/backend.ai/go/bai-dra-driver/nvmig"
)

func main() {
	var (
		driverName = flag.String("driver-name", envOr("BAI_DRA_DRIVER_NAME", ""), "DRA driver name, e.g. cuda.dra.backend.ai")
		nodeName   = flag.String("node-name", os.Getenv("NODE_NAME"), "this node")
		socket     = flag.String("bridge-socket", envOr("BAI_DRA_BRIDGE_SOCKET", "/run/bai-dra/bridge.sock"), "plugin host socket")
		cdiRoot    = flag.String("cdi-root", envOr("BAI_DRA_CDI_ROOT", "/var/run/cdi"), "CDI spec directory")
		healthAddr = flag.String("health-addr", envOr("BAI_DRA_HEALTH_ADDR", ":8081"), "address of /healthz and /readyz")
		resync     = flag.Duration("resync-interval", 30*time.Second, "how often to check the plugin host's devices")
		dynamicMig = flag.Bool("dynamic-mig", envOr("BAI_DRA_DYNAMIC_MIG", "false") == "true", "create NVIDIA MIG devices on demand (needs NVML)")
		driverRoot = flag.String("nvidia-driver-root", envOr("BAI_DRA_NVIDIA_DRIVER_ROOT", "/driver-root"), "the node's NVIDIA driver root, for libnvidia-ml (dynamic MIG)")
		procRoot   = flag.String("proc-root", envOr("BAI_DRA_PROC_ROOT", "/proc"), "procfs with /proc/driver/nvidia (dynamic MIG)")
	)
	klog.InitFlags(nil)
	flag.Parse()
	if *driverName == "" || *nodeName == "" {
		klog.Fatal("--driver-name and --node-name are required")
	}
	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer cancel()
	logger := klog.FromContext(ctx).WithValues("driver", *driverName, "node", *nodeName)
	ctx = klog.NewContext(ctx, logger)

	cfg, err := rest.InClusterConfig()
	if err != nil {
		klog.Fatal(err)
	}
	client := kubernetes.NewForConfigOrDie(cfg)
	d := newDriver(*driverName, *nodeName, newBridge(*socket), &cdiWriter{root: *cdiRoot})
	pluginDir := filepath.Join("/var/lib/kubelet/plugins", *driverName)
	if *dynamicMig {
		if err := setupDynamicMig(ctx, d, client, *driverRoot, *procRoot, pluginDir); err != nil {
			klog.Fatal(err)
		}
	}
	go serveHealth(ctx, *healthAddr, d)
	// The plugin host starts beside this container; wait until it answers.
	for {
		if err := d.bridge.Health(ctx); err == nil {
			break
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(2 * time.Second):
		}
	}
	// The kubelet does not create the plugin's socket directory.
	if err := os.MkdirAll(pluginDir, 0o750); err != nil {
		klog.Fatal(err)
	}
	helper, err := kubeletplugin.Start(ctx, d,
		kubeletplugin.KubeClient(client),
		kubeletplugin.NodeName(*nodeName),
		kubeletplugin.DriverName(*driverName),
	)
	if err != nil {
		klog.Fatal(err)
	}
	d.helper = helper
	if err := d.syncDevices(ctx); err != nil {
		klog.Fatal(err)
	}
	logger.Info("bai-dra driver started")
	go watchRegistration(ctx, helper)
	go resyncDevices(ctx, d, *resync)
	<-ctx.Done()
	helper.Stop()
	logger.Info("bai-dra driver stopped")
}

// setupDynamicMig loads NVML, inspects the GPUs and destroys the MIG devices no prepared claim
// holds (a restart after a crash).
func setupDynamicMig(ctx context.Context, d *driver, client kubernetes.Interface, driverRoot, procRoot, pluginDir string) error {
	lib, err := nvmig.Open(driverRoot)
	if err != nil {
		return err
	}
	m, err := nvmig.NewManager(lib, filepath.Join(pluginDir, "dynamic-mig.json"), procRoot)
	if err != nil {
		return err
	}
	if err := m.Reconcile(); err != nil {
		klog.FromContext(ctx).Error(err, "dynamic MIG cleanup left devices behind")
	}
	version, err := client.Discovery().ServerVersion()
	if err != nil {
		return fmt.Errorf("API server version: %w", err)
	}
	d.mig = m
	d.splitCounters = splitCounterSlices(version.Major, version.Minor)
	klog.FromContext(ctx).Info("dynamic MIG on", "splitCounterSlices", d.splitCounters)
	return nil
}

// splitCounterSlices: Kubernetes 1.35 and later reject counter sets next to devices.
func splitCounterSlices(major, minor string) bool {
	maj, err := strconv.Atoi(strings.TrimSuffix(major, "+"))
	if err != nil {
		return true
	}
	mnr, err := strconv.Atoi(strings.TrimRight(minor, "+-abcdefghijklmnopqrstuvwxyz"))
	if err != nil {
		return true
	}
	return maj > 1 || (maj == 1 && mnr >= 35)
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// resyncDevices republishes when the plugin host restarted or its devices changed (hot-plug,
// failure). The resourceslice controller of the helper repairs slices changed by others.
func resyncDevices(ctx context.Context, d *driver, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := d.syncDevices(ctx); err != nil {
				klog.FromContext(ctx).Error(err, "device resync failed")
			}
		}
	}
}

// serveHealth answers the kubelet's probes: /healthz when the plugin host answers, /readyz
// once the devices are published.
func serveHealth(ctx context.Context, addr string, d *driver) {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		hctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()
		if err := d.bridge.Health(hctx); err != nil {
			http.Error(w, err.Error(), http.StatusServiceUnavailable)
			return
		}
		_, _ = w.Write([]byte("ok"))
	})
	mux.HandleFunc("/readyz", func(w http.ResponseWriter, _ *http.Request) {
		if !d.published.Load() {
			http.Error(w, "devices not published", http.StatusServiceUnavailable)
			return
		}
		_, _ = w.Write([]byte("ok"))
	})
	server := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 5 * time.Second}
	go func() {
		<-ctx.Done()
		_ = server.Close()
	}()
	if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		klog.FromContext(ctx).Error(err, "health server stopped")
	}
}

// watchRegistration reports whether the kubelet confirmed the registration. A kubelet whose
// plugin manager is stuck never calls back (observed after repeated driver restarts); claims on
// the node then fail with "driver is not registered" until the kubelet restarts.
func watchRegistration(ctx context.Context, helper *kubeletplugin.Helper) {
	logger := klog.FromContext(ctx)
	deadline := time.Now().Add(registrationTimeout)
	for {
		if status := helper.RegistrationStatus(); status != nil {
			if status.PluginRegistered {
				logger.Info("kubelet registered the driver")
			} else {
				logger.Error(nil, "kubelet rejected the driver", "error", status.Error)
			}
			return
		}
		if time.Now().After(deadline) {
			logger.Error(nil, "kubelet has not registered the driver", "waited", registrationTimeout)
			deadline = time.Now().Add(registrationTimeout)
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(2 * time.Second):
		}
	}
}

const registrationTimeout = 60 * time.Second
