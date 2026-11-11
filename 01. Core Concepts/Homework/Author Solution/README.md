> **Kubernetes 1.37 (2026):** For actual repository filenames, full task order, expected results and cleanup, follow [CORE-2026.md](../../CORE-2026.md). The historical files disagree on the Service target port (80/5000/5500); the current lab consistently uses **Service 5000 → Pod 5000, NodePort 32000**.

# Task 1

Execute a series of commands to
1. Create a namespace named homework
2. Create a homework-1 pod in that namespace that uses this (shekeriev/k8s-oracle) image and set two labels on it (all at once) - app=hw and tier=gold
3. Remove the tier=gold label with a separate command
4. Create a homework-2 pod in that namespace that uses this (shekeriev/k8s-oracle) image
5. Add a label to the second pod app=hw with a separate command
6. Set annotation on both pods with the following content purpose=homework
7. Create a homerwork-svc service to expose both pods on port 32000 of every node in the cluster

Solution:

1. To create the required namespace execute
```bash
kubectl create namespace homework
```
2. Then create the first pod with
```bash
kubectl run homework-1 --image=shekeriev/k8s-oracle --labels=app=hw,tier=gold --namespace homework
```
3. We can remove the extra label with
```bash
kubectl label pods homework-1 tier- --namespace homework
```
4. Create the second pod
```bash
kubectl run homework-2 --image=shekeriev/k8s-oracle --namespace homework
```
5. We can add label at any time with
```bash
kubectl label pods homework-2 app=hw --namespace homework
```
6. Annotations are handled with a separate command. This one, we can execute it in two steps
```bash
kubectl annotate pods homework-1 purpose=homework --namespace homework
kubectl annotate pods homework-2 purpose=homework --namespace homework
```
Or in just one (by using selectors)

```bash
kubectl annotate pods purpose=homework --namespace homework --selector=app=hw
```
7. Creating a service can be achieved both via the expose and the create commands. However, they have different set of parameters. For this task, we must use the create command
```bash
kubectl create service nodeport homework-svc --node-port=32000 --tcp=5000:5000 --namespace homework
```
If we try now to access the application, we will notice that it won’t show. Should we want to know why, we can describe the service and notice that no pods are being associated (the **endpoints** list is empty). We can handle this by changing the automatically created selector (**app=homework-svc**) of the service with something more suitable (**app=hw**) that will select the two pods
```bash
kubectl set selector service homework-svc app=hw --namespace homework
```

## Task 2

> **Working directory:** `01. Core Concepts/Homework/` for the commands below. Remove previous `namespace/homework` from Task 1 so this exercise starts cleanly. Apply the Namespace first.

Create manifests for every object (the namespace, the two pods, and the service) from task 1 and apply them one by one

Solution:

hw-ns.yaml

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: homework
```
hw-pod-1.yaml

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    purpose: homework
  labels:
    app: hw
  name: homework-1
  namespace: homework
spec:
  containers:
  - image: shekeriev/k8s-oracle
    name: homework-1
```

hw-pod-2.yaml

```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    purpose: homework
  labels:
    app: hw
  name: homework-2
  namespace: homework
spec:
  containers:
  - image: shekeriev/k8s-oracle
    name: homework-2
```

Service manifest (corresponding file: `Homework/Task 2/homework-svc.yaml`):

```yaml
apiVersion: v1
kind: Service
metadata:
  labels:
    app: hw
  name: homework-svc
  namespace: homework
spec:
  ports:
  - name: 5000-5000
    nodePort: 32000
    port: 5000
    protocol: TCP
    targetPort: 5000
  selector:
    app: hw
  type: NodePort
```

```bash
kubectl apply -f "Task 2/homework-namespace.yaml"
kubectl apply -f "Task 2/homework-1-pod.yaml"
kubectl apply -f "Task 2/homework-2-pod.yaml"
kubectl apply -f "Task 2/homework-svc.yaml"
```

## Task 3

> **NOTE (2026):** The first version applies one multi-document YAML (Namespace first). For the second, create `namespace/homework` before using `kubectl apply -f "Task 2/"` (file enumeration order is not a safe dependency). Run the variants separately.

Is there a way to submit those manifests at once? Find and demonstrate two ways of doing it

Solution:

Under Windows

```cmd
kubectl apply -f "Task 3/Task 3A.yaml"
```

Or the following under UNIX-like OSes

```bash
kubectl apply -f "Task 2/"
```

## Task 4

Try to translate the attached ```docker-compose.yml``` file to a set of Kubernetes objects and the corresponding manifest(s)

```yaml
version: "3.9"
services:
  listener:
    image: "shekeriev/k8s-listener"
  speaker:
    image: "shekeriev/k8s-speaker"
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: hw
    role: listener
  name: listener
spec:
  containers:
  - image: shekeriev/k8s-listener
    name: listener
---
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: hw
    role: speaker
  name: speaker
spec:
  containers:
  - image: shekeriev/k8s-speaker
    name: speaker
---
apiVersion: v1
kind: Service
metadata:
  labels:
    app: hw
  name: listener
spec:
  ports:
  - name: listener-port
    nodePort: 32000
    port: 5000
    protocol: TCP
    targetPort: 5000
  selector:
    app: hw
    role: listener
  type: NodePort
---
apiVersion: v1
kind: Service
metadata:
  labels:
    app: hw
  name: speaker
spec:
  ports:
  - name: speaker-port
    port: 5000
    protocol: TCP
    targetPort: 5000
  selector:
    app: hw
    role: speaker
```
