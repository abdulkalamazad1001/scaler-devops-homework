# Troubleshooting lab: broken changes

Each file breaks one thing in the running TaskBoard deployment (namespace `taskboard`,
release `taskboard`). The full walk-through (symptom, investigation, root cause, fix,
verification, before/after output) is in the project README, section "Troubleshooting".

Pause Argo CD first, otherwise self-heal reverts patches 1, 2, 3, 5 and 6 within seconds:

    argocd app set taskboard --sync-policy none

| # | File | Apply with | Breaks |
|---|---|---|---|
| 1 | 01-wrong-image-tag.yaml | `kubectl -n taskboard patch deployment taskboard-backend --patch-file 01-wrong-image-tag.yaml` | image tag typo, ImagePullBackOff |
| 2 | 02-bad-readiness-path.yaml | `kubectl -n taskboard patch deployment taskboard-backend --patch-file 02-bad-readiness-path.yaml` | readiness probe 404, rollout stuck |
| 3 | 03-service-selector-mismatch.yaml | `kubectl -n taskboard patch service taskboard-backend --patch-file 03-service-selector-mismatch.yaml` | Service has no endpoints, 502 |
| 4 | 04-secret-wrong-key.yaml | `kubectl replace -f 04-secret-wrong-key.yaml` then `kubectl -n taskboard rollout restart deployment taskboard-backend` | CreateContainerConfigError |
| 5 | 05-hpa-no-requests.json | `kubectl -n taskboard patch deployment taskboard-backend --type json --patch-file 05-hpa-no-requests.json` | HPA shows `<unknown>` |
| 6 | 06-ingress-wrong-port.json | `kubectl -n taskboard patch ingress taskboard --type json --patch-file 06-ingress-wrong-port.json` | /api returns 503 |

Turn Argo CD back on afterwards; anything left behind is reverted to Git:

    argocd app set taskboard --sync-policy automated --self-heal --auto-prune
