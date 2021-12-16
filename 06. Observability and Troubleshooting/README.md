# Manifest files explanations (YAML)

## Part 1

### Liveness Probes

Indicate whether a container is running. If it fails, then kubelet kills the container. After that, the container is subject to the restart policy. It can be: Always, OnFailure, and Never. The default is Always. The restart policy is defined on pod level and applicable to all containers in the pod. If no liveness probe is provided, it is considered as if it was there and the return status is Success.

#### Exec Probe

Exec is used to exec a specified command inside the container. If the return code is 0 is considered successful.

```yaml 
apiVersion: v1
kind: Pod
metadata:
  labels:
    test: liveness
  name: liveness-cmd
spec:
  containers:
  - name: liveness
    image: busybox
    args:
    - /bin/sh
    - -c
    - touch /tmp/healthy; sleep 60; rm -rf /tmp/healthy; sleep 600
    # Exec liveness probe
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      # the number of seconds to wait before a probe to be initiated.
      initialDelaySeconds: 5
      # sets how often (in seconds) a probe to be performed.
      periodSeconds: 10
```

#### HTTP Probe

HTTP makes a GET request against the pod’s IP address on a specified port and path. It is considered successful if the status code is between 200 and 399

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    test: liveness
  name: liveness-http
spec:
  containers:
  - name: liveness
    image: k8s.gcr.io/liveness
    args:
    - /server
    # Http livenessProbe at /healthz
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
        httpHeaders:
        - name: Custom-Header
          value: Awesome
      initialDelaySeconds: 3
      periodSeconds: 3
```
