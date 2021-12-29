# Kubernetes

## Containerization

**OS-level virtualization** refers to an operating system paradigm in which the kernel allows the existence of multiple isolated user space instances known as containers, zones, jails, ...

On Unix-like operating systems, this feature can be seen as an advanced implementation of the standard chroot mechanism, which changes the apparent root folder for the current running process and its children. In addition to **isolation** mechanisms, the kernel often provides **resource-management features** to limit the impact of one container's activities on other containers.

With **operating-system-virtualization**, or **containerization**, it is possible to run programs within containers, to which only **parts of these resources are allocated**. A program expecting to see the whole computer, once run inside a container, can only see the allocated resources and believes them to be all that is available. Several containers can be created on each operating system, to each of which a subset of the computer's resources is allocated. Each **container may contain any number of computer programs**. These programs may run concurrently or separately, and may even interact with one another.

**Operating-system-level virtualization** is commonly used in virtual **hosting environments**, where it is useful for **securely allocating** finite **hardware** resources among a large number of mutually-distrusting users. System administrators may also use it for consolidating server hardware by moving services on separate hosts into containers on the one server.

Other typical scenarios include separating several programs to separate containers for **improved security**, **hardware independence**, and added **resource management features**. The improved security provided by the use of a chroot mechanism, however, is nowhere near ironclad. Operating-system-level virtualization implementations capable of live migration can also be used for **dynamic load balancing** of **containers between nodes in a cluster**.

**Operating-system-level virtualization** usually imposes **less overhead than full virtualization** because programs in OS-level virtual partitions use the operating system's normal system call interface and do not need to be subjected to emulation or be run in an intermediate virtual machine, as is the case with full virtualization (such as VMware ESXi, QEMU, or Hyper-V) 

![image](https://user-images.githubusercontent.com/34960418/147653601-f596fcdf-78ed-4b31-8e79-bb6c5b674a25.png)

## Docker Container

A **container** is a **standard unit of software that packages up code and all its dependencies** so the application runs quickly and reliably from one computing environment to another. A Docker container image is a lightweight, standalone, executable package of software that includes everything needed to run an application: code, runtime, system tools, system libraries and settings.

**Container images become containers at runtime** and in the case of Docker containers - images become containers when they run on Docker Engine. Available for both Linux and Windows-based applications, containerized software will always run the same, regardless of the infrastructure. Containers isolate software from its environment and ensure that it works uniformly despite differences for instance between development and staging.

![image](https://user-images.githubusercontent.com/34960418/147654316-422a936c-9489-4eb0-90fd-d89153f2f7b4.png)

- **Container** - A runnable instance of an image. Containers are processes with much more isolation.
- **Image** - A read-only template of a container built from layers. Images provide a way for simpler software distribution
- **Repository** - A collection of different versions of an image identified by tags
- **Registry** - A collection of repositories

## Kubernetes

- Runs a cluster of hosts
- Schedules containers to run on different hosts
- Facilitates the communication between the containers
- Provides and controls access to/from outside world
- Tracks and optimizes the resource usage

![image](https://user-images.githubusercontent.com/34960418/147655118-6ef8c3c7-9e8e-40b2-a371-a8cec74ab8ac.png)

### Control Plane (master) Nodes

- Responsible for **managing** the cluster
- Typically, **more than one** is installed
- In HA mode one node is the **Leader**
- It is **work-free** (this can be changed)
- Components running on master are also known as **Control Plane**
- Can be reached via **CLI** (kubectl), **APIs**, or **Dashboard**

![image](https://user-images.githubusercontent.com/34960418/147655346-15dcff5f-ec59-444c-ad8d-a9f95b868933.png)

#### Control Plane Nodes: Persistent Store

- Based on **etcd**
- **Persistent** storage
- Cluster **state** and **configuration**
- **Distributed** and **consistent**
- Provides single **source of truth**
- Can be installed **externally**

#### Control Plane Nodes: API Server

- Exposes the **Kubernetes API (REST)**
- **Front-end** for the control plane
- **Administrative** tasks
- Consumes **JSON** via **Manifest files (YAML)**

#### Control Plane Nodes: Controller

- Executes **control loops**
- Responsible for other controllers
  - Node controller
  - Endpoints controller
  - Namespace controller, etc.
- Watches for **changes**
- Maintains the **desired state**

#### Control Plane Nodes: Scheduler

- **Listens** API Server for new work
- **Assigns work** to nodes

### (Worker) Nodes

![image](https://user-images.githubusercontent.com/34960418/147656355-445cbf18-e506-458a-a952-49cb83d11295.png)

- **Container runtime** - Docker, containerd, CRI-O, etc
- **kubelet** - Communicates with the control plane
- **kube-proxy** - Network proxy

#### (Worker) Nodes: kubelet

- Main Kubernetes agent
- Registers node in the cluster
- Listens to the API Server
- Creates pods
- Reports back to the control plane
- Exposes endpoint on :10255
  - /spec
  - /healthz
  - /pods

#### (Worker) Nodes: Container Runtime

- Container management:
  - **Pulling** images
  - **Starting** and **stopping**
- It is **pluggable**
- By default, is **Docker**

#### (Worker) Nodes: kube-proxy

- Provides the **networking**
- Each pod has its **own address**
- All containers in a pod share the **same IP** address
- Offers **load balancing** across all pods in a **service**

### kubectl (kubernetes cli)

- Controls Kubernetes clusters
- Expects a file named **config** in the **$HOME/.kube** directory
- Other files can be specified by setting the **KUBECONFIG** environment variable or by setting the **--kubeconfig** flag

The syntax is 

```bash
kubectl [command] [TYPE] [NAME] [flags]
```

```command```: Specifies the operation that you want to perform on one or more resources, for example ```create```, ```get```, ```describe```, ```delete```

```TYPE```: Specifies the resource type. Resource types are case-insensitive and you can specify the singular, plural, or abbreviated forms.

```NAME```: Specifies the name of the resource. Names are case-sensitive. If the name is omitted, details for all resources are displayed.

```flags```: Specifies optional flags.

***Caution***: Flags that you specify from the command line override default values and any corresponding environment variables.

#### Operations

| Operation     | Syntax                                                                                                                                                                                               | Description                                                                                                                                                                                                                                               |
|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| alpha         | kubectl alpha SUBCOMMAND [flags]                                                                                                                                                                     | List the available commands that correspond to alpha features, which are not enabled in Kubernetes clusters by default.                                                                                                                                   |
| annotate      | kubectl annotate (-f FILENAME \| TYPE NAME \| TYPE/NAME) KEY_1=VAL_1 ... KEY_N=VAL_N [--overwrite] [--all] [--resource-version=version] [flags]                                                      | Add or update the annotations of one or more resources.                                                                                                                                                                                                   |
| api-resources | kubectl api-resources [flags]                                                                                                                                                                        | List the API resources that are available.                                                                                                                                                                                                                |
| api-versions  | kubectl api-versions [flags]                                                                                                                                                                         | List the API versions that are available.                                                                                                                                                                                                                 |
| apply         | kubectl apply -f FILENAME [flags]                                                                                                                                                                    | Apply a configuration change to a resource from a file or stdin.                                                                                                                                                                                          |
| attach        | kubectl attach POD -c CONTAINER [-i] [-t] [flags]                                                                                                                                                    | Attach to a running container either to view the output stream or interact with the container (stdin).                                                                                                                                                    |
| auth          | kubectl auth [flags] [options]                                                                                                                                                                       | Inspect authorization.                                                                                                                                                                                                                                    |
| autoscale     | kubectl autoscale (-f FILENAME \| TYPE NAME \| TYPE/NAME) [--min=MINPODS] --max=MAXPODS [--cpu-percent=CPU] [flags]                                                                                  | Automatically scale the set of pods that are managed by a replication controller.                                                                                                                                                                         |
| certificate   | kubectl certificate SUBCOMMAND [options]                                                                                                                                                             | Modify certificate resources.                                                                                                                                                                                                                             |
| cluster-info  | kubectl cluster-info [flags]                                                                                                                                                                         | Display endpoint information about the master and services in the cluster.                                                                                                                                                                                |
| completion    | kubectl completion SHELL [options]                                                                                                                                                                   | Output shell completion code for the specified shell (bash or zsh).                                                                                                                                                                                       |
| config        | kubectl config SUBCOMMAND [flags]                                                                                                                                                                    | Modifies kubeconfig files. See the individual subcommands for details.                                                                                                                                                                                    |
| convert       | kubectl convert -f FILENAME [options]                                                                                                                                                                | Convert config files between different API versions. Both YAML and JSON formats are accepted. Note - requires kubectl-convert plugin to be installed.                                                                                                     |
| cordon        | kubectl cordon NODE [options]                                                                                                                                                                        | Mark node as unschedulable.                                                                                                                                                                                                                               |
| cp            | kubectl cp <file-spec-src> <file-spec-dest> [options]                                                                                                                                                | Copy files and directories to and from containers.                                                                                                                                                                                                        |
| create        | kubectl create -f FILENAME [flags]                                                                                                                                                                   | Create one or more resources from a file or stdin.                                                                                                                                                                                                        |
| delete        | kubectl delete (-f FILENAME \| TYPE [NAME \| /NAME \| -l label \| --all]) [flags]                                                                                                                    | Delete resources either from a file, stdin, or specifying label selectors, names, resource selectors, or resources.                                                                                                                                       |
| describe      | kubectl describe (-f FILENAME \| TYPE [NAME_PREFIX \| /NAME \| -l label]) [flags]                                                                                                                    | Display the detailed state of one or more resources.                                                                                                                                                                                                      |
| diff          | kubectl diff -f FILENAME [flags]                                                                                                                                                                     | Diff file or stdin against live configuration.                                                                                                                                                                                                            |
| drain         | kubectl drain NODE [options]                                                                                                                                                                         | Drain node in preparation for maintenance.                                                                                                                                                                                                                |
| edit          | kubectl edit (-f FILENAME \| TYPE NAME \| TYPE/NAME) [flags]                                                                                                                                         | Edit and update the definition of one or more resources on the server by using the default editor.                                                                                                                                                        |
| exec          | kubectl exec POD [-c CONTAINER] [-i] [-t] [flags] [-- COMMAND [args...]]                                                                                                                             | Execute a command against a container in a pod.                                                                                                                                                                                                           |
| explain       | kubectl explain [--recursive=false] [flags]                                                                                                                                                          | Get documentation of various resources. For instance pods, nodes, services, etc.                                                                                                                                                                          |
| expose        | kubectl expose (-f FILENAME \| TYPE NAME \| TYPE/NAME) [--port=port] [--protocol=TCP\|UDP] [--target-port=number-or-name] [--name=name] [--external-ip=external-ip-of-service] [--type=type] [flags] | Expose a replication controller, service, or pod as a new Kubernetes service.                                                                                                                                                                             |
| get           | kubectl get (-f FILENAME \| TYPE [NAME \| /NAME \| -l label]) [--watch] [--sort-by=FIELD] [[-o \| --output]=OUTPUT_FORMAT] [flags]                                                                   | List one or more resources.                                                                                                                                                                                                                               |
| kustomize     | kubectl kustomize <dir> [flags] [options]                                                                                                                                                            | List a set of API resources generated from instructions in a kustomization.yaml file. The argument must be the path to the directory containing the file, or a git repository URL with a path suffix specifying same with respect to the repository root. |
| label         | kubectl label (-f FILENAME \| TYPE NAME \| TYPE/NAME) KEY_1=VAL_1 ... KEY_N=VAL_N [--overwrite] [--all] [--resource-version=version] [flags]                                                         | Add or update the labels of one or more resources.                                                                                                                                                                                                        |
| logs          | kubectl logs POD [-c CONTAINER] [--follow] [flags]                                                                                                                                                   | Print the logs for a container in a pod.                                                                                                                                                                                                                  |
| options       | kubectl options                                                                                                                                                                                      | List of global command-line options, which apply to all commands.                                                                                                                                                                                         |
| patch         | kubectl patch (-f FILENAME \| TYPE NAME \| TYPE/NAME) --patch PATCH [flags]                                                                                                                          | Update one or more fields of a resource by using the strategic merge patch process.                                                                                                                                                                       |
| plugin        | kubectl plugin [flags] [options]                                                                                                                                                                     | Provides utilities for interacting with plugins.                                                                                                                                                                                                          |
| port-forward  | kubectl port-forward POD [LOCAL_PORT:]REMOTE_PORT [...[LOCAL_PORT_N:]REMOTE_PORT_N] [flags]                                                                                                          | Forward one or more local ports to a pod.                                                                                                                                                                                                                 |
| proxy         | kubectl proxy [--port=PORT] [--www=static-dir] [--www-prefix=prefix] [--api-prefix=prefix] [flags]                                                                                                   | Run a proxy to the Kubernetes API server.                                                                                                                                                                                                                 |
| replace       | kubectl replace -f FILENAME                                                                                                                                                                          | Replace a resource from a file or stdin.                                                                                                                                                                                                                  |
| rollout       | kubectl rollout SUBCOMMAND [options]                                                                                                                                                                 | Manage the rollout of a resource. Valid resource types include: deployments, daemonsets and statefulsets.                                                                                                                                                 |
| run           | kubectl run NAME --image=image [--env="key=value"] [--port=port] [--dry-run=server\|client\|none] [--overrides=inline-json] [flags]                                                                  | Run a specified image on the cluster.                                                                                                                                                                                                                     |
| scale         | kubectl scale (-f FILENAME \| TYPE NAME \| TYPE/NAME) --replicas=COUNT [--resource-version=version] [--current-replicas=count] [flags]                                                               | Update the size of the specified replication controller.                                                                                                                                                                                                  |
| set           | kubectl set SUBCOMMAND [options]                                                                                                                                                                     | Configure application resources.                                                                                                                                                                                                                          |
| taint         | kubectl taint NODE NAME KEY_1=VAL_1:TAINT_EFFECT_1 ... KEY_N=VAL_N:TAINT_EFFECT_N [options]                                                                                                          | Update the taints on one or more nodes.                                                                                                                                                                                                                   |
| top           | kubectl top [flags] [options]                                                                                                                                                                        | Display Resource (CPU/Memory/Storage) usage.                                                                                                                                                                                                              |
| uncordon      | kubectl uncordon NODE [options]                                                                                                                                                                      | Mark node as schedulable.                                                                                                                                                                                                                                 |
| version       | kubectl version [--client] [flags]                                                                                                                                                                   | Display the Kubernetes version running on the client and server.                                                                                                                                                                                          |
| wait          | kubectl wait ([-f FILENAME] \| resource.group/resource.name \| resource.group [(-l label \| --all)]) [--for=delete\|--for condition=available] [options]                                             |                                                                                                                                                                                                                                                           |


#### Resource types

| NAME                            | SHORTNAMES | APIGROUP                     | NAMESPACED | KIND                           |
|---------------------------------|------------|------------------------------|------------|--------------------------------|
| bindings                        |            |                              | true       | Binding                        |
| componentstatuses               | cs         |                              | false      | ComponentStatus                |
| configmaps                      | cm         |                              | true       | ConfigMap                      |
| endpoints                       | ep         |                              | true       | Endpoints                      |
| events                          | ev         |                              | true       | Event                          |
| limitranges                     | limits     |                              | true       | LimitRange                     |
| namespaces                      | ns         |                              | false      | Namespace                      |
| nodes                           | no         |                              | false      | Node                           |
| persistentvolumeclaims          | pvc        |                              | true       | PersistentVolumeClaim          |
| persistentvolumes               | pv         |                              | false      | PersistentVolume               |
| pods                            | po         |                              | true       | Pod                            |
| podtemplates                    |            |                              | true       | PodTemplate                    |
| replicationcontrollers          | rc         |                              | true       | ReplicationController          |
| resourcequotas                  | quota      |                              | true       | ResourceQuota                  |
| secrets                         |            |                              | true       | Secret                         |
| serviceaccounts                 | sa         |                              | true       | ServiceAccount                 |
| services                        | svc        |                              | true       | Service                        |
| mutatingwebhookconfigurations   |            | admissionregistration.k8s.io | false      | MutatingWebhookConfiguration   |
| validatingwebhookconfigurations |            | admissionregistration.k8s.io | false      | ValidatingWebhookConfiguration |
| customresourcedefinitions       | crd,crds   | apiextensions.k8s.io         | false      | CustomResourceDefinition       |
| apiservices                     |            | apiregistration.k8s.io       | false      | APIService                     |
| controllerrevisions             |            | apps                         | true       | ControllerRevision             |
| daemonsets                      | ds         | apps                         | true       | DaemonSet                      |
| deployments                     | deploy     | apps                         | true       | Deployment                     |
| replicasets                     | rs         | apps                         | true       | ReplicaSet                     |
| statefulsets                    | sts        | apps                         | true       | StatefulSet                    |
| tokenreviews                    |            | authentication.k8s.io        | false      | TokenReview                    |
| localsubjectaccessreviews       |            | authorization.k8s.io         | true       | LocalSubjectAccessReview       |
| selfsubjectaccessreviews        |            | authorization.k8s.io         | false      | SelfSubjectAccessReview        |
| selfsubjectrulesreviews         |            | authorization.k8s.io         | false      | SelfSubjectRulesReview         |
| subjectaccessreviews            |            | authorization.k8s.io         | false      | SubjectAccessReview            |
| horizontalpodautoscalers        | hpa        | autoscaling                  | true       | HorizontalPodAutoscaler        |
| cronjobs                        | cj         | batch                        | true       | CronJob                        |
| jobs                            |            | batch                        | true       | Job                            |
| certificatesigningrequests      | csr        | certificates.k8s.io          | false      | CertificateSigningRequest      |
| leases                          |            | coordination.k8s.io          | true       | Lease                          |
| endpointslices                  |            | discovery.k8s.io             | true       | EndpointSlice                  |
| events                          | ev         | events.k8s.io                | true       | Event                          |
| ingresses                       | ing        | extensions                   | true       | Ingress                        |
| flowschemas                     |            | flowcontrol.apiserver.k8s.io | false      | FlowSchema                     |
| prioritylevelconfigurations     |            | flowcontrol.apiserver.k8s.io | false      | PriorityLevelConfiguration     |
| ingressclasses                  |            | networking.k8s.io            | false      | IngressClass                   |
| ingresses                       | ing        | networking.k8s.io            | true       | Ingress                        |
| networkpolicies                 | netpol     | networking.k8s.io            | true       | NetworkPolicy                  |
| runtimeclasses                  |            | node.k8s.io                  | false      | RuntimeClass                   |
| poddisruptionbudgets            | pdb        | policy                       | true       | PodDisruptionBudget            |
| podsecuritypolicies             | psp        | policy                       | false      | PodSecurityPolicy              |
| clusterrolebindings             |            | rbac.authorization.k8s.io    | false      | ClusterRoleBinding             |
| clusterroles                    |            | rbac.authorization.k8s.io    | false      | ClusterRole                    |
| rolebindings                    |            | rbac.authorization.k8s.io    | true       | RoleBinding                    |
| roles                           |            | rbac.authorization.k8s.io    | true       | Role                           |
| priorityclasses                 | pc         | scheduling.k8s.io            | false      | PriorityClass                  |
| csidrivers                      |            | storage.k8s.io               | false      | CSIDriver                      |
| csinodes                        |            | storage.k8s.io               | false      | CSINode                        |
| storageclasses                  | sc         | storage.k8s.io               | false      | StorageClass                   |
| volumeattachments               |            | storage.k8s.io               | false      | VolumeAttachment               |

#### Output options
  
| Output format                           | Description                                                                                           |
|-----------------------------------------|-------------------------------------------------------------------------------------------------------|
| ```-o custom-columns=<spec>```          | Print a table using a comma separated list of custom columns.                                         |
| ```-o custom-columns-file=<filename>``` | Print a table using the custom columns template in the <filename> file.                               |
| ```-o json```                           | Output a JSON formatted API object.                                                                   |
| ```-o jsonpath=<template>```            | Print the fields defined in a jsonpath expression.                                                    |
| ```-o jsonpath-file=<filename>```       | Print the fields defined by the jsonpath expression in the <filename> file.                           |
| ```-o name```                           | Print only the resource name and nothing else.                                                        |
| ```-o wide```                           | Output in the plain-text format with any additional information. For pods, the node name is included. |
| ```-o yaml```                           | Output a YAML formatted API object.                                                                   |

  
