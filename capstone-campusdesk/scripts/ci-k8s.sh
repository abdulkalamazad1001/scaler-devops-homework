#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
kind load docker-image "ghcr.io/abdulkalamazad1001/campusdesk-backend:$IMAGE_TAG" "ghcr.io/abdulkalamazad1001/campusdesk-frontend:$IMAGE_TAG" --name campusdesk-ci
kubectl apply -f k8s/namespace.yaml
# The chart generates campusdesk-db and campusdesk-grafana (secrets.create defaults to true).
helm upgrade --install campusdesk helm/campusdesk -n campusdesk \
  --set backend.tag="$IMAGE_TAG" --set frontend.tag="$IMAGE_TAG" \
  --set autoscaling.enabled=false --set ingress.enabled=false \
  --wait --wait-for-jobs --timeout 8m
kubectl -n campusdesk run smoke --restart=Never --image=curlimages/curl:8.12.1 \
  --command -- sh -ec 'curl --fail --retry 10 http://backend:8000/ready && curl --fail http://frontend:8080/api/tickets && curl --fail http://prometheus:9090/-/ready'
kubectl -n campusdesk wait --for=jsonpath='{.status.phase}'=Succeeded pod/smoke --timeout=120s
kubectl -n campusdesk logs smoke
