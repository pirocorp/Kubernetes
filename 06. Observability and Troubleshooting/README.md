# Health and Status Checks ([Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

Periodic checks executed by the **kubelet** against containers. Those checks are known as **probes**. They can be **liveness**, **readiness**, and **startup** probes. Their status can be either **Success**, **Failure**, or **Unknown**. Used for a better control over the container and pod lifecycle and better integration with other objects.

## Check Methods

Each probe type can use either **Exec**, **HTTP**, or **TCP** method

- **Exec** is used to **exec a specified command** inside the container. It is considered **successful** if the **return code** is **0**.
- **HTTP** makes a **GET request** against the pod’s **IP address** on a **specified port** and **path**. It is considered **successful** if the **status code is between 200 and 399**.
- **TCP** performs a check against the pod’s **IP address** on a **specified port**. It is considered **successful** if the **port is open**.

## [Common Fields](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#configure-probes)

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

# [Auditing](https://kubernetes.io/docs/tasks/debug-application-cluster/audit/)

Actions in the cluster are captured in chronological order. They can be initiated by the users, applications, or control plane. Answers who did what and when on what and what happened. Audit records begin their existence in the **kube-apiserver**. Each request on each stage of its execution generated an event. It is pre-processed according to the policy and send to a backend. Following stages are available **RequestReceived**, **ResponseStarted**, **ResponseComplete**, and **Panic**. Audit logging may increase the memory consumption.

Kubernetes auditing provides a security-relevant, chronological set of records documenting the sequence of actions in a cluster. The cluster audits the activities generated by users, by applications that use the Kubernetes API, and by the control plane itself.

Audit records begin their lifecycle inside the kube-apiserver component. Each request on each stage of its execution generates an audit event, which is then pre-processed according to a certain policy and written to a backend. The policy determines what's recorded and the backends persist the records. The current backend implementations include logs files and webhooks.

Each request can be recorded with an associated stage. The defined stages are

- **RequestReceived** - The stage for events generated as soon as the audit handler receives the request, and before it is delegated down the handler chain.
- **ResponseStarted** - Once the response headers are sent, but before the response body is sent. This stage is only generated for long-running requests (e.g. watch).
- **ResponseComplete** - The response body has been completed and no more bytes will be sent.
- **Panic** - Events generated when a panic occurred.

## [Audit Policy](https://kubernetes.io/docs/tasks/debug-application-cluster/audit/#audit-policy)

Defines the rules about what events should be captured and what data they should include. During processing, an event is compared against the list of rules in order. First match sets the audit level of the event. The available audit levels are **None**, **Metadata**, **Request**, and **RequestResponse**. A policy to be valid, should have at least one rule.

Audit policy defines rules about what events should be recorded and what data they should include. The audit policy object structure is defined in the audit.k8s.io API group. When an event is processed, it's compared against the list of rules in order. The first matching rule sets the audit level of the event. The defined audit levels are:

**None** - don't log events that match this rule.
**Metadata** - log request metadata (requesting user, timestamp, resource, verb, etc.) but not request or response body.
**Request** - log event metadata and request body but not response body. This does not apply for non-resource requests.
**RequestResponse** - log event metadata, request and response bodies. This does not apply for non-resource requests.

You can pass a file with the policy to **kube-apiserver** using the ```--audit-policy-file``` flag. If the flag is omitted, no events are logged. Note that the ```rules``` field must be provided in the audit policy file. A policy with no (0) rules is treated as illegal.

## [Audit backends](https://kubernetes.io/docs/tasks/debug-application-cluster/audit/#audit-backends)

Audit backends persist audit events to an external storage. Two backends are supported by default. **Log backend** writes events into the filesystem. Writes audit events to a file in **JSONlines** format. **Webhook backend** sends events to an external HTTP API. Both require kube-apiserver flags to be configured. Log backend requires two volumes and volume mounts too.

## Example:

Samples are either inspired and/or taken directly from [here](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application-introspection/)

For this, create a simple audit policy. It will log all requests on metadata level. This will include information like when, who, what, etc. but not the request or the response body

```yaml
# Log all requests at the Metadata level.
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
```

Then, copy it to the control plane node. Create a folder ```/var/lib/k8s-audit``` and copy it there. 

Next, prepare a folder to store the logs, create ```/var/log/k8s-audit```.

Change the configuration (```/etc/kubernetes/manifests/kube-apiserver.yaml```) of the **API Server**

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

Save and close the file this will give instructions to the API Server where it is and where to store the logs. Sit back and watch when the API Server will restart. It may return an error a few times, but it will start working eventually.

```bash
kubectl get pods -n kube-system -w
```

Once everything is up and running, let’s create a pod and see what happens. Start it with.

```bash
kubectl run logtest1 --image=alpine -- sleep 1d
```

Now, check if the pod is running 

```bash
kubectl get pods
```

And then check the audit log. Plenty of events for such a simple task. The output is not quite readable

```bash
cat /var/log/k8s-audit/audit.log | grep logtest1
```

Install utility like jq and use it to get a better look at what happened.

```bash
cat /var/log/k8s-audit/audit.log | grep logtest1 | jq
```

Still too much information but at least it is more readable. Check how many records we have with.

```bash
cat /var/log/k8s-audit/audit.log | grep logtest1 | jq -s length
```

Clean up and then check another sample policy. Stop and remove the pod

```bash
kubectl delete pod logtest1
```

New Policy. Then, copy it to the control plane node (folder ```/var/lib/k8s-audit```)

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

Save and close the file. Sit back and watch when the API Server will restart

```bash
kubectl get pods -n kube-system -w
```

Once everything is up and running, let’s create a pod and see what happens. Start it with

```bash
kubectl run logtest2 --image=alpine -- sleep 1d
```

Now, check if the pod is running 

```bash
kubectl get pods
```

And then check the audit log

```bash
cat /var/log/k8s-audit/audit.log | grep logtest2 | jq
```

Check how many records are there.

```bash
cat /var/log/k8s-audit/audit.log | grep logtest2 | jq -s length
```

Clean up

```bash
kubectl delete pod logtest2
```

Change the configuration (```/etc/kubernetes/manifests/kube-apiserver.yaml```) of the API Server. And remove those blocks that we added earlier. Save and close the file.


# [Logging](https://kubernetes.io/docs/concepts/cluster-administration/logging/)

Logs help us understand what is happening in our applications and cluster. They are used for debugging problems and monitoring activity. Most applications use logging either on the **stdout/stderr** or in a **file**. Container engines/runtimes even though providing logging capabilities are usually not enough. We need to access the logs even if and after a container or node crashes. Thus, we need a **cluster-level logging** solution that will store logs elsewhere and they will have different lifecycle compared to the resources or nodes in the cluster.

Application logs can help you understand what is happening inside your application. The logs are particularly useful for debugging problems and monitoring cluster activity. Most modern applications have some kind of logging mechanism. Likewise, container engines are designed to support logging. The easiest and most adopted logging method for containerized applications is writing to standard output and standard error streams.

However, the native functionality provided by a container engine or runtime is usually not enough for a complete logging solution. For example, you may want access your application's logs if a container crashes; a pod gets evicted; or a node dies. In a cluster, logs should have a separate storage and lifecycle independent of nodes, pods, or containers. This concept is called cluster-level logging.

Cluster-level logging architectures require a separate backend to store, analyze, and query logs. Kubernetes does not provide a native storage solution for log data. Instead, there are many logging solutions that integrate with Kubernetes. 

## Basic Logging

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

This pod has one container which publishes a message every five seconds on its **stdout**. Start the pod.

```bash
kubectl apply -f basic-logging.yaml
```

Now check its logs with

```bash
kubectl logs counter
```

We can use the above command in follow mode as well

```bash
kubectl logs counter --follow
```

Press **Ctrl+C** to stop following. Ask for the logs again.

```bash
kubectl logs counter
```

Now, restart the container

```bash
kubectl exec counter -- touch /stop.file
```

And check again for the logs. This will return the logs of the current instance

```bash
kubectl logs counter
```

And now for the previous

```bash
kubectl logs counter --previous
```

Cclean up

```bash
kubectl delete pod counter
```

## [Node Level](https://kubernetes.io/docs/concepts/cluster-administration/logging/#logging-at-the-node-level)

![image](https://user-images.githubusercontent.com/34960418/147955744-6567801a-c8ef-4594-8db8-9cae82cfd4ae.png)

- Even though not an ideal solution it can do the job
- We should pay attention to the following:
  - When a container is restarted, the kubelet keeps one terminated container with its logs
  - If a pod is evicted, all corresponding containers and their logs are deleted
  - We should set log rotation to do some housekeeping
  - Different container runtimes may have different requirements and capabilities
  - Not all system components are the same, so do their logs
  - Service based components log via systemd routines
  - Container based components use files in /var/log


## [Node Logging Agent](https://kubernetes.io/docs/concepts/cluster-administration/logging/#using-a-node-logging-agent)

![image](https://user-images.githubusercontent.com/34960418/147955944-05d5bf87-6df9-4885-a9e6-2ab3acceff83.png)

- This is considered cluster-level logging approach
- For this, we deploy a node logging agent on each node
- Typically, the logging agent is containerized and deployed via DaemonSet
- The agent exposes the logs and pushes them to a backend


## [Streaming Sidecar and Logging Agent](https://kubernetes.io/docs/concepts/cluster-administration/logging/#streaming-sidecar-container)

![image](https://user-images.githubusercontent.com/34960418/147954969-32844bf1-7cf7-4459-bcbb-2f463b34da62.png)

- This is considered cluster-level logging approach
- The sidecar container is publishing the log to its **stdout/stderr** and thus making it available for the **kubectl log** command.
- The sidecar container runs a logging agent, which is configured to pick up logs from an application container.
- Used to overcome limitations like separating multiple logs.
- We can have more than one sidecar container.

By having your sidecar containers write to their own **stdout** and **stderr** streams, you can take advantage of the kubelet and the logging agent that already run on each node. The sidecar containers read logs from a file, a socket, or journald. Each sidecar container prints a log to its own **stdout** or **stderr** stream.

This approach allows you to separate several log streams from different parts of your application, some of which can lack support for writing to **stdout** or **stderr**. The logic behind redirecting logs is minimal, so it's not a significant overhead. Additionally, because **stdout** and **stderr** are handled by the kubelet, you can use built-in tools like **kubectl logs**.

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

Send it to the cluster and check if started

```bash
kubectl get pods
```

Then, after a while, ask for the contents of each of the two files

```bash
kubectl exec counter -c main -- cat /var/log/1.log
kubectl exec counter -c main -- cat /var/log/2.log
```

Now, we can see them using the ```kubectl log``` command and the appropriate sidecar container

```bash
kubectl logs counter -c sidecar-1
kubectl logs counter -c sidecar-2
```

In the same manner each sidecar container may stream the logs to an external solution.

### [Sidecar with Logging Agent](https://kubernetes.io/docs/concepts/cluster-administration/logging/#sidecar-container-with-a-logging-agent)

![image](https://user-images.githubusercontent.com/34960418/147956411-65b12505-f836-4d1b-a9c2-cdf01ff6762f.png)

- This is considered cluster-level logging approach
- Used when the node-level logging agent doesn’t agree well with the application
- For this, we create a sidecar container with a logging agent that is especially configured and adjusted to the application’s needs
- These logs are not consumable by the kubectl log command


### [Exposed Directly from the Application](https://kubernetes.io/docs/concepts/cluster-administration/logging/#exposing-logs-directly-from-the-application)

![image](https://user-images.githubusercontent.com/34960418/147956664-3a1a9130-43f1-4111-b5bb-c7401984ecc1.png)


- This is considered cluster-level logging approach
- Every application pushes its logs to a backend
- Simple solution which requires every application to support the common backend which may not always be feasible

