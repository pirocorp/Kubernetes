# Kubernetes Objects

- Kubernetes objects are persistent entities.
- They are used to represent the state of the cluster.
- An object is a **"record of intent"**. Once created, the Kubernetes system will constantly work to ensure that object exists.
- Almost every object includes two nested object fields.
  - **Spec** provides a description of the characteristics (**desired state**).
  - **Status** describes the current state of the object.
- They include **Pods**, **Services**, **Namespaces**, **Volumes**, etc.

## Required Fields

In the ```.yaml``` file for the Kubernetes object you want to create, you'll need to set values for the following fields:

- ```apiVersion``` - Which version of the Kubernetes API you're using to create this object
- ```kind``` - What kind of object you want to create
- ```metadata``` - Data that helps uniquely identify the object, including a name string, UID, and optional namespace
- ```spec``` - What state you desire for the object

## Kubernetes Object Management

### Imperative commands

When using imperative commands, a user operates directly on live objects in a cluster. The user provides operations to the kubectl command as arguments or flags.

Commands are invoked against live objects. We directly state what should be done. Good for development or test and for one-off tasks

Example: 

```bash
kubectl create deployment nginx --image nginx
```

### Imperative object configuration

In imperative object configuration, the **kubectl** command specifies the operation (**create**, **replace**, etc.), optional flags and **at least one file name**. The file specified must contain a full definition of the object in YAML or JSON format.

Operations are specified together with at least one file, which contains the definition of target object(s). Can be used in production.

Example:
```bash
kubectl create -f nginx.yaml
```

### Declarative object configuration

When using declarative object configuration, a user operates on object configuration files stored locally, however the user does not define the operations to be taken on the files. Create, update, and delete operations are automatically detected per-object by kubectl. This enables working on directories, where different operations might be needed for different objects.

Operates with local configuration files but the actions are not stated explicitly. Can work with files and folders.

Examples:

Process all object configuration files in the ```configs``` directory, and create or patch the live objects. You can first diff to see what changes are going to be made, and then apply:

```bash
kubectl diff -f configs/
kubectl apply -f configs/
```

Recursively process directories:

```bash
kubectl diff -R -f configs/
kubectl apply -R -f configs/
```

## Namespaces

- Kubernetes supports multiple virtual clusters.
- These virtual clusters are called **namespaces**.
- Namespaces provide a **scope for names**.
- Names of resources need to be **unique** within a namespace.
- Namespaces **cannot be nested** inside one another.
- Each Kubernetes resource can **only be in one** namespace.
- Most Kubernetes resources are in some namespace.
- Namespace resources are not themselves (and others such as **nodes**) in a namespace.
- Deleting a Namespace will clean up everything under it.

### Namespaces and DNS

When you create a Service, it creates a corresponding DNS entry. This entry is of the form ```<service-name>.<namespace-name>.svc.cluster.local```, which means that if a container only uses ```<service-name>```, it will resolve to the service which is local to a namespace. This is useful for using the same configuration across multiple namespaces such as Development, Staging and Production. If you want to reach across namespaces, you need to use the fully qualified domain name (FQDN).

### Automatic labelling (since 1.21)

The Kubernetes control plane sets an immutable label kubernetes.io/metadata.name on all namespaces. The value of the label is the namespace name.

![Namespaces vs Clusters vs Data Centers](./Namespaces%20vs%20Clusters%20vs%20Data%20Centers.png)

## Pod

- Smallest **unit of scheduling**.
- **Scheduled** on nodes.
- **One** or **more** containers.
- Containers **share** the pod **environment**.
- **Deployed as one** and on **one node**. It is **atomic**.
- Created via **manifest files**.
- Pods are generally not created directly and are created using workload resources.

In terms of Docker concepts, a Pod is similar to a group of Docker containers with shared namespaces and shared filesystem volumes.

### Workload resources for managing pods

Usually you don't need to create Pods directly, even singleton Pods. Instead, create them using workload resources such as Deployment or Job. If your Pods need to track state, consider the StatefulSet resource.

Pods in a Kubernetes cluster are used in two main ways:

- Pods that run a single container. The "one-container-per-Pod" model is the most common Kubernetes use case; in this case, you can think of a Pod as a wrapper around a single container; Kubernetes manages Pods rather than managing the containers directly.
- Pods that run multiple containers that need to work together. A Pod can encapsulate an application composed of multiple co-located containers that are tightly coupled and need to share resources. These co-located containers form a single cohesive unit of service—for example, one container serving data stored in a shared volume to the public, while a separate sidecar container refreshes or updates those files. The Pod wraps these containers, storage resources, and an ephemeral network identity together as a single unit.

Each Pod is meant to run a single instance of a given application. If you want to scale your application horizontally (to provide more overall resources by running more instances), you should use multiple Pods, one for each instance. In Kubernetes, this is typically referred to as replication. Replicated Pods are usually created and managed as a group by a workload resource and its controller.

### How Pods manage multiple containers

Pods are designed to support multiple cooperating processes (as containers) that form a cohesive unit of service. The containers in a Pod are automatically co-located and co-scheduled on the same physical or virtual machine in the cluster. The containers can share resources and dependencies, communicate with one another, and coordinate when and how they are terminated.

For example, you might have a container that acts as a web server for files in a shared volume, and a separate "sidecar" container that updates those files from a remote source, as in the following diagram:

![image](https://user-images.githubusercontent.com/34960418/147664476-f1cd08e0-53f2-4100-84f4-fe4a1b1b0408.png)

Some Pods have init containers as well as app containers. Init containers run and complete before the app containers are started.

Pods natively provide two kinds of shared resources for their constituent containers: networking and storage.

### Working with Pods

You'll rarely create individual Pods directly in Kubernetes—even singleton Pods. This is because Pods are designed as relatively ephemeral, disposable entities. When a Pod gets created (directly by you, or indirectly by a controller), the new Pod is scheduled to run on a Node in your cluster. The Pod remains on that node until the Pod finishes execution, the Pod object is deleted, the Pod is evicted for lack of resources, or the node fails.

Note: Restarting a container in a Pod should not be confused with restarting a Pod. A Pod is not a process, but an environment for running container(s). A Pod persists until it is deleted.

### Pod Lifecycle

Pods follow a defined lifecycle, starting in the ```Pending``` phase, moving through ```Running``` if at least one of its primary containers starts OK, and then through either the ```Succeeded``` or ```Failed``` phases depending on whether any container in the Pod terminated in failure.

Whilst a Pod is running, the kubelet is able to restart containers to handle some kind of faults. Within a Pod, Kubernetes tracks different container states and determines what action to take to make the Pod healthy again.

Pods are only scheduled once in their lifetime. Once a Pod is scheduled (assigned) to a Node, the Pod runs on that Node until it stops or is terminated.

### Pod lifetime

Like individual application containers, Pods are considered to be relatively ephemeral (rather than durable) entities. Pods do not, by themselves, self-heal. Kubernetes uses a higher-level abstraction, called a controller, that handles the work of managing the relatively disposable Pod instances. A given Pod (as defined by a UID) is never "rescheduled" to a different node; instead, that Pod can be replaced by a new, near-identical Pod, with even the same name if desired, but with a different UID.

When something is said to have the same lifetime as a Pod, such as a volume, that means that the thing exists as long as that specific Pod (with that exact UID) exists. If that Pod is deleted for any reason, and even if an identical replacement is created, the related thing (a volume, in this example) is also destroyed and created anew.

### Pod phase



| Value     | Description                                                                                                                                                                                                                                                        |
|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Pending   | The Pod has been accepted by the Kubernetes cluster, but one or more of the containers has not been set up and made ready to run. This includes time a Pod spends waiting to be scheduled as well as the time spent downloading container images over the network. |
| Running   | The Pod has been bound to a node, and all of the containers have been created. At least one container is still running, or is in the process of starting or restarting.                                                                                            |
| Succeeded | All containers in the Pod have terminated in success, and will not be restarted.                                                                                                                                                                                   |
| Failed    | All containers in the Pod have terminated, and at least one container has terminated in failure. That is, the container either exited with non-zero status or was terminated by the system.                                                                        |
| Unknown   | For some reason the state of the Pod could not be obtained. This phase typically occurs due to an error in communicating with the node where the Pod should be running.                                                                                            |

### Container states

Once the scheduler assigns a Pod to a Node, the kubelet starts creating containers for that Pod using a container runtime. There are three possible container states: ```Waiting```, ```Running```, and ```Terminated```.

#### Waiting

If a container is not in either the ```Running``` or ```Terminated``` state, it is ```Waiting```. A container in the ```Waiting``` state is still running the operations it requires in order to complete start up: for example, pulling the container image from a container image registry, or applying Secret data. When you use ```kubectl``` to query a Pod with a container that is ```Waiting```, you also see a Reason field to summarize why the container is in that state.

#### Running

The ```Running``` status indicates that a container is executing without issues. If there was a ```postStart``` hook configured, it has already executed and finished. When you use ```kubectl``` to query a Pod with a container that is ```Running```, you also see information about when the container entered the ```Running``` state.

#### Terminated

A container in the ```Terminated``` state began execution and then either ran to completion or failed for some reason. When you use ```kubectl``` to query a Pod with a container that is ```Terminated```, you see a reason, an exit code, and the start and finish time for that container's period of execution.

### Example Pod manifest

```yaml
# Service information (Kubernetes Api version)
apiVersion: v1
# What kind of object you want
# Pod contains one or more containers.
kind: Pod
# Data that helps uniquely identify the object, including a name string, UID, and optional namespace
metadata:
  name: appa-pod
  # Labels are key value pairs. They can be used to target given objects
  labels:
    app: appa
    ver: v1
# What state you desire for the object
spec:
  # Specifies containers in the pod
  containers:
  # Container name (first)
  - name: appa-container
    # From which image, container should be build (docker image)
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
  # Port exposed by the service.
  - port: 80
  # Port exposed by the service but in the k8s cluster.
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
  # "Hidden" pod definition
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

Replica Set is rarely used in its own. It's commonly used with Deployment object.
  
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
    # Replica Set label selector is more sophisticated than Replication Controller label selector
    matchLabels:
      app: appa
  # "Hidden" pod definition
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
  
  
## Deployment Manifest (YAML)

Deployment creates ReplicaSet
  
```yaml
apiVersion: apps/v1
# Deployment simplifies updates and rollbacks, self documenting, suitable for versioning 
kind: Deployment
metadata:
  name: appa-deploy
spec:
  # Desired number of pods (Desired State)
  replicas: 10
  # Pods label selector
  selector:
    matchLabels: 
      app: appa
      ver: v1
  # optional, default 0, how many seconds 
  minReadySeconds: 15
  # the whole block can be skipped
  strategy:
    # strategy to replace old pods, defaults to RollingUpdate
    type: RollingUpdate
    rollingUpdate:
      # maximum number of unavailable pods, defaults to 25%
      maxUnavailable: 1
      # maximum number of pods that can be created in excess, defaults to 25%
      maxSurge: 1
  # "Hidden" pod definition
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

  ![Deployment](./Deployment.png)
  
# Overal Architecture

![Architecture Overview](./Architecture%20Overview.png)
