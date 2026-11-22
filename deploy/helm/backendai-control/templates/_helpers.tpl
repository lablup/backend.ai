{{- define "backendai-control.labels" -}}
app.kubernetes.io/part-of: backendai
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/* repository@digest when a digest is set, repository:tag otherwise; never a floating tag */}}
{{- define "backendai-control.image" -}}
{{- if .digest }}{{ .repository }}@{{ .digest }}{{ else }}{{ .repository }}:{{ required "an image tag or digest is required" .tag }}{{ end }}
{{- end }}
