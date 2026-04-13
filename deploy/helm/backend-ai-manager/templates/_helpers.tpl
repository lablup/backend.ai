{{- define "bai-manager.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-manager.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "bai-manager.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "bai-manager.labels" -}}
app.kubernetes.io/name: {{ include "bai-manager.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "bai-manager.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bai-manager.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Subchart service DNS — assumes default Bitnami chart fullnames. */}}
{{- define "bai-manager.postgresHost" -}}
{{- printf "%s-postgresql-ha-pgpool" .Release.Name -}}
{{- end -}}

{{- define "bai-manager.redisSentinelHost" -}}
{{- printf "%s-redis" .Release.Name -}}
{{- end -}}

{{- define "bai-manager.etcdHost" -}}
{{- printf "%s-etcd" .Release.Name -}}
{{- end -}}
