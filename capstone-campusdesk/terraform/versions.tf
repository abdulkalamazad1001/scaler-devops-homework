terraform {
  # terraform-aws-modules/eks 20.37.0 needs >= 1.3.2 (vpc 5.21.0, kms 2.1.0 and
  # iam 5.60.0 need >= 1.0); nothing in this root module needs a newer release.
  required_version = ">= 1.3.2, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.95"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project = "CampusDesk"
      Student = "T. Abdul Kalam Azad"
      Roll    = "24BCS10053"
      Managed = "Terraform"
    }
  }
}
