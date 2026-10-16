# CampusDesk on AWS (Terraform + EKS) - Runbook

Owner: T. Abdul Kalam Azad, 24BCS10053. Default region: `ap-south-1` (Mumbai).

This folder creates:

| Resource | Details |
|---|---|
| VPC | `10.42.0.0/16`, 2 public subnets + 2 private subnets in 2 AZs, 1 Internet gateway, 1 NAT gateway (+1 Elastic IP) |
| EKS | Cluster `campusdesk-24bcs10053`, public API restricted to `api_allowed_cidrs`, add-ons vpc-cni, coredns, kube-proxy, aws-ebs-csi-driver |
| Node group | Managed node group `application-*`: 2 x `t3.medium` (min 1, max 3), 30 GB disk, in the private subnets |
| IAM | Cluster/node roles, IRSA role for the EBS CSI driver |

The student runs this runbook against their own AWS account and stores the
screenshots in `../evidence/aws/` (create that folder). Every step marked
**SCREENSHOT** is evidence for the M7 rubric. All commands are for Windows
PowerShell 5.1 and are run from the `capstone-campusdesk\terraform` folder unless stated.

## Cost (read first)

AWS bills by the hour from `terraform apply` until `terraform destroy` finishes.
Approximate on-demand prices in `ap-south-1` (check the
[AWS Pricing Calculator](https://calculator.aws/); other regions differ slightly):

| Item | Approx. cost |
|---|---|
| EKS control plane | $0.10/hr |
| 2 x t3.medium worker nodes | ~$0.09/hr |
| 1 NAT gateway | ~$0.05/hr + ~$0.05 per GB processed |
| Public IPv4 addresses (NAT EIP, load balancer) | $0.005/hr each |
| Network Load Balancer (only if you deploy the app) | ~$0.025/hr + usage |
| EBS gp3 (2 x 30 GB node disks + 2 GB database) | ~$0.01/hr |
| CloudWatch control-plane logs, KMS key | a few cents per day |
| **Total** | **roughly $0.30-0.40/hr (about $8-10 per day if left running)** |

A full run (apply, screenshots, destroy) takes about 1-2 hours and costs about $1.
**Forgetting to destroy is the expensive mistake.** Create a budget alert first:
AWS Console > Billing and Cost Management > Budgets > Create budget >
"Zero spend budget" or a monthly cost budget of e.g. $10 with your email.

## 1. Install the tools

Open PowerShell (normal user) and run:

```powershell
winget install --id Amazon.AWSCLI -e
winget install --id Hashicorp.Terraform -e
winget install --id Kubernetes.kubectl -e
winget install --id Helm.Helm -e
```

Close and reopen PowerShell, then check:

```powershell
aws --version          # aws-cli/2.x
terraform version      # 1.3.2 or newer (1.x)
kubectl version --client
helm version
```

(This repository also ships `..\..\tools\terraform\terraform.exe`; you may use that
path instead of `terraform`.)

## 2. AWS credentials

1. Sign in to the AWS Console as the root user or an admin, open **IAM > Users >
   Create user** (e.g. `campusdesk-terraform`), choose **Attach policies directly >
   AdministratorAccess** (simplest for a one-off lab; delete the user afterwards).
2. Open the user > **Security credentials > Create access key > Command Line
   Interface (CLI)**. Copy the Access key ID and Secret access key.
3. Configure the CLI (the keys are stored in `%USERPROFILE%\.aws\credentials`,
   outside this repository):

```powershell
aws configure
# AWS Access Key ID:     <paste>
# AWS Secret Access Key: <paste>
# Default region name:   ap-south-1
# Default output format: json
aws sts get-caller-identity
```

Never put access keys in any file inside this repository, in `terraform.tfvars`,
or in a screenshot. Deactivate/delete the access key when you are finished.

Use the **same** IAM identity for `terraform apply`, `kubectl` and
`terraform destroy`: the identity that creates the cluster is the only one that
gets Kubernetes admin access.

## 3. Configure variables

```powershell
cd capstone-campusdesk\terraform
Copy-Item terraform.tfvars.example terraform.tfvars
$ip = (Invoke-RestMethod https://checkip.amazonaws.com).Trim()
"$ip/32"
(Get-Content terraform.tfvars) -replace '203\.0\.113\.10/32', "$ip/32" | Set-Content terraform.tfvars -Encoding ascii
Get-Content terraform.tfvars
```

`terraform.tfvars` is git-ignored. `api_allowed_cidrs` must contain your current
public IP with `/32`; only that address can reach the Kubernetes API. If your IP
changes later (new Wi-Fi, router restart), repeat the last three lines and run
`terraform apply` again.

`kubernetes_version = "1.35"` must be a version EKS currently offers. Check
<https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html> and
change it in `terraform.tfvars` if needed.

## 4. Init, validate, plan

```powershell
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan -out campusdesk.tfplan
```

The plan must end with `Plan: N to add, 0 to change, 0 to destroy.` (N is the number of resources to create).
**SCREENSHOT** `evidence/aws/01-terraform-plan.png`: the end of the plan output
including the `Plan:` line. (`*.tfplan` files are git-ignored; do not commit them.)

## 5. Apply

```powershell
terraform apply campusdesk.tfplan
```

This takes about 15-20 minutes (the EKS control plane alone takes ~10 minutes).
It ends with `Apply complete! Resources: N added, 0 changed, 0 destroyed.` and
prints the outputs.
**SCREENSHOT** `evidence/aws/02-terraform-apply.png`: the `Apply complete!` line and outputs.

```powershell
terraform output
```

Do not delete `terraform.tfstate` or this folder until destroy has finished: the
state file is how Terraform knows what to delete.

## 6. AWS Console screenshots

Select region **Asia Pacific (Mumbai) ap-south-1** in the top-right corner first.

- **SCREENSHOT** `evidence/aws/03-vpc.png`: VPC > Your VPCs, showing
  `campusdesk-24bcs10053-vpc` (10.42.0.0/16).
- **SCREENSHOT** `evidence/aws/04-subnets.png`: VPC > Subnets, filtered by the VPC,
  showing the 2 public (`...-public-ap-south-1a/b`) and 2 private subnets.
- **SCREENSHOT** `evidence/aws/05-eks-cluster.png`: EKS > Clusters >
  `campusdesk-24bcs10053`, showing **Status: Active** and the Kubernetes version.
- **SCREENSHOT** `evidence/aws/06-eks-nodegroup.png`: the cluster's **Compute** tab
  showing node group `application-...` as **Active** with 2 nodes.

## 7. Connect kubectl

```powershell
Invoke-Expression (terraform output -raw configure_kubectl)
kubectl config current-context    # campusdesk-24bcs10053
kubectl get nodes -o wide
```

Both nodes must show `Ready`.
**SCREENSHOT** `evidence/aws/07-kubectl-get-nodes.png`.

## 8. (Optional) Deploy CampusDesk to EKS

Run from the `capstone-campusdesk` folder. This creates a Network Load Balancer and an
EBS volume, which step 9 removes again.

```powershell
cd ..
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/storage-aws.yaml

# Secrets (random passwords, never written to a file)
$dbPassword = [guid]::NewGuid().ToString('N')
kubectl -n campusdesk create secret generic campusdesk-db `
  --from-literal=POSTGRES_USER=campusdesk `
  --from-literal=POSTGRES_DB=campusdesk `
  "--from-literal=POSTGRES_PASSWORD=$dbPassword" `
  "--from-literal=DATABASE_URL=postgresql+psycopg://campusdesk:$dbPassword@postgres:5432/campusdesk"
kubectl -n campusdesk create secret generic campusdesk-grafana "--from-literal=password=$([guid]::NewGuid().ToString('N'))"

# Ingress controller behind an AWS Network Load Balancer
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik --version 34.4.1 `
  --namespace ingress-system --create-namespace `
  -f terraform/k8s/traefik-aws-values.yaml --wait --timeout 10m
$lb = kubectl -n ingress-system get svc traefik -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
$lb

# Metrics Server (needed by the backend HorizontalPodAutoscaler)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.7.2/components.yaml

# Application: AWS values (gp3 storage, no NodePorts) + released image tags
helm upgrade --install campusdesk helm/campusdesk --namespace campusdesk `
  -f helm/campusdesk/values-aws.yaml `
  -f helm/campusdesk/values-release.json `
  --set "ingress.host=$lb" `
  --wait --wait-for-jobs --timeout 10m
kubectl -n campusdesk get pods,svc,ingress,hpa,pvc
```

`$lb` is empty for a minute or two after Traefik installs; re-run the `$lb = ...`
line until it prints a `...elb.ap-south-1.amazonaws.com` hostname. The NLB DNS name
can take another 2-3 minutes to resolve. Then open `http://<$lb>/` in a browser.
**SCREENSHOT** `evidence/aws/08-app-pods.png` (the `kubectl get` output) and
`evidence/aws/09-app-browser.png` (the app opened via the load balancer hostname).

If pods show `ImagePullBackOff`, the GHCR images are private: make the
`campusdesk-backend` / `campusdesk-frontend` packages public on GitHub
(Packages > Package settings > Change visibility), then
`kubectl -n campusdesk delete pod --all`.

## 9. Pre-destroy cleanup (always run before destroy)

Kubernetes creates AWS resources Terraform does not know about: the load balancer
for the Traefik `LoadBalancer` Service and EBS volumes for PVCs. If they still exist,
`terraform destroy` fails with `DependencyViolation` on the subnets/VPC. Remove them
while the cluster still exists:

```powershell
cd terraform        # only needed if you are in capstone-campusdesk after step 8
powershell -ExecutionPolicy Bypass -File .\scripts\pre-destroy.ps1
```

(Git Bash / Linux / macOS: `bash scripts/pre-destroy.sh`.) The script reads the
region, cluster name and VPC ID from `terraform output`, asks you to type the
cluster name, then:

1. uninstalls the `campusdesk` and `traefik` Helm releases,
2. deletes all PVCs in namespace `campusdesk` (their EBS volumes are deleted too),
3. deletes every Service of type `LoadBalancer` in the cluster and waits until they
   and the EBS-backed PersistentVolumes are gone,
4. polls `aws elbv2 describe-load-balancers` and `aws elb describe-load-balancers`
   until no load balancer remains in the VPC (exits with an error if one remains),
5. warns about any leftover CampusDesk EBS volumes.

It is safe to run even if you skipped step 8. Continue only when it prints
`OK: no load balancers remain in vpc-...`.

## 10. Destroy

```powershell
terraform destroy
```

Review the list, type `yes`. This takes about 10-15 minutes and must end with
`Destroy complete! Resources: N destroyed.`
**SCREENSHOT** `evidence/aws/10-terraform-destroy.png`.

## 11. Confirm nothing is left (region ap-south-1)

In the AWS Console check each page is empty for CampusDesk:

- VPC > Your VPCs: `campusdesk-24bcs10053-vpc` is gone.
- VPC > NAT gateways: none, or only in state `Deleted`.
- VPC > Elastic IPs: none.
- EKS > Clusters: none.
- EC2 > Instances: none running (terminated instances disappear after ~1 hour).
- EC2 > Volumes: none.
- EC2 > Load Balancers: none.

**SCREENSHOT** `evidence/aws/11-console-clean.png` (e.g. the VPC and EKS pages).
The same checks from the CLI (each should print nothing or `[]`):

```powershell
$r = 'ap-south-1'
aws ec2 describe-vpcs --region $r --filters Name=tag:Project,Values=CampusDesk --query 'Vpcs[].VpcId'
aws eks list-clusters --region $r --query clusters
aws ec2 describe-nat-gateways --region $r --filter Name=state,Values=available,pending --query 'NatGateways[].NatGatewayId'
aws ec2 describe-addresses --region $r --query 'Addresses[].PublicIp'
aws ec2 describe-volumes --region $r --query 'Volumes[].VolumeId'
aws elbv2 describe-load-balancers --region $r --query 'LoadBalancers[].LoadBalancerName'
aws elb describe-load-balancers --region $r --query 'LoadBalancerDescriptions[].LoadBalancerName'
```

Notes: the EKS module's KMS key stays "Pending deletion" for its waiting period
(no charge). If EKS re-creates the CloudWatch log group `/aws/eks/campusdesk-24bcs10053/cluster`
after destroy, delete it in CloudWatch > Log groups. Finally delete the IAM
access key (or the whole IAM user) from step 2.

## Troubleshooting

**`terraform destroy` hangs or fails with `DependencyViolation`** (subnet, internet
gateway or VPC "has dependencies and cannot be deleted"). A load balancer, its
security group, or an ENI created by Kubernetes is still in the VPC.

```powershell
$vpc = terraform output -raw vpc_id
powershell -ExecutionPolicy Bypass -File .\scripts\pre-destroy.ps1   # works even if EKS is already gone
aws ec2 describe-network-interfaces --region ap-south-1 --filters "Name=vpc-id,Values=$vpc" --query 'NetworkInterfaces[].[NetworkInterfaceId,Status,Description]' --output table
aws ec2 describe-security-groups --region ap-south-1 --filters "Name=vpc-id,Values=$vpc" --query 'SecurityGroups[].[GroupId,GroupName]' --output table
```

Delete any remaining load balancer in EC2 > Load Balancers, wait 2-5 minutes for its
ENIs to disappear (ENIs in use by a load balancer cannot be deleted manually), delete
leftover `k8s-elb-...`/`k8s-...` security groups, then run `terraform destroy` again.
Terraform resumes where it stopped.

**`kubectl` says `Unauthorized` / `You must be logged in to the server`.** You are
using a different IAM identity than the one that ran `terraform apply`. Compare
`aws sts get-caller-identity` with the identity used for apply, switch back
(`aws configure` or `$env:AWS_PROFILE`), and re-run step 7.

**`kubectl` times out (`dial tcp ...:443: i/o timeout`).** Your public IP changed and
is no longer in `api_allowed_cidrs`. Redo the IP lines in step 3, then
`terraform apply`.

**`AddressLimitExceeded` / NAT gateway limit.** An account has 5 Elastic IPs per
region by default. Release unused addresses in VPC > Elastic IPs, or request an
increase in Service Quotas, then `terraform apply` again.

**Unsupported Kubernetes version** during apply: set `kubernetes_version` in
`terraform.tfvars` to a version listed by `aws eks describe-cluster-versions --region ap-south-1`
(or the AWS docs page above) and re-run plan/apply.

**Node group fails to create (`instance type not supported` / vCPU limit).** Some new
accounts have low EC2 vCPU quotas. Request an increase for "Running On-Demand
Standard instances" in Service Quotas, or try `node_instance_types = ["t3a.medium"]`.

**Error acquiring the state lock / lost state.** State is local (`terraform.tfstate`
in this folder). Never delete it while resources exist. If it is lost, delete the
resources manually in the Console in the order: load balancers, EKS node group,
EKS cluster, NAT gateway, Elastic IP, VPC.

## Security notes

- `terraform.tfvars`, `*.tfstate*`, `.terraform/` and `*.tfplan` are git-ignored.
  The state file contains infrastructure details; never commit it. For shared use,
  configure an encrypted, access-controlled remote backend (S3 + DynamoDB lock).
- The EKS API is public but limited to `api_allowed_cidrs`; `0.0.0.0/0` is rejected
  by variable validation.
