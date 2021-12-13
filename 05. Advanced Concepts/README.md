# Manifest files explanations (YAML)

## Part 1

### Static pod

- Static Pods are managed directly by the kubelet
- The spec of a static Pod cannot refer to other API objects
- Their manifests are standard but are stored in a specific folder on controle plane node
- Usually, this is /etc/kubernetes/manifests
- And it is regulated by the kublet configuration file


```yaml
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

### Sidecar (Pattern)

Sidecar containers enhance the main container. For example, it may sync the local file system with a remote repository. In any case, both share the same filesystem.

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

### Adapter (Pattern)

Adapter containers are used to standardize and normalize the output

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

### Init Container

**Specialized containers** that **run before app containers** in a Pod. Contain utilities or setup scripts not present in an app image. **App Containers** are specified via **containers** section and the **Init Containers** are specified via **initContainers** section. Init Containers **always run to completion**. If one of them **fails**, the **kubelet** repeatedly **restarts it until it succeeds**. Each Init Container **must complete successfully** before the **next one starts**.


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

## Part 2

### Autoscalling

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


### Scheduling

**Taints** are applied to nodes and allow them to repel pods. They have **key**, **value** and taint **effect** and are set like ```kubectl taint nodes node1 key1=value1:NoSchedule```. Effect must be ```NoSchedule``` , ```PreferNoSchedule``` or ```NoExecute```. 

**Tolerations** are applied to pods and allow them to schedule on nodes with matching taints. They are specified with **key**, **operator** (**Exists** or **Equal**), **value** (if the operator is equal) and **effect**.


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

#### Single service (default backend)

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

![image](https://user-images.githubusercontent.com/34960418/145848881-55dcf30f-699e-4cfa-a898-78e8efc80271.png)


```yaml            
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-ctrl
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


