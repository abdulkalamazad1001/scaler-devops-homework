# Project-by-Project Review

Student: **T. Abdul Kalam Azad, 24BCS10053**. Review date: **15 October 2026**.

This review covers every numbered homework directory, not just CampusDesk.
The [comparison repository](https://github.com/arju-prog/devops-assignment) was
consulted for topic coverage, not copied as personal evidence. Imported instructor
material in `devops-heros-main` remains reference material, not another original project.

## Status and Evidence

There are 20 numbered directories: tasks 1-7 and 9-21. Course session 8 is Docker
networking/volumes, covered by this repository's task 7. The original tasks 9-21
write-ups and terminal-style screenshots remain **expected-output examples**.
Fresh logs below are genuine local test output, with limited scope stated explicitly.

| Task | Review and verification | Still not established by these checks |
|---|---|---|
| [1 Linux](../task-1-linux-basics/README.md) | Documentation/link review; reproducible links, permissions and archive checks passed | Full systemd/journal/user-administration session not replayed |
| [2 Shell](../task-2-shell-scripting/README.md) | Fixed false success after write failure and CRLF portability; EOF/default, spaced-path and failed-write checks passed | Historical macOS transcript not re-recorded |
| [3 Networking](../task-3-networking/README.md) | Documentation/link review; container interface, route, socket and loopback checks passed | Every privileged routing exercise not replayed |
| [4 Git](../task-4-git/README.md) | Documentation/link review; disposable commit/staging/branch/merge regression checks passed | Every historical interactive exercise not replayed |
| [5 Docker](../task-5-docker/README.md) | All six images built and returned HTTP 200: Node, Python, Java, React, Nginx, Apache | Browser interaction and full image security audit not performed for these simple demos |
| [6 Multi-stage](../task-6-docker-multistage/README.md) | Built, HTTP 200; runtime changed to non-root and verified UID 1000 | Production hardening beyond this lab is not claimed |
| [7 Networks/volumes](../task-7-docker-networking-volume/README.md) | Frontend/backend connectivity, backend/database connectivity, frontend isolation and named-volume persistence passed | Database role is an Alpine network fixture, not a new MySQL application run |
| [9 Kubernetes](../task-9-kubernetes-fundamentals/README.md) | All manifests schema-validated; nginx pod reached Ready on Kind; installer now checks both binaries and its platform | Ubuntu Minikube installer not executed on this Windows host |
| [10 Deployments](../task-10-k8s-deployments-pod-lifecycle/README.md) | All manifests schema-validated; blue/green rollout and actual service traffic switch passed | Other strategies and every deliberate lifecycle failure not replayed |
| [11 Services/DNS](../task-11-k8s-services-dns/README.md) | All manifests schema-validated; ClusterIP DNS and HTTP on its configured port 8080 passed | External LoadBalancer provisioning and every service type not tested |
| [12 Config/Secrets/Ingress](../task-12-ingress-configmaps-secrets/README.md) | All manifests schema-validated; ConfigMap env/file and Secret env/file consumption passed without logging secret values | This task's Nginx Ingress controller setup not deployed |
| [13 Storage/HPA/probes](../task-13-storage-hpa-probes/README.md) | Fixed read-only reader startup race; shared emptyDir and PVC survival after pod recreation passed | This task's full HPA, node-local retention and probe-failure exercises not replayed |
| [14 Troubleshooting](../task-14-k8s-troubleshooting/README.md) | All manifests schema-validated; corrected image-pull pods reached Ready | Every intentionally broken/fixed scenario not run; broken fixtures deliberately retained |
| [15 Helm](../task-15-helm/README.md) | Fixed malformed test-hook argument; both value sets lint/render checked; live install, Helm test, upgrade to two replicas, rollback, restored-content check and cleanup passed | Production operation and cloud deployment not claimed |
| [16 CI/CD](../task-16-cicd-github-actions/README.md) | 22 tests passed, 97.92% app coverage; non-finite input/overflow fixed; GitHub CI and GHCR/Kind CD passed | Staging is an ephemeral runner cluster, not AWS |
| [17 DevSecOps](../task-17-devsecops/README.md) | 46 tests passed, 98.25% app coverage; malformed API input fixed; security gate rejects malformed/incomplete reports; GitHub scan, gate, GHCR push and Kind deploy passed | Policy excludes unfixed image CVEs; not production security certification |
| [18 Terraform S3](../task-18-terraform-aws/README.md) | Format, backend-disabled init and validate passed | No credentialed AWS plan/apply/destroy |
| [19 Terraform cloud](../task-19-terraform-cloud-project/README.md) | Format, backend-disabled init and validate passed | No AWS provisioning, public endpoint or Console evidence captured |
| [20 Monitoring/GitOps](../task-20-monitoring-gitops/README.md) | 17 app tests passed; invalid load inputs fixed; Argo repository URL corrected; 7 rules validated and rule unit tests passed | Full task-specific Prometheus/Loki/Grafana/Argo stack not replayed |
| [21 TaskBoard reference](../task-21-final-devops-project/README.md) | 21 backend tests passed; explicit-null and blank-title updates fixed; frontend image built; Helm and Terraform format/init/validate passed in GitHub CI | Local Terraform retry hit registry DNS failures; no AWS plan/apply/destroy or full TaskBoard browser run; separate from original CampusDesk |

Task 21's default Helm chart deliberately requires a database secret. Rendering
uses `database.existingSecret=review-placeholder` only as a **non-deployed fixture**;
no real secret is stored in the review. Dev/prod files retain their own settings.
The first test harness attempted port 80 for task 11; the manifest correctly uses
8080. The harness was corrected, not the valid service configuration.

The live Helm test found that an unquoted colon caused the test hook's shell argument
to render as a YAML mapping. A block scalar fixed it. Rendered command/argument type
checks and the live Helm lifecycle now guard against that regression.

## Verified GitHub Runs

- [Task 16 CI: passed](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38778348181)
- [Task 16 CD: passed](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38778505023)
- [Task 17 DevSecOps: passed](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38778348129)
- [Homework apps, shell, Docker and infrastructure validation: passed](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38779552339)
- [Expanded homework pipeline including live Kubernetes and Helm lifecycle: passed](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38782743063)
- [CampusDesk tests, scans, browser checks, deployment and guarded GitOps promotion: passed](https://github.com/abdulkalamazad1001/scaler-devops-homework/actions/runs/38782743221)

Downloaded reports: [task 16](results/task16-ci-38778348181/),
[task 17](results/task17-ci-38778348129/),
[homework validation](results/ci-38779552339/) and
[expanded validation with live Kubernetes](results/ci-38782743063/) and
[CampusDesk verification](results/campusdesk-ci-38782743221/).
[GitHub run metadata](results/github-runs.json) records exact source SHAs and job states.
The expanded run reports 106 Python tests across four application projects, 26 Helm/
Terraform/rule checks, 41 Kubernetes operations/checks and 11 Helm lifecycle operations,
all successful. Operation totals include setup/cleanup; they are not counts of
independent test cases. The promotion-fix CampusDesk run also completed successfully.

An earlier CampusDesk rerun passed tests/scans/deployment but failed during GitOps
promotion because concurrent runs edited the same release file. The promotion now
fetches the current tip, rejects newer untested source, preserves unrelated changes
and retries bounded push races instead of rebasing stale release values. Three local
Git integration tests passed. Capstone-only path filters avoid rebuilding it for
unrelated homework changes. The previous failed run remains visible in GitHub history.

## Repeat the Checks

Prerequisites: Python with PyYAML, Docker, Helm and Terraform. Kubernetes checks need
an explicitly selected disposable/local cluster. No script runs `terraform apply`.

```console
python review/check_sources.py
python review/run_checks.py all
python review/smoke_containers.py
python review/check_networks.py
python review/check_kubernetes.py --context kind-campusdesk
python review/check_helm_lifecycle.py --context kind-campusdesk
```

Windows tooling is also discovered in the ignored `tools/` folder. The review
creates isolated containers, temporary Terraform directories and a unique Kubernetes
namespace, then removes only its own test resources. Images remain cached locally.
Task 7 volume checks use disposable test data, not CampusDesk's database volumes.

- [Syntax and relative file-link checks](results/source-checks.json)
- [Docker build and HTTP results](results/containers.json)
- [Network isolation and volume results](results/networks.json)
- [Linux, shell, networking and Git checks](results/shell.json)
- [Kubernetes checks and cleanup](results/kubernetes.json)
- [Helm lifecycle checks and cleanup](results/helm-lifecycle.json)
- [Task 21 Terraform validation in CI](results/ci-38779552339/homework-infra/task21-terraform-validate.txt)
- Raw command transcripts are under [results/](results/).
- [Active repository validation workflow](../.github/workflows/homework-review.yml)
- [Active task 16 CI](../.github/workflows/task16-ci.yml) and [CD](../.github/workflows/task16-cd.yml)
- [Active task 17 DevSecOps pipeline](../.github/workflows/task17-devsecops.yml)

`results/all.json` retains the first local suite attempt, including its failures.
Subsequent shell/Helm checks passed after correcting LF line endings and supplying
the chart's required secret fixture. `results/infra.json` retains the local provider
DNS failure; the separate downloaded CI report records successful Terraform validation.
Named local logs are overwritten on reruns; the downloaded CI artifact directories
are run-specific snapshots. A passing CI check does not erase an earlier failed run.

## Authorship Correction

The owner explicitly confirmed that the two commits recorded under Suja's account
were their own work. Those two author identities and the owner's older account email
were normalized to `abdulkalamazad1001`. File trees and messages were checked unchanged
for every rewritten commit; GitHub Actions bot authors remain intact.

[Original-to-corrected commit mapping](results/authorship-correction.json) preserves
the relationship with historical CI artifacts and SHA-tagged images. Earlier evidence
continues to name the commit actually executed; screenshots were not relabelled.
A verified pre-rewrite Git bundle is retained outside this repository in the local
`history-backups` folder. Other people's source acknowledgements, license notices and
credited shared AWS evidence have not been removed. No Claude author or co-author was
found in this repository's current history; GitHub's contributor display can lag history
updates. Other GitHub repositories were not rewritten in this task.

## Evidence Secret Review

Before publishing, Gitleaks scanned the review directory. Its two
[redacted findings](results/gitleaks-review-findings.json) are the same **public Python
release-signing key fingerprint** embedded in the task 17 Trivy image metadata, not
an access token or private key. It matches the `GPG_KEY` used to verify Python releases
in the [official Python image Dockerfile](https://raw.githubusercontent.com/docker-library/python/master/3.12/slim-trixie/Dockerfile).
The downloaded scanner report was left unchanged; no broad scanner exclusion was added.

## Capstone and Submission Limits

CampusDesk remains the original capstone. Its [grading audit](../capstone-campusdesk/GRADING-AUDIT.md)
documents earlier successful API/browser/security/CI/local-Kubernetes checks and the
separately credited shared AWS images. This homework review does not turn those shared
TaskBoard images into a CampusDesk AWS deployment.

AWS execution or an explicitly accepted alternative, the complete explained live
walkthrough, and final course submission remain unresolved. Neither syntax checks nor
a green workflow guarantees full marks or completion of every practical exercise.
