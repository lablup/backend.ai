{{- define "bai-storage-proxy.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-storage-proxy.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "bai-storage-proxy.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-storage-proxy.labels" -}}
app.kubernetes.io/name: {{ include "bai-storage-proxy.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "bai-storage-proxy.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bai-storage-proxy.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
