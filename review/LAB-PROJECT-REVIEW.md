# Lab project review — 18 October 2026

This review compares the project exercises with the instructor's
[devops-heros revision 68be534e](https://github.com/Nency-Ravaliya/devops-heros/tree/68be534ed67dd6de7ce520821e07e4dde137e26c)
and its linked homework document. The instructor repository was rechecked and remains at that revision.

| Project | Implementation | Verification |
|---|---|---|
| Session 13: persistent web app, HPA and probes | [Task 13](../task-13-storage-hpa-probes/README.md) | [Scale-out/scale-down and probe recovery](results/2026-10-18/ci-homework-39060263538/homework-autoscaling/probes.json); supplemental check below verifies this project's own PVC and Service. |
| Session 14: troubleshooting mini-project | [Task 14](../task-14-k8s-troubleshooting/README.md) | [Broken image, endpoint diagnosis, repair and recovered HTTP](results/2026-10-18/mini.json). |
| Session 15: Helm notes application | [Task 15](../task-15-helm/README.md) | [Install, two upgrades and rollback](results/2026-10-18/helm-lifecycle.json); supplemental check below covers the instructor's broken upgrade and recovery to production values. |
| Session 16: CI/CD demo | [Task 16](../task-16-cicd-github-actions/README.md) | [Successful CI](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/39059479821) and [image publication/deployment](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/39059558499). |
| Session 17: DevSecOps demo | [Task 17](../task-17-devsecops/README.md) | [Successful full security, publication and deployment pipeline](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/39059479655). |
| Sessions 18/19: Terraform projects | [S3](../task-18-terraform-aws/README.md) and [VPC/EC2/S3](../task-19-terraform-cloud-project/README.md) | [Actual AWS command results](results/2026-10-18/aws/results.json), public HTTP verification and [cleanup](results/2026-10-18/aws/cleanup-verified.json). |
| Session 20: monitoring and GitOps | [Task 20](../task-20-monitoring-gitops/README.md) | [Metrics, logs and firing/resolved alert](results/2026-10-18/monitoring/result.json), [v2 HTTP response](results/2026-10-18/task20-gitops-v2-http.txt) and [replica drift correction](results/2026-10-18/task20-gitops-selfheal.txt). |
| Session 21: final project | [CampusDesk](https://github.com/abdulkalamazad1001/campusdesk-devops-capstone) | [Final implementation/evidence audit](https://github.com/abdulkalamazad1001/campusdesk-devops-capstone/blob/main/FINAL-AUDIT.md). |

## What the closer review found

The earlier green workflow established the checks it actually ran. It did not
prove two specific mini-project steps: persistence in **Task 13's own** `/data`
volume after replacing a Pod, or a **bad image upgrade** followed by Helm recovery
in Task 15. Separate volume exercises and a healthy-release rollback were already
verified. The supplemental runner now targets the exact two project scenarios.

These checks run in uniquely named namespaces on the existing local Kind cluster.
They use the course manifests and chart; the Helm Service is scoped as ClusterIP
to avoid reserving the course's fixed NodePort on a shared cluster. They do not
provision AWS resources or change the existing CampusDesk release.

```bash
HOMEWORK_RESULTS_DIR=review/results/my-project-run \
  python review/check_project_scenarios.py --context YOUR_LAB_CONTEXT
```

## Supplemental results

Both exact scenarios passed: [Task 13 results](results/2026-10-18/project-followup/storage-project.json)
and [Task 15 results](results/2026-10-18/project-followup/helm-project.json), each recording
16 operations including setup and cleanup. These are local Kind results; the earlier
seven-job GitHub run predates this supplemental runner.

Task 13 read the saved student record from the replacement Pod and served HTTP
before and after replacement. Task 15 installed the chart, applied the actual
production values, observed an `ErrImagePull` Pod after the invalid-image upgrade,
rolled back to revision 2, restored three ready replicas and passed the Helm HTTP test.
The initial helper attempt used an incorrect environment-variable name; its
[failed check and cleanup](results/2026-10-18/project-followup/initial-helper-attempt/helm-project.json)
are preserved. The corrected helper checks the chart's `ENVIRONMENT` value.

[Persistence screenshot](results/2026-10-18/screenshots/task13-project-persistence.png) ·
[Helm recovery screenshot](results/2026-10-18/screenshots/task15-project-rollback.png) ·
[Namespace cleanup and CampusDesk health](results/2026-10-18/project-followup/cleanup.json).
The screenshots show labelled views of the actual saved logs.

## Final project versus reference folder

Session 21 asks for a complete DevOps project. CampusDesk provides the original
application and recorded delivery, security, Kubernetes/Helm, Terraform/AWS,
monitoring, GitOps and troubleshooting evidence. It is linked as the capstone;
this is an evidence mapping, not an instructor grading decision.

The `task-21-final-devops-project/` TaskBoard folder remains a reference project.
Its backend tests, frontend image build, chart rendering and Terraform validation
were checked. Its `.github/workflows/ci-cd.yml` is nested inside that folder, so it
is not an active workflow for this repository. Its Argo CD manifests retain the
reference `devops-student/final-devops-project` URL. It has not independently
completed a TaskBoard registry → GitOps → cloud deployment. The expected-output
walkthrough is labelled accordingly. No extra TaskBoard AWS deployment is claimed.

The complete dated [evidence index](results/2026-10-18/README.md) distinguishes
application screenshots, saved-log views, local clusters and real AWS runs.
