data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.21.0"

  name                 = "${var.cluster_name}-vpc"
  cidr                 = "10.42.0.0/16"
  azs                  = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnets       = ["10.42.1.0/24", "10.42.2.0/24"]
  private_subnets      = ["10.42.11.0/24", "10.42.12.0/24"]
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  public_subnet_tags   = { "kubernetes.io/role/elb" = "1" }
  private_subnet_tags  = { "kubernetes.io/role/internal-elb" = "1" }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.37.0"

  cluster_name                             = var.cluster_name
  cluster_version                          = var.kubernetes_version
  cluster_endpoint_private_access          = true
  cluster_endpoint_public_access           = true
  cluster_endpoint_public_access_cidrs     = var.api_allowed_cidrs
  enable_cluster_creator_admin_permissions = true
  enable_irsa                              = true
  vpc_id                                   = module.vpc.vpc_id
  subnet_ids                               = module.vpc.private_subnets
  cluster_enabled_log_types                = ["api", "audit", "authenticator"]
  cluster_addons = {
    vpc-cni    = { before_compute = true }
    coredns    = {}
    kube-proxy = {}
    aws-ebs-csi-driver = {
      service_account_role_arn = module.ebs_csi.iam_role_arn
    }
  }
  eks_managed_node_groups = {
    application = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.node_instance_types
      min_size       = 1
      desired_size   = 2
      max_size       = 3
      disk_size      = 30
    }
  }
}

module "ebs_csi" {
  source                = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version               = "5.60.0"
  role_name             = "${var.cluster_name}-ebs-csi"
  attach_ebs_csi_policy = true
  oidc_providers = {
    cluster = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
}
