#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
kind load docker-image "ghcr.io/abdulkalamazad1001/campusdesk-backend:$IMAGE_TAG" "ghcr.io/abdulkalamazad1001/campusdesk-frontend:$IMAGE_TAG" --name campusdesk-ci
kubectl apply -f k8s/namespace.yaml
password="$(openssl rand -hex 20)"
kubectl -n campusdesk create secret generic campusdesk-db \
  --from-literal=POSTGRES_DB=campusdesk --from-literal=POSTGRES_USER=campusdesk \
  --from-literal="POSTGRES_PASSWORD=$password" \
  --from-literal="DATABASE_URL=postgresql+psycopg://campusdesk:$password@postgres:5432/campusdesk"
kubectl -n campusdesk create secret generic campusdesk-grafana --from-literal="password=$(openssl rand -hex 20)"
helm upgrade --install campusdesk helm/campusdesk -n campusdesk \
  --set backend.tag="$IMAGE_TAG" --set frontend.tag="$IMAGE_TAG" \
  --set autoscaling.enabled=false --set ingress.enabled=false \
  --wait --wait-for-jobs --timeout 8m
kubectl -n campusdesk run smoke --restart=Never --image=curlimages/curl:8.12.1 \
  --command -- sh -ec 'curl --fail --retry 10 http://backend:8000/ready && curl --fail http://frontend:8080/api/tickets && curl --fail http://prometheus:9090/-/ready'
kubectl -n campusdesk wait --for=jsonpath='{.status.phase}'=Succeeded pod/smoke --timeout=120s
kubectl -n campusdesk logs smoke
