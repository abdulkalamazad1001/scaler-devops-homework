variable "region" {
  type    = string
  default = "ap-south-1"
}
variable "cluster_name" {
  type    = string
  default = "campusdesk-24bcs10053"
}
variable "kubernetes_version" {
  type    = string
  default = "1.35"
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
  type    = list(string)
  default = ["t3.medium"]
}
