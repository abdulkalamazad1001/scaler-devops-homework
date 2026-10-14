# Local Quality Review

Reviewed on 15 October 2026 (Asia/Calcutta). Scope: the implemented local application
and DevOps workflow. This is a verification record, not a claim of perfect software
or a guaranteed grade. AWS execution remains outside this completed local scope.

## Issues Corrected

| Finding | Correction | Regression check |
|---|---|---|
| Unhandled API errors bypassed request metrics | Record status and latency in `finally`, including HTTP 500 failures | `test_unhandled_failure_is_counted` |
| Exactly 12 tickets enabled an empty extra page | Fetch one look-ahead row; display 12 and enable Next only when another exists | Browser fixture with exactly 24 records |
| Failed reloads left misleading pagination controls | Disable paging and display unavailable state on errors | Browser outage/retry check |
| Collapsed sidebar buttons lost their accessible names | Explicit labels, titles and pressed state on navigation buttons | Tablet navigation check at 768px |
| Browser checks depended on pre-seeded ticket titles | Use a unique test ticket and clean it up; exercise empty-list actions | Real CRUD plus explicit empty-desk regression |
| UI tests did not gate publication | Run Playwright against CI's Kubernetes deployment before publishing/promoting | GitHub Actions browser-results artifact |
| Bootstrap could compete with Argo CD | Refuse Helm bootstrap when the GitOps Application exists | Guard refusal verified on the actual managed cluster |
| GitOps setup required undocumented manual steps | Add checked, idempotent `scripts/local-gitops.ps1` | Script completed with Synced/Healthy status |
| Public images retained an unnecessary pull credential | Remove pull-secret references and the unused local Secret | Deployment specifications inspected; public images verified |
| Evidence collection could exit successfully after a failed check | Return a nonzero exit code if any captured command fails | Current collected commands all returned zero |
| Setup note gave incorrect password-encoding advice | Document Compose's alphanumeric password constraint | README and `.env.example` agree |

## Verification

- 20 API tests passed locally and in PostgreSQL CI, including failed updates, stable paging and metrics.
- 17 browser checks passed locally and against CI's Kubernetes deployment, covering real CRUD,
  accessible navigation and labeled mocked edge cases.
- The same 17 checks passed through local Ingress after Argo CD deployed the published
  `475f2ae689f673c6cb329e92145c3176e150ca39` images; both Deployments had two ready replicas.
- Layout checked at 320, 390, 768, 1440 and 1920 pixels; no page-level horizontal overflow.
- Both rebuilt local application images passed Trivy's HIGH/CRITICAL gate.
- Compose rebuilt and started successfully; the eight existing demo tickets persisted.
- Ruff, Helm lint and Terraform validation passed. Terraform validation is not AWS deployment.
- Both PowerShell deployment scripts parsed successfully; GitOps setup ran successfully.
- Repository-history pattern checks found only the documented AWS example identifier in
  an older course-reference file, not an actual credential matching those patterns.

The first expanded CI browser run correctly blocked publication because its selector
was ambiguous on an empty desk. A second run exposed an early assertion during retry.
Both test issues were corrected and regression coverage strengthened without bypassing
the publication gate. See the latest successful run linked in [SUBMISSION.md](SUBMISSION.md).

[Run 38644518494](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38644518494)
passed the complete workflow for source `475f2ae689f673c6cb329e92145c3176e150ca39`,
including image publication and automated GitOps promotion.

## Evidence And Limits

Use [the evidence inventory](evidence/README.md) for original reports and screenshots.
Rendered command transcripts are labeled as such. Mocked browser edge cases are
identified in `browser-results.json`; they are not represented as deployment proof.
Older CI reports remain as historical records, not the latest release's results.

The app intentionally lacks authentication/RBAC and is kept on loopback interfaces.
PostgreSQL remains single-instance and monitoring storage ephemeral. Pytest reports
one upstream Starlette/httpx deprecation warning; it does not fail the tests.
The local video is a silent rehearsal. Real AWS deployment, cloud cleanup evidence,
the complete student-narrated walkthrough and submission remain pending.
