# Terraform and AWS

Student: T. Abdul Kalam Azad, 24BCS10053.

## Deliverables

- [Terraform S3 demo](terraform-s3-demo/): provider configuration, variables,
  resource configuration and outputs.
- [AWS service notes](aws-services/): IAM, EC2, S3, VPC and database services.
- [Full assignment](submission.md): initialization, planning, applying and cleanup.

## Validate Without Provisioning

With Terraform installed, from this directory:

```bash
cd terraform-s3-demo
terraform fmt -check
terraform init -backend=false
terraform validate
```

These commands check formatting, install dependencies and validate configuration;
they do not create AWS resources. A real plan/apply requires your own authorized
AWS account and may incur costs. Keep credentials, private variable files and
Terraform state out of Git. AWS execution is not claimed by the validation reports.

## Evidence

- [Assignment write-up and commands](submission.md)
- [Current verification results and remaining work](../review/README.md)

The output and terminal-style images in the original write-up are labelled expected
output, not captures from a live deployment. Current test logs are kept separately
under the project review. Validation alone does not prove every exercise was run.
