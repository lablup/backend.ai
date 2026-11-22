{{- define "backendai-cluster.image" -}}
{{- if .digest -}}
{{ .repository }}@{{ .digest }}
{{- else -}}
{{ .repository }}:{{ required "an image tag or digest is required" .tag }}
{{- end -}}
{{- end -}}

{{- define "backendai-cluster.labels" -}}
app.kubernetes.io/part-of: backendai
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "backendai-cluster.eventEnv" -}}
- {name: BACKENDAI_GATEWAY_ID, value: {{ required "cluster.agentId is required" .Values.cluster.agentId | quote }}}
- {name: BACKENDAI_VALKEY_ADDR, value: {{ required "controlPlane.valkey.addr is required" .Values.controlPlane.valkey.addr | quote }}}
{{- if .Values.controlPlane.valkey.passwordSecret.name }}
- name: BACKENDAI_VALKEY_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.controlPlane.valkey.passwordSecret.name }}
      key: {{ .Values.controlPlane.valkey.passwordSecret.key }}
{{- end }}
{{- end -}}

{{/* The cluster's GPU allocation policy (suggestion-1122 4.11), validated. */}}
{{- define "backendai-cluster.gpuAllocationPolicy" -}}
{{- $policy := .Values.gpuAllocationPolicy | default "dra" -}}
{{- if not (has $policy (list "dra" "device-plugin")) -}}
{{- fail (printf "gpuAllocationPolicy must be dra or device-plugin, not %q" $policy) -}}
{{- end -}}
{{- $policy -}}
{{- end -}}

{{- define "backendai-cluster.gpuPolicyEnv" -}}
- {name: BACKENDAI_GPU_ALLOCATION_POLICY, value: {{ include "backendai-cluster.gpuAllocationPolicy" . | quote }}}
{{- end -}}

{{/*
Replicas of a leader-elected component: (dict "root" $ "replicas" <component replicas>).
Without leader election only one replica may run.
*/}}
{{- define "backendai-cluster.replicas" -}}
{{- $le := .root.Values.leaderElection -}}
{{- if $le.enabled -}}
{{- .replicas | default $le.replicas -}}
{{- else if gt (int (.replicas | default 1)) 1 -}}
{{- fail "more than one replica needs leaderElection.enabled" -}}
{{- else -}}
1
{{- end -}}
{{- end -}}

{{/* Rollout of a leader-elected component: standbys take over, so replace one at a time. */}}
{{- define "backendai-cluster.strategy" -}}
{{- if .Values.leaderElection.enabled -}}
type: RollingUpdate
rollingUpdate: {maxSurge: 1, maxUnavailable: 0}
{{- else -}}
type: Recreate
{{- end -}}
{{- end -}}

{{/* A PodDisruptionBudget when more than one replica runs: (dict "root" $ "name" <app name> "replicas" <n>). */}}
{{- define "backendai-cluster.pdb" -}}
{{- if gt (int .replicas) 1 }}
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ .name }}
  namespace: {{ .root.Release.Namespace }}
  labels:
    {{- include "backendai-cluster.labels" .root | nindent 4 }}
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ .name }}
{{- end }}
{{- end -}}

{{/*
Node affinity of a bai-dra DaemonSet: the entry's affinity or nodeSelector, plus NotIn on the
labels of nodes whose GPUs another allocator owns. (dict "root" $ "driver" <baiDra.drivers entry>)
*/}}
{{- define "backendai-cluster.baiDraAffinity" -}}
{{- $exclude := list -}}
{{- range $key, $values := .root.Values.baiDra.excludeNodeLabels -}}
{{- $exclude = append $exclude (dict "key" $key "operator" "NotIn" "values" $values) -}}
{{- end -}}
{{- $affinity := deepCopy (.driver.affinity | default dict) -}}
{{- $nodeAffinity := $affinity.nodeAffinity | default dict -}}
{{- $required := $nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution | default dict -}}
{{- $terms := list -}}
{{- range ($required.nodeSelectorTerms | default (list dict)) -}}
{{- $exprs := concat (.matchExpressions | default list) $exclude -}}
{{- $terms = append $terms (merge (dict "matchExpressions" $exprs) (omit . "matchExpressions")) -}}
{{- end -}}
{{- $_ := set $required "nodeSelectorTerms" $terms -}}
{{- $_ = set $nodeAffinity "requiredDuringSchedulingIgnoredDuringExecution" $required -}}
{{- $_ = set $affinity "nodeAffinity" $nodeAffinity -}}
{{- toYaml $affinity -}}
{{- end -}}

{{/* Tolerations of a DaemonSet that serves session nodes: sokovan's dedicated taint, then `extra`. */}}
{{- define "backendai-cluster.sessionNodeTolerations" -}}
- {key: sokovan.backend.ai/dedicated, operator: Equal, value: "true", effect: NoSchedule}
{{- with .extra }}
{{ toYaml . }}
{{- end }}
{{- end }}
