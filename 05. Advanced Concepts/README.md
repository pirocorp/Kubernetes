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
