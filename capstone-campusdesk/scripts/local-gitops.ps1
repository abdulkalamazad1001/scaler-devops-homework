$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$repoRoot = Split-Path $projectRoot -Parent
$env:PATH = "$repoRoot\tools\helm\windows-amd64;$repoRoot\tools;$env:PATH"
Set-Location $projectRoot
function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Command" }
}
Invoke-Checked { kubectl --context kind-campusdesk -n campusdesk get secret campusdesk-db campusdesk-grafana -o name }
Invoke-Checked { helm repo add argo https://argoproj.github.io/argo-helm }
Invoke-Checked { helm repo update argo }
Invoke-Checked { helm upgrade --install argocd argo/argo-cd --version 10.10.3 --namespace argocd --create-namespace --kube-context kind-campusdesk -f gitops/values-argocd.yaml --wait --timeout 8m }
Invoke-Checked { kubectl --context kind-campusdesk wait --for=condition=Established crd/applications.argoproj.io --timeout=60s }
Invoke-Checked { kubectl --context kind-campusdesk apply -f gitops/argocd-ingress.yaml -f gitops/application.yaml }
Invoke-Checked { kubectl --context kind-campusdesk -n argocd wait --for=jsonpath='{.status.sync.status}'=Synced application/campusdesk --timeout=300s }
Invoke-Checked { kubectl --context kind-campusdesk -n argocd wait --for=jsonpath='{.status.health.status}'=Healthy application/campusdesk --timeout=300s }
Write-Output 'GitOps ready: http://argocd.localhost:8088'
Write-Output 'Username: admin. The initial password remains in argocd-initial-admin-secret; never commit it.'
