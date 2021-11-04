# Manifest files explanations (YAML)

## Simple Pod Manifest (YAML)

```yaml
# service information
apiVersion: v1
# kubernetes object type
kind: Pod
metadata:
  name: appa-pod
# object specification
spec:
  # specifies containers in the object (pod)
  containers:
  # container name (first)
  - name: appa-container
    # from which image container should be build (docker)
    image: shekeriev/k8s-appa:v1
    ports:
    # containerPort sets the port that container will expose.
    - containerPort: 80
```

![Pod Comunication](./Pod%20Comunication.png)
