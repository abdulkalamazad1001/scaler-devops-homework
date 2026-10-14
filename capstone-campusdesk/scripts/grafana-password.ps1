$encoded = kubectl --context kind-campusdesk -n campusdesk get secret campusdesk-grafana -o jsonpath='{.data.password}'
if ($LASTEXITCODE -ne 0) { throw 'Grafana secret unavailable' }
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))
