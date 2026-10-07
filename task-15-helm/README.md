# Task 15: Helm

The full write-up with every command and its output is in [`submission.md`](submission.md).

## What is here

```text
task-15-helm/
├── README.md
├── submission.md            write-up: Helm commands, rollback workflow, mini project
└── notes-chart/             the mini-project chart
    ├── Chart.yaml
    ├── values.yaml          dev defaults: 1 replica, nginx:1.24, NodePort 30090
    ├── values-prod.yaml     prod overrides: 3 replicas, nginx:1.25, NodePort 30091
    └── templates/
        ├── _helpers.tpl
        ├── configmap.yaml   env vars + the index.html page
        ├── deployment.yaml
        ├── service.yaml
        ├── NOTES.txt
        └── tests/test-connection.yaml
```

## Quick start (minikube)

```bash
helm lint notes-chart
helm install notes ./notes-chart                                   # revision 1 (dev)
helm upgrade notes ./notes-chart -f notes-chart/values-prod.yaml   # revision 2 (prod)
curl http://$(minikube ip):30091
helm test notes

helm upgrade notes ./notes-chart -f notes-chart/values-prod.yaml --set image.tag=doesnotexist   # revision 3 (broken)
helm rollback notes 2                                              # revision 4 = copy of 2
helm history notes

helm uninstall notes
```

## Sections in submission.md

1. Task 1: hands-on with `helm create`, `install`, `list`, `status`, `get`, `upgrade`,
   `history`, `rollback`, `uninstall`, `repo` and `search`
2. Task 2: install, upgrade, verify, bad upgrade, verify, rollback, verify, with
   `helm history` and `kubectl` checks of image and replica count
3. Task 3: the notes-chart mini project (lint, template, dev and prod installs, `helm test`,
   rollback, clean up)
