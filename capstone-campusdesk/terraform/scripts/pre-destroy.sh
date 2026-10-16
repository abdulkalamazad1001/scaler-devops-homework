#!/usr/bin/env bash
# Remove Kubernetes-created AWS resources (load balancers, EBS volumes) so that
# `terraform destroy` does not hang on DependencyViolation errors.
#
# Usage (from anywhere):  bash terraform/scripts/pre-destroy.sh [--yes]
# Optional environment overrides: TERRAFORM, REGION, CLUSTER_NAME, VPC_ID, TIMEOUT_SECONDS
set -uo pipefail

TF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TERRAFORM="${TERRAFORM:-terraform}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-600}"
APP_NAMESPACE="campusdesk"
APP_RELEASE="campusdesk"
INGRESS_NAMESPACE="ingress-system"
INGRESS_RELEASE="traefik"
ASSUME_YES=false
[ "${1:-}" = "--yes" ] && ASSUME_YES=true

info() { printf '\n==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

for tool in aws kubectl helm "$TERRAFORM"; do
  command -v "$tool" >/dev/null 2>&1 || fail "'$tool' is not on PATH."
done

tf_output() { "$TERRAFORM" -chdir="$TF_DIR" output -raw "$1" 2>/dev/null; }

REGION="${REGION:-$(tf_output region)}"
CLUSTER_NAME="${CLUSTER_NAME:-$(tf_output cluster_name)}"
VPC_ID="${VPC_ID:-$(tf_output vpc_id)}"
[ -n "$REGION" ] || fail "Could not read 'region' from terraform output. Run from a directory with state or set REGION."
[ -n "$CLUSTER_NAME" ] || fail "Could not read 'cluster_name' from terraform output. Set CLUSTER_NAME."
[ -n "$VPC_ID" ] || fail "Could not read 'vpc_id' from terraform output. Set VPC_ID."

echo "Region:  $REGION"
echo "Cluster: $CLUSTER_NAME"
echo "VPC:     $VPC_ID"
aws sts get-caller-identity --query Arn --output text || fail "AWS CLI is not authenticated (run 'aws configure')."

if [ "$ASSUME_YES" != true ]; then
  printf "This deletes the CampusDesk release, its data volumes and ALL LoadBalancer Services in '%s'.\nType the cluster name to continue: " "$CLUSTER_NAME"
  read -r answer
  [ "$answer" = "$CLUSTER_NAME" ] || fail "Confirmation did not match; nothing was changed."
fi

CLUSTER_UP=false
if aws eks describe-cluster --region "$REGION" --name "$CLUSTER_NAME" --query cluster.status --output text >/dev/null 2>&1; then
  CLUSTER_UP=true
fi

if [ "$CLUSTER_UP" = true ]; then
  info "Updating kubeconfig (context '$CLUSTER_NAME')"
  aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME" --alias "$CLUSTER_NAME" >/dev/null \
    || fail "aws eks update-kubeconfig failed."
  K=(kubectl --context "$CLUSTER_NAME")
  H=(helm --kube-context "$CLUSTER_NAME")
  "${K[@]}" get nodes >/dev/null || fail "kubectl cannot reach the cluster (see README troubleshooting: Unauthorized / API CIDR)."

  info "Uninstalling Helm releases"
  for pair in "$APP_NAMESPACE/$APP_RELEASE" "$INGRESS_NAMESPACE/$INGRESS_RELEASE"; do
    ns="${pair%%/*}"; rel="${pair##*/}"
    if "${H[@]}" status "$rel" -n "$ns" >/dev/null 2>&1; then
      echo "helm uninstall $rel -n $ns"
      "${H[@]}" uninstall "$rel" -n "$ns" --wait --timeout 5m || warn "helm uninstall $rel failed; continuing."
    else
      echo "Release $ns/$rel not installed; skipping."
    fi
  done

  info "Deleting PersistentVolumeClaims in namespace $APP_NAMESPACE (EBS volumes are deleted with them)"
  if "${K[@]}" get namespace "$APP_NAMESPACE" >/dev/null 2>&1; then
    "${K[@]}" delete pvc --all -n "$APP_NAMESPACE" --wait=true --timeout=5m || warn "PVC deletion did not finish."
  else
    echo "Namespace $APP_NAMESPACE not found; skipping."
  fi

  info "Deleting every Service of type LoadBalancer (all namespaces)"
  lb_services() {
    "${K[@]}" get svc -A -o jsonpath='{range .items[?(@.spec.type=="LoadBalancer")]}{.metadata.namespace}{"/"}{.metadata.name}{"\n"}{end}'
  }
  for svc in $(lb_services); do
    echo "kubectl delete svc ${svc##*/} -n ${svc%%/*}"
    "${K[@]}" delete svc "${svc##*/}" -n "${svc%%/*}" --wait=false
  done

  info "Waiting for LoadBalancer Services and EBS-backed PersistentVolumes to disappear"
  deadline=$((SECONDS + TIMEOUT_SECONDS))
  while :; do
    remaining_svc="$(lb_services)"
    remaining_pv="$("${K[@]}" get pv -o jsonpath='{range .items[?(@.spec.csi.driver=="ebs.csi.aws.com")]}{.metadata.name}{"\n"}{end}')"
    [ -z "$remaining_svc" ] && [ -z "$remaining_pv" ] && break
    if [ $SECONDS -ge $deadline ]; then
      [ -n "$remaining_svc" ] && warn "LoadBalancer Services still present: $remaining_svc"
      [ -n "$remaining_pv" ] && warn "EBS PersistentVolumes still present: $remaining_pv"
      break
    fi
    sleep 10
  done
  echo "Kubernetes cleanup finished."
else
  warn "EKS cluster '$CLUSTER_NAME' not found in $REGION; skipping Kubernetes cleanup and checking AWS only."
fi

info "Checking AWS for load balancers left in $VPC_ID"
deadline=$((SECONDS + TIMEOUT_SECONDS))
while :; do
  v2="$(aws elbv2 describe-load-balancers --region "$REGION" --query "LoadBalancers[?VpcId=='$VPC_ID'].LoadBalancerName" --output text)" \
    || fail "aws elbv2 describe-load-balancers failed."
  classic="$(aws elb describe-load-balancers --region "$REGION" --query "LoadBalancerDescriptions[?VPCId=='$VPC_ID'].LoadBalancerName" --output text)" \
    || fail "aws elb describe-load-balancers failed."
  [ "$v2" = "None" ] && v2=""
  [ "$classic" = "None" ] && classic=""
  [ -z "$v2$classic" ] && break
  if [ $SECONDS -ge $deadline ]; then
    echo "ALB/NLB still in VPC: ${v2:-none}"
    echo "Classic ELB still in VPC: ${classic:-none}"
    fail "Load balancers remain in $VPC_ID. Delete them in the EC2 console (Load Balancers) before running terraform destroy."
  fi
  echo "Waiting for AWS to delete: ${v2} ${classic}"
  sleep 15
done
echo "OK: no load balancers remain in $VPC_ID."

info "Checking for EBS volumes created by the EBS CSI driver for namespace $APP_NAMESPACE"
vols="$(aws ec2 describe-volumes --region "$REGION" \
  --filters "Name=tag:kubernetes.io/created-for/pvc/namespace,Values=$APP_NAMESPACE" \
  --query "Volumes[].[VolumeId,State]" --output text)" || warn "aws ec2 describe-volumes failed."
if [ -n "$vols" ] && [ "$vols" != "None" ]; then
  warn "EBS volumes still exist (they do not block destroy but keep costing money):"
  echo "$vols"
  echo "Delete them in EC2 > Volumes once they show 'available'."
else
  echo "OK: no CampusDesk EBS volumes remain."
fi

info "Pre-destroy cleanup complete. Next: cd terraform; terraform destroy"
