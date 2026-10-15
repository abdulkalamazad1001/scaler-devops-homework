# Reference Comparison

Compared the owner's suggested [Session 21 example](https://github.com/Shaikh-Suja-Rahaman/devops-heros/tree/a966ab3a8f9772e69e786f411a9f1ccbb3765701/session21-python)
and its `MyReadme.md`, workflow and security configuration with CampusDesk and the
[instructor rubric](https://github.com/Nency-Ravaliya/devsecops-python/blob/main/GRADING.md).
The example is inspiration for coverage, not independent proof that its claimed
deployments occurred. No application code, screenshots, identities or deployment
results were copied. CampusDesk remains an original campus IT helpdesk.

| Area in the example | CampusDesk comparison and action |
|---|---|
| App, migrations, CRUD, responsive UI | Already implemented; 20 API tests and 17 browser checks in the previous verified release |
| Docker, GHCR SHA tags, CI, Helm, Ingress | Already implemented and verified in local/CI Kubernetes |
| Source security beyond Trivy | Added Bandit, pip-audit, npm audit and Gitleaks gates, pinned scanner versions, saved reports and four failure-policy tests |
| HPA, monitoring, GitOps promotion | Already demonstrated; retained our Kind/Traefik and chart-provisioned monitoring architecture |
| Troubleshooting | Existing image-pull and Service-selector exercises; added isolated readiness failure, diagnosis, repair and cleanup |
| Deliverable navigation | Submission checklist and evidence inventory already exist; linked this comparison and security instructions |
| Terraform cloud infrastructure | Prepared and validated, but actual AWS plan/apply/destroy and console proof remain pending |
| Presentation | Existing 12-slide PDF and silent local recording; final complete narrated walkthrough remains pending |

The reference uses different tools in places (Minikube, ingress-nginx,
kube-prometheus-stack). Those are alternatives, not additional rubric requirements;
replacing working equivalents would not establish missing AWS proof. Its extra
failure scenarios are not a requirement to duplicate exactly. The instructor brief
explicitly illustrates broken images and Service selectors, both already exercised.

The active workflow belongs at the repository root, `.github/workflows/campusdesk.yml`.
A workflow only nested inside a project subdirectory is not automatically discovered
by GitHub Actions. Our existing workflow is already correctly located.

## Verification And Remaining Work

The added checks were executed locally: Bandit, pip-audit, npm audit and Gitleaks
all exited zero. [Saved scanner reports](evidence/source-security-local/summary.json)
include the exact commands and timestamps. That local history scan covered the
20 existing capstone commits before the additions were committed; the new CI run
scans the pushed source commit as well. Four security-runner regression tests and
the existing 20 API tests passed. Ruff passed for all three new scripts. Pytest
still reports the previously documented upstream Starlette/httpx deprecation warning.

The [readiness transcript](evidence/readiness-troubleshooting.txt) records the actual
404 failure, successful repair and namespace deletion. The application workloads
were not modified by this exercise.

Source commit: `a6e9361`. [Revised GitHub Actions run](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38765329150)
was still running when these local results were recorded; it is not yet claimed
as a successful release. The previous green release remains linked in the README.

Security report directories record each scanner's actual exit code and timestamp;
they are not fabricated successful output. Local scans are not a substitute for a
successful run of the revised GitHub workflow. See `security/README.md` for scope
and limitations and `SUBMISSION.md` for the previous release evidence and remaining
AWS/video/submission work. No full-marks claim follows from this comparison.
