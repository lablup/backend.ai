{{- define "backendai-control.labels" -}}
app.kubernetes.io/part-of: backendai
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/* repository@digest when a digest is set, repository:tag otherwise */}}
{{- define "backendai-control.image" -}}
{{- if .digest }}{{ .repository }}@{{ .digest }}{{ else }}{{ .repository }}:{{ .tag | default "latest" }}{{ end }}
{{- end }}
