terraform {
  required_version = ">= 1.11, < 2.0"
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
