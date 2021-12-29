# Task 1

Create a two node **Minikube**-based **Kubernetes** cluster and deploy a simple app on it. For example, shekeriev/k8s-oracle from the previous HW.

Solution:

To create a **minikube**-based two node **Kubernetes** cluster we must execute the following command.

Adjust the **--driver** option to match your situation. You can select one of the following **virtualbox**, **vmwarefusion**, **hyperv**, **vmware**, **docker**, or **ssh**. If not specified, the most suitable option will be auto detected and selected.

```bash
minikube start --driver=hyperv --nodes=2
```

Now, that we have our cluster, we can check if it is reachable

```bash
kubectl cluster-info
kubectl get nodes -o wide
```

Next, we can deploy a simple application on it (using the files from the previous HW)

```bash
kubectl apply -f homework.yaml
```

Then check the deployed resources
```bash
kubectl get pods,svc -n homework -o wide
```

And try to reach the application on ```http://<minikube-ip>:32000```
**Minikube IP** address can be retrieved with

```bash
minikube ip
```
Or directly the service **URL** with

```bash
minikube service list
```
Once done, clean up the application with

```bash
kubectl delete -f homework.yaml
```

And then the **minikube** cluster with

```bash
minikube delete
```

# Task 2

Create a three node **KIND**-based **Kubernetes** cluster and deploy a simple app on it. For example, ```shekeriev/k8s-oracle``` from the previous HW 

Solution:

kind-cluster.yaml

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 32000
    hostPort: 8080
- role: worker
- role: worker
```

Then start the cluster with

```bash
kind create cluster --name hw --config kind-cluster.yaml
```

Finally, switch the context to the new cluster

```bash
kubectl config use-context kind-hw
```

Ask for some information about the cluster

```bash
kubectl cluster-info
kubectl get nodes -o wide
```

Then spin up the application

```bash
kubectl apply -f homework.yaml
```

And check its components

```bash
kubectl get pods,svc -n homework -o wide
```

Try to reach the application on ```http://localhost:8080```
Once done exploring, remove the application with

```bash
kubectl delete -f homework.yaml
```

And finally, remove the cluster with

```bash
kind delete cluster --name hw
```
