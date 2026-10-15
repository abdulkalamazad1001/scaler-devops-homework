# Presentation Walkthrough

Presenter: **T. Abdul Kalam Azad (24BCS10053)**.

The final submission requires a video beginning with at least eight slides, followed
by the real project walkthrough. A local demonstration is incomplete until the AWS
portion has also been recorded. Do not claim pending work was executed.

`slides.pdf` contains 12 slides. `local-walkthrough.mp4` is an automated, silent local
demonstration using the real application, source, command transcripts, CI page and
monitoring services. It is a rehearsal asset, not a substitute for the complete
student-narrated recording with AWS evidence required for final submission.

1. Explain CampusDesk's purpose: campus IT tickets with assignment and resolution.
2. Present the architecture: browser, React/Nginx, FastAPI, PostgreSQL and observability.
3. Show source code, input validation, migration, and isolated tests.
4. Create a ticket, search for it, assign it, resolve it, and demonstrate deletion.
5. Show Compose services and non-root image users.
6. Commit an actual small change, push, and show the GitHub Actions run completing.
7. Show both Trivy reports and the SHA-tagged GHCR packages.
8. Show Terraform plan and actual AWS VPC/EKS console evidence when available.
9. Show Argo CD sync status and explain that Git contains desired configuration.
10. Show Kubernetes pods, Services, Ingress, Helm history and HPA metrics.
11. Show Prometheus targets UP and Grafana panels after generating API traffic.
12. Run the separate broken-Service/image exercises and explain the observed fix.
13. State verified results and limitations, then show AWS cleanup evidence.

## Explain These In Your Own Words

- Git preserves source history; GitHub hosts it and runs Actions.
- Docker images package the application; Kubernetes manages running containers.
- Terraform provisions cloud infrastructure; Helm packages Kubernetes resources.
- CI tests changes before publishing; Argo CD reconciles desired state from Git.
- Liveness tests the process; readiness tests whether requests can be served.
- HPA needs Metrics Server and CPU requests to calculate utilization.
- Prometheus collects time series; Grafana visualizes them.
- A clean Trivy report means no matching findings in its database at scan time,
  not proof of complete security.

Capture your final narration with these concepts understood. Never show credentials,
browser authorization codes or decoded Kubernetes Secrets in the recording.

## Final Recording Checks

- Explain the source-security job as well as the existing Trivy image gates.
- Use a real code/documentation change for the recorded push, without `[skip ci]`,
  and show that run completing. An older green run alone is not the requested sequence.
- For shared AWS work, identify the original TaskBoard environment, source of the
  screenshots and your actual contribution. Do not describe it as CampusDesk on EKS.
- The current shared images are terminal captures, not Console proof. Add genuine
  VPC/EKS Console material or the instructor-approved alternative before finalizing.
- Keep the rehearsal labeled as such; upload the complete final recording separately.
- Use the [grading audit](../GRADING-AUDIT.md) to check outstanding items before submitting.
