{{/* Base name for every object: "<release>" if it already contains the chart name, else "<release>-taskboard". */}}
{{- define "taskboard.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 50 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 50 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "taskboard.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: taskboard
{{- end -}}

{{/* Selector labels. Call with (dict "ctx" $ "component" "backend"). */}}
{{- define "taskboard.selectorLabels" -}}
app.kubernetes.io/name: {{ .ctx.Chart.Name }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "taskboard.secretName" -}}
{{- default (printf "%s-db" (include "taskboard.fullname" .)) .Values.database.existingSecret -}}
{{- end -}}

{{- define "taskboard.dbHost" -}}
{{- default (printf "%s-postgres" (include "taskboard.fullname" .)) .Values.postgres.host -}}
{{- end -}}

{{- define "taskboard.image" -}}
{{- printf "%s/%s:%s" .ctx.Values.image.registry .repository (toString .ctx.Values.image.tag) -}}
{{- end -}}

{{- define "taskboard.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "taskboard.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop: ["ALL"]
{{- end -}}
