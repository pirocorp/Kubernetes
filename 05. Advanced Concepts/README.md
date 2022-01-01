# [Static Pods](https://kubernetes.io/docs/tasks/configure-pod-container/static-pod/)

- Static Pods are managed directly by the **kubelet**.
- The API server is not looking after them.
- The **spec** of a static Pod **cannot refer to other API objects**.
- Their manifests are **standard** but are stored in a **specific folder**.
- Usually, this is **/etc/kubernetes/manifests**.
- And it is regulated by the **kublet configuration file**.
- We can serve static Pods from the **local filesystem** or the **web**.
- he Pod names will be **suffixed** with the **node hostname** with a leading hyphen.


Static Pods are managed directly by the kubelet daemon on a specific node, without the API server observing them. Unlike Pods that are managed by the control plane (for example, a Deployment); instead, the kubelet watches each static Pod (and restarts it if it fails).

Static Pods are always bound to one Kubelet on a specific node.

The kubelet automatically tries to create a mirror Pod on the Kubernetes API server for each static Pod. This means that the Pods running on a node are visible on the API server, but cannot be controlled from there. The Pod names will be suffixed with the node hostname with a leading hyphen.


## Example:

With static pods, instead of passing it via the API server by using for example the kubectl tool, we save it to a special folder. Special means a one which to be dedicated for this and is registered and monitored by the kubelet service.


First, log on to the control plane node. Then, let’s see some details about the **kubelet** process.

```bash
ps ax | grep /usr/bin/kubelet
```

We may notice that it is reading different parts of its configuration from different files. Let’s check the contents of the ```/var/lib/kubelet/config.yaml``` file

```bash
cat /var/lib/kubelet/config.yaml
```

There are some interesting settings here, but we are interested in this row. ```staticPodPath: /etc/kubernetes/manifests```. According to it, to create a static pod, must place its manifest into the stated folder. Should keep in mind that this will spin up the pod on the node in which folder we stored the manifest. Should we want the pod to run on another node, then we must save it in its special folder.


Now, let’s see if there are any files in the folder. Four components of the control plane are in fact running as static pods (at least in a cluster, created by kubeadm)

```bash
ls -al /etc/kubernetes/manifests
```

Check the manifest of the etcd database for example

```bash
cat /etc/kubernetes/manifests/etcd.yaml
```

Create custom static pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-pod
  labels:
    app: static-pod
spec:
  containers:
  - image: alpine
    name: main
    command: ["sleep"]
    args: ["1d"]
```

Copy it in the special folder and wait a few seconds. Then execute. The pod ran no matter that we are working on control plane node. The name of the pod has the name of the node as a suffix. 


```bash
kubectl get pods -o wide
```

To delete the pod delete the manifest from the special folder where we copied it earlier


```yaml
rm /etc/kubernetes/manifests/static-pod.yaml
```


# Multi-container Pods

Pods often have just one container. However, we may want do add more than one. This may be due to the need of a helper process, or container with the same lifecycle, etc.

There are [three common](https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/) **design patterns** for this.

- Sidecar
- Adapter
- Ambassador


# Sidecar Pattern

- **Sidecar** containers enhance the main container
- For example, it may sync the local file system with a remote repository
- Or it may parse the logs of the main container and send them somewhere
- In any case, both share the same filesystem

![image](https://user-images.githubusercontent.com/34960418/145599526-702a9b5d-d35e-4383-bc4b-56c56ddad6ba.png)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sidecar
spec:
  replicas: 3
  selector:
    matchLabels: 
      app: sidecar
  minReadySeconds: 15
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: sidecar
    spec:
      containers:
      # First container
      - name: cont-main
        image: shekeriev/k8s-appb
        imagePullPolicy: Always
        # Same volume is mounted in both containers, but on a different path
        volumeMounts:
        - name: data
          mountPath: /var/www/html/data
        ports:
        - containerPort: 80 
      # Second container
      - name: cont-sidecar
        image: alpine
        # Same volume is mounted in both containers, but on a different path
        volumeMounts:
        - name: data
          mountPath: /data
        command: ["/bin/sh", "-c"]
        args:
          - while true; do
              date >> /data/generated-data.txt;
              sleep 10;
            done
      volumes:
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: sidecar
  labels:
    app: sidecar
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: sidecar
```

# Adapter Pattern

Adapter containers are used to standardize and normalize the output. This may be done in order to prepare it for a monitoring system. This way, no matter the actual application or applications, the monitoring system will receive prepared data flow. 


![image](https://user-images.githubusercontent.com/34960418/145601960-9dc33487-d722-4a2f-a320-3626aa3ca147.png)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: adapter
spec:
  containers:
  - name: cont-main
    image: alpine
    volumeMounts:
    - name: log
      mountPath: /var/log
    command: ["/bin/sh", "-c"]
    args:
      - while true; do
          echo $(date +'%Y-%m-%d %H:%M:%S') $(uname) OP$(tr -cd 0-1 </dev/urandom | head -c 1) $(tr -cd a-z </dev/urandom | head -c 5).html RE$(tr -cd 0-1 </dev/urandom | head -c 1) >> /var/log/app.log;
          sleep 3;
        done
  - name: cont-adapter
    image: alpine
    volumeMounts:
    - name: log
      mountPath: /var/log
    command: ["/bin/sh", "-c"]
    args:
      - tail -f /var/log/app.log | sed -e 's/^/MSG:/' -e 's/OP0/GET/' -e 's/OP1/SET/' -e 's/RE0/OK/' -e 's/RE1/ER/' > /var/log/out.log
  volumes:
  - name: log
    emptyDir: {}
```

# [Init Container](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)

**Specialized containers** that **run before app containers** in a Pod. Contain utilities or setup scripts not present in an app image. **App Containers** are specified via **containers** section and the **Init Containers** are specified via **initContainers** section. Init Containers **always run to completion**. If one of them **fails**, the **kubelet** repeatedly **restarts it until it succeeds**. Each Init Container **must complete successfully** before the **next one starts**.

To specify an init container for a Pod, add the **initContainers** field into the Pod specification, as an array of **container** items (similar to the app **containers** field and its contents). 


```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-init
  labels:
    app: pod-init
spec:
# Application Containers
  containers:
  - name: cont-main
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  # Init Containers
  initContainers:
  - name: cont-init
    image: alpine
    command: ["/bin/sh", "-c"]
    args:
      - for i in $(seq 1 5); do
          echo $(date +'%Y-%m-%d %H:%M:%S') '<br />' >> /data/index.html;
          sleep 5;
        done
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: svc-init
  labels:
    app: svc-init
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: pod-init
```

# [Autoscaling](https://cloud.redhat.com/blog/kubernetes-autoscaling-3-common-methods-explained)

Environments are not static but dynamic and changing. This applies to the running pods and the resources they need. Kubernetes, being a container orchestrator, has an answer. It offers the capability to perform autoscaling of resources. There are three types:

- [Scale out the pods](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) by increasing their replica count.
- [Scale up the pods](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) by increasing their resources limits.
- [Scale out the cluster](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) by increasing the number of nodes.


Scale Out Pods (Horizontal Pod Autoscaler)

The **Horizontal Pod Autoscaler (HPA)** automatically scales the number of pods in a replication controller, deployment, replica set or stateful set based on observed CPU utilization. It is implemented as a Kubernetes API **resource** and a **controller**. The resource determines the behavior of the controller. The controller periodically adjusts the number of replicas in a replication controller or deployment. The Horizontal Pod Autoscaler is implemented as a **control loop**, with a period controlled by a flag with default value set to **15 seconds**. Both upscale and downscale intervals are also controlled by flags and their default value is set to **5 minutes**.


Scale Up Pods (Vertical Pod Autoscaler)

The **Vertical Pod Autoscaler (VPA)** maintains the resource limits and requests for the containers in their pods up to date. It can adjust the requests based on the usage. It also maintains the ratio between requests and limits. Implemented via a **Custom Resource Definition (CRD)** object and has three components. 
- **Recommender** monitors current and past resource consumption and provides recommended values. 
- **Updater** checks which resources have correct resources set and if not, kills them in order to be recreated with updated values. 
- **Admission** Plugin sets the correct resource requests on new pods


Scale Out Cluster Nodes (Cluster Autoscaler)

Like the HPA but for cluster nodes. Based on cluster utilization it can **change the number of nodes**. This is useful also for **cost optimization**. It checks for pods that cannot be scheduled on existing nodes. Then checks if node addition will solve the issue. In the same manner, if pods can be rescheduled on other nodes to utilize them better, they will be evicted from a node and then the node will be removed.


## Horizontal Pod Autoscaler Example

On a **custom made/standard Kubernetes** cluster install it by downloading the manifest

```bash
wget https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml -O metrics-server.yaml
```

Then open it and on line #137 add the following

```bash
--kubelet-insecure-tls
```

Save and close the file. Use it to install the [metrics server](https://github.com/kubernetes-sigs/metrics-server).

```bash
kubectl apply -f metrics-server.yaml
```

Autoscale deployment manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auto-scale-deploy
spec:
  replicas: 3 
  selector:
    matchLabels: 
      app: auto-scale
  template:
    metadata:
      labels:
        app: auto-scale
    spec:
      containers:
      - name: auto-scale-container
        image: shekeriev/terraform-docker
        ports:
        - containerPort: 80 
        resources: 
          requests: 
            cpu: 100m
---
apiVersion: v1
kind: Service
metadata:
  name: auto-scale-svc
  labels:
    app: auto-scale
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: auto-scale    
---
apiVersion: autoscaling/v2beta2
kind: HorizontalPodAutoscaler
metadata:
  name: auto-scale-deploy
spec:
  # Maximum replicas count
  maxReplicas: 5
  # Minimum replicas count
  minReplicas: 1
  # Target for scalling (Pod, Deployment, etc)
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auto-scale-deploy
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        # If average utilization for the pods in this deployment drop below 10%, pods will be scaled down. If it's above 10%, pods will be scaled up.
        averageUtilization: 10
```

And create the resources

```bash
kubectl apply -f auto-scale-hpa.yaml
```

Check that all replicas are there by running

```bash
kubectl get pods
```

Ask for more information

```bash
kubectl get horizontalpodautoscalers auto-scale-deploy
```

Wait a few minutes for the metrics to be collected and ask again

```bash
kubectl get horizontalpodautoscalers auto-scale-deploy -o yaml
```

After a few minutes (at least 5) the system should scale down our deployment to one replica.

```bash
kubectl get pods -o wide
kubectl get deployments
```

Now we can open second terminal in order to monitor the scaling process 

```bash
watch -n 1 kubectl get hpa,deployment
```

In the first terminal, we are going to simulate workload to trigger scale up

```bash
kubectl run -it --rm --restart=Never load-generator --image=busybox -- sh -c "while true; do wget -O - -q http://auto-scale-svc.default; done"
```

If switch to the other terminal, will see the scale up process in action. Return to the first terminal and press **Ctrl+C** to stop the load generator pod. Check current quantity of replicas.

```bash
kubectl get deployments
```

The scale down process will take some time (approx. 5 minutes). Close the second terminal. Clean up.

```bash
kubectl delete -f auto-scale-hpa.yaml
```

Disable the metrics add on a standard Kubernetes cluster, uninstall the metrics server.

```bash
kubectl delete -f metrics-server.yaml
```

# Scheduling

## [Taints and Tolerations](https://user-images.githubusercontent.com/34960418/147854592-6b1ce2b3-bde1-49a8-88f3-3c1d3be7e5fd.png)


Node affinity is a property of Pods that attracts them to a set of nodes (either as a preference or a hard requirement). Taints are the opposite -- they allow a node to repel a set of pods.

Tolerations are applied to pods, and allow (but do not require) the pods to schedule onto nodes with matching taints.

Taints and tolerations work together to ensure that pods are not scheduled onto inappropriate nodes. One or more taints are applied to a node; this marks that the node should not accept any pods that do not tolerate the taints.

**Taints** are applied to nodes and allow them to repel pods. They have **key**, **value** and taint **effect** and are set like ```kubectl taint nodes node1 key1=value1:NoSchedule```. Effect must be ```NoSchedule``` , ```PreferNoSchedule``` or ```NoExecute```. 

**Tolerations** are applied to pods and allow them to schedule on nodes with matching taints. They are specified with **key**, **operator** (**Exists** or **Equal**), **value** (if the operator is equal) and **effect**.

***Note***: There are two special cases:

- An empty ```key``` with operator ```Exists``` matches all keys, values and effects which means this will tolerate everything.
- An empty ```effect``` matches all effects with key ```key1```.

## [Node Selectors](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)

- A pod can be **constrained** to run only on **particular nodes**.
- One of the ways to do this is to use **node selectors**.
- **nodeSelector** is a field part of the pod specification.
- It specifies a **map of key-value pairs**.
- For a pod to be able to run on a node, the node must have all **indicated key-value pairs** (it may have others as well).


## Scheduling example by using taints and tolerations 


Let’s first see if there are any existing taints in cluster by executing this. Pay attention to the **Taints** section.

![image](https://user-images.githubusercontent.com/34960418/147854913-01c5d5af-af65-479f-a90e-2109da8e6f59.png)


```bash
kubectl describe node node-1.k8s
```


















```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: schedule-deploy
spec:
  replicas: 3 
  selector:
    matchLabels: 
      app: schedule
  template:
    metadata:
      labels:
        app: schedule
    spec:
      containers:
      - name: schedule-container
        image: shekeriev/terraform-docker
        ports:
        - containerPort: 80 
        resources: 
          requests: 
            cpu: 100m
      # Pods from this deployment have tolerations for nodes with taint (demo-taint=nomorework:NoSchedule)
      tolerations:
      - key: demo-taint
        operator: Equal
        value: nomorework
        effect: NoSchedule
```

### Daemon Sets

**Daemon Sets** are like the **Deployments**, **Replication Controllers** and **Replica Sets**

There is one important difference though – their workload goes to every node or only to specific nodes and with only one copy, so no multiple replicas spread across the cluster.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: daemon-set
spec: 
  selector:
    matchLabels: 
      app: daemon-set
  template:
    metadata:
      labels: 
        app: daemon-set
    spec:
      # Node selector limits nodes (worker nodes) that will receive a copy of the given pod
      nodeSelector: 
        disk: samsung
      containers:
      - name: main
        image: shekeriev/k8s-appa:v1
        ports:
        - containerPort: 80
```

### Job

There are situations in which we need to run tasks that start, do something, and then finish. This is covered by a special object type – Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec: 
  template:
    metadata:
      labels: 
        app: batch-job
    spec:
      restartPolicy: OnFailure
      containers:
      - name: main
        image: shekeriev/sleeper
```

Serial job execution

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job-serial
spec: 
  completions: 3
  template:
    metadata:
      labels: 
        app: batch-job
    spec:
      containers:
      - name: main
        image: shekeriev/sleeper
      restartPolicy: Never
```

Parallel job execution

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job-parallel
spec: 
  # Expect a total of four executions by two in parallel
  completions: 4
  parallelism: 2
  template:
    metadata:
      labels: 
        app: batch-job
    spec:
      containers:
      - name: main
        image: shekeriev/sleeper
      restartPolicy: Never
```

### CronJob

A CronJob creates Jobs on a repeating schedule. CronJobs are useful for creating periodic and recurring tasks, like running backups, reports generation, sending emails, etc.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: batch-job-cron
spec: 
  # It will run every two minutes
  schedule: "*/2 * * * *"
  jobTemplate:
    spec: 
      template:
        metadata:
          labels: 
            app: batch-job-cron
        spec:
          restartPolicy: OnFailure
          containers:
          - name: main
            image: shekeriev/sleeper
```

## Part 3

### Ingress and Ingress Controllers

Ingress exposes HTTP and HTTPS routes from outside the cluster to services within the cluster. Traffic routing is controlled by rules defined on the Ingress resource. We must have an Ingress controller to satisfy the Ingress

Types
- Single service (default backend)
- Fanout
![image](https://user-images.githubusercontent.com/34960418/145839121-8dff2f25-ac48-4f65-98d8-f3793cad7b7c.png)
- Name based virtual hosting
- ![image](https://user-images.githubusercontent.com/34960418/145839272-6393f239-c9b7-450e-b682-810d22130dbf.png)
- TLS

#### IngressClass

Ingress Controllers must be annotated with the appropriate Ingress Class. [image]

![image](https://user-images.githubusercontent.com/34960418/145843008-8d64c7c6-d6e5-4805-a701-440fe24795b4.png)


```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: haproxy
spec:
  controller: haproxy-ingress.github.io/controller
```

#### Single service

![image](https://user-images.githubusercontent.com/34960418/145848801-a6b3828a-adb0-44df-b870-df6daea0e797.png)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod1
  labels:
    app: pod1
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: main
    env:
    - name: TOPOLOGY
      value: "POD1 -> SERVICE1"
    - name: FOCUSON
      value: "TOPOLOGY"
---
apiVersion: v1
kind: Service
metadata:
  name: service1
spec:
  ports:
  - port: 80
    protocol: TCP
  selector:
    app: pod1
    
---
 
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-ctrl
spec:
  # Which Ingress Class will be used. (nginx/haproxy in this case)
  ingressClassName: nginx
  # Every rule is for given host. (Specific entry point.)
  rules:
  - host: demo.lab
    http:
      # All request to demo.lab will be redirected to service1, port 80
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: service1
            port:
              number: 80

```

#### Custom Path (Single service)

![image](https://user-images.githubusercontent.com/34960418/145851656-f5f23898-07c9-41b9-8667-b6090074d223.png)


```yaml            
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-ctrl
  # Urls for service1 are rewrited to the service root (/).
  # Anotations are controller specific
  annotations:
    nginx.org/rewrites: "serviceName=service1 rewrite=/"
spec:
  ingressClassName: nginx
  rules:
  - host: demo.lab
    http:
      paths:
        # All request to demo.lab/service1 will be redirected to service1, port 80
      - path: /service1
        pathType: Prefix
        backend:
          service:
            name: service1
            port:
              number: 80
```

#### Default Backend (Single service)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: podd
  labels:
    app: podd
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: main
    env:
    - name: TOPOLOGY
      value: "PODd -> SERVICEd (default backend)"
    - name: FOCUSON
      value: "TOPOLOGY"

---
apiVersion: v1
kind: Service
metadata:
  name: serviced
spec:
  ports:
  - port: 80
    protocol: TCP
  selector:
    app: podd
    
---

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-ctrl
  annotations:
    nginx.org/rewrites: "serviceName=service1 rewrite=/"
spec:
  ingressClassName: nginx
  # default requests (not specified in rules:paths) to "demo.lab" are send to "serviced"
  defaultBackend:
    service:
      name: serviced
      port:
        number: 80
  rules:
  - host: demo.lab
    http:
      paths:
        # All request to "demo.lab/service1" will be redirected to "service1"
      - path: /service1
        pathType: Prefix
        backend:
          service:
            name: service1
            port:
              number: 80
```

#### Fanout

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod2
  labels:
    app: pod2
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: main
    env:
    - name: TOPOLOGY
      value: "POD2 -> SERVICE2"
    - name: FOCUSON
      value: "TOPOLOGY"
---
apiVersion: v1
kind: Service
metadata:
  name: service2
spec:
  ports:
  - port: 80
    protocol: TCP
  selector:
    app: pod2
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-ctrl
  annotations:
    nginx.org/rewrites: "serviceName=service1 rewrite=/;serviceName=service2 rewrite=/"
spec:
  ingressClassName: nginx
  defaultBackend:
    service:
      name: serviced
      port:
        number: 80
  rules:
  - host: demo.lab
    http:
      paths:
      - path: /service1
        pathType: Prefix
        backend:
          service:
            name: service1
            port:
              number: 80
      - path: /service2
        pathType: Prefix
        backend:
          service:
            name: service2
            port:
              number: 80
```

#### Name based virtual hosting

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-ctrl
spec:
  ingressClassName: nginx
  rules:
  - host: demo.lab
    http:
      paths:
      - pathType: Prefix
        path: "/"
        backend:
          service:
            name: service1
            port:
              number: 80
  - host: awesome.lab
    http:
      paths:
      - pathType: Prefix
        path: "/"
        backend:
          service:
            name: service2
            port:
              number: 80
```
