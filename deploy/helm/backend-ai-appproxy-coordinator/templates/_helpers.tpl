{{- define "bai-appproxy-coordinator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-appproxy-coordinator.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "bai-appproxy-coordinator.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-appproxy-coordinator.labels" -}}
app.kubernetes.io/name: {{ include "bai-appproxy-coordinator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "bai-appproxy-coordinator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bai-appproxy-coordinator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
