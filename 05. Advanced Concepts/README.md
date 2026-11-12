# Module 05 — Advanced Concepts

> **Integrated edition · Kubernetes 1.37 (2026).** This README now contains the entire current hands-on lesson **and** the untouched original explanation and examples. The historical material remains educational but its retired APIs/CNI/scripts must not be replayed on the modern cluster.

## Recommended learning path

1. Use the course-wide [Kubernetes 1.37 roadmap](../README.md) to establish the required environment.
2. Read the preserved original lecture for conceptual depth, then complete [the integrated labs](#kubernetes-137-integrated-labs) in order with their verification and cleanup steps.
3. Contrast historical methods with their current counterparts below; retain the principle, not obsolete commands or manifest API versions.

| Preserved original concepts | Integrated current treatment |
|---|---|
| Static and multi-container Pods, init containers | Working two-init-container exercise and expected output |
| Scheduling, DaemonSets, Jobs and CronJobs | Original controller and workload theory retained |
| Ingress and controllers | F5 NGINX HTTPS fanout; distinct Traefik ingress lab |
| Autoscaling and Metrics Server | autoscaling/v2 HPA and live CPU metrics prerequisites |

## Kubernetes 1.37 integrated labs

> **Supported execution path:** Follow these instructions and modernized repository manifests. Historical lecture commands after this section are a reference, not a deployable 1.37 runbook. The written procedure is statically reviewed, not live-cluster certified.

## Module 05 — Advanced Concepts and Homework (Kubernetes 1.37)

> **NOTE (2026):** Executable lab path for autoscaling and all three original advanced homework problems (two init containers, TLS fanout Ingress, **another Ingress controller**). The original 2021 DOCX and Contour install snippet remain historical; the 2026 third-controller solution deliberately uses **Traefik**. This avoids relying on unpinned archived manifest URLs. Start on a disposable Kubernetes **1.37 + containerd + Calico 3.33** cluster from [Module 02](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md). Run lab applications **sequentially** to avoid NodePort 30001/name conflicts.

### 0. Prerequisites

- Admin `kubectl` configured for the **lab** cluster; worker Nodes Ready, Calico running; `helm` client; image-pull and Helm repository access; openssl and curl on the workstation.
- At least one Node IP reachable from the workstation; TCP NodePorts allowed if testing from outside. Where possible use `kubectl port-forward` to avoid host firewall restrictions.
- All manifest examples below assume your working directory is the **root of the cloned Kubernetes repository**.

```bash
kubectl version
kubectl get nodes -o wide
kubectl config current-context
helm version
kubectl get ingressclass
kubectl get svc -A
```

Expected: 1.37 cluster, Ready nodes, valid Helm installation. The canonical module [README.md](./README.md) has the complete preserved historical theory on static/multi-container Pods, sidecars, scaling, scheduling, Jobs, CronJobs and Ingress.

### 1. Original Homework Problem 1 — two init containers, NGINX app container

Use the executable `Homework/Solution/Problem 1/problem-1.yaml`. The YAML creates a `Pod/pod-init` with **two sequential** Alpine init containers and an NGINX app container sharing an `emptyDir` at `/usr/share/nginx/html`. First init container records begin/end timestamps separated by 10s. Second writes a "launching" timestamp. Their output is the application index page.

```bash
kubectl apply -f "05. Advanced Concepts/Homework/Solution/Problem 1/problem-1.yaml"
kubectl wait pod/pod-init --for=condition=Ready --timeout=180s
kubectl get pod pod-init -o wide
kubectl describe pod pod-init
kubectl logs pod-init -c cont-init-0
kubectl exec pod-init -c cont-main -- cat /usr/share/nginx/html/index.html
kubectl port-forward svc/svc-init 8080:80
# In another terminal: curl http://localhost:8080/
```

**Expected:** index page contains **3 timestamped lines**, with about 10 seconds between the first two; NGINX is Ready after both init containers exit successfully; HTTP response is the generated page. Press Ctrl+C to stop port-forward.

```bash
kubectl delete -f "05. Advanced Concepts/Homework/Solution/Problem 1/problem-1.yaml" --ignore-not-found
```

### 2. Original Homework Problem 2 — HTTPS fanout with F5 NGINX Ingress

#### 2.1 Install the correct NGINX Ingress controller

Follow the **current section** [Installing Ingress Controllers — Kubernetes 1.37 lab (2026)](./README.md#installing-ingress-controllers--kubernetes-137-lab-2026). It pins **F5 NGINX Ingress Controller v5.7.1, Helm chart 2.8.1**, uses class `nginx` and Service type NodePort. The NGINX-specific `nginx.org/rewrites` annotation in the homework requires this **F5 NGINX** implementation, not the similarly named community ingress-nginx or Traefik.

Verify:

```bash
kubectl get ingressclass nginx -o yaml
helm status nginx-ingress -n nginx-ingress
kubectl get pods,svc -n nginx-ingress
```

#### 2.2 TLS Secret and fanout manifest

In a terminal at the **repository root**, create a fresh self-signed certificate with SAN `demo.lab` instead of using the 2021 demo secret:

```bash
TLS_DIR="$(mktemp -d)"
openssl req -x509 -nodes -days 30 -newkey rsa:2048 \
  -keyout "$TLS_DIR/tls.key" -out "$TLS_DIR/tls.crt" \
  -subj "/CN=demo.lab" -addext "subjectAltName=DNS:demo.lab"
kubectl create secret tls demo-lab-secret \
  --cert="$TLS_DIR/tls.crt" --key="$TLS_DIR/tls.key" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "05. Advanced Concepts/Homework/Solution/Problem 2/solution.yaml"
kubectl wait --for=condition=Ready pod/pod1 pod/pod2 pod/podd --timeout=180s
kubectl get ingress ingress-ctrl -o yaml
kubectl get pods,svc,ingress
kubectl get endpointslices
```

**Expected:** three backend Pods Ready and Ingress class `nginx` with HTTPS host `demo.lab`; the three Ingress backends reference **Service port 80**, whereas client HTTPS uses listener **443** via its **mapped NodePort**. The Ingress default backend routes `/` to `serviced`.

#### 2.3 Validate the HTTPS paths

```bash
kubectl get svc -n nginx-ingress
# In the Service ports mapping, locate the NodePort assigned to 443/TCP.
# Replace BOTH values below; never use documentation example addresses unchanged.
NODE_IP=192.0.2.10           # REPLACE with your reachable cluster node IP
HTTPS_NODEPORT=30443        # REPLACE with the assigned HTTPS NodePort
curl -ksS --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" "https://demo.lab:${HTTPS_NODEPORT}/service1"
curl -ksS --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" "https://demo.lab:${HTTPS_NODEPORT}/service2"
curl -ksS --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" "https://demo.lab:${HTTPS_NODEPORT}/"
```

Expected body text from the historical example: `POD1 -> SERVICE1`, `POD2 -> SERVICE2`, and `PODd -> SERVICEd (default backend)`. `-k` skips trust validation of the self-signed lab certificate **only for this lab**, never production.

If a path fails, inspect `kubectl describe ingress ingress-ctrl`, class/annotations, NGINX controller logs, Pod readiness, `kubectl get endpointslices`, and node firewall. Ingress Controller may take a few moments to reconcile after applying the objects.

```bash
kubectl delete -f "05. Advanced Concepts/Homework/Solution/Problem 2/solution.yaml" --ignore-not-found
kubectl delete secret demo-lab-secret --ignore-not-found
rm -rf "$TLS_DIR"
# Only if this dedicated lab has no other nginx-ingress uses:
helm uninstall nginx-ingress -n nginx-ingress
kubectl delete namespace nginx-ingress
```

### 3. Original Homework Problem 3 — another controller (Traefik, not NGINX/HAProxy)

The archived author solution used Contour with a moving `quickstart` URL and manual changes by approximate file line numbers. Instead, the new executable solution uses **Traefik chart 42.3.0** (chart requires Kubernetes >= 1.30) and standard `networking.k8s.io/v1` Ingress on **a separate clean lab**.

This is a standalone demonstration with two HTTP echo Deployments, so it does **not** need NGINX-specific URL rewrite annotations. Two URLs route to two Services; backend Service ports are 80.

```bash
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik \
  --version 42.3.0 --namespace traefik-lab --create-namespace \
  --set service.type=ClusterIP \
  --set ingressClass.name=traefik \
  --set ingressClass.isDefaultClass=false \
  --set providers.kubernetesIngress.enabled=true \
  --set providers.kubernetesIngress.ingressClass=traefik \
  --wait --timeout 180s

kubectl get ingressclass traefik
kubectl get svc,pods -n traefik-lab
kubectl apply -f "05. Advanced Concepts/Homework/Solution/Problem 3 - Traefik/traefik-fanout.yaml"
kubectl -n m05-alt rollout status deploy/service1 --timeout=180s
kubectl -n m05-alt rollout status deploy/service2 --timeout=180s
kubectl -n m05-alt get svc,pods,ingress
kubectl -n traefik-lab port-forward svc/traefik 8888:80
# On another terminal:
# curl -fsS http://localhost:8888/service1
# curl -fsS http://localhost:8888/service2
```

**Expected:** HTTP response **`service1 via Traefik`** at `/service1` and **`service2 via Traefik`** at `/service2`. The host-local `8888` is a port-forward to the Traefik HTTP entrypoint; no DNS or NodePort is required. Ensure local 8888 is free.

```bash
# Stop kubectl port-forward with Ctrl+C first.
kubectl delete -f "05. Advanced Concepts/Homework/Solution/Problem 3 - Traefik/traefik-fanout.yaml" --ignore-not-found
helm uninstall traefik -n traefik-lab
kubectl delete namespace traefik-lab
```

**Important:** The historical Contour-based solution is **archived for comparison**. It is not the recommended execution path for Kubernetes 1.37. Original requirement was simply "another Ingress Controller, not NGINX or HAProxy"; Traefik satisfies it. For this course, prefer standard Ingress for the task; Kubernetes Gateway API is a separate topic.

### 4. Horizontal Pod Autoscaler (HPA) practical lab

The module's [modern HPA section](./README.md#horizontal-pod-autoscaler-example) provides the full commands; the checked-in [autoscaling/v2 manifest](./labs/auto-scale-hpa-2026.yaml) includes Deployment, NodePort Service, CPU requests and HPA min1/max5. Install **Metrics Server 0.9.1** compatible with Kubernetes 1.37, verify `kubectl top`, and apply this manifest.

Do not blindly add `--kubelet-insecure-tls`: only consider the lab-only flag when kubelet serving certificate verification fails, and prefer real trust configuration for non-lab clusters.

**Expected:** CPU metrics available, HPA has non-unknown targets, workload generates CPU demand and causes scaling within bounds. HPA behavior depends on actual measured utilization.

### 5. Additional module topics

Read the existing sections in [README.md](./README.md) and practice them **sequentially**: static Pods, init/sidecar/adapter containers, taints/tolerations and node selectors, DaemonSets, Jobs, CronJobs and HPA. Their original embedded commands and DOCX/ZIP screenshots may show 2021-era images and cluster versions; use the validated K8s 1.37 baseline and inspect current API versions with `kubectl api-resources` and `kubectl explain`.

Troubleshooting order: `kubectl get` / `describe` / `get events` / `logs` / `rollout status` / `get endpointslices`. Never apply an `Ingress` alone and expect traffic to route without an active matching controller.

### Acceptance checklist

- [ ] All app Pods and Services reach Ready/available
- [ ] Problem 1 produces 3 timestamped lines with about a 10-second pause
- [ ] Problem 2 has fresh TLS Secret and responds correctly for all three HTTPS paths
- [ ] Problem 3 responds through the Traefik Ingress at two independent paths
- [ ] HPA uses **autoscaling/v2** and real Metrics Server CPU data
- [ ] NodePort assignments do not conflict and all lab-created objects are cleaned up

---

## Preserved original lecture — historical reference

> **2021 course snapshot.** This original Markdown lecture is preserved byte-for-byte to retain its educational value. For runnable commands, use the modern lab above.

<!-- ORIGINAL_MODULE_README_PRESERVED_START -->
> **Kubernetes 1.37 (2026):** Use [ADVANCED-2026.md](./ADVANCED-2026.md) for modern HPA/Metrics Server installation and the fully documented NGINX + Traefik homework labs. Historical DOCX/ZIP and old Contour examples are preserved for context.

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

> **NOTE (2026):** `autoscaling/v2beta2` was removed in Kubernetes 1.26; the supported HPA API is `autoscaling/v2`. Use Metrics Server **v0.9.1**, compatible with Kubernetes 1.37. Do **not** edit arbitrary upstream YAML by line number to add insecure flags: check TLS errors first and use the dedicated lab-only workaround below if needed. The ready-to-use manifest is [labs/auto-scale-hpa-2026.yaml](./labs/auto-scale-hpa-2026.yaml).

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.1/components.yaml
kubectl -n kube-system rollout status deployment/metrics-server --timeout=180s
kubectl top nodes
kubectl top pods -A
```

If `kubectl top` reports an X.509 error about **untrusted kubelet serving certificates**, first inspect `kubectl -n kube-system logs deploy/metrics-server` and configure trusted serving certificates where possible. **Disposable test cluster only:** to bypass kubelet certificate verification temporarily, run:

```bash
kubectl -n kube-system patch deployment metrics-server --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl -n kube-system rollout status deployment/metrics-server --timeout=180s
kubectl top nodes
```

Do **not** use the insecure TLS workaround in production.

Use the provided modern example (Deployment, Service, `autoscaling/v2` HPA):

```bash
kubectl apply -f "05. Advanced Concepts/labs/auto-scale-hpa-2026.yaml"
kubectl rollout status deployment/auto-scale-deploy --timeout=180s
kubectl get hpa,deploy,pods,svc
kubectl describe hpa auto-scale-deploy
```

**Expected:** initial target / CPU metrics become available after Metrics Server has collected samples, initial Deployment starts with 3 replicas and the HPA adjusts between **1 and 5** Pods as load changes. Scaling down may take several minutes.

Load generator (in a second terminal, stop with Ctrl+C):

```bash
kubectl run -it --rm --restart=Never load-generator --image=busybox:1.36 -- \
  sh -c "while true; do wget -q -O- http://auto-scale-svc.default.svc.cluster.local >/dev/null; done"
```

While load runs:

```bash
kubectl get hpa,deployment --watch
```

**Expected:** CPU pressure can cause scale-up; HPA responds based on observed metrics, not an exact fixed time. Confirm `kubectl get hpa auto-scale-deploy -o yaml` shows target values rather than `<unknown>`.

```bash
kubectl delete -f "05. Advanced Concepts/labs/auto-scale-hpa-2026.yaml" --ignore-not-found
# Only if Metrics Server was installed specifically for this disposable lab:
kubectl delete -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.1/components.yaml --ignore-not-found
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

Now, try to get them for all nodes. 

![image](https://user-images.githubusercontent.com/34960418/147854935-133ddd15-8414-4e31-8cf8-1ada032cc318.png)

```bash
kubectl describe node | grep Taints
```

The other two nodes don’t have any taints for now. This is the reason why there aren’t any user scheduled pods there (on the control plane node(s)). If taintis removed should be able to schedule pods there as well.

This is done with (***skip it for now***)

```bash
kubectl taint nodes node-1.k8s node-role.kubernetes.io/master:NoSchedule-
```

The system pods are scheduled on the control plane, because they have tolerations for the taints of the control plane nodes. Get the list of some of those pods.

```bash
kubectl get pods -n kube-system -o wide
```

Describe one of the coredns pods

![image](https://user-images.githubusercontent.com/34960418/147855124-bf53c6f5-257d-4f9d-b92e-344180435611.png)

```bash
kubectl describe pod coredns--<identifier> -n kube-system
```

Add a taint to one of the other two nodes

```bash
kubectl taint node node-2.k8s demo-taint=nomorework:NoSchedule
```

Check the situation with the **taints** again

```bash
kubectl describe node | grep Taints
```

Spin a new deployment from this 

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

Send it to the cluster

```bash
kubectl apply -f schedule-toleration.yaml
```

And check the distribution of the pods again

```bash
kubectl get pods -o wide
```

Clean up

```bash
kubectl taint node node-2.k8s demo-taint-
kubectl delete -f schedule-toleration.yaml
```


# [Daemon Sets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)

**Daemon Sets** are like the **Deployments**, **Replication Controllers** and **Replica Sets**

A **DaemonSet** ensures that all (or some) Nodes run a copy of a Pod. As nodes are added to the cluster, Pods are added to them. As nodes are removed from the cluster, those Pods are garbage collected. Deleting a **DaemonSet** will clean up the Pods it created.

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
      # Node selector limits nodes (worker nodes) that will receive a copy of the given pod.
      nodeSelector: 
        disk: samsung
      containers:
      - name: main
        image: shekeriev/k8s-appa:v1
        ports:
        - containerPort: 80
```

# [Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/)

- A **Job** creates one or more Pods and ensures that a specified number of them successfully terminate
- As pods successfully complete, the Job tracks the successful completions
- When a specified number of successful completions is reached, the Job is complete
- Deleting a Job will clean up the Pods it created
- The Job object will start a new Pod if the first Pod fails or is deleted
- They can run Pods either in **sequence** or in **parallel**


Job example:

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

# [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)

- A CronJob creates Jobs on a repeating schedule
- One CronJob object is like one line of a crontab (cron table) file
- CronJobs are useful for creating periodic and recurring tasks, like running backups, reports generation, sending emails, etc.

CronJobs are meant for performing regular scheduled actions such as backups, report generation, and so on. Each of those tasks should be configured to recur indefinitely (for example: once a day / week / month); you can define the point in time within that interval when the job should start.

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

# [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) and [Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)

**Ingress** exposes **HTTP** and **HTTPS** routes from outside the cluster to services within the cluster. **Traffic routing** is controlled by **rules** defined on the Ingress resource. We must have an **Ingress controller** to satisfy the Ingress.

An API object that manages **external access to the services in a cluster**, typically HTTP. Ingress may provide load balancing, SSL termination and name-based virtual hosting.

Terminology

- **Node**: A worker machine in Kubernetes, part of a cluster.
- **Cluster**: A set of Nodes that run containerized applications managed by Kubernetes. For this example, and in most common Kubernetes deployments, nodes in the cluster are not part of the public internet.
- **Edge router**: A router that enforces the firewall policy for your cluster. This could be a gateway managed by a cloud provider or a physical piece of hardware.
- **Cluster network**: A set of links, logical or physical, that facilitate communication within a cluster according to the Kubernetes networking model.
- **Service**: A Kubernetes Service that identifies a set of Pods using label selectors. Unless mentioned otherwise, Services are assumed to have virtual IPs only routable within the cluster network.

Ingress exposes HTTP and HTTPS routes from outside the cluster to services within the cluster. Traffic routing is controlled by rules defined on the Ingress resource. Here is a simple example where an Ingress sends all its traffic to one Service.

![image](https://user-images.githubusercontent.com/34960418/147927984-958a4e8a-479f-4431-96cb-84f42056693e.png)

An Ingress may be configured to give Services externally-reachable URLs, load balance traffic, terminate SSL / TLS, and offer name-based virtual hosting. An Ingress controller is responsible for fulfilling the Ingress, usually with a load balancer, though it may also configure your edge router or additional frontends to help handle the traffic.

An Ingress does not expose arbitrary ports or protocols. Exposing services other than HTTP and HTTPS to the internet typically uses a service of type ```Service.Type=NodePort``` or ```Service.Type=LoadBalancer```.

You must have an Ingress controller to satisfy an Ingress. Only creating an Ingress resource has no effect.

Ingress rules. Each HTTP rule contains the following information:

- An optional host. In this example, no host is specified, so the rule applies to all inbound HTTP traffic through the IP address specified. If a host is provided (for example, foo.bar.com), the rules apply to that host.
- A list of paths (for example, ```/testpath```), each of which has an associated backend defined with a ```service.name``` and a ```service.port.name``` or ```service.port.number```. Both the host and path must match the content of an incoming request before the load balancer directs traffic to the referenced Service.
- A backend is a combination of Service and port names as described in the Service doc or a custom resource backend by way of a CRD. HTTP (and HTTPS) requests to the Ingress that matches the host and path of the rule are sent to the listed backend.

A ```defaultBackend``` is often configured in an Ingress controller to service any requests that do not match a path in the spec.

An Ingress with no rules sends all traffic to a single default backend. The defaultBackend is conventionally a configuration option of the Ingress controller and is not specified in your Ingress resources.

If none of the hosts or paths match the HTTP request in the Ingress objects, the traffic is routed to your default backend.


Types
- Single service (default backend)
- [Fanout](https://kubernetes.io/docs/concepts/services-networking/ingress/#simple-fanout)
![image](https://user-images.githubusercontent.com/34960418/145839121-8dff2f25-ac48-4f65-98d8-f3793cad7b7c.png)
- [Name based virtual hosting](https://kubernetes.io/docs/concepts/services-networking/ingress/#name-based-virtual-hosting)
- ![image](https://user-images.githubusercontent.com/34960418/145839272-6393f239-c9b7-450e-b682-810d22130dbf.png)
- TLS

## Ingress Controllers

- **Ingress controller**s are **not started automatically** with a cluster.
- The Kubernetes project defines the Ingress API; controllers such as **F5 NGINX**, **HAProxy**, and cloud-provider implementations are maintained by their respective projects/providers.
- Some of the others include **HAProxy**, **Istio**, **Contour**, etc.
- We may deploy **any number of ingress controllers** within a cluster.
- An Ingress normally selects its controller using `spec.ingressClassName`; the controller must provide the corresponding **IngressClass** resource.

![image](https://user-images.githubusercontent.com/34960418/145843008-8d64c7c6-d6e5-4805-a701-440fe24795b4.png)

### Using multiple Ingress controllers

You may deploy any number of ingress controllers using ingress class within a cluster. Note the ```.metadata.name``` of your ingress class resource. When you create an ingress you would need that name to specify the ```ingressClassName``` field on your Ingress object (refer to IngressSpec v1 reference. ```ingressClassName``` is a replacement of the older annotation method.

If you do not specify an IngressClass for an Ingress, and your cluster has exactly one IngressClass marked as default, then Kubernetes applies the cluster's default IngressClass to the Ingress. You mark an IngressClass as default by setting the ```ingressclass.kubernetes.io/is-default-class``` annotation on that IngressClass, with the string value ```"true"```.

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: haproxy
spec:
  controller: haproxy.org/ingress-controller
```

## Installing Ingress Controllers — Kubernetes 1.37 lab (2026)

> **NOTE (2026):** The original 2021 manifest-based NGINX v2.0.3 and HAProxy `master` installation steps are retained in the **historical section** below, not recommended for the current lab. For the exercises here, use **F5 NGINX Ingress Controller** (NGINX Open Source edition) with Helm, which understands the existing `nginx.org/rewrites` annotation. This is **not** the retired community `ingress-nginx` controller. Start with a working Kubernetes 1.37 + Calico cluster from [SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md) and an installed Helm 3.19+ client.

### NGINX — primary lab controller (Helm chart 2.8.1 / controller 5.7.1)

Use a fresh lab cluster without a conflicting `IngressClass` named `nginx`. This pinned F5 chart/controller release is listed as compatible with Kubernetes 1.37.

```bash
kubectl get nodes
helm version
kubectl get ingressclass

helm upgrade --install nginx-ingress oci://ghcr.io/nginx/charts/nginx-ingress \
  --version 2.8.1 \
  --namespace nginx-ingress --create-namespace \
  --set controller.service.type=NodePort \
  --set controller.ingressClass.name=nginx

# The Helm chart creates the IngressClass and controller resources.
kubectl get ingressclass nginx -o yaml
kubectl get pods -n nginx-ingress
kubectl get svc -n nginx-ingress
helm status nginx-ingress -n nginx-ingress
```

**Expected:** NGINX controller Pod(s) become `Running/Ready`, `IngressClass/nginx` exists, and a NodePort Service exposes HTTP (Service port 80) and HTTPS (Service port 443). Note the **HTTPS NodePort** from `kubectl get svc -n nginx-ingress` (usually 30000–32767). You must be able to reach a cluster node on this port from your browser/workstation; check the node firewall.

#### HTTPS fanout verification (Homework / Solution / Problem 2)

Execute this from the **repository root**. The original committed test certificate is historical, so generate a *fresh* temporary certificate; do not overwrite or commit a private key into the repo.

```bash
LAB_TLS_DIR="$(mktemp -d)"
openssl req -x509 -nodes -days 30 -newkey rsa:2048 \
  -keyout "$LAB_TLS_DIR/tls.key" -out "$LAB_TLS_DIR/tls.crt" \
  -subj "/CN=demo.lab" -addext "subjectAltName=DNS:demo.lab"
kubectl create secret tls demo-lab-secret \
  --cert="$LAB_TLS_DIR/tls.crt" --key="$LAB_TLS_DIR/tls.key" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "05. Advanced Concepts/Homework/Solution/Problem 2/solution.yaml"
kubectl describe ingress ingress-ctrl
kubectl get pods,svc,ingress
```

Set `NODE_IP` to an address reachable from your workstation and `HTTPS_NODEPORT` to the NodePort assigned to **443/TCP** by the NGINX controller Service, **not** the backend Service port 80. Then run:

```bash
NODE_IP=192.0.2.10           # REPLACE with a reachable cluster-node IP
HTTPS_NODEPORT=30443        # REPLACE with the actual mapped HTTPS NodePort
curl -k --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" \
  "https://demo.lab:${HTTPS_NODEPORT}/service1"
curl -k --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" \
  "https://demo.lab:${HTTPS_NODEPORT}/service2"
curl -k --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" \
  "https://demo.lab:${HTTPS_NODEPORT}/"
```

**Expected:** `/service1` routes to `POD1 -> SERVICE1`, `/service2` routes to `POD2 -> SERVICE2`, and `/` routes to default backend `PODd -> SERVICEd`. `curl -k` bypasses trust checking for the self-signed lab certificate; do not use `-k` for production validation. The client uses **HTTPS 443** (through the mapped NodePort), while `Ingress.spec.rules[].http.paths[].backend.service.port.number` and `defaultBackend.service.port.number` must reference the declared **Service port 80**. This is the alignment fixed in Homework Problem 2.

If routing fails, inspect `kubectl describe ingress ingress-ctrl`, `kubectl get endpoints`, and `kubectl logs -n nginx-ingress` for the controller Pods. Confirm the ingress class, service port, TLS Secret, node firewall, and HTTP rewrite behavior. Use unique names or delete `ingress-ctrl` before applying the **separate** single-service, default-backend, fanout, or virtual-hosting examples below.

### HAProxy — optional alternative (separate lab, Helm chart 1.54.4)

HAProxy is **optional** for this course. For a separate clean lab, use its maintained official chart instead of an unpinned `master` YAML URL:

```bash
helm upgrade --install haproxy-ingress \
  oci://ghcr.io/haproxytech/helm-charts/kubernetes-ingress \
  --version 1.54.4 \
  --namespace haproxy-controller --create-namespace \
  --set controller.service.type=NodePort \
  --set controller.ingressClass=haproxy

kubectl get ingressclass haproxy
kubectl get pods,svc -n haproxy-controller
```

For HAProxy Ingress resources use `spec.ingressClassName: haproxy`. **Do not expect NGINX-specific annotations (`nginx.org/rewrites`) to work with HAProxy**: the original rewrite-based exercises must be adapted to HAProxy's features. Do not install the alternative controller just to execute the primary NGINX exercises.

Reference documentation: [F5 NGINX Helm](https://docs.nginx.com/nginx-ingress-controller/install/helm/open-source/), [NGINX Helm parameters](https://docs.nginx.com/nginx-ingress-controller/install/helm/parameters/), [HAProxy community installation](https://www.haproxy.com/documentation/kubernetes-ingress/community/installation/on-prem/).

<details>
<summary>Historical (2021) manual NGINX and HAProxy install instructions — do not run on the 2026 lab</summary>

## Installing Ingress Controller NGINX

The detailed installation procedure can be found [here](https://docs.nginx.com/nginx-ingress-controller/installation/installation-with-manifests/)

And here is the main [repository](https://github.com/nginxinc/kubernetes-ingress)


First, we must make sure that we have a git client installed on the machine, which we will use for the procedure. Then, we must clone the repo locally.

```bash
git clone https://github.com/nginxinc/kubernetes-ingress/
cd kubernetes-ingress/deployments
git checkout v2.0.3
```

Next, we must configure **RBAC**. Create the namespace and service account

```bash
kubectl apply -f common/ns-and-sa.yaml
```

Create the cluster role and cluster role binding

```bash
kubectl apply -f rbac/rbac.yaml
```

Then, we must create the needed common resources. First, we will create a secret that will hold the self-signed **TLS** certificate.

```bash
kubectl apply -f common/default-server-secret.yaml
```


Next, the configuration map that may be used for **NGINX** customization

```bash
kubectl apply -f common/nginx-config.yaml
```

Then, we must create the ingress class resource

```bash
kubectl apply -f common/ingress-class.yaml
```

And a few more required custom resource definitions - for **VirtualServer**, **VirtualServerRoute**, **TransportServer** and **Policy**.

```bash
kubectl apply -f common/crds/k8s.nginx.org_virtualservers.yaml
kubectl apply -f common/crds/k8s.nginx.org_virtualserverroutes.yaml
kubectl apply -f common/crds/k8s.nginx.org_transportservers.yaml
kubectl apply -f common/crds/k8s.nginx.org_policies.yaml
```

Ready to deploy the ingress controller. For this, can use either **Deployment** (if want to be in control and be able to change the number of replicas) or **DaemonSet** (if want one controller per node or set of nodes). Let’s go with the **Deployment** option.

```bash
kubectl apply -f deployment/nginx-ingress.yaml
```

We can watch the installation process with

```bash
kubectl get pods --namespace=nginx-ingress -w
```

Press **Ctrl+C** when done. Now, create a **NodePort** service to access the ingress controller

```bash
kubectl create -f service/nodeport.yaml
```

Check the service with

```bash
kubectl get service -n nginx-ingress
```

Successfully installed NGINX ingress controller.


## Installing Ingress Controller HAProxy

The main repository with any additional information can be found [here](https://github.com/haproxytech/kubernetes-ingress)

With **HAProxy**, the installation procedure is simpler compared to **NGINX**. It is enough to execute this. Of course, should we want to customize it, we must clone the repository locally first.

```bash
kubectl apply -f https://raw.githubusercontent.com/haproxytech/kubernetes-ingress/master/deploy/haproxy-ingress.yaml
```

Having two ingress controllers, create an ingress class for this one (the **NGINX** one created one). Prepare a ```haproxy-class.yaml``` manifest with the following content.

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: haproxy
spec:
  controller: haproxy-ingress.github.io/controller
```

Save it and close it. Send it to the cluster.

```bash
kubectl apply -f haproxy-class.yaml
```

Let’s see if have both classes

```bash
kubectl get ingressclass
```

Successfully installed and HAProxy ingress controller.

</details>

## Single service

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

Sent it to the cluster

```bash
kubectl apply -f nginx-single.yaml
```

Then can check if the resource is ready

```bash
kubectl get ingress
```

And why not, describe it with

```bash
kubectl describe ingress ingress-ctrl
```

Get the NodePort of the ingress service

```bash
kubectl get svc -n nginx-ingress
```

For the HAProxy, you must execute

```bash
kubectl get svc -n haproxy-controller
```

*Please note that you should have a record in your **hosts file** that matches **demo.lab** to the **IP address of the control plane node**.*

Open a browser tab and navigate to ```http://demo.lab:<node-port>```.


## Custom Path (Single service)

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
        # All request to demo.lab/service1 will be redirected to service1  port 80
      - path: /service1
        pathType: Prefix
        backend:
          service:
            name: service1
            port:
              number: 80
```

Send it to the cluster. It will overwrite the existing ingress controller.
  
```bash
kubectl apply -f nginx-custom-path.yaml
```
  
Check how it was changed.

```bash
kubectl describe ingress ingress-ctrl
```

Open a browser tab and navigate to ```http://demo.lab:<node-port>/service1```


## Default Backend (Single service)

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

Send it to the cluster (it will overwrite the existing one)

```bash
kubectl apply -f nginx-default-back.yaml
```

And then check how the ingress controller changed. Note the **Default backend** section and the **Rules** section. 

```bash
kubectl describe ingress ingress-ctrl
```

Open a browser tab and navigate to ```http://demo.lab:<node-port>```. It is working and showing different output. Check the previous URL - ```http://demo.lab:<node-port>/service1```. Also working.


## Fanout

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

Send it to cluster.

```bash
kubectl apply -f nginx-fan-out.yaml
```

Once sent to the cluster, check how the ingress controller has changed. Pay attention to the **Rules** section

```bash
kubectl describe ingress ingress-ctrl
```

Now, test all three **URLs**. Open a browser tab and navigate to ```http://demo.lab:<node-port>```. Now, check the **service1 URL** - ```http://demo.lab:<node-port>/service1```. And finally, check the service2 URL - ```http://demo.lab:<node-port>/service2```. All three are working.


## Name based virtual hosting

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

Send it to the cluster.

```bash
kubectl apply -f nginx-name-vhost.yaml
```

Check how the ingress controller has changed. Pay attention to the **Rules** section.

```bash
kubectl describe ingress ingress-ctrl
```

Before testing, make sure that you have records for both ```demo.lab``` and ```awesome.lab``` in your hosts file. Then, open a browser and navigate to ```http://demo.lab:<node-port>```. It should work and show the contents of **service1**. Now, open another browser tab and navigate to ```http://awesome.lab:<node-port>```. It should work also and show the contents of ***service2***.


## Clean Up

Clean up ingress, pods and services

```bash
kubectl delete pods podd pod1 pod2
kubectl delete svc serviced service1 service2
kubectl delete ingress ingress-ctrl
```

### NGINX (2026 Helm installation)

```bash
helm uninstall nginx-ingress -n nginx-ingress
kubectl delete namespace nginx-ingress
```

**Note:** Helm-installed CRDs may remain after uninstall. Do not delete shared CRDs merely to clean up a lab.

### HAProxy (optional Helm installation)

```bash
helm uninstall haproxy-ingress -n haproxy-controller
kubectl delete namespace haproxy-controller
```

<details>
<summary>Historical cleanup commands for the old manual installations</summary>

### NGINX

Delete the whole namespace

```bash
kubectl delete namespace nginx-ingress
```

Then the cluster role and cluster role binding

```bash
kubectl delete clusterrolebinding nginx-ingress
kubectl delete clusterrole nginx-ingress
```

And finally, all custom resource definitions. Navigate back to the cloned repository and execute

```bash
kubectl delete -f common/crds/
```

### HAProxy

Delete everything at once 

```bash
kubectl delete -f https://raw.githubusercontent.com/haproxytech/kubernetes-ingress/master/deploy/haproxy-ingress.yaml
```

</details>
