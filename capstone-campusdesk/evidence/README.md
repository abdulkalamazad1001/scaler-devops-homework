# Verification Evidence

These files come from actual local commands, real browser interactions and GitHub
Actions artifacts. The sample ticket records are explicitly synthetic demo data.

| Evidence | Origin |
|---|---|
| `application-desktop.png`, `application-mobile.png` | Running Docker Compose UI |
| `ticket-create.png`, `ticket-mobile.png` | Real ticket creation forms |
| `browser-results.json` | Playwright CRUD, responsive layout, error/retry checks |
| `pytest.txt`, `ruff.txt` | Captured local checks, command, timestamp and exit code |
| `compose.txt`, `non-root.txt` | Running containers and configured runtime UIDs |
| `kubernetes.txt`, `helm.txt` | Actual Kind cluster workloads and Helm release |
| `prometheus-targets.png`, `.json` | Real scrape targets and UP status |
| `grafana-dashboard.png`, `live-metrics.json` | Actual application traffic and dashboard |
| `argocd-application.png`, `argocd.json` | Real GitOps application status |
| `terraform-validate.txt` | Actual validation; not an AWS plan/apply claim |
| `trivy-*-initial.json` | Initial scans, including the original backend findings |
| `trivy-backend.json`, `trivy-frontend.json` | Rescans of the remediated local images |
| `ci-run-38638277372/` | Downloaded reports from the successful GitHub Actions run |
| `ci-run-38639295103/` | Reports from the successful automated-promotion workflow |
| `github-actions.png`, `registry-*.png` | Actual GitHub run and public package pages |
| `application-ingress.png` | Application reached through local Kubernetes Ingress |
| `*-output.png` | Browser-rendered, clearly labeled original command transcripts |
| `troubleshooting.txt` | Observed failures, fixes, verification and cleanup |
| `commit-history.txt` | Real project source history |
| `autoscaling.txt`, `load-test.txt` | Observed four-replica HPA scale-out and real bounded load results |

The `.txt` transcripts are original captured outputs. Browser-rendered transcript
images are labeled as captured output and are not presented as native terminal
screenshots. No AWS deployment screenshots exist because cloud deployment was deferred.

## Security Findings And Resolution

The first Debian-based backend image contained HIGH findings in operating-system
packages and unused package-installer dependencies. `CVE-2025-47273`, for example,
concerned path traversal in an older setuptools package index implementation.
The backend was rebuilt on patched Alpine with only runtime application dependencies;
pip was removed after installation because the running service does not install packages.
Both final image scans returned no HIGH/CRITICAL findings. The CI reports independently
verify both published images. This is a point-in-time result against Trivy's database,
not a guarantee of complete application security.

## Reproduce

```powershell
node scripts/browser-check.mjs
.venv/Scripts/python scripts/collect-evidence.py
node scripts/capture-monitoring.mjs
python scripts/troubleshooting-check.py
```

Browser tooling is installed outside the deliverable under the repository's ignored
`tools/browser`: `npm install --prefix ../tools/browser playwright @hpcc-js/wasm-graphviz`.
Then install Chromium with `node ../tools/browser/node_modules/playwright/cli.js install chromium`.
PDF/video build dependencies are `reportlab`, `pymupdf`, and `imageio-ffmpeg`.
