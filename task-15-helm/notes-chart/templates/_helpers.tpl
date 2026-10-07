{{/*
Chart name and version, used in the helm.sh/chart label.
*/}}
{{- define "notes-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Selector labels. These go on the pod template and the Service selector,
so they must never change between upgrades.
*/}}
{{- define "notes-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common labels for every object.
*/}}
{{- define "notes-chart.labels" -}}
helm.sh/chart: {{ include "notes-chart.chart" . }}
{{ include "notes-chart.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
environment: {{ .Values.app.environment }}
{{- end }}
