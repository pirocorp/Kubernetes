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

We assume that all we are working on a machine with minikube installed and running. Open a terminal session and make sure that your cluster is ready and reachable

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
