<#
.SYNOPSIS
Removes Kubernetes-created AWS resources (load balancers, EBS volumes) so that
`terraform destroy` does not hang on DependencyViolation errors.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\pre-destroy.ps1
Run from the terraform folder after `terraform apply`. Works on Windows PowerShell 5.1.
#>
param(
    [string]$Terraform = 'terraform',
    [string]$Region = '',
    [string]$ClusterName = '',
    [string]$VpcId = '',
    [int]$TimeoutSeconds = 600,
    [switch]$Force
)

$ErrorActionPreference = 'Continue'
$tfDir = Split-Path $PSScriptRoot -Parent
$appNamespace = 'campusdesk'
$appRelease = 'campusdesk'
$ingressNamespace = 'ingress-system'
$ingressRelease = 'traefik'

function Write-Step([string]$Message) { Write-Host ''; Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Warn([string]$Message) { Write-Host "WARNING: $Message" -ForegroundColor Yellow }
function Stop-Script([string]$Message) { Write-Host "ERROR: $Message" -ForegroundColor Red; exit 1 }

foreach ($tool in @('aws', 'kubectl', 'helm', $Terraform)) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { Stop-Script "'$tool' is not on PATH." }
}

function Get-TfOutput([string]$Name) {
    $value = & $Terraform "-chdir=$tfDir" output -raw $Name 2>$null
    if ($LASTEXITCODE -ne 0) { return '' }
    return ([string]$value).Trim()
}

if (-not $Region) { $Region = Get-TfOutput 'region' }
if (-not $ClusterName) { $ClusterName = Get-TfOutput 'cluster_name' }
if (-not $VpcId) { $VpcId = Get-TfOutput 'vpc_id' }
if (-not $Region) { Stop-Script "Could not read 'region' from terraform output. Pass -Region." }
if (-not $ClusterName) { Stop-Script "Could not read 'cluster_name' from terraform output. Pass -ClusterName." }
if (-not $VpcId) { Stop-Script "Could not read 'vpc_id' from terraform output. Pass -VpcId." }

Write-Host "Region:  $Region"
Write-Host "Cluster: $ClusterName"
Write-Host "VPC:     $VpcId"
aws sts get-caller-identity --query Arn --output text
if ($LASTEXITCODE -ne 0) { Stop-Script "AWS CLI is not authenticated (run 'aws configure')." }

if (-not $Force) {
    Write-Host "This deletes the CampusDesk release, its data volumes and ALL LoadBalancer Services in '$ClusterName'."
    $answer = Read-Host 'Type the cluster name to continue'
    if ($answer -ne $ClusterName) { Stop-Script 'Confirmation did not match; nothing was changed.' }
}

aws eks describe-cluster --region $Region --name $ClusterName --query cluster.status --output text 2>$null | Out-Null
$clusterUp = ($LASTEXITCODE -eq 0)

function Get-LbServices {
    $json = kubectl --context $ClusterName get svc -A -o json
    if ($LASTEXITCODE -ne 0) { return @() }
    $items = ($json | Out-String | ConvertFrom-Json).items
    return @($items | Where-Object { $_.spec.type -eq 'LoadBalancer' } | ForEach-Object { "$($_.metadata.namespace)/$($_.metadata.name)" })
}

function Get-EbsPvs {
    $json = kubectl --context $ClusterName get pv -o json
    if ($LASTEXITCODE -ne 0) { return @() }
    $items = ($json | Out-String | ConvertFrom-Json).items
    return @($items | Where-Object { $_.spec.csi -and $_.spec.csi.driver -eq 'ebs.csi.aws.com' } | ForEach-Object { $_.metadata.name })
}

if ($clusterUp) {
    Write-Step "Updating kubeconfig (context '$ClusterName')"
    aws eks update-kubeconfig --region $Region --name $ClusterName --alias $ClusterName | Out-Null
    if ($LASTEXITCODE -ne 0) { Stop-Script 'aws eks update-kubeconfig failed.' }
    kubectl --context $ClusterName get nodes | Out-Null
    if ($LASTEXITCODE -ne 0) { Stop-Script 'kubectl cannot reach the cluster (see README troubleshooting: Unauthorized / API CIDR).' }

    Write-Step 'Uninstalling Helm releases'
    $releases = @(@($appNamespace, $appRelease), @($ingressNamespace, $ingressRelease))
    foreach ($release in $releases) {
        $ns = $release[0]
        $name = $release[1]
        helm --kube-context $ClusterName status $name -n $ns 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "helm uninstall $name -n $ns"
            helm --kube-context $ClusterName uninstall $name -n $ns --wait --timeout 5m
            if ($LASTEXITCODE -ne 0) { Write-Warn "helm uninstall $name failed; continuing." }
        } else {
            Write-Host "Release $ns/$name not installed; skipping."
        }
    }

    Write-Step "Deleting PersistentVolumeClaims in namespace $appNamespace (EBS volumes are deleted with them)"
    kubectl --context $ClusterName get namespace $appNamespace 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        kubectl --context $ClusterName delete pvc --all -n $appNamespace --wait=true --timeout=5m
        if ($LASTEXITCODE -ne 0) { Write-Warn 'PVC deletion did not finish.' }
    } else {
        Write-Host "Namespace $appNamespace not found; skipping."
    }

    Write-Step 'Deleting every Service of type LoadBalancer (all namespaces)'
    foreach ($svc in (Get-LbServices)) {
        $parts = $svc.Split('/')
        Write-Host "kubectl delete svc $($parts[1]) -n $($parts[0])"
        kubectl --context $ClusterName delete svc $parts[1] -n $parts[0] --wait=false
    }

    Write-Step 'Waiting for LoadBalancer Services and EBS-backed PersistentVolumes to disappear'
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ($true) {
        $remainingSvc = Get-LbServices
        $remainingPv = Get-EbsPvs
        if ($remainingSvc.Count -eq 0 -and $remainingPv.Count -eq 0) { break }
        if ((Get-Date) -gt $deadline) {
            if ($remainingSvc.Count -gt 0) { Write-Warn "LoadBalancer Services still present: $($remainingSvc -join ', ')" }
            if ($remainingPv.Count -gt 0) { Write-Warn "EBS PersistentVolumes still present: $($remainingPv -join ', ')" }
            break
        }
        Start-Sleep -Seconds 10
    }
    Write-Host 'Kubernetes cleanup finished.'
} else {
    Write-Warn "EKS cluster '$ClusterName' not found in $Region; skipping Kubernetes cleanup and checking AWS only."
}

Write-Step "Checking AWS for load balancers left in $VpcId"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ($true) {
    $v2 = aws elbv2 describe-load-balancers --region $Region --query "LoadBalancers[?VpcId=='$VpcId'].LoadBalancerName" --output text
    if ($LASTEXITCODE -ne 0) { Stop-Script 'aws elbv2 describe-load-balancers failed.' }
    $classic = aws elb describe-load-balancers --region $Region --query "LoadBalancerDescriptions[?VPCId=='$VpcId'].LoadBalancerName" --output text
    if ($LASTEXITCODE -ne 0) { Stop-Script 'aws elb describe-load-balancers failed.' }
    $v2 = ([string]$v2).Trim()
    $classic = ([string]$classic).Trim()
    if ($v2 -eq 'None') { $v2 = '' }
    if ($classic -eq 'None') { $classic = '' }
    if (-not $v2 -and -not $classic) { break }
    if ((Get-Date) -gt $deadline) {
        Write-Host "ALB/NLB still in VPC: $v2"
        Write-Host "Classic ELB still in VPC: $classic"
        Stop-Script "Load balancers remain in $VpcId. Delete them in the EC2 console (Load Balancers) before running terraform destroy."
    }
    Write-Host "Waiting for AWS to delete: $v2 $classic"
    Start-Sleep -Seconds 15
}
Write-Host "OK: no load balancers remain in $VpcId." -ForegroundColor Green

Write-Step "Checking for EBS volumes created by the EBS CSI driver for namespace $appNamespace"
$vols = aws ec2 describe-volumes --region $Region --filters "Name=tag:kubernetes.io/created-for/pvc/namespace,Values=$appNamespace" --query 'Volumes[].[VolumeId,State]' --output text
if ($LASTEXITCODE -ne 0) {
    Write-Warn 'aws ec2 describe-volumes failed.'
} else {
    $vols = ([string]($vols | Out-String)).Trim()
    if ($vols -and $vols -ne 'None') {
        Write-Warn 'EBS volumes still exist (they do not block destroy but keep costing money):'
        Write-Host $vols
        Write-Host "Delete them in EC2 > Volumes once they show 'available'."
    } else {
        Write-Host 'OK: no CampusDesk EBS volumes remain.' -ForegroundColor Green
    }
}

Write-Step 'Pre-destroy cleanup complete. Next: terraform destroy'
exit 0
