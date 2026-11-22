package main

import (
	"context"
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	corelisters "k8s.io/client-go/listers/core/v1"
	resourcelisters "k8s.io/client-go/listers/resource/v1"
	"k8s.io/client-go/tools/cache"
	"k8s.io/klog/v2"
)

const (
	// The NVIDIA DRA driver's GPUs; its ComputeDomain driver (compute-domain.nvidia.com) is not one.
	nvidiaDRADriver = "gpu.nvidia.com"
	// The NVIDIA device plugin's extended resource.
	nvidiaExtendedResource corev1.ResourceName = "nvidia.com/gpu"

	conflictCondition corev1.NodeConditionType = "BaiDraGPUConflict"
	conflictReason                             = "OtherGPUAllocator"
	noConflictReason                           = "NoOtherGPUAllocator"
	resolvedReason                             = "OtherGPUAllocatorGone"
	conflictRecheck                            = 30 * time.Second
)

// otherAllocators names the other GPU allocators on the node: the NVIDIA DRA driver with GPU
// devices in a slice of the node, and the device plugin with allocatable nvidia.com/gpu.
func otherAllocators(node *corev1.Node, slices []*resourceapi.ResourceSlice) []string {
	var others []string
	devices := 0
	for _, s := range slices {
		if s.Spec.Driver == nvidiaDRADriver && s.Spec.NodeName != nil && *s.Spec.NodeName == node.Name {
			devices += len(s.Spec.Devices)
		}
	}
	if devices > 0 {
		others = append(others, fmt.Sprintf("%s (%d devices)", nvidiaDRADriver, devices))
	}
	if q, ok := node.Status.Allocatable[nvidiaExtendedResource]; ok && q.Sign() > 0 {
		others = append(others, fmt.Sprintf("device plugin (%s: %s)", nvidiaExtendedResource, q.String()))
	}
	sort.Strings(others)
	return others
}

// conflictWatch withdraws the driver's GPUs while another GPU allocator is on its node, and
// reports it as the node condition BaiDraGPUConflict and an Event.
type conflictWatch struct {
	client   kubernetes.Interface
	driver   *driver
	nodeName string
	now      func() time.Time
	nodes    corelisters.NodeLister
	slices   resourcelisters.ResourceSliceLister
	synced   []cache.InformerSynced
	trigger  chan struct{}
}

// newConflictWatch watches the node and the ResourceSlices of the node only.
func newConflictWatch(client kubernetes.Interface, d *driver, nodeName string) (*conflictWatch, func(<-chan struct{})) {
	w := &conflictWatch{client: client, driver: d, nodeName: nodeName, now: time.Now, trigger: make(chan struct{}, 1)}
	nodeFactory := informers.NewSharedInformerFactoryWithOptions(client, 0,
		informers.WithTweakListOptions(func(o *metav1.ListOptions) {
			o.FieldSelector = fields.OneTermEqualSelector("metadata.name", nodeName).String()
		}))
	sliceFactory := informers.NewSharedInformerFactoryWithOptions(client, 0,
		informers.WithTweakListOptions(func(o *metav1.ListOptions) {
			o.FieldSelector = fields.OneTermEqualSelector(resourceapi.ResourceSliceSelectorNodeName, nodeName).String()
		}))
	nodeInformer := nodeFactory.Core().V1().Nodes()
	sliceInformer := sliceFactory.Resource().V1().ResourceSlices()
	handler := cache.ResourceEventHandlerFuncs{
		AddFunc:    func(any) { w.poke() },
		UpdateFunc: func(any, any) { w.poke() },
		DeleteFunc: func(any) { w.poke() },
	}
	for _, inf := range []cache.SharedIndexInformer{nodeInformer.Informer(), sliceInformer.Informer()} {
		if _, err := inf.AddEventHandler(handler); err != nil {
			klog.Background().Error(err, "conflict watch: event handler not added")
		}
		w.synced = append(w.synced, inf.HasSynced)
	}
	w.nodes, w.slices = nodeInformer.Lister(), sliceInformer.Lister()
	start := func(stop <-chan struct{}) {
		nodeFactory.Start(stop)
		sliceFactory.Start(stop)
	}
	return w, start
}

func (w *conflictWatch) poke() {
	select {
	case w.trigger <- struct{}{}:
	default:
	}
}

// sync waits for the informers and evaluates once: the first publish already knows the state.
func (w *conflictWatch) sync(ctx context.Context) error {
	if !cache.WaitForCacheSync(ctx.Done(), w.synced...) {
		return fmt.Errorf("conflict watch: caches of node %s not synced", w.nodeName)
	}
	return w.check(ctx)
}

// run evaluates on every change of the node or its slices, and every conflictRecheck.
func (w *conflictWatch) run(ctx context.Context, recheck time.Duration) {
	ticker := time.NewTicker(recheck)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-w.trigger:
		case <-ticker.C:
		}
		if err := w.check(ctx); err != nil {
			klog.FromContext(ctx).Error(err, "GPU allocator check failed")
		}
	}
}

func (w *conflictWatch) check(ctx context.Context) error {
	node, err := w.nodes.Get(w.nodeName)
	if err != nil {
		return err
	}
	all, err := w.slices.List(labels.Everything())
	if err != nil {
		return err
	}
	return w.evaluate(ctx, node, all)
}

// evaluate withdraws or republishes the GPUs, then reports the state on the node.
func (w *conflictWatch) evaluate(ctx context.Context, node *corev1.Node, slices []*resourceapi.ResourceSlice) error {
	if !w.driver.gpu {
		return nil
	}
	logger := klog.FromContext(ctx)
	others := otherAllocators(node, slices)
	conflict := len(others) > 0
	changed, err := w.driver.withdraw(ctx, conflict)
	if err != nil {
		return fmt.Errorf("publish after the GPU allocator check: %w", err)
	}
	message := w.message(others)
	if changed {
		if conflict {
			logger.Error(nil, "another GPU allocator is on the node; bai-dra GPUs withdrawn", "allocators", others)
			w.event(ctx, node, corev1.EventTypeWarning, conflictReason, message)
		} else {
			logger.Info("no other GPU allocator on the node; bai-dra GPUs published again")
			w.event(ctx, node, corev1.EventTypeNormal, resolvedReason, message)
		}
	}
	return w.setCondition(ctx, node, conflict, message)
}

func (w *conflictWatch) message(others []string) string {
	if len(others) == 0 {
		return fmt.Sprintf("bai-dra %s is the only GPU allocator on the node", w.driver.name)
	}
	return fmt.Sprintf("bai-dra %s withdrew its GPUs: also allocated by %s", w.driver.name, strings.Join(others, ", "))
}

// setCondition patches the node's BaiDraGPUConflict condition when it differs; without a conflict
// a node that never had the condition is left alone.
func (w *conflictWatch) setCondition(ctx context.Context, node *corev1.Node, conflict bool, message string) error {
	status, reason := corev1.ConditionFalse, noConflictReason
	if conflict {
		status, reason = corev1.ConditionTrue, conflictReason
	}
	var current *corev1.NodeCondition
	for i := range node.Status.Conditions {
		if node.Status.Conditions[i].Type == conflictCondition {
			current = &node.Status.Conditions[i]
		}
	}
	if current == nil && !conflict {
		return nil
	}
	if current != nil && current.Status == status && current.Reason == reason && current.Message == message {
		return nil
	}
	now := metav1.NewTime(w.now())
	transition := now
	if current != nil && current.Status == status {
		transition = current.LastTransitionTime
	}
	patch, err := json.Marshal(map[string]any{"status": map[string]any{"conditions": []corev1.NodeCondition{{
		Type:               conflictCondition,
		Status:             status,
		Reason:             reason,
		Message:            message,
		LastHeartbeatTime:  now,
		LastTransitionTime: transition,
	}}}})
	if err != nil {
		return err
	}
	_, err = w.client.CoreV1().Nodes().PatchStatus(ctx, node.Name, patch)
	return err
}

// event records the transition on the node; a failed Event is only logged.
func (w *conflictWatch) event(ctx context.Context, node *corev1.Node, eventType, reason, message string) {
	now := metav1.NewTime(w.now())
	ev := &corev1.Event{
		// Named as the kubelet names node events: <node>.<hex nanoseconds>.
		ObjectMeta: metav1.ObjectMeta{Name: fmt.Sprintf("%s.%x", node.Name, now.UnixNano()), Namespace: metav1.NamespaceDefault},
		InvolvedObject: corev1.ObjectReference{
			APIVersion: "v1", Kind: "Node", Name: node.Name, UID: types.UID(node.Name),
		},
		Reason:              reason,
		Message:             message,
		Type:                eventType,
		Source:              corev1.EventSource{Component: "bai-dra", Host: node.Name},
		ReportingController: "dra.backend.ai/bai-dra",
		ReportingInstance:   w.driver.name + "/" + node.Name,
		Action:              "PublishDevices",
		FirstTimestamp:      now,
		LastTimestamp:       now,
		Count:               1,
	}
	if _, err := w.client.CoreV1().Events(metav1.NamespaceDefault).Create(ctx, ev, metav1.CreateOptions{}); err != nil {
		klog.FromContext(ctx).Error(err, "node event not recorded", "reason", reason)
	}
}
