// bai-dra-driver: the node part of bai-dra (suggestion-1122 4.5). It registers with the kubelet,
// publishes the devices of the Python plugin host as a ResourceSlice and prepares claims as CDI.
package main

import (
	"context"
	"flag"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/dynamic-resource-allocation/kubeletplugin"
	"k8s.io/klog/v2"
)

func main() {
	var (
		driverName = flag.String("driver-name", envOr("BAI_DRA_DRIVER_NAME", ""), "DRA driver name, e.g. cuda.dra.backend.ai")
		nodeName   = flag.String("node-name", os.Getenv("NODE_NAME"), "this node")
		socket     = flag.String("bridge-socket", envOr("BAI_DRA_BRIDGE_SOCKET", "/run/bai-dra/bridge.sock"), "plugin host socket")
		cdiRoot    = flag.String("cdi-root", envOr("BAI_DRA_CDI_ROOT", "/var/run/cdi"), "CDI spec directory")
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
	d := &driver{
		name:     *driverName,
		nodeName: *nodeName,
		bridge:   newBridge(*socket),
		cdi:      &cdiWriter{root: *cdiRoot},
		prepared: map[types.UID][]kubeletplugin.Device{},
	}
	// The plugin host starts beside this container; wait until it answers.
	for {
		if _, err := d.bridge.Devices(ctx); err == nil {
			break
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(2 * time.Second):
		}
	}
	// The kubelet does not create the plugin's socket directory.
	if err := os.MkdirAll(filepath.Join("/var/lib/kubelet/plugins", *driverName), 0o750); err != nil {
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
	if err := d.publish(ctx); err != nil {
		klog.Fatal(err)
	}
	logger.Info("bai-dra driver started")
	go watchRegistration(ctx, helper)
	<-ctx.Done()
	helper.Stop()
	logger.Info("bai-dra driver stopped")
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
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
