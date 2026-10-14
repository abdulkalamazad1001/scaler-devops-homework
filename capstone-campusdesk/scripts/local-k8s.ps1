param([string]$ImageTag = "local")
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
$clusters = kind get clusters
if ($LASTEXITCODE -ne 0) { throw 'Docker/kind is unavailable' }
if ($clusters -notcontains 'campusdesk') {
    Invoke-Checked { kind create cluster --config k8s/kind.yaml --wait 180s }
}
Invoke-Checked { kind load docker-image "campusdesk-backend:$ImageTag" "campusdesk-frontend:$ImageTag" --name campusdesk }
Invoke-Checked { kubectl --context kind-campusdesk apply -f k8s/namespace.yaml }
function Ensure-Secret {
    param([string]$Name, [hashtable]$Data)
    $existing = kubectl --context kind-campusdesk -n campusdesk get secret $Name -o name --ignore-not-found
    if ($LASTEXITCODE -ne 0) { throw 'Cannot query cluster Secrets' }
    if ($existing) { return }
    $object = @{apiVersion='v1'; kind='Secret'; metadata=@{name=$Name; namespace='campusdesk'}; type='Opaque'; stringData=$Data}
    $object | ConvertTo-Json -Depth 5 -Compress | kubectl --context kind-campusdesk apply -f -
    if ($LASTEXITCODE -ne 0) { throw "Could not create $Name" }
}
$dbPassword = [guid]::NewGuid().ToString('N')
Ensure-Secret 'campusdesk-db' @{POSTGRES_USER='campusdesk'; POSTGRES_DB='campusdesk'; POSTGRES_PASSWORD=$dbPassword; DATABASE_URL="postgresql+psycopg://campusdesk:$dbPassword@postgres:5432/campusdesk"}
Ensure-Secret 'campusdesk-grafana' @{password=[guid]::NewGuid().ToString('N')}
Invoke-Checked { helm repo add traefik https://traefik.github.io/charts }
Invoke-Checked { helm repo update }
Invoke-Checked { helm upgrade --install traefik traefik/traefik --version 34.4.1 --namespace ingress-system --create-namespace --kube-context kind-campusdesk -f k8s/traefik-values.yaml --wait --timeout 5m }
Invoke-Checked { kubectl --context kind-campusdesk apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.7.2/components.yaml }
# Kind kubelet certificates are self-signed; this flag is limited to the local cluster.
$metricsDeployment = kubectl --context kind-campusdesk -n kube-system get deployment metrics-server -o json | ConvertFrom-Json
if ($metricsDeployment.spec.template.spec.containers[0].args -notcontains '--kubelet-insecure-tls') {
    $metricsDeployment.spec.template.spec.containers[0].args += '--kubelet-insecure-tls'
    $metricsDeployment | ConvertTo-Json -Depth 40 | kubectl --context kind-campusdesk replace -f -
    if ($LASTEXITCODE -ne 0) { throw 'Could not configure local Metrics Server' }
}
Invoke-Checked { helm upgrade --install campusdesk helm/campusdesk --namespace campusdesk --kube-context kind-campusdesk -f helm/campusdesk/values-local.yaml --set "backend.tag=$ImageTag" --set "frontend.tag=$ImageTag" --wait --wait-for-jobs --timeout 8m }
Invoke-Checked { kubectl --context kind-campusdesk -n campusdesk get pods,svc,ingress,hpa }
Write-Output 'Application: http://campusdesk.localhost:8088'
Write-Output 'Prometheus: http://localhost:9090'
Write-Output 'Grafana: http://localhost:3001 (admin; retrieve password with scripts/grafana-password.ps1)'
