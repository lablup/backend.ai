//go:build integration

package integration

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"testing"
)

const resourcePolicyPath = "/v2/resource-policies"

type object = map[string]any

// policyKind describes one of the three resource policy kinds: the fields it
// is created with, the fields an update changes, and what the server returns.
type policyKind struct {
	name       string
	payloadKey string
	create     object
	created    object
	update     object
	updated    object
}

var policyKinds = []policyKind{
	{
		name:       "keypair",
		payloadKey: "keypair_resource_policy",
		create: object{
			"default_for_unspecified":      "LIMITED",
			"total_resource_slots":         []object{{"resource_type": "cpu", "quantity": "4"}},
			"max_session_lifetime":         3600,
			"max_concurrent_sessions":      2,
			"max_concurrent_sftp_sessions": 1,
			"max_containers_per_session":   1,
			"idle_timeout":                 600,
			"allowed_vfolder_hosts":        []object{},
		},
		created: object{
			"default_for_unspecified": "LIMITED",
			"max_session_lifetime":    3600.0,
			"max_concurrent_sessions": 2.0,
			"idle_timeout":            600.0,
		},
		update:  object{"max_session_lifetime": 7200, "idle_timeout": 900},
		updated: object{"max_session_lifetime": 7200.0, "idle_timeout": 900.0},
	},
	{
		name:       "user",
		payloadKey: "user_resource_policy",
		create: object{
			"max_vfolder_count":                   10,
			"max_quota_scope_size":                object{"expr": "1g"},
			"max_session_count_per_model_session": 1,
			"max_customized_image_count":          1,
		},
		created: object{
			"max_vfolder_count":          10.0,
			"max_quota_scope_size":       object{"expr": "1073741824"},
			"max_customized_image_count": 1.0,
		},
		update:  object{"max_vfolder_count": 20, "max_customized_image_count": 3},
		updated: object{"max_vfolder_count": 20.0, "max_customized_image_count": 3.0},
	},
	{
		name:       "project",
		payloadKey: "project_resource_policy",
		create: object{
			"max_vfolder_count":    5,
			"max_quota_scope_size": object{"expr": "1g"},
			"max_network_count":    2,
		},
		created: object{
			"max_vfolder_count":    5.0,
			"max_quota_scope_size": object{"expr": "1073741824"},
			"max_network_count":    2.0,
		},
		update:  object{"max_network_count": 7},
		updated: object{"max_network_count": 7.0, "max_vfolder_count": 5.0},
	},
}

// assertSubset fails the test for each field of want that got does not hold.
// A nested object in want is compared as a subset too.
func assertSubset(t *testing.T, got, want object, where string) {
	t.Helper()
	for key, wantValue := range want {
		gotValue, ok := got[key]
		if !ok {
			t.Errorf("%s: field %q is missing", where, key)
			continue
		}
		if wantObject, isObject := wantValue.(object); isObject {
			gotObject, ok := gotValue.(object)
			if !ok {
				t.Errorf("%s.%s: want an object, got %v", where, key, gotValue)
				continue
			}
			assertSubset(t, gotObject, wantObject, where+"."+key)
			continue
		}
		if !jsonEqual(gotValue, wantValue) {
			t.Errorf("%s.%s: want %v, got %v", where, key, wantValue, gotValue)
		}
	}
}

// jsonEqual compares two values by their JSON encoding.
func jsonEqual(a, b any) bool {
	rawA, errA := json.Marshal(a)
	rawB, errB := json.Marshal(b)
	return errA == nil && errB == nil && string(rawA) == string(rawB)
}

func isStatus(err error, status int) bool {
	var apiErr *apiError
	return errors.As(err, &apiErr) && apiErr.Status == status
}

// createPolicy creates a policy named prefix+kind and registers its purge.
// It returns the node of the response.
func createPolicy(t *testing.T, c *client, kind policyKind, prefix string) object {
	t.Helper()
	name := prefix + kind.name
	body := object{"name": name}
	for key, value := range kind.create {
		body[key] = value
	}
	var created map[string]object
	path := resourcePolicyPath + "/" + kind.name
	if err := c.do(t.Context(), http.MethodPost, path, body, &created); err != nil {
		t.Fatalf("create %s policy: %v", kind.name, err)
	}
	node := created[kind.payloadKey]
	entityID, _ := node["entity_id"].(string)
	if entityID == "" {
		t.Fatalf("create %s policy: no entity_id in %v", kind.name, created)
	}
	t.Cleanup(func() {
		ctx, cancel := context.WithTimeout(context.Background(), requestTimeout)
		defer cancel()
		err := c.do(ctx, http.MethodDelete, path+"/"+entityID, nil, nil)
		if err != nil && !isStatus(err, http.StatusNotFound) {
			t.Errorf("purge %s policy %s: %v", kind.name, name, err)
		}
	})
	return node
}

func TestResourcePolicyREST(t *testing.T) {
	c := newClient(t)
	for _, kind := range policyKinds {
		t.Run(kind.name, func(t *testing.T) {
			ctx := t.Context()
			path := resourcePolicyPath + "/" + kind.name
			prefix := newPrefix(t)
			name := prefix + kind.name

			// create
			node := createPolicy(t, c, kind, prefix)
			assertSubset(t, node, object{"name": name}, "create")
			assertSubset(t, node, kind.created, "create")
			entityID, _ := node["entity_id"].(string)

			// get
			var got object
			if err := c.do(ctx, http.MethodGet, path+"/"+name, nil, &got); err != nil {
				t.Fatalf("get: %v", err)
			}
			assertSubset(t, got, object{"name": name, "entity_id": entityID}, "get")
			assertSubset(t, got, kind.created, "get")

			// search
			var found struct {
				Items      []object `json:"items"`
				TotalCount int      `json:"total_count"`
			}
			search := object{"filter": object{"name": object{"equals": name}}}
			if err := c.do(ctx, http.MethodPost, path+"/search", search, &found); err != nil {
				t.Fatalf("search: %v", err)
			}
			if found.TotalCount != 1 || len(found.Items) != 1 {
				t.Fatalf("search: want one policy named %s, got %d (%d items)", name, found.TotalCount, len(found.Items))
			}
			assertSubset(t, found.Items[0], object{"name": name, "entity_id": entityID}, "search")

			// update
			var updated map[string]object
			if err := c.do(ctx, http.MethodPatch, path+"/"+entityID, kind.update, &updated); err != nil {
				t.Fatalf("update: %v", err)
			}
			assertSubset(t, updated[kind.payloadKey], kind.updated, "update")
			var reread object
			if err := c.do(ctx, http.MethodGet, path+"/"+name, nil, &reread); err != nil {
				t.Fatalf("get after update: %v", err)
			}
			assertSubset(t, reread, kind.updated, "get after update")

			// delete (purge)
			var purged object
			if err := c.do(ctx, http.MethodDelete, path+"/"+entityID, nil, &purged); err != nil {
				t.Fatalf("purge: %v", err)
			}
			assertSubset(t, purged, object{"name": name, "entity_id": entityID}, "purge")
			err := c.do(ctx, http.MethodGet, path+"/"+name, nil, nil)
			if !isStatus(err, http.StatusNotFound) {
				t.Errorf("get after purge: want status 404, got %v", err)
			}
		})
	}
}

const keypairPoliciesQuery = `
query ($filter: KeypairResourcePolicyV2Filter) {
  adminKeypairResourcePoliciesV2(filter: $filter) {
    count
    edges { node { name maxSessionLifetime idleTimeout } }
  }
}`

func TestResourcePolicyGraphQLSearch(t *testing.T) {
	c := newClient(t)
	kind := policyKinds[0]
	prefix := newPrefix(t)
	createPolicy(t, c, kind, prefix)
	name := prefix + kind.name

	variables := object{"filter": object{"name": object{"equals": name}}}
	data, err := c.graphQL(t.Context(), keypairPoliciesQuery, variables)
	if err != nil {
		t.Fatalf("search: %v", err)
	}
	var result struct {
		Policies struct {
			Count int `json:"count"`
			Edges []struct {
				Node object `json:"node"`
			} `json:"edges"`
		} `json:"adminKeypairResourcePoliciesV2"`
	}
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatalf("decode %s: %v", data, err)
	}
	if result.Policies.Count != 1 || len(result.Policies.Edges) != 1 {
		t.Fatalf("want one policy named %s, got %s", name, data)
	}
	assertSubset(t, result.Policies.Edges[0].Node, object{
		"name":               name,
		"maxSessionLifetime": 3600.0,
		"idleTimeout":        600.0,
	}, "graphql search")
}
