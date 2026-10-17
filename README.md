# Scaler DevOps Homework

**T. Abdul Kalam Azad | 24BCS10053**

GitHub: [abdulkalamazad1001](https://github.com/abdulkalamazad1001)

Course assignments covering Linux, Git, Docker, Kubernetes, Helm, CI/CD,
DevSecOps, Terraform and monitoring. **CampusDesk** is the original capstone;
the numbered directories contain the individual assignments and lab references.

## CampusDesk

A campus IT helpdesk built with React, FastAPI and PostgreSQL. The delivery stack
includes Docker, GitHub Actions, Helm, Argo CD, Prometheus and Grafana, with
Terraform configuration for AWS VPC/EKS.

| Deliverable | Location |
|---|---|
| Application, architecture and setup | [Current CampusDesk README](https://github.com/abdulkalamazad1001/campusdesk-devops-capstone) |
| Submission status by rubric module | [Current submission checklist](https://github.com/abdulkalamazad1001/campusdesk-devops-capstone/blob/main/SUBMISSION.md) |
| Detailed requirements and evidence | [Final audit](https://github.com/abdulkalamazad1001/campusdesk-devops-capstone/blob/main/FINAL-AUDIT.md) |
| Screenshots and test reports | [Verified evidence](https://github.com/abdulkalamazad1001/campusdesk-devops-capstone/tree/main/evidence/2026-10-17) |
| AWS provisioning and cleanup instructions | [Terraform runbook](capstone-campusdesk/terraform/README.md) |
| Presentation and videos | [12-slide PDF and narrated demonstrations](https://github.com/abdulkalamazad1001/campusdesk-devops-capstone/tree/main/demo) |

The `capstone-campusdesk/` directory is an earlier local snapshot retained with the submitted work. The links above lead to the completed capstone and its current evidence.

### Run Locally

With Docker Desktop running, execute from the repository root:

```powershell
cd capstone-campusdesk
docker compose up --build -d
python scripts/seed.py
```

Open [CampusDesk](http://localhost:3000). Seeding adds synthetic demonstration
tickets. The application is a classroom project without authentication, not a
production service.

## Assignments

Each linked directory contains its own instructions and supporting files.
There are 20 numbered directories: tasks 1-7 and 9-21. Course session 8's Docker
networking and volumes topic is covered by task 7.

| Task | Topic | Files |
|---|---|---|
| 1 | Linux basics | [Task 1](task-1-linux-basics/README.md) |
| 2 | Shell scripting | [Task 2](task-2-shell-scripting/README.md) |
| 3 | Networking | [Task 3](task-3-networking/README.md) |
| 4 | Git | [Task 4](task-4-git/README.md) |
| 5 | Docker: six application images | [Task 5](task-5-docker/README.md) |
| 6 | Docker multi-stage builds | [Task 6](task-6-docker-multistage/README.md) |
| 7 | Docker networking and volumes | [Task 7](task-7-docker-networking-volume/README.md) |
| 9 | Kubernetes fundamentals | [Task 9](task-9-kubernetes-fundamentals/README.md) |
| 10 | Deployments and Pod lifecycle | [Task 10](task-10-k8s-deployments-pod-lifecycle/README.md) |
| 11 | Services and DNS | [Task 11](task-11-k8s-services-dns/README.md) |
| 12 | Ingress, ConfigMaps and Secrets | [Task 12](task-12-ingress-configmaps-secrets/README.md) |
| 13 | Storage, HPA and probes | [Task 13](task-13-storage-hpa-probes/README.md) |
| 14 | Kubernetes troubleshooting | [Task 14](task-14-k8s-troubleshooting/README.md) |
| 15 | Helm | [Task 15](task-15-helm/README.md) |
| 16 | CI/CD with GitHub Actions | [Task 16](task-16-cicd-github-actions/README.md) |
| 17 | DevSecOps | [Task 17](task-17-devsecops/README.md) |
| 18 | Terraform and AWS services | [Task 18](task-18-terraform-aws/README.md) |
| 19 | Terraform cloud project | [Task 19](task-19-terraform-cloud-project/README.md) |
| 20 | Monitoring and GitOps | [Task 20](task-20-monitoring-gitops/README.md) |
| 21 | TaskBoard reference project | [Task 21](task-21-final-devops-project/README.md) |

## Verification and Evidence

The [project-by-project review](review/README.md) links the recorded checks,
successful CI runs, fixes and the scope of each lab verification. Verification scripts and
run-specific reports are kept together under `review/`.

- Recorded checks include 106 Python tests across tasks 16, 17, 20 and 21,
  Docker builds, infrastructure validation and selected live Kubernetes/Helm exercises.
- CampusDesk's tests, security scans, browser checks and local GitOps deployment
  have passed; detailed evidence is linked above.
- CampusDesk's completed AWS deployment/cleanup, narrated walkthrough and submission
  status are recorded in its [current final audit](https://github.com/abdulkalamazad1001/campusdesk-devops-capstone/blob/main/FINAL-AUDIT.md).
  The older snapshot and separately credited reference images remain historical material.
- The `submission.md` transcripts and terminal-style images in tasks 9-21 are
  labelled expected-output examples. Actual execution evidence is in the review
  reports; examples are not substitutes for completed exercises.

### Latest lab rerun — 18 October 2026

The [task-by-task evidence index](review/results/2026-10-18/README.md) links real
execution logs and screenshots for Linux through GitOps, including AWS provisioning
and cleanup. Existing assignment instructions and earlier reports are retained.

- Six Docker application pages and the multi-stage app were checked in a browser.
- Minikube, Kubernetes routing, persistence, failure recovery and Helm were exercised.
- The [final homework workflow](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/39060263538) passed all seven jobs, including scale-out and scale-down for both HPA exercises.
- Task 16 and 17 completed their image publication and deployment pipelines.
- Task 18 and 19 AWS resources were verified and destroyed after the demonstration.
- Monitoring recorded a firing/resolved alert; GitOps deployed v2 and corrected drift.

Screenshots distinguish actual application interfaces from clearly labelled views
of saved command output. Raw results accompany both.

## Reference Material

`devops-heros-main/` contains imported instructor material, separate from the
student projects. Original acknowledgements and licenses are retained. Historical
lab transcripts describe the environment used for those runs; the later review
records Windows/Docker/Kind and GitHub runner checks separately.
