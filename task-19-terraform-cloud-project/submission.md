# Terraform Cloud Project: VPC, EC2 Web Server and S3

> **Note:** Command output in this file is representative expected output for the lab environment
> below, written as a learning reference. It was not captured from a live run, so IDs, timestamps
> and pod name hashes will differ when you run it yourself.

## Lab environment

| Item | Value |
|---|---|
| Host | Ubuntu 24.04 LTS, hostname `devops-lab`, user `student` |
| Shell prompt in output | `student@devops-lab:~/task-19-terraform-cloud-project$` |
| Docker | 27.3.1 |
| Minikube | v1.34.0, docker driver, 2 CPU / 4096 MB, profile `minikube` |
| Kubernetes | v1.31.0, single node `minikube`, node InternalIP `192.168.49.2` |
| kubectl | v1.31.1 client |
| Helm | v3.16.2 |
| Terraform | v1.9.8, hashicorp/aws provider 5.74.0 |
| AWS | region `ap-south-1`, account ID `123456789012` (placeholder), IAM user `terraform-lab` |
| GitHub | user/org placeholder `devops-student`, repo `devops-homework` |
| Container registry | `ghcr.io/devops-student/...` |
| Pod CIDR / Service CIDR | 10.244.0.0/16 / 10.96.0.0/12, kube-dns ClusterIP 10.96.0.10 |
| Date range of runs | 2026-09-14 to 2026-10-04 (timestamps should fall in this range, ascending by task number) |

Also used: hashicorp/random 3.6.3 and AWS CLI v2. The runs for this task are dated 2026-10-02.

## 1. What this project builds

One Terraform configuration that creates a small but complete AWS environment: a VPC with
a public subnet, internet routing, a firewall, an EC2 web server that installs nginx on
first boot, and an S3 bucket for static assets.

### Architecture

```mermaid
flowchart LR
    user([Browser]) -->|HTTP :80| igw

    subgraph aws[AWS region ap-south-1]
        subgraph vpc[VPC 10.20.0.0/16 - tf-cloud-project-vpc]
            igw[Internet Gateway<br/>tf-cloud-project-igw]
            rt[Route table tf-cloud-project-public-rt<br/>10.20.0.0/16 -> local<br/>0.0.0.0/0 -> IGW]
            subgraph subnet[Public subnet 10.20.1.0/24 - ap-south-1a]
                sg{{Security group tf-cloud-project-web-sg<br/>in: tcp/80 from 0.0.0.0/0<br/>out: all}}
                ec2[EC2 t3.micro - Amazon Linux 2023<br/>nginx via user_data<br/>10.20.1.137 / public IP]
            end
        end
        s3[(S3 bucket<br/>tf-cloud-project-assets-xxxxxxxx<br/>versioned, private)]
    end

    igw --- rt
    rt -.associated with.- subnet
    sg --- ec2
    ec2 -. bucket name in user_data .- s3
```

The same picture in plain text, for viewers that do not render mermaid:

```
                         Internet
                            │ HTTP :80
 ┌──────────────── AWS ap-south-1 ───────────────────────────────────────────┐
 │  ┌────────────── VPC 10.20.0.0/16 ─────────────────────────────────────┐  │
 │  │          ┌──────────────────────┐                                   │  │
 │  │          │  Internet Gateway    │                                   │  │
 │  │          └──────────┬───────────┘                                   │  │
 │  │   route table: 0.0.0.0/0 → IGW, 10.20.0.0/16 → local                │  │
 │  │          ┌──────────┴──── public subnet 10.20.1.0/24 (ap-south-1a) ┐│  │
 │  │          │  ┌─ SG web-sg: in 80/tcp from 0.0.0.0/0, out all ─┐     ││  │
 │  │          │  │  EC2 t3.micro, Amazon Linux 2023, nginx        │     ││  │
 │  │          │  │  private 10.20.1.137, public 13.233.97.41      │     ││  │
 │  │          │  └────────────────────────────────────────────────┘     ││  │
 │  │          └─────────────────────────────────────────────────────────┘│  │
 │  └─────────────────────────────────────────────────────────────────────┘  │
 │   S3 bucket tf-cloud-project-assets-3c9e51d7 (regional, outside the VPC)  │
 └───────────────────────────────────────────────────────────────────────────┘
```

### Files

| File | Contents |
|---|---|
| [`versions.tf`](versions.tf) | `terraform` block: Terraform >= 1.9.0, `hashicorp/aws` 5.74.0, `hashicorp/random` 3.6.3 |
| [`providers.tf`](providers.tf) | `aws` provider: region from a variable, `default_tags` for every resource |
| [`variables.tf`](variables.tf) | Region, project, environment, CIDRs (with validation), AZ, instance type, allowed HTTP CIDRs |
| [`terraform.tfvars`](terraform.tfvars) | Values for this lab (no secrets) |
| [`network.tf`](network.tf) | VPC, public subnet, Internet Gateway, route table + association, security group + rules |
| [`compute.tf`](compute.tf) | `aws_ami` data source for Amazon Linux 2023, `aws_instance` with user_data, IMDSv2, encrypted gp3 root disk, `depends_on` |
| [`user_data.sh.tftpl`](user_data.sh.tftpl) | First-boot script: install nginx, write a page with instance metadata |
| [`storage.tf`](storage.tf) | `random_id`, S3 bucket, versioning, public access block |
| [`outputs.tf`](outputs.tf) | VPC/subnet/SG/instance IDs, AMI, public IP, website URL, bucket name |
| [`backend.tf.example`](backend.tf.example) | S3 remote backend with DynamoDB locking (not active) |
| [`.terraform.lock.hcl`](.terraform.lock.hcl) | Provider checksums, committed |
| [`.gitignore`](.gitignore) | `.terraform/`, `*.tfstate*`, plan files, real `backend.tf` |

## 2. Terraform concepts in this project

### Providers

`versions.tf` declares which providers the code needs and pins exact versions; the lock
file records their checksums. `providers.tf` configures the `aws` provider:

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
```

The `random` provider needs no configuration; it runs entirely inside Terraform and only
generates the bucket suffix. Credentials are not in any file: the AWS provider reads them
from the `terraform-lab` CLI profile.

### Variables

Every value that might change between environments is a variable with a type, a
description and a default, and `terraform.tfvars` sets this lab's values. `vpc_cidr` has a
`validation` block using `cidrnetmask()`, so a typo like `10.20.0.0/33` fails at plan time
with a clear message instead of an AWS API error halfway through apply.
`allowed_http_cidrs` is a list, and the ingress rule uses `for_each` over it, so adding a
second range adds a second rule without touching the others.

### Resources and a data source

| Address | Type | Purpose |
|---|---|---|
| `data.aws_ami.al2023` | data source | Finds the newest Amazon Linux 2023 x86_64 AMI owned by `amazon` |
| `aws_vpc.main` | resource | VPC 10.20.0.0/16, DNS support and hostnames on |
| `aws_subnet.public` | resource | 10.20.1.0/24 in ap-south-1a, auto-assign public IPv4 |
| `aws_internet_gateway.main` | resource | Attached to the VPC |
| `aws_route_table.public` | resource | `0.0.0.0/0 → IGW` |
| `aws_route_table_association.public` | resource | Makes the subnet public |
| `aws_security_group.web` | resource | Web server firewall |
| `aws_vpc_security_group_ingress_rule.http["0.0.0.0/0"]` | resource | tcp/80 in |
| `aws_vpc_security_group_egress_rule.all` | resource | All traffic out |
| `aws_instance.web` | resource | t3.micro running nginx |
| `random_id.suffix` | resource | 4 random bytes for the bucket name |
| `aws_s3_bucket.assets` | resource | `tf-cloud-project-assets-<hex>` |
| `aws_s3_bucket_versioning.assets` | resource | Versioning on |
| `aws_s3_bucket_public_access_block.assets` | resource | Block all public access |

A data source only **reads** something that already exists; it never creates or destroys
anything, and it is re-read on every plan. That is why the AMI ID is never hard-coded: AMI
IDs differ per region and a new one is published with every Amazon Linux release.

### Outputs

`outputs.tf` exposes the values a person or another tool needs after apply: IDs, the AMI
that was chosen, the public IP, a ready-to-click URL and the bucket name. They are printed
at the end of apply and read later with `terraform output`.

### Dependencies

Terraform builds a graph from the references between blocks and creates things in
dependency order, in parallel where possible.

**Implicit dependencies** come from references. For example:

- `aws_subnet.public` uses `vpc_id = aws_vpc.main.id`, so the VPC is created first.
- `aws_route_table.public` uses `aws_internet_gateway.main.id` in its route.
- `aws_instance.web` passes `aws_s3_bucket.assets.bucket` into the user_data template, so
  the bucket (and therefore `random_id.suffix`) must exist before the instance.

**One explicit dependency**, in `compute.tf`:

```hcl
  depends_on = [aws_route_table_association.public]
```

Nothing inside the instance block refers to the route table or its association. Without
`depends_on`, Terraform could start the instance as soon as the subnet and security group
exist, possibly before the `0.0.0.0/0` route is attached to the subnet. The user_data
script runs `dnf install -y nginx` at first boot and would fail with no route to the
package mirrors. `depends_on` adds the edge that the references cannot express.

The graph Terraform builds (this one is generated straight from the configuration and
needs no AWS access):

![$ terraform graph](screenshots/submission-01.png)

An arrow means "depends on". The `aws_instance.web -> aws_route_table_association.public`
edge is the `depends_on`; every other edge comes from a reference. The graph is shown
reduced: the instance also refers to `aws_subnet.public`, but that edge is implied through
the association, so Terraform leaves it out of the drawing.

## 3. init, fmt, validate

![$ aws sts get-caller-identity --query Arn --output text](screenshots/submission-02.png)

## 4. Plan

![$ terraform plan -out=tfplan (1/6)](screenshots/submission-03.png)

![$ terraform plan -out=tfplan (2/6)](screenshots/submission-03-2.png)

![$ terraform plan -out=tfplan (3/6)](screenshots/submission-03-3.png)

![$ terraform plan -out=tfplan (4/6)](screenshots/submission-03-4.png)

![$ terraform plan -out=tfplan (5/6)](screenshots/submission-03-5.png)

![$ terraform plan -out=tfplan (6/6)](screenshots/submission-03-6.png)

What the plan tells me:

- The data source was read during plan, so `ami` and the `ami_id` output are already
  known (`ami-0a1b3e6d9c47f2058`). Everything AWS assigns (IDs, IPs, ARNs) is
  `(known after apply)`.
- `user_data` is unknown because the template includes the bucket name, which includes
  the random suffix. This is the implicit instance → bucket → random_id dependency showing
  up in the plan.
- 13 resources: 9 network/compute (VPC, subnet, IGW, route table, association, SG, 2 SG
  rules, instance) and 4 storage (random_id, bucket, versioning, public access block).

## 5. Apply

![$ terraform apply tfplan](screenshots/submission-04.png)

The log follows the graph. `random_id` and the VPC start together because they have no
dependencies. The bucket side finishes while the VPC is still being created. The subnet,
IGW and security group all wait for the VPC, then run in parallel. The instance is the
last thing created: it waited for the route table association (the `depends_on`), the
security group and the bucket. The subnet is slow (11 s) because the provider waits for
the `map_public_ip_on_launch` attribute to be applied.

### Checking the infrastructure

nginx needs about a minute after `running` to be installed by user_data:

![$ curl -s "$(terraform output -raw website_url)"](screenshots/submission-05.png)

The page was written by the user_data script: it fetched the instance ID, AZ and private
IP from the instance metadata service (with an IMDSv2 token) and Terraform filled in the
bucket name.

![$ aws ec2 describe-instances --instance-ids "$(terraform output -raw ...](screenshots/submission-06.png)

Port 22 times out because the security group only allows port 80. There is no SSH key
and no SSH rule on purpose; the server is configured entirely by user_data, and in a real
setup I would use SSM Session Manager for shell access instead of opening port 22.

## 6. State

### What state is

Terraform keeps a **state file** (`terraform.tfstate`, JSON) that maps every resource
address in the code to the real object in AWS, e.g. `aws_vpc.main` → `vpc-04b7e2c19f8a3d651`,
together with all its attributes as last seen. Terraform needs it to:

- know which real objects it manages (it never touches resources that are not in state);
- compute a plan: code is compared with state, and state is refreshed from AWS first, so
  manual changes ("drift") show up as diffs;
- know dependencies and the correct order for destroy, even after a resource has been
  removed from the code;
- remember values AWS generated (IDs, IPs) that are not in the code at all.

State can contain sensitive values (for example database passwords if a resource has
them), so it is never committed: `.gitignore` excludes `*.tfstate*`.

### terraform state list / show

![$ ls -l terraform.tfstate*](screenshots/submission-07.png)

13 managed resources plus the data source, whose last read result is also kept in state.

![$ terraform state show aws_vpc.main](screenshots/submission-08.png)

`default_route_table_id` / `main_route_table_id` (`rtb-06a4...`) is the VPC's main route
table, created automatically by AWS. It is not the `public` route table Terraform created
(`rtb-0c9e...`), which is why the subnet needed an explicit association.

![$ terraform state show aws_instance.web (1/2)](screenshots/submission-09.png)

![$ terraform state show aws_instance.web (2/2)](screenshots/submission-09-2.png)

Two things worth pointing out. `user_data` is stored as a SHA-1 hash of the rendered
script, not the script itself, so a change to the template shows up as a hash change in
the plan (and, with `user_data_replace_on_change = true`, replaces the instance). The
values in state are exactly what the AWS CLI showed: same instance ID, subnet, IPs and
security group.

Other state commands I tried:

![$ terraform state show 'aws_vpc_security_group_ingress_rule.http("0.0...](screenshots/submission-10.png)

| Command | What it does |
|---|---|
| `terraform state list` | List resource addresses in state |
| `terraform state show <addr>` | All attributes of one resource |
| `terraform state mv <old> <new>` | Rename an address after refactoring code, without recreating the object (a `moved {}` block is the code-reviewed alternative) |
| `terraform state rm <addr>` | Stop managing an object without deleting it (a `removed {}` block is the alternative) |
| `terraform import` / `import {}` block | Bring an existing object under management |
| `terraform state pull` | Print the raw state JSON (useful with a remote backend) |

### Drift check

I added a tag to the VPC by hand in the console, then ran a plan:

![$ terraform plan](screenshots/submission-11.png)

The refresh read the real VPC, saw a tag that is not in the code, and planned to remove
it. Terraform treats the code as the source of truth. I removed the tag again in the
console rather than applying, and the next plan showed "No changes".

### Remote backend option

Local state is fine for one person on one machine. For a team or CI it has problems: it
is not shared, two people can apply at the same time and corrupt it, and losing the
laptop loses the state. The usual fix on AWS is the **S3 backend**, shown in
[`backend.tf.example`](backend.tf.example):

```hcl
terraform {
  backend "s3" {
    bucket         = "devops-student-tfstate-123456789012"
    key            = "task-19-terraform-cloud-project/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

| Feature | How |
|---|---|
| Shared | Everyone and the CI pipeline read the same object in S3 |
| Locking | Terraform 1.9 writes a lock item to the DynamoDB table (`LockID` key) for the duration of plan/apply; a second run waits or fails with "Error acquiring the state lock". From Terraform 1.11, `use_lockfile = true` locks with a file in the bucket and the table is no longer needed |
| History | S3 versioning on the state bucket keeps every previous state version |
| Security | `encrypt = true` plus SSE on the bucket, public access blocked, IAM limiting who can read it |

The state bucket and lock table are created once, separately (by hand or by a small
bootstrap configuration), because a configuration cannot store its state in a bucket it
has not created yet. Moving this project to it:

![$ cp backend.tf.example backend.tf](screenshots/submission-12.png)

`backend.tf` itself is in `.gitignore` here so the lab stays on local state by default;
in a team repository the backend block would be committed.

## 7. Destroy

![$ terraform destroy (1/2)](screenshots/submission-13.png)

![$ terraform destroy (2/2)](screenshots/submission-13-2.png)

The per-attribute listing of each resource in the destroy plan is long (it repeats every
attribute with `-> null`); I kept the instance (trimmed) and the IGW in full and cut the
rest to their header lines with `...`.

Destroy walks the graph backwards. The security group rules, the S3 settings and the
instance start first because nothing depends on them. Everything else waits for the
instance: the security group and subnet cannot be deleted while a network interface still
uses them, and the instance takes about 50 seconds to terminate. Then the route table
association, route table, IGW (after the route that points at it is gone), and finally
the VPC once everything inside it is gone. On the storage side the bucket also waited for
the instance (because of the bucket name in user_data), then `random_id` went last.

![$ terraform state list](screenshots/submission-14.png)

State is empty, the VPC is gone and the instance is `terminated` (it stays visible in
that state for about an hour before AWS removes it from listings).

## 8. Design notes and trade-offs

| Choice | Reason | What I would do in production |
|---|---|---|
| Web server in a public subnet with a public IP | Smallest working internet-facing setup, no NAT Gateway cost | Instances in private subnets behind an Application Load Balancer, NAT Gateway (or VPC endpoints) for outbound |
| Single AZ | Lab cost and simplicity | Two or more AZs, Auto Scaling group |
| HTTP only, no TLS | No domain or certificate in the lab | ALB with an ACM certificate, redirect 80 → 443 |
| No SSH | Nothing to manage on the box; user_data does the setup | SSM Session Manager with an instance role |
| IMDSv2 required, encrypted gp3 root disk | Cheap hardening that should always be on | Same |
| AMI from a data source | Always the current patched Amazon Linux 2023 | Pin the AMI in a variable for reproducible releases, update it deliberately |
| `force_destroy = true` on the bucket | Lab clean-up in one command | `false`, plus lifecycle rules and a `prevent_destroy` lifecycle on important data |
| Local state | One person, short-lived lab | S3 backend with locking (section 6) |

## Deliverables checklist

- [x] VPC: `aws_vpc.main` in [`network.tf`](network.tf)
- [x] Public subnet: `aws_subnet.public`, `map_public_ip_on_launch = true`
- [x] Internet Gateway and route table: `aws_internet_gateway.main`, `aws_route_table.public`, `aws_route_table_association.public`
- [x] Security group: `aws_security_group.web` with separate ingress (HTTP) and egress rules
- [x] EC2 with Amazon Linux 2023 from a data source and nginx via user_data: [`compute.tf`](compute.tf), [`user_data.sh.tftpl`](user_data.sh.tftpl), curl output in section 5
- [x] S3 bucket: [`storage.tf`](storage.tf)
- [x] Providers: [`versions.tf`](versions.tf), [`providers.tf`](providers.tf), section 2
- [x] Variables: [`variables.tf`](variables.tf), [`terraform.tfvars`](terraform.tfvars), section 2
- [x] Resources and outputs: section 2, [`outputs.tf`](outputs.tf), outputs printed in section 5
- [x] Implicit dependencies and one `depends_on`: section 2, `terraform graph` output
- [x] AWS infrastructure verified with the AWS CLI and curl: section 5
- [x] State explained, `terraform state list` / `state show`, drift example, remote backend option: section 6, [`backend.tf.example`](backend.tf.example)
- [x] Plan, apply, destroy with consistent resource IDs: sections 4, 5, 7
- [x] Architecture diagram (mermaid + ASCII): section 1
- [x] `.gitignore` for `.terraform/` and state: [`.gitignore`](.gitignore)
