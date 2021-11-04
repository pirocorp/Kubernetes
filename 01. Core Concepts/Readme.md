# Manifest files explanations (YAML)

## Simple Pod Manifest (YAML)

```yaml
# Service information
apiVersion: v1
# Kubernetes object type
# Pod contains one or more containers.
kind: Pod
metadata:
  name: appa-pod
  # Labels are key value pairs. They can be used to target given objects
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


## Simple Service Manifest (YAML)

```yaml
apiVersion: v1
# Expose pods to the outside world. Provide reliable network endpoint
kind: Service
metadata:
  name: appa-svc
  labels:
    app: appa
    ver: v1
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: appa
    ver: v1
```

![Service Comunication](./Services.png)
