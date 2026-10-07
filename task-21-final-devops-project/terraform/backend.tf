# State is local by default so `terraform init` works for anyone.
# For a team, keep state in S3 with locking. Create the bucket once, then
# uncomment and run `terraform init -migrate-state`.
#
# terraform {
#   backend "s3" {
#     bucket       = "devops-student-tfstate-123456789012"
#     key          = "final-devops-project/terraform.tfstate"
#     region       = "ap-south-1"
#     encrypt      = true
#     use_lockfile = true
#   }
# }
