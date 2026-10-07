variable "aws_region" {
  description = "AWS region for every resource."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Short name used in resource names and tags."
  type        = string
  default     = "taskboard"
}

variable "environment" {
  description = "Environment name, used in tags."
  type        = string
  default     = "dev"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "taskboard-eks"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Pick one that is in standard support to avoid extended-support charges."
  type        = string
  default     = "1.33"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC. Subnets are /24s carved out of it."
  type        = string
  default     = "10.20.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr must be a valid CIDR block, for example 10.20.0.0/16."
  }
}

variable "az_count" {
  description = "Number of availability zones (one public and one private subnet in each)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "EKS needs subnets in at least two AZs; this project supports 2 or 3."
  }
}

variable "node_instance_types" {
  description = "Instance types for the managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "api_allowed_cidrs" {
  description = "CIDRs allowed to reach the public EKS API endpoint, e.g. [\"203.0.113.10/32\"] for your own IP."
  type        = list(string)

  validation {
    condition     = length(var.api_allowed_cidrs) > 0 && !contains(var.api_allowed_cidrs, "0.0.0.0/0")
    error_message = "Give at least one CIDR and do not open the Kubernetes API to 0.0.0.0/0."
  }
}
