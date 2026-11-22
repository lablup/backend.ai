// sokovan-binder: the Go parts of the sokovan scheduler in its KAI form (suggestion-1122 3.3).
//
//	sokovan-binder allocator  DRA allocator sidecar: claim allocations for a gang placement
//	sokovan-binder binder     BindRequest → claim status → Pod binding
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/klog/v2"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: sokovan-binder allocator|binder [flags]")
		os.Exit(2)
	}
	command, args := os.Args[1], os.Args[2:]
	fs := flag.NewFlagSet(command, flag.ExitOnError)
	klog.InitFlags(fs)
	listen := fs.String("listen", "127.0.0.1:8786", "allocator: HTTP listen address")
	interval := fs.Duration("interval", defaultBinderInterval, "binder: BindRequest poll interval")
	leaderElect := fs.Bool("leader-elect", false, "binder: run as one of several replicas; the Lease holder binds")
	leaseNamespace := fs.String("lease-namespace", os.Getenv("POD_NAMESPACE"), "binder: namespace of the Lease")
	_ = fs.Parse(args)

	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer cancel()
	ctx = klog.NewContext(ctx, klog.FromContext(ctx).WithValues("component", command))
	cfg, err := rest.InClusterConfig()
	if err != nil {
		klog.Fatal(err)
	}
	client := kubernetes.NewForConfigOrDie(cfg)
	switch command {
	case "allocator":
		err = runAllocator(ctx, client, *listen)
	case "binder":
		run := func(ctx context.Context) {
			if err := runBinder(ctx, client, dynamic.NewForConfigOrDie(cfg), *interval); err != nil {
				klog.FromContext(ctx).Error(err, "binder stopped")
			}
		}
		if *leaderElect {
			err = runAsLeader(ctx, client, *leaseNamespace, "sokovan-binder", run)
		} else {
			run(ctx)
		}
	default:
		err = fmt.Errorf("unknown command %q", command)
	}
	if err != nil && ctx.Err() == nil {
		klog.Fatal(err)
	}
}
