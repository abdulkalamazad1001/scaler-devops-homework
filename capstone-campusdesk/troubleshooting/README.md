# Troubleshooting Demonstration

These exercises use separate demo objects and do not break the real backend.

## ImagePullBackOff

```powershell
kubectl --context kind-campusdesk apply -f troubleshooting/broken-image.yaml
kubectl --context kind-campusdesk -n campusdesk get pods -l app=broken-image-demo
kubectl --context kind-campusdesk -n campusdesk describe deployment broken-image-demo
kubectl --context kind-campusdesk -n campusdesk get events --sort-by=.lastTimestamp
```

The deliberately nonexistent image tag cannot be pulled. Inspect the pod's events
to identify the exact image error. Fix it with a known image, verify rollout, then
remove only the demo Deployment:

```powershell
kubectl --context kind-campusdesk -n campusdesk set image deployment/broken-image-demo demo=nginx:stable-alpine
kubectl --context kind-campusdesk -n campusdesk rollout status deployment/broken-image-demo --timeout=180s
kubectl --context kind-campusdesk -n campusdesk delete deployment broken-image-demo
```

## Service Has No Endpoints

```powershell
kubectl --context kind-campusdesk apply -f troubleshooting/broken-service.yaml
kubectl --context kind-campusdesk -n campusdesk get endpointslices -l kubernetes.io/service-name=broken-backend-demo
kubectl --context kind-campusdesk -n campusdesk get pods --show-labels
```

Compare the Service selector `app=nonexistent-backend` with the real `app=backend`
labels. Correct the selector and check that endpoint addresses appear, then remove
the demo Service:

```powershell
kubectl --context kind-campusdesk -n campusdesk set selector service/broken-backend-demo app=backend
kubectl --context kind-campusdesk -n campusdesk get endpointslices -l kubernetes.io/service-name=broken-backend-demo
kubectl --context kind-campusdesk -n campusdesk delete service broken-backend-demo
```

## Database Or Migration Failure

Use `kubectl logs job/campusdesk-migrate-<revision> -n campusdesk`, PostgreSQL pod
logs and PVC events. A healthy process is insufficient: `/ready` returns 503 when
the database or schema is unavailable, preventing traffic to an unready backend.

## Helm Recovery

Inspect `helm history campusdesk -n campusdesk` and `kubectl rollout status`.
`helm rollback campusdesk <revision> -n campusdesk --wait` restores chart configuration,
but does not automatically reverse a database migration. Backward-compatible schema
changes and backups are required for dependable application rollback.
