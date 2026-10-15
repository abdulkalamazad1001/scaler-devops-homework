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

## Running But Not Ready

```powershell
.venv/Scripts/python scripts/readiness-check.py
```

This exercise creates a uniquely named disposable namespace in `kind-campusdesk`,
using the published backend image without database credentials. It changes only
the demo Deployment, not the real CampusDesk services or Argo-managed workloads.

1. An intentionally wrong `/missing-probe` readiness path returns HTTP 404.
2. The script inspects pod status, events, logs and EndpointSlices. The process is
   Running but NotReady; no ready endpoint can receive Service traffic.
3. A direct `/health` request succeeds, isolating the problem to probe configuration.
4. Correcting the demo probe to `/health` makes the new pod Ready. A request through
   its Service then succeeds, and the script deletes its own namespace.

Real command output is saved in `evidence/readiness-troubleshooting.txt`, including
cleanup. This tests process readiness routing only; the real application continues
to use `/ready` with database/schema checks. Do not replace that production probe
with `/health`. A failed readiness check removes traffic; it does not itself restart
a container, unlike a failed liveness check.

## Helm Recovery

Inspect `helm history campusdesk -n campusdesk` and `kubectl rollout status`.
`helm rollback campusdesk <revision> -n campusdesk --wait` restores chart configuration,
but does not automatically reverse a database migration. Backward-compatible schema
changes and backups are required for dependable application rollback.
