package main

// The binder: for each pending BindRequest, record the claim allocations, release the
// scheduling gate and bind the Pod. A request that keeps failing, or that the scheduler marks
// failed, rolls its claims back; the scheduler deletes it once the rollback shows. A request
// that succeeded is deleted after a grace period, when the allocator's informer shows its claims.

import (
	"context"
	"encoding/json"
	"fmt"
	"slices"
	"sort"
	"strconv"
	"time"

	corev1 "k8s.io/api/core/v1"
	resourceapi "k8s.io/api/resource/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/dynamic/dynamicinformer"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	resourcelisters "k8s.io/client-go/listers/resource/v1"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/util/retry"
	"k8s.io/klog/v2"
)

const (
	defaultBinderInterval = time.Second
	sokovanGate           = "scheduling.backend.ai/sokovan"
	phasePending          = "Pending"
	phaseSucceeded        = "Succeeded"
	phaseFailed           = "Failed"
	// How long a Succeeded request stays: the scheduler sends its allocations to the allocator
	// until the allocator's informer shows them on the claims.
	succeededRetention = 30 * time.Second
	// How long a claim allocation this binder wrote counts in the conflict check while the
	// claim informer may not show it yet.
	writtenRetention = time.Minute
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

type writtenAllocation struct {
	allocation      resourceapi.AllocationResult
	uid             types.UID
	resourceVersion string
	at              time.Time
}

type binder struct {
	client   kubernetes.Interface
	dynamic  dynamic.Interface
	requests cache.GenericLister
	claims   resourcelisters.ResourceClaimLister
	// claim key → allocation this binder wrote, until the claim informer surely shows it
	written map[string]writtenAllocation
	// bind request key → when it was first seen Succeeded
	succeededAt map[string]time.Time
	now         func() time.Time
}

func newBinder(client kubernetes.Interface, dyn dynamic.Interface) *binder {
	return &binder{
		client:      client,
		dynamic:     dyn,
		written:     map[string]writtenAllocation{},
		succeededAt: map[string]time.Time{},
		now:         time.Now,
	}
}

func runBinder(ctx context.Context, client kubernetes.Interface, dyn dynamic.Interface, interval time.Duration) error {
	b := newBinder(client, dyn)
	requestInformers := dynamicinformer.NewDynamicSharedInformerFactory(dyn, 10*time.Minute)
	b.requests = requestInformers.ForResource(bindRequestGVR).Lister()
	claimInformers := informers.NewSharedInformerFactory(client, 10*time.Minute)
	b.claims = claimInformers.Resource().V1().ResourceClaims().Lister()
	requestInformers.Start(ctx.Done())
	claimInformers.Start(ctx.Done())
	for typ, ok := range requestInformers.WaitForCacheSync(ctx.Done()) {
		if !ok {
			return fmt.Errorf("informer for %v did not sync", typ)
		}
	}
	for typ, ok := range claimInformers.WaitForCacheSync(ctx.Done()) {
		if !ok {
			return fmt.Errorf("informer for %v did not sync", typ)
		}
	}
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
	objects, err := b.requests.List(labels.Everything())
	if err != nil {
		return err
	}
	b.expireWritten()
	seen := map[string]bool{}
	for _, obj := range objects {
		item, ok := obj.(*unstructured.Unstructured)
		if !ok {
			continue
		}
		var br bindRequest
		if err := runtime.DefaultUnstructuredConverter.FromUnstructured(item.Object, &br); err != nil {
			klog.FromContext(ctx).Error(err, "malformed bind request", "name", item.GetName())
			continue
		}
		key := br.Namespace + "/" + br.Name
		seen[key] = true
		phase := phasePending
		if br.Status != nil && br.Status.Phase != "" {
			phase = br.Status.Phase
		}
		switch phase {
		case phasePending:
			b.process(ctx, &br)
		case phaseFailed:
			// Marked failed by the scheduler (bind timeout, gang cancelled) or left by a
			// rollback that did not finish: the scheduler deletes it once the claims are free.
			b.rollback(ctx, &br)
		case phaseSucceeded:
			b.deleteSucceeded(ctx, &br, key)
		}
	}
	for key := range b.succeededAt {
		if !seen[key] {
			delete(b.succeededAt, key)
		}
	}
	return nil
}

func (b *binder) process(ctx context.Context, br *bindRequest) {
	status := bindRequestStatus{Phase: phasePending}
	if br.Status != nil {
		status = *br.Status
		status.Phase = phasePending
	}
	if err := b.bind(ctx, br); err != nil {
		status.FailedAttempts++
		status.Reason = err.Error()
		if status.FailedAttempts > br.Spec.BackoffLimit {
			b.rollback(ctx, br)
			status.Phase = phaseFailed
		}
		klog.FromContext(ctx).Error(err, "bind failed", "pod", klog.KRef(br.Namespace, br.Spec.PodName), "attempts", status.FailedAttempts)
	} else {
		status = bindRequestStatus{Phase: phaseSucceeded, FailedAttempts: status.FailedAttempts}
		klog.FromContext(ctx).Info("pod bound", "pod", klog.KRef(br.Namespace, br.Spec.PodName), "node", br.Spec.SelectedNode)
	}
	if err := b.writeStatus(ctx, br, status); err != nil {
		klog.FromContext(ctx).Error(err, "bind request status not written", "name", br.Name)
	}
}

func (b *binder) deleteSucceeded(ctx context.Context, br *bindRequest, key string) {
	first, ok := b.succeededAt[key]
	if !ok {
		b.succeededAt[key] = b.now()
		return
	}
	if b.now().Sub(first) < succeededRetention {
		return
	}
	uid := br.UID
	err := b.dynamic.Resource(bindRequestGVR).Namespace(br.Namespace).Delete(
		ctx, br.Name, metav1.DeleteOptions{Preconditions: &metav1.Preconditions{UID: &uid}})
	if err != nil && !apierrors.IsNotFound(err) {
		klog.FromContext(ctx).Error(err, "succeeded bind request not deleted", "name", br.Name)
		return
	}
	delete(b.succeededAt, key)
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
		patch, err := json.Marshal([]map[string]any{{"op": "replace", "path": "/spec/schedulingGates", "value": gates}})
		if err != nil {
			return err
		}
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
	return retry.RetryOnConflict(retry.DefaultRetry, func() error {
		claim, err := claims.Get(ctx, ca.Name, metav1.GetOptions{})
		if err != nil {
			return err
		}
		changed := false
		if claim.Status.Allocation == nil {
			if err := b.checkConflicts(ns, ca); err != nil {
				return err
			}
			allocation := *ca.Allocation.DeepCopy()
			claim.Status.Allocation = &allocation
			changed = true
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
			changed = true
		}
		if !changed {
			return nil
		}
		updated, err := claims.UpdateStatus(ctx, claim, metav1.UpdateOptions{})
		if err != nil {
			return err
		}
		if b.written != nil {
			b.written[ns+"/"+ca.Name] = writtenAllocation{
				allocation:      *updated.Status.Allocation,
				uid:             updated.UID,
				resourceVersion: updated.ResourceVersion,
				at:              b.now(),
			}
		}
		return nil
	})
}

// checkConflicts refuses an allocation whose devices another claim already holds: a whole
// device held by anyone, or a share of a device held whole.
func (b *binder) checkConflicts(ns string, ca ClaimAllocation) error {
	self := ns + "/" + ca.Name
	held := map[string]*resourceapi.AllocationResult{}
	seen := map[string]*resourceapi.ResourceClaim{}
	if b.claims != nil {
		all, err := b.claims.List(labels.Everything())
		if err != nil {
			return err
		}
		for _, c := range all {
			seen[c.Namespace+"/"+c.Name] = c
			if c.Status.Allocation != nil {
				held[c.Namespace+"/"+c.Name] = c.Status.Allocation
			}
		}
	}
	for key, w := range b.written {
		if held[key] == nil && !b.informerCaughtUp(seen, key, w) {
			held[key] = &w.allocation
		}
	}
	for key, alloc := range held {
		if key == self {
			continue
		}
		for _, mine := range ca.Allocation.Devices.Results {
			for _, theirs := range alloc.Devices.Results {
				if deviceKey(mine) != deviceKey(theirs) {
					continue
				}
				if mine.ShareID == nil || theirs.ShareID == nil || *mine.ShareID == *theirs.ShareID {
					return fmt.Errorf("device %s of claim %s is held by claim %s", deviceKey(mine), ca.Name, key)
				}
			}
		}
	}
	return nil
}

// informerCaughtUp tells whether the claim informer already shows the claim at or past the
// write, so a missing allocation there means it was freed. A claim gone from the informer
// (deleted or recreated) no longer holds the write either.
func (b *binder) informerCaughtUp(seen map[string]*resourceapi.ResourceClaim, key string, w writtenAllocation) bool {
	if b.claims == nil {
		return false
	}
	c, ok := seen[key]
	if !ok || c.UID != w.uid {
		return true
	}
	current, err1 := strconv.ParseUint(c.ResourceVersion, 10, 64)
	written, err2 := strconv.ParseUint(w.resourceVersion, 10, 64)
	return err1 == nil && err2 == nil && current >= written
}

func (b *binder) expireWritten() {
	for key, w := range b.written {
		if b.now().Sub(w.at) > writtenRetention {
			delete(b.written, key)
		}
	}
}

func deviceKey(r resourceapi.DeviceRequestAllocationResult) string {
	return r.Driver + "/" + r.Pool + "/" + r.Device
}

// sameDevices compares the devices (and shares) of two allocations in any order.
func sameDevices(a, b *resourceapi.AllocationResult) bool {
	keys := func(alloc *resourceapi.AllocationResult) []string {
		out := make([]string, 0, len(alloc.Devices.Results))
		for _, r := range alloc.Devices.Results {
			share := ""
			if r.ShareID != nil {
				share = string(*r.ShareID)
			}
			out = append(out, deviceKey(r)+"#"+share)
		}
		sort.Strings(out)
		return out
	}
	return slices.Equal(keys(a), keys(b))
}

// rollback frees what this request wrote to its claims, unless its Pod is bound as asked: the
// Pod leaves the claims' reservations, and a claim nobody else reserves loses its allocation.
func (b *binder) rollback(ctx context.Context, br *bindRequest) {
	pod, err := b.client.CoreV1().Pods(br.Namespace).Get(ctx, br.Spec.PodName, metav1.GetOptions{})
	if err == nil && string(pod.UID) == br.Spec.PodUID && pod.Spec.NodeName == br.Spec.SelectedNode {
		return
	}
	if err != nil && !apierrors.IsNotFound(err) {
		klog.FromContext(ctx).Error(err, "pod of a failed bind request not read", "pod", klog.KRef(br.Namespace, br.Spec.PodName))
		return
	}
	claims := b.client.ResourceV1().ResourceClaims(br.Namespace)
	uid := types.UID(br.Spec.PodUID)
	for _, ca := range br.Spec.ResourceClaimAllocations {
		err := retry.RetryOnConflict(retry.DefaultRetry, func() error {
			claim, err := claims.Get(ctx, ca.Name, metav1.GetOptions{})
			if err != nil {
				return err
			}
			if claim.Status.Allocation == nil || !sameDevices(claim.Status.Allocation, &ca.Allocation) {
				return nil
			}
			reservedFor := slices.DeleteFunc(slices.Clone(claim.Status.ReservedFor), func(r resourceapi.ResourceClaimConsumerReference) bool {
				return r.UID == uid
			})
			if len(reservedFor) == len(claim.Status.ReservedFor) && len(reservedFor) > 0 {
				return nil
			}
			claim.Status.ReservedFor = reservedFor
			if len(reservedFor) == 0 {
				claim.Status.Allocation = nil
			}
			_, err = claims.UpdateStatus(ctx, claim, metav1.UpdateOptions{})
			return err
		})
		if apierrors.IsNotFound(err) {
			continue
		}
		if err != nil {
			klog.FromContext(ctx).Error(err, "claim rollback failed", "claim", klog.KRef(br.Namespace, ca.Name))
			continue
		}
		delete(b.written, br.Namespace+"/"+ca.Name)
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
