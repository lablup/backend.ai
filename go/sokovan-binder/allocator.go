package main

// The DRA allocator: the structured allocator of k8s.io/dynamic-resource-allocation over an
// informer snapshot, for the Pods of one gang in order. The caller's in-flight allocations
// (BindRequests not yet written to claims) arrive as `reserved`.

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	resourceapi "k8s.io/api/resource/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/util/sets"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	corelisters "k8s.io/client-go/listers/core/v1"
	resourcelisters "k8s.io/client-go/listers/resource/v1"
	"k8s.io/dynamic-resource-allocation/cel"
	"k8s.io/dynamic-resource-allocation/structured"
	"k8s.io/klog/v2"
)

type ClaimRef struct {
	Namespace string `json:"namespace"`
	Name      string `json:"name"`
}

type PodPlacement struct {
	Name   string     `json:"name"`
	Node   string     `json:"node"`
	Claims []ClaimRef `json:"claims"`
}

type AllocateRequest struct {
	Reserved []resourceapi.DeviceRequestAllocationResult `json:"reserved"`
	Pods     []PodPlacement                              `json:"pods"`
}

type ClaimAllocation struct {
	Name       string                       `json:"name"`
	Allocation resourceapi.AllocationResult `json:"allocation"`
}

type PodAllocations struct {
	Name        string            `json:"name"`
	Allocations []ClaimAllocation `json:"allocations"`
}

type AllocateResponse struct {
	Fits   bool             `json:"fits"`
	Reason string           `json:"reason,omitempty"`
	Pods   []PodAllocations `json:"pods,omitempty"`
}

type classLister struct {
	lister resourcelisters.DeviceClassLister
}

func (c classLister) List() ([]*resourceapi.DeviceClass, error) {
	return c.lister.List(labels.Everything())
}

func (c classLister) Get(name string) (*resourceapi.DeviceClass, error) {
	return c.lister.Get(name)
}

type allocator struct {
	nodes   corelisters.NodeLister
	slices  resourcelisters.ResourceSliceLister
	claims  resourcelisters.ResourceClaimLister
	classes classLister
	cel     *cel.Cache
}

func runAllocator(ctx context.Context, client kubernetes.Interface, listen string) error {
	factory := informers.NewSharedInformerFactory(client, 10*time.Minute)
	a := &allocator{
		nodes:   factory.Core().V1().Nodes().Lister(),
		slices:  factory.Resource().V1().ResourceSlices().Lister(),
		claims:  factory.Resource().V1().ResourceClaims().Lister(),
		classes: classLister{factory.Resource().V1().DeviceClasses().Lister()},
		cel:     cel.NewCache(100, cel.Features{EnableConsumableCapacity: true}),
	}
	factory.Start(ctx.Done())
	for typ, ok := range factory.WaitForCacheSync(ctx.Done()) {
		if !ok {
			return fmt.Errorf("informer for %v did not sync", typ)
		}
	}
	mux := http.NewServeMux()
	mux.HandleFunc("POST /v1/allocate", a.handle)
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusOK) })
	server := &http.Server{Addr: listen, Handler: mux}
	go func() {
		<-ctx.Done()
		_ = server.Close()
	}()
	klog.FromContext(ctx).Info("DRA allocator listening", "addr", listen)
	return server.ListenAndServe()
}

func (a *allocator) handle(w http.ResponseWriter, r *http.Request) {
	var req AllocateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	resp, err := a.allocate(r.Context(), &req)
	if err != nil {
		klog.FromContext(r.Context()).Error(err, "allocation failed")
		http.Error(w, err.Error(), http.StatusUnprocessableEntity)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(resp)
}

func (a *allocator) allocate(ctx context.Context, req *AllocateRequest) (*AllocateResponse, error) {
	requested := sets.New[string]()
	for _, p := range req.Pods {
		for _, c := range p.Claims {
			requested.Insert(c.Namespace + "/" + c.Name)
		}
	}
	state := structured.AllocatedState{
		AllocatedDevices:         sets.New[structured.DeviceID](),
		AllocatedSharedDeviceIDs: sets.New[structured.SharedDeviceID](),
		AggregatedCapacity:       structured.NewConsumedCapacityCollection(),
	}
	all, err := a.claims.List(labels.Everything())
	if err != nil {
		return nil, err
	}
	for _, c := range all {
		if c.Status.Allocation != nil && !requested.Has(c.Namespace+"/"+c.Name) {
			addAllocated(&state, c.Status.Allocation)
		}
	}
	for _, r := range req.Reserved {
		addResult(&state, r)
	}
	slices, err := a.slices.List(labels.Everything())
	if err != nil {
		return nil, err
	}
	resp := &AllocateResponse{Fits: true}
	for _, p := range req.Pods {
		node, err := a.nodes.Get(p.Node)
		if err != nil {
			return nil, err
		}
		var claims []*resourceapi.ResourceClaim
		for _, ref := range p.Claims {
			c, err := a.claims.ResourceClaims(ref.Namespace).Get(ref.Name)
			if err != nil {
				return nil, err
			}
			if c.Status.Allocation == nil {
				claims = append(claims, c.DeepCopy())
			}
		}
		out := PodAllocations{Name: p.Name}
		if len(claims) > 0 {
			alloc, err := structured.NewAllocator(ctx, allocatorFeatures, state, a.classes, slices, a.cel)
			if err != nil {
				return nil, err
			}
			results, err := alloc.Allocate(ctx, node, claims)
			if err != nil {
				return nil, err
			}
			if results == nil {
				return &AllocateResponse{Fits: false, Reason: fmt.Sprintf("devices for pod %s do not fit on node %s", p.Name, p.Node)}, nil
			}
			for i := range results {
				addAllocated(&state, &results[i])
				out.Allocations = append(out.Allocations, ClaimAllocation{Name: claims[i].Name, Allocation: results[i]})
			}
		}
		resp.Pods = append(resp.Pods, out)
	}
	return resp, nil
}

// The cluster runs with DRAConsumableCapacity: devices may be shared by capacity.
var allocatorFeatures = structured.Features{ConsumableCapacity: true}

func addAllocated(state *structured.AllocatedState, alloc *resourceapi.AllocationResult) {
	for _, r := range alloc.Devices.Results {
		addResult(state, r)
	}
}

// addResult marks a device used: whole, or one share of it with the capacity it consumes.
func addResult(state *structured.AllocatedState, r resourceapi.DeviceRequestAllocationResult) {
	id := structured.MakeDeviceID(r.Driver, r.Pool, r.Device)
	if r.ShareID == nil {
		state.AllocatedDevices.Insert(id)
		return
	}
	state.AllocatedSharedDeviceIDs.Insert(structured.MakeSharedDeviceID(id, r.ShareID))
	if len(r.ConsumedCapacity) > 0 {
		state.AggregatedCapacity.Insert(structured.NewDeviceConsumedCapacity(id, r.ConsumedCapacity))
	}
}
