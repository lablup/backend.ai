{{- define "bai-apollo-router.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-apollo-router.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "bai-apollo-router.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-apollo-router.labels" -}}
app.kubernetes.io/name: {{ include "bai-apollo-router.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "bai-apollo-router.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bai-apollo-router.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
