package main

// The binder: for each pending BindRequest, record the claim allocations, release the
// scheduling gate and bind the Pod. A request that keeps failing rolls its claims back.

import (
	"context"
	"encoding/json"
	"fmt"
	"slices"
	"time"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/klog/v2"
)

const (
	defaultBinderInterval = time.Second
	sokovanGate           = "scheduling.backend.ai/sokovan"
	phasePending          = "Pending"
	phaseSucceeded        = "Succeeded"
	phaseFailed           = "Failed"
)

var bindRequestGVR = schema.GroupVersionResource{Group: "scheduling.backend.ai", Version: "v1alpha1", Resource: "bindrequests"}

type bindRequestSpec struct {
	PodName                  string            `json:"podName"`
	PodUID                   string            `json:"podUid"`
	SelectedNode             string            `json:"selectedNode"`
	ResourceClaimAllocations []ClaimAllocation `json:"resourceClaimAllocations"`
	BackoffLimit             int               `json:"backoffLimit"`
}

type bindRequestStatus struct {
	Phase          string `json:"phase,omitempty"`
	FailedAttempts int    `json:"failedAttempts,omitempty"`
	Reason         string `json:"reason,omitempty"`
}

type bindRequest struct {
	metav1.ObjectMeta `json:"metadata"`
	Spec              bindRequestSpec    `json:"spec"`
	Status            *bindRequestStatus `json:"status,omitempty"`
}

type binder struct {
	client  kubernetes.Interface
	dynamic dynamic.Interface
}

func runBinder(ctx context.Context, client kubernetes.Interface, dyn dynamic.Interface, interval time.Duration) error {
	b := &binder{client: client, dynamic: dyn}
	klog.FromContext(ctx).Info("binder started")
	for {
		if err := b.cycle(ctx); err != nil {
			klog.FromContext(ctx).Error(err, "bind cycle failed")
		}
		select {
		case <-ctx.Done():
			return nil
		case <-time.After(interval):
		}
	}
}

func (b *binder) cycle(ctx context.Context) error {
	list, err := b.dynamic.Resource(bindRequestGVR).List(ctx, metav1.ListOptions{})
	if err != nil {
		return err
	}
	for _, item := range list.Items {
		var br bindRequest
		if err := runtime.DefaultUnstructuredConverter.FromUnstructured(item.Object, &br); err != nil {
			klog.FromContext(ctx).Error(err, "malformed bind request", "name", item.GetName())
			continue
		}
		if br.Status != nil && br.Status.Phase != "" && br.Status.Phase != phasePending {
			continue
		}
		status := bindRequestStatus{Phase: phasePending}
		if br.Status != nil {
			status = *br.Status
		}
		if err := b.bind(ctx, &br); err != nil {
			status.FailedAttempts++
			status.Reason = err.Error()
			if status.FailedAttempts > br.Spec.BackoffLimit {
				status.Phase = phaseFailed
				b.rollback(ctx, &br)
			}
			klog.FromContext(ctx).Error(err, "bind failed", "pod", klog.KRef(br.Namespace, br.Spec.PodName), "attempts", status.FailedAttempts)
		} else {
			status = bindRequestStatus{Phase: phaseSucceeded, FailedAttempts: status.FailedAttempts}
			klog.FromContext(ctx).Info("pod bound", "pod", klog.KRef(br.Namespace, br.Spec.PodName), "node", br.Spec.SelectedNode)
		}
		if err := b.writeStatus(ctx, &br, status); err != nil {
			klog.FromContext(ctx).Error(err, "bind request status not written", "name", br.Name)
		}
	}
	return nil
}

func (b *binder) bind(ctx context.Context, br *bindRequest) error {
	pods := b.client.CoreV1().Pods(br.Namespace)
	pod, err := pods.Get(ctx, br.Spec.PodName, metav1.GetOptions{})
	if err != nil {
		return err
	}
	if string(pod.UID) != br.Spec.PodUID {
		return fmt.Errorf("pod %s was replaced", br.Spec.PodName)
	}
	if pod.Spec.NodeName != "" {
		if pod.Spec.NodeName != br.Spec.SelectedNode {
			return fmt.Errorf("pod %s is bound to %s", pod.Name, pod.Spec.NodeName)
		}
		return nil
	}
	for _, ca := range br.Spec.ResourceClaimAllocations {
		if err := b.allocateClaim(ctx, br.Namespace, pod, ca); err != nil {
			return err
		}
	}
	if gates := withoutGate(pod.Spec.SchedulingGates); len(gates) != len(pod.Spec.SchedulingGates) {
		patch, _ := json.Marshal([]map[string]any{{"op": "replace", "path": "/spec/schedulingGates", "value": gates}})
		if _, err := pods.Patch(ctx, pod.Name, types.JSONPatchType, patch, metav1.PatchOptions{}); err != nil {
			return err
		}
	}
	return pods.Bind(ctx, &corev1.Binding{
		ObjectMeta: metav1.ObjectMeta{Name: pod.Name, Namespace: pod.Namespace, UID: pod.UID},
		Target:     corev1.ObjectReference{Kind: "Node", Name: br.Spec.SelectedNode},
	}, metav1.CreateOptions{})
}

func withoutGate(gates []corev1.PodSchedulingGate) []corev1.PodSchedulingGate {
	out := []corev1.PodSchedulingGate{}
	for _, g := range gates {
		if g.Name != sokovanGate {
			out = append(out, g)
		}
	}
	return out
}

func (b *binder) allocateClaim(ctx context.Context, ns string, pod *corev1.Pod, ca ClaimAllocation) error {
	claims := b.client.ResourceV1().ResourceClaims(ns)
	claim, err := claims.Get(ctx, ca.Name, metav1.GetOptions{})
	if err != nil {
		return err
	}
	if claim.Status.Allocation == nil {
		allocation := ca.Allocation
		claim.Status.Allocation = &allocation
	} else if !sameDevices(claim.Status.Allocation, &ca.Allocation) {
		return fmt.Errorf("claim %s is allocated to other devices", claim.Name)
	}
	reserved := slices.ContainsFunc(claim.Status.ReservedFor, func(r resourceapi.ResourceClaimConsumerReference) bool {
		return r.UID == pod.UID
	})
	if !reserved {
		claim.Status.ReservedFor = append(claim.Status.ReservedFor, resourceapi.ResourceClaimConsumerReference{
			Resource: "pods", Name: pod.Name, UID: pod.UID,
		})
	}
	_, err = claims.UpdateStatus(ctx, claim, metav1.UpdateOptions{})
	return err
}

func sameDevices(a, b *resourceapi.AllocationResult) bool {
	key := func(r resourceapi.DeviceRequestAllocationResult) string {
		return r.Driver + "/" + r.Pool + "/" + r.Device
	}
	if len(a.Devices.Results) != len(b.Devices.Results) {
		return false
	}
	for i := range a.Devices.Results {
		if key(a.Devices.Results[i]) != key(b.Devices.Results[i]) {
			return false
		}
	}
	return true
}

// rollback frees the claims this request allocated, so the next placement starts clean.
func (b *binder) rollback(ctx context.Context, br *bindRequest) {
	claims := b.client.ResourceV1().ResourceClaims(br.Namespace)
	for _, ca := range br.Spec.ResourceClaimAllocations {
		claim, err := claims.Get(ctx, ca.Name, metav1.GetOptions{})
		if apierrors.IsNotFound(err) {
			continue
		}
		if err != nil || claim.Status.Allocation == nil || !sameDevices(claim.Status.Allocation, &ca.Allocation) {
			continue
		}
		claim.Status.Allocation = nil
		claim.Status.ReservedFor = nil
		if _, err := claims.UpdateStatus(ctx, claim, metav1.UpdateOptions{}); err != nil {
			klog.FromContext(ctx).Error(err, "claim rollback failed", "claim", klog.KObj(claim))
		}
	}
}

func (b *binder) writeStatus(ctx context.Context, br *bindRequest, status bindRequestStatus) error {
	body, err := json.Marshal(map[string]any{"status": status})
	if err != nil {
		return err
	}
	_, err = b.dynamic.Resource(bindRequestGVR).Namespace(br.Namespace).Patch(
		ctx, br.Name, types.MergePatchType, body, metav1.PatchOptions{}, "status")
	return err
}
