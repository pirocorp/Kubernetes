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

### Service Types

#### ClusterIP

exposes the Service on a **cluster-internal IP**. This way the Service will be only reachable from within the cluster. **This is the default**.

#### NodePort

exposes the Service on each Node's IP at a static port specified by the NodePort. A ClusterIP Service, to which the NodePort Service routes, is automatically created. We can contact the NodePort Service, from outside the cluster, by requesting **<NodeIP>:<NodePort>**. Default range is between **30000** and **32767**.

#### LoadBalancer

exposes the Service externally using a cloud provider's load balancer. NodePort and ClusterIP Services, to which the external load balancer routes, are automatically created.

#### ExternalName
  
maps the Service to the contents of the **externalName** field (e.g. foo.bar.example.com), by returning a **CNAME** record with its value. No proxying of any kind is set up.

  
```yaml
apiVersion: v1
# Service object expose pods to the outside world. Provide reliable network endpoint
kind: Service
metadata:
  name: appa-svc
  labels:
    app: appa
    ver: v1
spec:
  # Specifies service type.
  type: NodePort
  ports:
  # On which port (target port) request will be send to pod (pods).
  - port: 80
  # On which port (source port) the service object will listen for requests.
    nodePort: 30001
    protocol: TCP
  # Pods which have these labels and label values will be targeted (load balanced).
  selector:
    app: appa
    ver: v1
```

![Service Comunication](./Services.png)
  
## Replication Controller Manifest (YAML)

```yaml
apiVersion: v1
# Replication Controller looks after pod or set of pods, scale up/down pods, sets Desired State.
kind: ReplicationController
metadata:
  name: appa-rc
spec:
  # Desired number of pods (Desired State)
  replicas: 3
  # Pods label selector
  selector:
    app: appa
  # "Hidden" pod manifest
  template:
    metadata:
      labels:
        app: appa
        ver: v1
    spec:
      containers:
      - name: appa-container
        image: shekeriev/k8s-appa:v1
        ports:
        - containerPort: 80
```

![Replication Controllers](./Replication%20Controllers.png)
  
## Replica Set Manifest (YAML)
  
```yaml
apiVersion: apps/v1
# Replica Set looks after pod or set of pods, scale up/down pods, sets desired state, preferred over Replication Controllers
kind: ReplicaSet
metadata:
  name: appa-rs
spec:
  # Desired number of pods (Desired State)
  replicas: 3
  # Pods label selector
  selector:
    matchLabels:
      app: appa
  # "Hidden" pod manifest
  template:
    metadata:
      labels:
        app: appa
        ver: v1
    spec:
      containers:
      - name: appa-container
        image: shekeriev/k8s-appa:v1
        ports:
        - containerPort: 80
```

  ![Replica Set](./Replica%20Set.png)
