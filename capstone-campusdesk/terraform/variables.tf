variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  description = "EKS cluster name; also used as the prefix for the VPC and IAM role names."
  type        = string
  default     = "campusdesk-24bcs10053"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Must be a version EKS currently supports in standard support."
  type        = string
  default     = "1.35"
}

variable "api_allowed_cidrs" {
  description = "Trusted public IPs allowed to reach the EKS API, including the deployment runner."
  type        = list(string)
  validation {
    condition     = length(var.api_allowed_cidrs) > 0 && alltrue([for cidr in var.api_allowed_cidrs : can(cidrnetmask(cidr)) && cidr != "0.0.0.0/0"])
    error_message = "Supply specific trusted IPv4 CIDRs; unrestricted API access is not accepted."
  }
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed worker node group."
  type        = list(string)
  default     = ["t3.medium"]
}
