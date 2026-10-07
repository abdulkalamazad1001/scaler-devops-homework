variable "aws_region" {
  description = "AWS region for every resource in this project."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project name, used in Name tags and resource names."
  type        = string
  default     = "tf-cloud-project"
}

variable "environment" {
  description = "Environment tag."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC."
  type        = string
  default     = "10.20.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block, e.g. 10.20.0.0/16."
  }
}

variable "public_subnet_cidr" {
  description = "CIDR block of the public subnet. Must sit inside vpc_cidr."
  type        = string
  default     = "10.20.1.0/24"
}

variable "availability_zone" {
  description = "Availability Zone for the public subnet."
  type        = string
  default     = "ap-south-1a"
}

variable "instance_type" {
  description = "EC2 instance type for the web server."
  type        = string
  default     = "t3.micro"
}

variable "allowed_http_cidrs" {
  description = "IPv4 ranges allowed to reach the web server on port 80."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
