#!/usr/bin/env bash
# Installs kubectl v1.31.1 and minikube v1.34.0 on Ubuntu 24.04 (amd64) and starts
# a single node cluster on the docker driver. Docker must already be installed and
# the current user must be in the docker group.
set -euo pipefail

KUBECTL_VERSION="v1.31.1"
MINIKUBE_VERSION="v1.34.0"
K8S_VERSION="v1.31.0"

cd "$(mktemp -d)"

# kubectl, checked against the published sha256
curl -fsSLO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
curl -fsSLO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# minikube
curl -fsSLO "https://storage.googleapis.com/minikube/releases/${MINIKUBE_VERSION}/minikube-linux-amd64"
sudo install minikube-linux-amd64 /usr/local/bin/minikube

kubectl version --client
minikube version

# Plain "*" bullets instead of emoji in minikube output
export MINIKUBE_IN_STYLE=false

minikube config set driver docker
minikube config set cpus 2
minikube config set memory 4096
minikube start --kubernetes-version="${K8S_VERSION}"

minikube status
kubectl get nodes -o wide
