# CampusDesk Submission

**Name:** T. Abdul Kalam Azad  
**Roll number:** 24BCS10053  
**Repository:** https://github.com/abdulkalamazad1001/scaler-devops-homework  
**Project directory:** `capstone-campusdesk/`

This checklist records actual verification. It does not claim a grade or use generated
screenshots as substitutes for operations that were not executed.

| Rubric module | Implementation and evidence | Status |
|---|---|---|
| M1 Application | React/FastAPI/PostgreSQL, Alembic, CRUD, `evidence/application-desktop.png` | Compose and Ingress running; browser checks passed |
| M2 Testing | `backend/tests/`, 20 API tests; browser regressions | Local tests passed; historical PostgreSQL results and latest CI linked below |
| M3 Git/GitHub | Root repository, more than 10 scoped implementation commits, `.gitignore` | Published to the owner's repository |
| M4 Docker | Non-root Dockerfiles, migration service, healthy Compose stack | Verified locally |
| M5 CI/CD | Root `.github/workflows/campusdesk.yml`, tests/build/scan/Kind/GHCR/GitOps promotion | Two successful real workflow runs |
| M6 Security | Trivy HIGH/CRITICAL gate, initial findings and remediation recorded | Both published application images passed the gate |
| M7 Terraform | VPC, subnets, EKS, nodes, EBS CSI, `.tfvars.example` | Init/validate passed; AWS plan/apply/destroy deferred |
| M8 Kubernetes | Helm chart, Ingress, HPA, StatefulSet/PVC, Argo CD | Local Helm deployment and GitOps verified; scale-out to four observed |
| M9 Observability | Prometheus scrape config, Grafana dashboard, alert rules | Live targets and populated dashboard captured |
| M10 Presentation | `demo/slides.pdf` (12 slides), walkthrough guide, `demo/local-walkthrough.mp4` | Silent local rehearsal recorded; student-narrated AWS walkthrough pending |

## Verified Deliverables

- [Successful CI/CD and automated promotion](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38639295103)
- [Earlier successful independent run](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38638277372)
- [Evidence inventory](evidence/README.md), including actual test and scan artifacts
- [12-slide presentation](demo/slides.pdf)
- [Local walkthrough recording](demo/local-walkthrough.mp4), an automated silent rehearsal, not the final narrated AWS video
- [Backend image](https://github.com/users/abdulkalamazad1001/packages/container/package/campusdesk-backend) and [frontend image](https://github.com/users/abdulkalamazad1001/packages/container/package/campusdesk-frontend)

## Evidence Rules

Screenshots are captured from the application or real tool output. `scripts/seed.py`
contains synthetic ticket data for demonstrations. Terraform examples and the AWS
runbook are instructions, not claimed execution results. The earlier `task-21-*`
reference folder is not this capstone's verification evidence.

## Still Required Before Claiming Full Completion

- Provision AWS with Terraform, capture VPC/EKS console proof and destroy completion.
- Record the final narrated walkthrough including the actual AWS work, CI/CD and GitOps.
- Review the complete submission against the current instructor rubric.

The instructor's [submission guide](https://github.com/Nency-Ravaliya/devsecops-python/blob/main/SUBMISSION.md)
requires a repository link, video and slide deck. The student must review and submit
their own work using the linked form. No form has been submitted automatically.
