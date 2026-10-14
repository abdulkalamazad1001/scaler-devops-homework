# CampusDesk Submission

**Name:** T. Abdul Kalam Azad  
**Roll number:** 24BCS10053  
**Repository:** https://github.com/abdulkalamazad1001/scaler-devops-homework  
**Project directory:** `capstone-campusdesk/`

This checklist records actual verification. It does not claim a grade or use generated
screenshots as substitutes for operations that were not executed.

| Rubric module | Implementation and evidence | Status |
|---|---|---|
| M1 Application | React/FastAPI/PostgreSQL, Alembic, CRUD, `evidence/application-desktop.png` | Compose running; browser verification in progress |
| M2 Testing | `backend/tests/`, 16 passing API tests | Local tests passed; CI PostgreSQL verification pending |
| M3 Git/GitHub | Root repository, scoped source commits, `.gitignore` | Publication in progress |
| M4 Docker | Non-root Dockerfiles, migration service, healthy Compose stack | Verified locally |
| M5 CI/CD | Root `.github/workflows/campusdesk.yml`, tests/build/scan/Kind/GHCR | Workflow execution pending |
| M6 Security | Trivy HIGH/CRITICAL gate, initial findings recorded | Remediation and rescan in progress |
| M7 Terraform | VPC, subnets, EKS, nodes, EBS CSI, `.tfvars.example` | Init/validate passed; AWS plan/apply/destroy deferred |
| M8 Kubernetes | Helm chart, Ingress, HPA, StatefulSet/PVC | Local rollout in progress |
| M9 Observability | Prometheus scrape config, Grafana dashboard, alert rules | Live evidence in progress |
| M10 Presentation | `demo/slides.pdf` (12 slides), walkthrough guide | Local video in progress; full AWS walkthrough pending |

## Evidence Rules

Screenshots are captured from the application or real tool output. `scripts/seed.py`
contains synthetic ticket data for demonstrations. Terraform examples and the AWS
runbook are instructions, not claimed execution results. The earlier `task-21-*`
reference folder is not this capstone's verification evidence.

## Still Required Before Claiming Full Completion

- Finish the checks marked in progress above and link the actual successful workflow.
- Provision AWS with Terraform, capture VPC/EKS console proof and destroy completion.
- Record the final narrated walkthrough including the actual AWS work, CI/CD and GitOps.
- Review the complete submission against the current instructor rubric.

The instructor's [submission guide](https://github.com/Nency-Ravaliya/devsecops-python/blob/main/SUBMISSION.md)
requires a repository link, video and slide deck. The student must review and submit
their own work using the linked form. No form has been submitted automatically.
