# Manifest files explanations (YAML)

## Simple Pod Manifest (YAML)

```yaml
# Service information
apiVersion: v1
# Kubernetes object type
kind: Pod
metadata:
  name: appa-pod
  # Labels are key value pairs. They 
  labels:
    app: appa
    ver: v1
# Object specification
spec:
  # Specifies containers in the object (pod)
  containers:
  # Container name (first)
  - name: appa-container
    # From which image container should be build (docker image)
    image: shekeriev/k8s-appa:v1
    ports:
    # containerPort sets the port that container will expose.
    - containerPort: 80
```

![Pod Comunication](./Pod%20Comunication.png)
