# Monitoring

The application Helm chart contains runnable Prometheus and Grafana Deployments,
configuration ConfigMaps, Services, provisioning and alert rules. Apply these values
to that chart; they are not values for a different upstream chart.

```powershell
helm upgrade campusdesk helm/campusdesk -n campusdesk -f helm/campusdesk/values-local.yaml -f monitoring/values-local.yaml --wait
```

The dashboard source is `helm/campusdesk/dashboards/campusdesk.json`. Prometheus uses
DNS discovery on the headless `backend-metrics` Service to collect per-replica metrics.
This lightweight deployment does not require the Prometheus Operator. The course's
ServiceMonitor approach is an alternative when the Operator is installed.

Open Prometheus Targets at `http://localhost:9090/targets`. Open Grafana at
`http://localhost:3001/d/campusdesk` and log in with the generated local admin password.
Generate real traffic using `python scripts/load.py --seconds 60` and inspect the panels.

Both monitoring servers keep local history in ephemeral volumes. All configuration
and dashboards are provisioned from the chart and re-created on redeployment.
