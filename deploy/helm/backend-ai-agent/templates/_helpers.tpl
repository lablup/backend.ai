{{- define "bai-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-agent.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "bai-agent.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-agent.labels" -}}
app.kubernetes.io/name: {{ include "bai-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "bai-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bai-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
