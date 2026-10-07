terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.74.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.6.3"
    }
  }

  # State is local for this lab (terraform.tfstate, ignored by git).
  # backend.tf.example shows the S3 remote backend used for team work.
}
