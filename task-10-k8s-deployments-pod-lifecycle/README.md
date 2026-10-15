# Deployments and Pod Lifecycle

Student: T. Abdul Kalam Azad, 24BCS10053.

## Deliverables

| Lab | Files | Purpose |
|---|---|---|
| Rolling update | [01-rolling-update](deployment-strategies/01-rolling-update/) | Update v1 to v2 and roll back |
| Blue/green | [02-blue-green](deployment-strategies/02-blue-green/) | Switch the Service selector between versions |
| Canary | [03-canary](deployment-strategies/03-canary/) | Route to nine stable and one canary replica |
| Recreate | [04-recreate](deployment-strategies/04-recreate/) | Replace old Pods before starting the new version |
| Pod lifecycle | [pod-lifecycle](pod-lifecycle/) | Phases, failure states, init containers, hooks, restart policies and liveness |

## Run and Verify

Prerequisites: `kubectl`, a disposable cluster, and enough capacity for the listed
replicas. Apply one deployment version at a time, not both YAML files together.
The lifecycle directory deliberately includes broken and failing Pods.

From the repository root, the isolated regression runner checks updates, rollback,
NodePort traffic, canary responses and lifecycle states, then deletes its namespaces:

```bash
python -m pip install PyYAML==6.0.3
python review/check_lab_scenarios.py --context kind-campusdesk --suite deployments
```

Use your own local context name when different. A successful traffic check does
not by itself measure zero downtime or prove an exact 90/10 request distribution.

## Evidence

- [Assignment write-up and commands](submission.md)
- [Current verification results and remaining work](../review/README.md)

The output and terminal-style images in the original write-up are labelled expected
output, not captures from a live deployment. Current test logs are kept separately
under the project review. Validation alone does not prove every exercise was run.
