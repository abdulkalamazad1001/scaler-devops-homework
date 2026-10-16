# Presentation Video Script

Target length: **12-15 minutes**. Record the screen with your voice (OBS Studio, or
Windows `Win + Alt + R` / Clipchamp). Export as MP4 and save it as
`demo/campusdesk-presentation.mp4`. Speak in your own words; the lines below are a
guide, not text to read word for word.

The order follows the rubric: slides first, then the live walkthrough.

## Before Recording (do not record this part)

```powershell
cd C:\Users\abdul\Downloads\devops\scaler-devops-homework\capstone-campusdesk
docker compose up -d --wait              # app at http://localhost:3000
kubectl config use-context kind-campusdesk
kubectl get pods -A                      # everything Running
python scripts/load.py                   # generate traffic so Grafana panels have data
```

Open these tabs in advance:

| Tab | URL |
|---|---|
| Slides | `demo/slides.pdf` (full screen) |
| App via Ingress | http://campusdesk.localhost:8088 |
| GitHub Actions | https://github.com/abdulkalamazad1001/scaler-devops-homework/actions |
| GHCR packages | https://github.com/abdulkalamazad1001?tab=packages |
| Argo CD | http://argocd.localhost:8088 (user `admin`) |
| Prometheus targets | http://localhost:9090/targets |
| Grafana | http://localhost:3001 |
| AWS Console | VPC and EKS pages in `ap-south-1` (only while the cluster exists) |

Get the Argo CD password with
`kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"`
and decode it, and the Grafana password with `scripts/grafana-password.ps1`.
Never show either password on screen.

Close notifications and anything personal. Use a large terminal font (18pt+).

## Part 1: Slides (3-4 min)

1. **Title.** "I'm T. Abdul Kalam Azad, 24BCS10053. This is CampusDesk, my DevOps capstone."
2. **Application.** What problem it solves: students report IT issues; support staff
   assign, prioritise and resolve them.
3. **Technology.** React + Nginx frontend, FastAPI backend, PostgreSQL with Alembic.
4. **Architecture.** Walk the diagram left to right: browser, Ingress, frontend and
   API replicas, database; then GitHub, CI, GHCR, Argo CD; then Prometheus/Grafana;
   then Terraform for AWS.
5. **CI/CD.** Tests, then build, then Trivy, then publish with the commit SHA tag.
6. **Kubernetes / GitOps / Observability / Terraform.** One sentence each; you will
   show them live.
7. **Learnings.** Pick two real ones (e.g. why images must not run as root; why
   `terraform destroy` needs load balancers removed first).

## Part 2: Codebase (2 min)

Show the folder tree in VS Code and open, briefly:

- `backend/app/main.py`: "These are the REST endpoints: GET, POST, PUT, DELETE on
  `/api/tickets`, plus `/health` and `/metrics`. Input is validated, so bad input
  returns 422 instead of crashing."
- `backend/alembic/versions/0001_tickets.py`: "The table is created by an Alembic
  migration, not by the app."
- `backend/tests/conftest.py`: "Tests use a separate test database, never production."
- `backend/Dockerfile` and `frontend/Dockerfile`: point at `USER` and the two stages
  of the frontend build (Node builds, Nginx serves).
- One design decision in your own words (e.g. why images are tagged with the commit SHA).

## Part 3: CI/CD Live (3 min, start this early)

Make a small real change, for example a comment in `backend/app/main.py`, then:

```powershell
git add -A
git commit -m "docs(api): explain ticket id bounds"
git push
```

Open GitHub Actions and show the new run starting. Explain each job while it runs:
`source-security`, `test` (pytest against PostgreSQL), `build-scan-deploy` (images,
Trivy, Kind deploy, browser checks) and `publish` (GHCR push and GitOps promotion).
Continue with Part 4 and come back when it finishes, about 10 minutes later.

When it is green: open the Trivy step output and explain the result, then the GHCR
package page showing the tag that equals the commit SHA.

## Part 4: Terraform and AWS (2-3 min)

From your AWS run (see `terraform/README.md`):

- Show `terraform plan` output: VPC, two public and two private subnets, NAT gateway,
  EKS cluster, managed node group.
- Show the AWS Console: the VPC with its subnets, and the EKS cluster as Active with
  the node group on the Compute tab.
- Show `kubectl get nodes` against EKS.
- Show the `terraform destroy` result and say why you destroyed it (cost).

If you recorded the Console part separately while the cluster existed, cut it in
here. Do not show access keys or your account ID.

## Part 5: Argo CD and Kubernetes (2 min)

- Argo CD: application `campusdesk` is **Synced** and **Healthy**. "Git is the
  source of truth: CI writes the new image SHA to `values-release.json`, and Argo CD
  applies it."
- Terminal:

```powershell
kubectl get pods -n campusdesk
kubectl get svc -n campusdesk
kubectl get ingress -n campusdesk
helm list -A
```

Point out 2 backend and 2 frontend replicas, ClusterIP Services, and the Ingress
routing `/` to the frontend and `/api` to the backend. Open
http://campusdesk.localhost:8088, create a ticket, resolve it, delete it.

## Part 6: Observability (2 min)

```powershell
curl.exe http://campusdesk.localhost:8088/metrics
```

- Prometheus **Targets** page: the CampusDesk backend targets are **UP**.
- Grafana: open the CampusDesk dashboard and show request rate and latency panels
  moving after you click around the app.

## Part 7: Close (30 s)

Summarise what works, one limitation you would improve next (e.g. authentication,
HTTPS), and thank the viewer.

## After Recording

1. Check that the audio is clear and nothing secret is visible.
2. Save as `demo/campusdesk-presentation.mp4`. If it is larger than 100 MB, attach it
   to a GitHub Release instead and link it from `demo/README.md`, because GitHub
   rejects files over 100 MB in a normal push.
3. Commit and push it.
