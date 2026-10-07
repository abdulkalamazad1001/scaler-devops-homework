provider "aws" {
  region = var.aws_region

  # Every resource gets these tags, which makes cost tracking and clean-up easy.
  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
