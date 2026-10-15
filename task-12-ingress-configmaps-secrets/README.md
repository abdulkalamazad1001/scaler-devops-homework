# Ingress, ConfigMaps and Secrets

Student: T. Abdul Kalam Azad, 24BCS10053.

## Deliverables

- [ConfigMap example](01-configmap/): consume configuration through environment variables and mounted files.
- [Secret example](02-secret/): consume demonstration credentials; the committed values are not production secrets.
- [Ingress example](03-ingress/): backend apps, Services and host/path routing.
- [Ingress versus controller](ingress-vs-controller/README.md): why an Ingress object needs a controller.
- [Troubleshooting](troubleshooting/README.md): missing configuration, wrong backend/class and newline mistakes.

## Run the Configuration Labs

From this directory, on a disposable cluster:

```bash
kubectl create namespace homework-config
kubectl -n homework-config apply -f 01-configmap/
kubectl -n homework-config apply -f 02-secret/
kubectl -n homework-config wait --for=condition=Ready pod/config-demo pod/secret-demo --timeout=180s
kubectl -n homework-config exec config-demo -- printenv APP_LOG_LEVEL
kubectl -n homework-config exec config-demo -- cat /etc/config/theme.txt
kubectl delete namespace homework-config
```

Do not print real Secret values into submission logs. The Ingress lab additionally
requires the controller/class and host routing described in the write-up; applying
the Ingress YAML alone is not an end-to-end routing test. The troubleshooting
manifests intentionally contain errors and should be applied one scenario at a time.

## Evidence

- [Assignment write-up and commands](submission.md)
- [Current verification results and remaining work](../review/README.md)

The output and terminal-style images in the original write-up are labelled expected
output, not captures from a live deployment. Current test logs are kept separately
under the project review. Validation alone does not prove every exercise was run.
