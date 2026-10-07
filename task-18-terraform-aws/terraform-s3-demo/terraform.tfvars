# Values for this lab. Nothing secret goes in here: AWS credentials come from
# the environment (aws configure / AWS_PROFILE), never from Terraform files.
aws_region    = "ap-south-1"
bucket_prefix = "tf-s3-demo"
environment   = "dev"
force_destroy = true
