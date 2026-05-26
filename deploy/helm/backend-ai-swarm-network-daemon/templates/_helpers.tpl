{{- define "bai-swarm-net.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-swarm-net.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "bai-swarm-net.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-swarm-net.labels" -}}
app.kubernetes.io/name: {{ include "bai-swarm-net.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "bai-swarm-net.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bai-swarm-net.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
