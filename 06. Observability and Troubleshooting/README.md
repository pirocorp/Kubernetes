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
    # Exec liveness probe - check if /tmp/healthy file exists.
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

### Readiness Probes

Indicate whether a container is ready to respond to requests. If it fails, then the endpoints controller removes the pod’s IP address from the endpoints of all services that match the pod. A pod is considered ready when all its containers are ready. The default state, before the initial delay is Failure. If no readiness probe is provided it is considered as if it was there and the return status is Success.

#### Exec Probe

Exec is used to exec a specified command inside the container. If the return code is 0 is considered successful.

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: readiness-cmd
  name: readiness-cmd
spec:
  # In the case of the example, the init container makes an index file.
  initContainers:
  - name: init-data
    image: alpine
    command: ["/bin/sh", "-c"]
    args:
      - echo '(Almost) Always Ready to Serve ;)' > /data/index.html
    volumeMounts:
    - name: data
      mountPath: /data
  containers:
  - name: cont-main
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
    - name: check
      mountPath: /check
    # Rediness exec probe - check if /check/healthy file exists.
    readinessProbe:
      exec:
        command:
        - cat
        - /check/healthy
      initialDelaySeconds: 5
      periodSeconds: 5
    # The first sidecar container simulates application startup before creating file /check/healthy.
  - name: cont-sidecar-postpone
    image: alpine
    command: ["/bin/sh", "-c"]
    args:
      - while true; do
          sleep 20; 
          touch /check/healthy; 
          sleep 60;
        done
    volumeMounts:
    - name: check
      mountPath: /check
    # The second sidecar container simulates the breaking of the application.
  - name: cont-sidecar-break
    image: alpine
    command: ["/bin/sh", "-c"]
    args:
      - while true; do
          sleep 60; 
          rm /check/healthy;
          sleep 20;
        done
    volumeMounts:
    - name: check
      mountPath: /check
  volumes:
  - name: data
    emptyDir: {}
  - name: check
    emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: readiness-cmd
  labels:
    app: readiness-cmd
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: readiness-cmd
```

#### HTTP Probe

HTTP makes a GET request against the pod’s IP address on a specified port and path. It is considered successful if the status code is between 200 and 399

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: readiness-http
  name: readiness-http
spec:
  initContainers:
  - name: init-data
    image: alpine
    command: ["/bin/sh", "-c"]
    args:
      - echo '(Almost) Always Ready to Serve ;)' > /data/index.html
    volumeMounts:
    - name: data
      mountPath: /data
  containers:
  - name: cont-main
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
    readinessProbe:
      httpGet:
        path: /healthy.html
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
  - name: cont-sidecar-postpone
    image: alpine
    command: ["/bin/sh", "-c"]
    args:
      - while true; do
          sleep 20; 
          echo 'WORKING' > /check/healthy.html; 
          sleep 60;
        done
    volumeMounts:
    - name: data
      mountPath: /check
  - name: cont-sidecar-break
    image: alpine
    command: ["/bin/sh", "-c"]
    args:
      - while true; do
          sleep 60; 
          rm /check/healthy.html;
          sleep 20;
        done
    volumeMounts:
    - name: data
      mountPath: /check
  volumes:
  - name: data
    emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: readiness-cmd
  labels:
    app: readiness-cmd
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: readiness-cmd
```

### Startup Probes

Indicate whether the application in the container is started. If it fails, then kubelet kills the container. After that, the container is subject to the restart policy. All other probes are disabled if a startup probe is present until it succeeds. If no startup probe is provided it is considered as if it was there and the return status is Success.

#### Exec Probe

Exec is used to exec a specified command inside the container. If the return code is 0 is considered successful.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: startup-same
spec:
  containers:
  - name: startup
    image: alpine
    command: ["/bin/sh", "-c"]
    args:
    - t=$(( 10 + $RANDOM % 100 )); echo 'Sleep for '$t; sleep $t; touch /tmp/healthy; sleep 60; rm -rf /tmp/healthy; sleep 600
    # Liveness probe check if file /tmp/healthy is present
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      initialDelaySeconds: 5
      periodSeconds: 5
    # Startup probe check if file /tmp/healthy is present
    startupProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      # Number of failed attempts
      failureThreshold: 22
      periodSeconds: 5
```
