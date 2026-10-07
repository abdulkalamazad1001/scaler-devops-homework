variable "aws_region" {
  description = "AWS region to create the bucket in."
  type        = string
  default     = "ap-south-1"
}

variable "bucket_prefix" {
  description = "Start of the bucket name. A random suffix is added because bucket names are global."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,40}$", var.bucket_prefix))
    error_message = "bucket_prefix must be 3-41 characters of lowercase letters, digits and hyphens."
  }
}

variable "project" {
  description = "Project tag applied to every resource."
  type        = string
  default     = "terraform-s3-demo"
}

variable "environment" {
  description = "Environment tag applied to every resource."
  type        = string
  default     = "dev"
}

variable "enable_versioning" {
  description = "Keep old versions of objects when they are overwritten or deleted."
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Allow terraform destroy to delete the bucket even if it still has objects. Fine for a lab, false for real data."
  type        = bool
  default     = false
}
