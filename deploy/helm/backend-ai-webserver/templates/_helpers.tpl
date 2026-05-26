{{- define "bai-webserver.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-webserver.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "bai-webserver.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-webserver.labels" -}}
app.kubernetes.io/name: {{ include "bai-webserver.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "bai-webserver.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bai-webserver.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
