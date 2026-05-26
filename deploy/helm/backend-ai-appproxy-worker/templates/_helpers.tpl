{{- define "bai-appproxy-worker.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-appproxy-worker.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "bai-appproxy-worker.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-appproxy-worker.labels" -}}
app.kubernetes.io/name: {{ include "bai-appproxy-worker.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "bai-appproxy-worker.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bai-appproxy-worker.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
