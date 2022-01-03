# Health and Status Checks (Probes)

Periodic checks executed by the **kubelet** against containers. Those checks are known as **probes**. They can be **liveness**, **readiness**, and **startup** probes. Their status can be either **Success**, **Failure**, or **Unknown**. Used for a better control over the container and pod lifecycle and better integration with other objects.

## Check Methods

Each probe type can use either **Exec**, **HTTP**, or **TCP** method

- **Exec** is used to **exec a specified command** inside the container. It is considered **successful** if the **return code** is **0**.
- **HTTP** makes a **GET request** against the pod’s **IP address** on a **specified port** and **path**. It is considered **successful** if the **status code is between 200 and 399**.
- **TCP** performs a check against the pod’s **IP address** on a **specified port**. It is considered **successful** if the **port is open**.

## Common Fields

- **initialDelaySeconds** sets the number of seconds to wait before a probe to be initiated. **Defaults** to **0** with **minimal value** of **0**.
- **periodSeconds** sets how often (in seconds) a probe to be performed. **Defaults** to **10** with **minimal value** of **1**.
- **timeoutSeconds** sets the number of seconds before a probe times out. **Defaults** to **1** with **minimal value** of **1**.
- **successThreshold** sets the minimum consecutive successes for a probe to be considered successful after a failure. **Defaults** to **1** with **minimal value** of **1**.
- **failureThreshold** sets the number of times for Kubernetes to try failing probe before giving up (for **liveness – restart**, for **readiness – unready**). Defaults to **3** with **minimal value** of **1**.


## Liveness Probes 

- Indicate whether a **container is running**.
- If it fails, then **kubelet** kills the container.
- After that, the container is **subject** to the **restart policy**.
- It can be **Always**, **OnFailure**, and **Never**. The default is **Always**.
- The **restart policy** is defined on **pod level** and applicable to **all containers** in the pod.
- If no liveness probe is provided it is considered as if it was there and the return status is **Success**.

The kubelet uses liveness probes to know when to restart a container. For example, liveness probes could catch a deadlock, where an application is running, but unable to make progress. Restarting a container in such a state can help to make the application more available despite bugs.

### Exec Liveness Probe

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

### HTTP Liveness Probe

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

## Readiness Probes

- Indicate whether a container is **ready to respond to requests**.
- If it **fails**, then the **endpoints controller removes** the **pod’s IP address** from the **endpoints** of **all services** that match the pod.
- A pod is considered ready when all its containers are ready.
- The default state, before the initial delay is Failure.
- If no readiness probe is provided it is considered as if it was there and the return status is **Success**.

The kubelet uses readiness probes to know when a container is ready to start accepting traffic. A Pod is considered ready when all of its containers are ready. One use of this signal is to control which Pods are used as backends for Services. When a Pod is not ready, it is removed from Service load balancers.

### Exec Readiness Probe

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

### HTTP Readiness Probe

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

## Startup Probes (startupProbe)

- Indicate whether the application in the container is **started**.
- If it fails, then **kubelet** kills the container.
- After that, the container is **subject** to the **restart policy**.
- All **other probes** are **disabled** if a startup probe is present **until it succeeds**.
- If no startup probe is provided it is considered as if it was there and the return status is **Success**.

The kubelet uses startup probes to know when a container application has started. If such a probe is configured, it disables liveness and readiness checks until it succeeds, making sure those probes don't interfere with the application startup. This can be used to adopt liveness checks on slow starting containers, avoiding them getting killed by the kubelet before they are up and running.

### Exec Startup Probe

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

### Mixed Startup Probe

HTTP makes a GET request against the pod’s IP address on a specified port and path. It is considered successful if the status code is between 200 and 399

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: startup-mixed
  name: startup-mixed
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
    livenessProbe:
      httpGet:
        path: /healthy.html
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
    startupProbe:
      exec:
        command:
        - cat
        - /usr/share/nginx/html/healthy.html
      failureThreshold: 10
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
  name: startup-mixed
  labels:
    app: startup-mixed
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: startup-mixed
```


# Manifest files explanations (YAML)


## Part 2

### Auditing and Logging

#### Auditing

Actions in the cluster are captured in chronological order. They can be initiated by the users, applications, or control plane. Answers who did what and when on what and what happened. Audit records begin their existence in the kube-apiserver. Each request on each stage of its execution generated an event. It is pre-processed according to the policy and send to a backend. Following stages are available **RequestReceived**, **ResponseStarted**, **ResponseComplete**, and **Panic**. Audit logging may increase the memory consumption.

##### Audit Policy

Defines the rules about what events should be captured and what data they should include. During processing, an event is compared against the list of rules in order. First match sets the audit level of the event. The available audit levels are None, Metadata, Request, and RequestResponse. A policy to be valid, should have at least one rule.

The policy is configured in the kube-apiserver manifest ```/etc/kubernetes/manifests/kube-apiserver.yaml```

In the ```volumes``` section add

```yaml
  - hostPath: 
      path: /var/lib/k8s-audit/1-audit-simple.yaml
      type: File
    name: audit-policy
  - hostPath:
      path: /var/log/k8s-audit/audit.log
      type: FileOrCreate
    name: audit-log
```

In the ```volumesMounts``` section add

```yaml
  - mountPath: /var/lib/k8s-audit/1-audit-simple.yaml
    name: audit-policy  
    readOnly: true
  - mountPath: /var/log/k8s-audit/audit.log
    name: audit-log  
    readOnly: false
```

Add parameters to the ```kube-apiserver``` in section ```containers```

```yaml
  - --audit-policy-file=/var/lib/k8s-audit/1-audit-simple.yaml
  - --audit-log-path=/var/log/k8s-audit/audit.log
```

###### Simple Audit Policy

```yaml
# Log all requests at the Metadata level.
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
```

###### Audit Policy

Change kube-apiserver manifest ```/etc/kubernetes/manifests/kube-apiserver.yaml```

In the ```volumes``` section change

```yaml
  - hostPath: 
      path: /var/lib/k8s-audit/2-audit.yaml
      type: File
    name: audit-policy
```

In the ```volumesMounts``` section change

```yaml
  - mountPath: /var/lib/k8s-audit/2-audit.yaml
    name: audit-policy  
    readOnly: true
```

Change parameters in ```kube-apiserver``` in section ```containers```

```yaml
  - --audit-policy-file=/var/lib/k8s-audit/2-audit.yaml
```

```yaml
apiVersion: audit.k8s.io/v1 # This is required.
kind: Policy
# Don't generate audit events for all requests in RequestReceived stage.
omitStages:
  - "RequestReceived"
rules:
  # Log pod changes at RequestResponse level
  - level: RequestResponse
    resources:
    - group: ""
      # Resource "pods" doesn't match requests to any subresource of pods,
      # which is consistent with the RBAC policy.
      resources: ["pods"]
  # Log "pods/log", "pods/status" at Metadata level
  - level: Metadata
    resources:
    - group: ""
      resources: ["pods/log", "pods/status"]

  # Don't log requests to a configmap called "controller-leader"
  - level: None
    resources:
    - group: ""
      resources: ["configmaps"]
      resourceNames: ["controller-leader"]

  # Don't log watch requests by the "system:kube-proxy" on endpoints or services
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
    - group: "" # core API group
      resources: ["endpoints", "services"]

  # Don't log authenticated requests to certain non-resource URL paths.
  - level: None
    userGroups: ["system:authenticated"]
    nonResourceURLs:
    - "/api*" # Wildcard matching.
    - "/version"

  # Log the request body of configmap changes in kube-system.
  - level: Request
    resources:
    - group: "" # core API group
      resources: ["configmaps"]
    # This rule only applies to resources in the "kube-system" namespace.
    # The empty string "" can be used to select non-namespaced resources.
    namespaces: ["kube-system"]

  # Log configmap and secret changes in all other namespaces at the Metadata level.
  - level: Metadata
    resources:
    - group: "" # core API group
      resources: ["secrets", "configmaps"]

  # Log all other resources in core and extensions at the Request level.
  - level: Request
    resources:
    - group: "" # core API group
    - group: "extensions" # Version of group should NOT be included.

  # A catch-all rule to log all other requests at the Metadata level.
  - level: Metadata
    # Long-running requests like watches that fall under this rule will not
    # generate an audit event in RequestReceived.
    omitStages:
      - "RequestReceived"
```

#### Logging

Logs help us understand what is happening in our applications and cluster. They are used for debugging problems and monitoring activity. Most applications use logging either on the stdout/stderr or in a file. Container engines/runtimes even though providing logging capabilities are usually not enough. We need to access the logs even if and after a container or node crashes. Thus, we need a cluster-level logging solution that will store logs elsewhere and they will have different lifecycle compared to the resources or nodes in the cluster.

##### Basic Logging

The most basic form of logging is for containers to emit messages on their **stdout/stderr**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: counter
spec:
  containers:
  - name: count
    image: alpine
    args: [/bin/sh, -c,
            'i=0; while true; do echo "$i: $(date)"; i=$((i+1)); if [ -f /stop.file ]; then exit; fi; sleep 5; done']
```

##### Streaming Sidecar

One application container with two different log files and two streaming sidecar containers – one for each log file

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: counter
spec:
  containers:
  - name: main
    image: busybox
    args:
    - /bin/sh
    - -c
    - >
      i=0;
      while true;
      do
        echo "$i: $(date)" >> /var/log/1.log;
        echo "$(date) INFO $i" >> /var/log/2.log;
        i=$((i+1));
        if [ -f /stop.file ]; then exit; fi;
        sleep 5;
      done      
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  - name: sidecar-1
    image: busybox
    args: [/bin/sh, -c, 'tail -n+1 -f /var/log/1.log']
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  - name: sidecar-2
    image: busybox
    args: [/bin/sh, -c, 'tail -n+1 -f /var/log/2.log']
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  volumes:
  - name: varlog
    emptyDir: {}
```
