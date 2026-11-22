package main

import (
	"context"
	"fmt"
	"os"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/leaderelection"
	"k8s.io/client-go/tools/leaderelection/resourcelock"
	"k8s.io/klog/v2"
)

// runAsLeader runs `work` while this replica holds the Lease. Losing it ends the process so that
// it comes back as a standby (suggestion-1122 12.1).
func runAsLeader(ctx context.Context, client kubernetes.Interface, namespace, name string, work func(context.Context)) error {
	identity, err := os.Hostname()
	if err != nil {
		return err
	}
	if namespace == "" {
		return fmt.Errorf("--lease-namespace (POD_NAMESPACE) is required with --leader-elect")
	}
	lock := &resourcelock.LeaseLock{
		LeaseMeta:  metav1.ObjectMeta{Name: name, Namespace: namespace},
		Client:     client.CoordinationV1(),
		LockConfig: resourcelock.ResourceLockConfig{Identity: identity},
	}
	logger := klog.FromContext(ctx)
	leaderelection.RunOrDie(ctx, leaderelection.LeaderElectionConfig{
		Lock:            lock,
		LeaseDuration:   15 * time.Second,
		RenewDeadline:   10 * time.Second,
		RetryPeriod:     2 * time.Second,
		ReleaseOnCancel: true,
		Callbacks: leaderelection.LeaderCallbacks{
			OnStartedLeading: func(ctx context.Context) {
				logger.Info("leader elected", "lease", name, "identity", identity)
				work(ctx)
			},
			OnStoppedLeading: func() {
				logger.Info("leadership lost", "lease", name, "identity", identity)
				if ctx.Err() == nil {
					os.Exit(1)
				}
			},
		},
	})
	return nil
}
