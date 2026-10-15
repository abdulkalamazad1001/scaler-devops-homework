# Kubernetes Services and DNS

Student: T. Abdul Kalam Azad, 24BCS10053.

## Deliverables

| Topic | Files |
|---|---|
| ClusterIP, NodePort, LoadBalancer, ExternalName and headless Services | [Service examples](services/) |
| Deployment, ReplicaSet, DaemonSet and StatefulSet comparison | [Object comparison](comparison/README.md) |
| Namespace-qualified Service and StatefulSet Pod names | [FQDN exercise](fqdn/README.md) |
| DNS service discovery and troubleshooting | [CoreDNS exercise](coredns/README.md) |

## Run and Verify

Use a disposable cluster. From this directory, the ClusterIP example listens on
Service port **8080**, forwarding to the application's container port:

```bash
kubectl create namespace homework-services
kubectl -n homework-services apply -f services/01-clusterip/
kubectl -n homework-services rollout status deployment/web-clusterip
kubectl -n homework-services run client --image=busybox:1.36 --restart=Never -- sleep 3600
kubectl -n homework-services wait --for=condition=Ready pod/client --timeout=180s
kubectl -n homework-services exec client -- wget -qO- http://web-clusterip:8080
kubectl delete namespace homework-services
```

An external LoadBalancer address needs an installed implementation or cloud
provider. A pending external address on bare Kind is not proof of a broken Service.

## Evidence

- [Assignment write-up and commands](submission.md)
- [Current verification results and remaining work](../review/README.md)

The output and terminal-style images in the original write-up are labelled expected
output, not captures from a live deployment. Current test logs are kept separately
under the project review. Validation alone does not prove every exercise was run.
