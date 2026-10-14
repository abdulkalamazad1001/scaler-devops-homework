# AWS Runbook

Owner: T. Abdul Kalam Azad, 24BCS10053. Region: `ap-south-1`.

AWS deployment has not been executed. These are instructions, not captured outputs.
EKS, EC2, NAT and load balancers are chargeable resources. The current task scope
keeps deployment local and prepares this code for a later AWS session.

## Prepare And Plan

1. Install AWS CLI and authenticate locally with `aws configure sso` / `aws sso login`.
2. Verify the account with `aws sts get-caller-identity`.
3. Copy `terraform.tfvars.example` to ignored `terraform.tfvars` and set trusted
   API CIDRs to your public address `/32` and any fixed deployment runner egress IP.
4. Run `terraform init`, `terraform fmt -check`, `terraform validate`.
5. Run `terraform plan -out=campusdesk.tfplan`. Review resources and capture actual output.
6. Apply the reviewed plan: `terraform apply campusdesk.tfplan`.
7. Run the `configure_kubectl` output. Confirm the expected context before deploying.

The EKS version is configurable. Before applying, check AWS's current support calendar:
<https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html>.
Version 1.35 is an example supported at the time this configuration was prepared.

## Deploy

1. Apply `../k8s/namespace.yaml` and `../k8s/storage-aws.yaml`.
2. Create `campusdesk-db` and `campusdesk-grafana` Secrets in namespace `campusdesk`.
   The database Secret needs `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
   and a URL-encoded `DATABASE_URL` pointing to `postgres:5432`.
3. Install Traefik with a LoadBalancer Service and configure DNS/TLS for your hostname.
4. Install Metrics Server without the local Kind insecure-kubelet flag.
5. Set public GHCR images or an image-pull Secret, then deploy:

```bash
helm upgrade --install campusdesk ../helm/campusdesk -n campusdesk \
  -f ../helm/campusdesk/values-aws.yaml \
  --set backend.tag="$COMMIT_SHA" --set frontend.tag="$COMMIT_SHA" \
  --set ingress.host="$HOSTNAME" --set ingress.tlsSecret=campusdesk-tls \
  --wait --wait-for-jobs --timeout 10m
```

For GitOps, point Argo CD at `values-aws.yaml` plus a committed release values file
containing the verified image SHA. Only enable automated sync after this works manually.
The state file contains sensitive infrastructure metadata; keep it out of Git. Use an
encrypted, access-controlled remote backend before sharing Terraform operations.

## Required AWS Evidence

- Real non-empty `terraform plan` output.
- VPC and EKS console screenshots from the correct region.
- Running nodes and application workloads.
- Terraform destroy completion after evaluation.

## Cleanup

First back up any data you intend to retain. Remove Kubernetes Ingress/LoadBalancer
Services while EKS still exists so AWS controllers can delete cloud load balancers.
Remove the application and its data PVC only when no longer needed. Then run
`terraform plan -destroy` and `terraform destroy`, review the result, and check AWS
for remaining EBS volumes/load balancers. Record real completion output.

Do not run cleanup against another project or a context you have not verified.
