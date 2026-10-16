output "region" {
  description = "AWS region that holds every resource in this configuration."
  value       = var.region
}

output "vpc_id" {
  description = "ID of the CampusDesk VPC (used by scripts/pre-destroy to find leftover load balancers)."
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnets (one per AZ); internet-facing load balancers are placed here."
  value       = module.vpc.public_subnets
}

output "private_subnet_ids" {
  description = "Private subnets (one per AZ) used by the EKS control plane ENIs and worker nodes."
  value       = module.vpc.private_subnets
}

output "nat_gateway_ids" {
  description = "NAT gateway IDs (a single NAT gateway is created to limit cost)."
  value       = module.vpc.natgw_ids
}

output "cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS Kubernetes API endpoint."
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "Kubernetes version running on the EKS control plane."
  value       = module.eks.cluster_version
}

output "node_group_names" {
  description = "EKS managed node group names, keyed by the node group key in main.tf."
  value       = { for key, group in module.eks.eks_managed_node_groups : key => try(split(":", group.node_group_id)[1], null) }
}

output "kubectl_context" {
  description = "kubectl context name written by the configure_kubectl command."
  value       = module.eks.cluster_name
}

output "configure_kubectl" {
  description = "Run this command to add the cluster to your kubeconfig."
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name} --alias ${module.eks.cluster_name}"
}
