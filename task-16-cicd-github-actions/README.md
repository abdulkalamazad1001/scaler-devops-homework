# Task 16: CI/CD with GitHub Actions

A small Flask calculator API with unit tests, a Dockerfile, and two GitHub Actions
workflows: CI (lint, security check, tests with coverage, Docker build, artifacts) and CD
(push the image to GHCR, deploy it to a kind cluster in the `staging` environment, smoke
test). The full write-up, including concepts and the pipeline run output, is in
[`submission.md`](submission.md).

## Current Repository Pipelines

The active workflows are [Task16 CI](../.github/workflows/task16-ci.yml) and
[Task16 CD](../.github/workflows/task16-cd.yml) at the repository root. The `staging`
environment and its `APP_SECRET_KEY` have been configured without committing the
secret. CD accepts only a successful CI push run on `main`; the nested files below
remain standalone teaching templates. See [review results](../review/README.md)
for actual runs, separate from the expected output in `submission.md`.

## Layout

```text
task-16-cicd-github-actions/
├── app/                    Flask app (calculator.py, main.py)
├── tests/                  pytest unit and API tests
├── k8s/                    Deployment + Service used by the CD job
├── .github/workflows/
│   ├── ci.yml              CI pipeline
│   └── cd.yml              CD pipeline
├── Dockerfile
├── requirements.txt        runtime deps
├── requirements-dev.txt    test + lint deps
├── setup.cfg               flake8 / pytest config
└── submission.md
```

## Run locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
flake8 app tests
pytest --cov=app

docker build --build-arg APP_VERSION=local -t cicd-demo:local .
docker run --rm -p 8000:8000 cicd-demo:local
curl "localhost:8000/api/add?a=2&b=3"
```

## Enable the Pipelines in Another Repository

GitHub only runs workflows from `.github/workflows/` at the repository root, so:

1. Copy `.github/workflows/ci.yml` and `cd.yml` to `<repo-root>/.github/workflows/`.
   They assume this folder is `task-16-cicd-github-actions/` in the repo; if you push
   this folder as its own repo, change `APP_DIR`, `working-directory` and the `paths`
   filters to `.`.
2. Create an environment named `staging` (Settings > Environments) and add the secret
   `APP_SECRET_KEY` to it:
   `openssl rand -hex 32 | gh secret set APP_SECRET_KEY --env staging`
3. Push to `main`. CI runs first; when it succeeds, CD builds and pushes
   `ghcr.io/<owner>/cicd-demo:sha-<short-sha>` using the built-in `GITHUB_TOKEN` and
   deploys it.

## Repeating the complete pipeline

A push to `main` that changes this task starts the complete pipeline. Manual
workflow runs validate the code and security checks; publishing and deployment
are restricted to successful runs triggered by a push to `main`. Review the
individual job results, since a green manual run can contain skipped deployment jobs.
