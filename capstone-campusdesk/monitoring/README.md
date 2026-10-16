# Monitoring

The backend exposes Prometheus text metrics at `/metrics` (for example
`campusdesk_http_requests_total` and `campusdesk_http_request_duration_seconds`). The app
chart always renders the headless `backend-metrics` Service so Prometheus can scrape every
backend replica individually. Through the Ingress, `http://campusdesk.localhost:8088/metrics`
reaches the backend (`ingress.exposeMetrics`, default `true`).

There are two ways to run Prometheus and Grafana:

| Option | Files | Used by |
| --- | --- | --- |
| Community Helm charts (submission values) | `prometheus-values.yaml`, `grafana-values.yaml`, `values-community.yaml` | Namespace `monitoring` |
| Built-in Deployments in the app chart | `values-local.yaml`, `values-aws.yaml` (app-chart overlays) | Argo CD-managed `campusdesk` namespace |

## Community charts (prometheus-community/prometheus + Grafana)

Tested with `prometheus-community/prometheus` 29.37.0 (Prometheus v3.15.0) and
`grafana-community/grafana` 14.0.0 (Grafana 13.2.4) on the local kind cluster. The
`grafana/grafana` chart in `https://grafana.github.io/helm-charts` is deprecated and was
moved to `grafana-community`. The same values also render with `grafana/grafana` 10.5.15.

Run these commands from `capstone-campusdesk/`:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo update

# Grafana admin Secret (keys: user, password) and the dashboard ConfigMap, built from the
# single dashboard source helm/campusdesk/dashboards/campusdesk.json.
kubectl create namespace monitoring
kubectl -n monitoring create secret generic campusdesk-grafana \
  --from-literal=user=admin --from-literal="password=$(openssl rand -hex 20)"
kubectl -n monitoring create configmap campusdesk-dashboard \
  --from-file=campusdesk.json=helm/campusdesk/dashboards/campusdesk.json

helm upgrade --install prometheus prometheus-community/prometheus --version 29.37.0 \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml --wait
helm upgrade --install grafana grafana-community/grafana --version 14.0.0 \
  -n monitoring -f monitoring/grafana-values.yaml --wait
```

When CampusDesk is deployed with Helm and only the community stack is wanted, remove the
built-in Prometheus and Grafana with `-f monitoring/values-community.yaml`
(`monitoring.enabled=false`). The `backend-metrics` Service stays. The Argo CD-managed
local deployment keeps the built-in stack, so both can run side by side.

Prometheus runs without the Operator or CRDs. Alertmanager, Pushgateway, node-exporter and
kube-state-metrics are disabled. The `campusdesk` job uses `kubernetes_sd_configs`
(endpoints in namespace `campusdesk`, filtered to the `backend-metrics` Service) and adds
`namespace` and `pod` labels. The chart also loads the same two alert rules as the
built-in stack.

### Verify

```bash
kubectl -n monitoring get pods,svc
kubectl -n monitoring port-forward svc/prometheus-server 9091:80   # terminal 1
kubectl -n monitoring port-forward svc/grafana 3002:80             # terminal 2

# Each backend replica appears as an UP target in job "campusdesk".
curl -s 'http://127.0.0.1:9091/api/v1/targets?state=active'
curl -s 'http://127.0.0.1:9091/api/v1/query' --data-urlencode 'query=sum by (pod) (campusdesk_http_requests_total)'
curl -s http://127.0.0.1:3002/api/health
kubectl -n monitoring get secret campusdesk-grafana -o jsonpath='{.data.password}' | base64 -d
```

Open Prometheus targets at `http://127.0.0.1:9091/targets`. Open Grafana at
`http://127.0.0.1:3002/d/campusdesk` and log in as `admin` with the password above. The
dashboard is in the `CampusDesk` folder. Grafana's Service is a NodePort (30301), but
`k8s/kind.yaml` maps only 30300 and 30900 to the host, so use the port-forward on kind.
Generate traffic using `python scripts/load.py --seconds 60` and inspect the panels.

Remove the community stack with
`helm uninstall grafana prometheus -n monitoring && kubectl delete namespace monitoring`.

## Built-in stack (app chart)

The app chart also contains runnable Prometheus and Grafana Deployments, configuration
ConfigMaps, Services, provisioning and alert rules (`monitoring.enabled`, default `true`).
`values-local.yaml` and `values-aws.yaml` in this folder are overlays for that chart, not
for an upstream chart. The local bootstrap already enables it. The following Helm command
is only for the Helm-managed phase, before Argo CD adoption:

```powershell
helm upgrade campusdesk helm/campusdesk -n campusdesk --kube-context kind-campusdesk -f helm/campusdesk/values-local.yaml -f monitoring/values-local.yaml --wait
```

Once Argo CD owns CampusDesk, change the tracked Helm values in Git instead. Do not
run a second deployment owner against the same resources.

The built-in Prometheus uses DNS discovery on `backend-metrics`. Open Prometheus Targets
at `http://localhost:9090/targets`. Open Grafana at `http://localhost:3001/d/campusdesk`
and log in with the generated local admin password (`scripts/grafana-password.ps1`).

Both stacks keep metric history in ephemeral volumes. All configuration and dashboards are
provisioned from Git and re-created on redeployment.
