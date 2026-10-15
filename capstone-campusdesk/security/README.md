# Security Gates

Run from the project directory with Docker running and a full Git checkout:

```powershell
.venv/Scripts/python -m pip install -r security/requirements.txt
npm --prefix frontend ci
.venv/Scripts/python scripts/security-check.py
```

The script runs every check, saves actual reports under `evidence/local/security/`,
and exits nonzero if any check fails, times out or cannot start. `SECURITY_OUTPUT`
can select another report directory. CI uploads `source-security-reports` even on
failure; image build/publication and GitOps promotion depend on this job succeeding.

| Layer | Tool and scope | Blocking policy |
|---|---|---|
| SAST | Bandit 1.9.4; API and Alembic Python source | Any MEDIUM/HIGH finding, any confidence; no `nosec` bypass |
| Python SCA | pip-audit 2.10.1; resolved runtime and test requirements | Any reported advisory or dependency collection error |
| JavaScript SCA | npm audit; frontend lockfile including development dependencies | HIGH/CRITICAL findings or audit failure |
| Secrets | Gitleaks 8.30.1 built-in rules; fetched Git history for the capstone and active workflow | Any finding; redacted logs/reports, one narrowly scoped public-fingerprint exception |
| Containers | Existing Trivy steps; both built application images | HIGH/CRITICAL findings |

Secret scanning is scoped to `capstone-campusdesk/` and
`.github/workflows/campusdesk.yml`, not the unrelated historical course homework.
It scans committed history, not ignored `.env` files or uncommitted edits. Run it
after committing changes; CI checks the pushed commit before publication. Redaction
is not a substitute for rotating an exposed credential and removing it from history.

The initial history scan flagged four occurrences of Python's **public** release
signing fingerprint inside two original Trivy image-metadata reports. It matches
the [official Python Dockerfile](https://github.com/docker-library/python/blob/master/3.13/alpine3.23/Dockerfile),
where GPG retrieves the public verification key. `gitleaks.toml` allows only that
exact fingerprint in those two exact report paths. It does not exclude those files,
all GPG keys, or any private credential. The original redacted findings are retained
in `evidence/source-security-initial-gitleaks.json`.

These controls do not provide authentication, authorization, penetration testing,
runtime threat detection or an assurance that no vulnerability exists. Advisory
databases change: a previously clean commit can fail a later scan. Resolve findings
and rerun the pipeline instead of suppressing the gate to obtain a green result.

References: [Bandit](https://bandit.readthedocs.io/en/latest/man/bandit.html),
[pip-audit](https://github.com/pypa/pip-audit),
[Gitleaks](https://github.com/gitleaks/gitleaks).
