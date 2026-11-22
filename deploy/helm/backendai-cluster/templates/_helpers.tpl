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
