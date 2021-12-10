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
