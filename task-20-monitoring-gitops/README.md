# Task 20: Monitoring, Observability and GitOps

> **Note:** Command output in this file is representative expected output for the lab environment
> below, written as a learning reference. It was not captured from a live run, so IDs, timestamps
> and pod name hashes will differ when you run it yourself.

The full write-up with every command and its output is in [submission.md](submission.md).
Lab environment: minikube v1.34.0 (Kubernetes v1.31.0, 2 CPU / 4096 MB), Helm v3.16.2,
kube-prometheus-stack 65.1.1, loki-stack 2.10.2, Argo CD v2.12.4.

## What is in here

| Part | Where | Summary |
|---|---|---|
| Monitoring demo | [monitoring/](monitoring/), submission.md Task 1 | Flask app with `/metrics`, `/health`, `/ready`. Prometheus, Alertmanager, Grafana, node-exporter and kube-state-metrics from kube-prometheus-stack, Loki + Promtail for logs. ServiceMonitor, PrometheusRule (CPU, memory, error rate, target down, unavailable replicas), Grafana dashboard as a ConfigMap, webhook alert receiver |
| Observability doc | submission.md Task 2 | Metrics, logs and traces, why observability is needed, common tools, observability in Kubernetes |
| GitOps demo | [gitops/](gitops/), submission.md Task 3 | Argo CD Application that syncs [gitops/manifests/](gitops/manifests/) from Git, a change deployed by commit, drift reverted by self-heal, app history |

## Run it

Monitoring (from this folder, on a running minikube):

```bash
minikube addons enable metrics-server
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --version 65.1.1 -n monitoring --create-namespace -f monitoring/helm-values/kube-prometheus-stack-values.yaml
helm upgrade --install loki grafana/loki-stack --version 2.10.2 \
  -n monitoring -f monitoring/helm-values/loki-stack-values.yaml

minikube image build -t metrics-demo:1.0 monitoring/app
kubectl apply -f monitoring/k8s/
kubectl apply -f monitoring/grafana/

# check the alert rules locally
promtool check rules monitoring/rules/metrics-demo-rules.yaml
(cd monitoring/rules && promtool test rules metrics-demo-rules.test.yaml)
```

GitOps:

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.12.4/manifests/install.yaml
# edit repoURL in gitops/argocd/application.yaml if your fork lives elsewhere
kubectl apply -f gitops/argocd/application.yaml
argocd app get gitops-demo
```
