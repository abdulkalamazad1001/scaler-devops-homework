# Grading Audit

Reviewed on **15 October 2026 (IST)** against the instructor's current
[rubric](https://github.com/Nency-Ravaliya/devsecops-python/blob/main/GRADING.md) and
[submission guide](https://github.com/Nency-Ravaliya/devsecops-python/blob/main/SUBMISSION.md).
This is an evidence audit, not an awarded or predicted grade.

Follow-up: the [project-by-project homework review](../review/README.md) records later
fixes and [successful CampusDesk CI run 38782743221](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38782743221),
including the guarded GitOps promotion. Historical evidence below retains its original
execution SHAs; the [author-correction mapping](../review/results/authorship-correction.json)
relates those commits to the corrected history. The remaining submission requirements
below are unchanged.

## Verdict

The implemented local application and delivery stack are verified. The submission
is **not yet complete**. Open items are the full live walkthrough, AWS Console
evidence or an instructor-approved alternative, the final submission form, and
review of secret-scanner matches in older homework/reference history.

Shared AWS screenshots are credited and included under the student's reported
instructor permission. That permission is not treated as proof that CampusDesk was
deployed to AWS, or as an automatic waiver of every cloud/video requirement.

## Verification Basis

- [Successful CI run 38765329150](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38765329150),
  source `a6e93611db267935157a22e566a422e8824249d0`: source security, tests,
  frontend build, Terraform/Helm validation, both image scans, Kubernetes/browser
  checks, GHCR publication and GitOps promotion succeeded.
- [Downloaded original CI artifacts](evidence/ci-run-38765329150/): 20 API tests,
  zero failures/errors/skips, 17 browser checks, and four passing source security scans.
- [Fresh local command captures](evidence/audit-2026-10-15/checks.json): all ten
  commands exited zero, including a new 20-test run, Ruff and Terraform validation.
  Four security-runner regression tests also passed. The known upstream
  Starlette/httpx deprecation warning remains non-blocking.
- Live inspection: backend/frontend each 2/2 ready, all seven app-namespace pods
  Running, Argo CD Synced/Healthy, API readiness successful and Ingress API responding.
- Live monitoring: both backend scrape targets UP with no errors, Grafana health
  reports database OK, and Prometheus returns a nonzero application request counter.
- Repository visibility checked as public; required ignore patterns verified.
- Older screenshots and recordings retain their original capture provenance;
  downloading newer CI artifacts does not make older screenshots new captures.

## Criteria

**Verified** means implementation/evidence was inspected or executed, not that
marks are guaranteed. **Shared** means externally supplied collaborative evidence,
whose grading acceptance belongs to the instructor. **Open** needs completion.

| Module / points | Criterion | Finding and evidence |
|---|---|---|
| M1 / 2 | API health | Verified: `/health`, fresh API/Compose evidence |
| M1 / 3 | Four REST operations | Verified: GET/POST/PUT/DELETE ticket routes and tests |
| M1 / 2 | PostgreSQL and migrations | Verified: Alembic migration, Compose/Kind DB, CI PostgreSQL |
| M1 / 2 | Working frontend/API integration | Verified: real CRUD in CI browser results |
| M1 / 1 | Usable responsive UI | Verified: 320/768/1920px checks and screenshots |
| M2 / 3 | Passing pytest | Verified: 20 passing locally and in CI |
| M2 / 4 | Test breadth | Verified: more than five tests across health, readiness, CRUD, stats and metrics |
| M2 / 2 | Isolated test database | Verified: `backend/tests/conftest.py`, dedicated CI PostgreSQL |
| M2 / 1 | Test configuration | Verified: `backend/pytest.ini` and fixtures |
| M3 / 2 | Public repository submitted | Public repository verified; **form submission open** |
| M3 / 2 | Meaningful history | Verified: more than ten scoped implementation commits and history capture |
| M3 / 1 | Ignore local/generated files | Verified: `.env`, `.venv`, caches and node_modules ignored |
| M4 / 2 | Backend image build | Verified: successful CI build and running local image |
| M4 / 3 | Multistage frontend | Verified: Node build and Nginx runtime stages |
| M4 / 2 | Non-root containers | Verified: backend UID 10001, frontend UID 101 |
| M4 / 3 | Compose full stack | Verified: retained build/start proof and fresh healthy service listing |
| M5 / 1 | Workflow exists | Verified: repository-root `.github/workflows/campusdesk.yml` |
| M5 / 1 | Main push trigger | Configured; intentional `[skip ci]` on evidence/promotion commits is documented |
| M5 / 3 | Tests block release | Verified: test job required by build/scan/deploy; no failure bypass |
| M5 / 2 | Frontend CI build | Verified in successful run |
| M5 / 3 | Both image builds | Verified in successful run |
| M5 / 3 | Registry publication | Verified: successful GHCR push steps and public packages |
| M5 / 2 | Commit-based tags | Verified: full source SHA in image names and GitOps release values |
| M6 / 3 | Both Trivy scans | Verified: downloaded backend/frontend reports |
| M6 / 1 | HIGH/CRITICAL gate | Verified: nonzero scanner exit configured to block publication |
| M6 / 1 | Explain findings | Written explanation present; student's understanding must be demonstrated |
| M7 / 2 | Valid Terraform source | Verified: `terraform/`, fresh validate success |
| M7 / 1 | Terraform initialization | Verified in CI; does not provision AWS |
| M7 / 2 | Non-empty cloud plan | Shared TaskBoard screenshot; no CampusDesk cloud plan executed |
| M7 / 3 | VPC and public subnets | Shared report/images; CampusDesk configuration exists but was not applied |
| M7 / 4 | EKS and worker group | Shared apply/node screenshot; not independently verified against AWS |
| M7 / 2 | Cloud cleanup | Shared destroy screenshot; no CampusDesk AWS resources created here |
| M7 / 1 | Example variables without credentials | Verified: `terraform.tfvars.example`; history review noted below |
| M8 / 1 | Namespace manifest | Verified: `k8s/namespace.yaml`, running namespace and CI deployment |
| M8 / 3 | Helm chart | Verified: Chart, values and templates; CI lint/render |
| M8 / 3 | Helm install/upgrade | Verified: original local Helm bootstrap and current CI deployment |
| M8 / 2 | Two application replicas | Verified live: backend 2/2 and frontend 2/2 |
| M8 / 2 | ClusterIP services | Verified live for frontend/backend |
| M8 / 2 | Ingress routes | Verified: `/` frontend, `/api` backend and functioning Ingress API |
| M8 / 2 | Running pods | Verified live: all seven application namespace pods Running |
| M9 / 2 | Metrics endpoint | Verified: current Prometheus-formatted response |
| M9 / 3 | Application scraping | Verified live: two targets UP |
| M9 / 2 | Accessible Grafana | Verified: health endpoint OK; prior authenticated UI evidence |
| M9 / 3 | Populated application panel | Existing genuine dashboard screenshot and live nonzero metrics |
| M10 / 2 | Technical README | Present: root overview and linked comprehensive project documentation |
| M10 / 2 | Complete presentation video | **Open:** committed MP4 is a silent local rehearsal, not the full required walkthrough |
| M10 / 1 | Slide deck | Present: 12-slide PDF, above the eight-slide minimum |

## Evidence And Video Gaps

The required application, test, Compose, Git history, GHCR, scan, Kubernetes, Helm,
Ingress, metrics, Prometheus and Grafana images are present in `evidence/`.
Command-output images are explicitly labeled rendered captures, not claimed to be
native terminal screenshots. Seek instructor confirmation if native terminal
screenshots are required literally; the raw original output is also committed.

The three shared AWS images show terminal output. There is **no AWS Console image**
showing VPC and EKS. Use genuine images from the authorized shared exercise or an
explicitly accepted alternative; do not relabel terminal output as Console proof.

The final video must present slides, show source code, trigger a real push and show
the resulting CI run, explain Terraform/shared AWS evidence and the Console portion,
then show Argo CD, Kubernetes, Prometheus and Grafana. The existing rehearsal does
not establish this complete sequence. Narration is recommended to explain the work;
the written rubric specifically requires a clear, complete live walkthrough, not
merely an audio track added to an incomplete video.

The root [demo index](../demo/README.md) links the actual committed assets without
duplicating them. The course submission form is linked in `SUBMISSION.md` and has
not been submitted by this agent.

## Whole-Repository Secret Review

The capstone/workflow history gate passed in CI. An additional **whole-repository**
Gitleaks scan during this audit examined 32 commits and exited 1 with 15 findings.
The [redacted original report](evidence/audit-2026-10-15/full-history-gitleaks.json)
is retained, rather than converting that failure into a clean-scan claim.

| Location | Findings | Initial triage |
|---|---|---|
| `task-12-ingress-configmaps-secrets/` | 5 | Explicitly labeled demo-only DB values and a deliberate newline/base64 exercise |
| `task-18-terraform-aws/aws-services/02-ec2/README.md` | 1 | A displayed public SSH key fingerprint, not private key material |
| `devops-heros-main/session-12-ingress-configmaps-secrets/` | 9 | Imported teaching Secret manifests and instructional database examples |

These are outside CampusDesk and do not by themselves establish a live credential
leak. The owner must confirm that teaching values were never reused for real services;
rotate any that were. No historical files were deleted, no history was rewritten,
and no broad exclusions were added to hide these findings. Because the rubric is
strict about committed secrets, retain this distinction during final review.

## Before Submission

1. Finish the full explained live walkthrough and upload the final video.
2. Supply the AWS Console portion or record the instructor-approved shared-evidence alternative.
3. Review historical demo Secret findings and rotate any value used outside teaching examples.
4. Verify that the final repository/video links work, then submit the course form.

The instructor alone decides accepted exceptions and marks. This audit does not
claim 100% completion or a guaranteed score.
