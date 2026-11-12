# Kubernetes & OpenShift — self-contained hands-on course

**16 modules (00–15)** · **Kubernetes 1.37 baseline** · Ubuntu Server 24.04 LTS · containerd 2.x · Calico 3.33 (VXLAN; BGP disabled)

> **Start here.** This `README.md` is the **single course guide and navigation hub**. Each module's own README contains its explanations, current hands-on labs, expected results, troubleshooting and cleanup. **Modules 01–08 preserve the useful original conceptual explanations, while replacing obsolete 2021 lab procedures with the Kubernetes 1.37 exercises at the relevant points in each lesson.** Original DOCX/PPTX/ZIP resources remain in the repository for historical reference. The **complete original root-level foundational lecture** (containerization, Docker and Kubernetes concepts, diagrams, and command examples) is preserved [at the bottom of this README](#original-foundations-lecture--historical-reference).

> **Verification boundary:** The Kubernetes 1.37 modules 00–08 have been **statically audited** for prerequisites, source references, command paths, manifest versions, expected results and cleanup. **They have not been executed end-to-end on a live Kubernetes 1.37 cluster**; actual success requires accessible VMs, images/charts and permissions. Other modules have their own distinct validation status; a passing CI run is not proof of a real OpenShift deployment.

## Getting started

1. **Read [Module 00 — resources and blueprint](./00.%20Resources/README.md)** to understand the original learning objectives and assessment scope.
2. **Build your lab cluster** by following [Module 02 — integrated Kubernetes 1.37 setup](./02.%20Cluster%20Setup%20and%20Management/README.md#kubernetes-137-integrated-labs), sections **0–8**. The default topology is one control-plane VM and two worker VMs. Check that all nodes are `Ready`, Calico is healthy and your workstation `kubectl` context works.
3. **Study [Module 01](./01.%20Core%20Concepts/Readme.md)**, then return to Module 02 for its optional homework and advanced cluster management; continue through Modules 03–08 in order. **Complete one lab at a time**, including its verification and cleanup.
4. **Take [Module 08 — practice exam](./08.%20Exam%20Preparation/README.md#kubernetes-137-integrated-labs)** after the preceding modules. Continue with Module 09 OpenShift, then Modules 10–15 for full-stack, API, service-mesh, event-driven and CDC projects.

**Recommended lab sequence:** 02 setup → 01 → 02 homework/extensions → 03 → 04 → 05 → 06 → 07 → 08 exam → 09 → 10 → 11 → 12 → 13 → 14 → 15.

## Modules and learning outcomes

| Module | Full lesson / lab | Learning outcome |
|---|---|---|
| 00 — Resources | [Module 00 README](./00.%20Resources/README.md) | Exam blueprint and course prerequisites; not a runnable lab |
| 01 — Core Concepts | [Integrated Module 01 README](./01.%20Core%20Concepts/Readme.md) | Four tasks: Namespaces, labels, Pods, NodePort Service, declarative files and optional kind |
| 02 — Cluster Setup & Management | [Integrated Module 02 README](./02.%20Cluster%20Setup%20and%20Management/README.md) | Basic/HA kubeadm clusters, etcd, upgrades, Calico; Minikube/kind/Vagrant homework |
| 03 — Security & Policies | [Integrated Module 03 README](./03.%20Security%20and%20Policies/README.md) | X.509 users, RBAC, quota/LimitRange, Calico NetworkPolicy allow/deny tests |
| 04 — Storage & Persistence | [Integrated Module 04 README](./04.%20Storage%20and%20Persistence/README.md) | NFS, ConfigMaps/Secrets, three PVC/PV StatefulSet, Retain, supported Git init-container alternative |
| 05 — Advanced Concepts | [Integrated Module 05 README](./05.%20Advanced%20Concepts/README.md) | Init containers, HTTP page, F5 NGINX HTTPS fanout, Traefik and modern HPA |
| 06 — Observability & Troubleshooting | [Integrated Module 06 README](./06.%20Observability%20and%20Troubleshooting/README.md) | Broken scenarios and corrected manifests, NFS StatefulSet, logging/probes/debug |
| 07 — Templating & Helm | [Integrated Module 07 README](./07.%20Templating%20Tools%20and%20Package%20Management/README.md) | sed, Kustomize overlays, Helm chart and ConfigMap HTML/SVG |
| 08 — Exam Preparation | [Integrated Module 08 README](./08.%20Exam%20Preparation/README.md) | Nine-task/36-point, three-namespace practice exam with setup and separate solutions |
| 09 — OpenShift | [OpenShift](./09.%20OpenShift/README.md) | Projects, Builds, Routes, security, storage and virtualization |
| 10 — Full-stack JavaScript on OpenShift | [URL Shortener](./10.%20Full-Stack%20JavaScript%20on%20OpenShift/README.md) | Node.js frontend/backend/redirector, PostgreSQL, Docker Compose, five labs |
| 11 — API-First Development & API Management | [API-First](./11.%20API-First%20Development%20and%20API%20Management/README.md) | OpenAPI contracts, registry, mocking, ASP.NET Core |
| 12 — API Versioning & Lifecycle Management | [API Versioning](./12.%20API%20Versioning%20and%20Lifecycle%20Management/README.md) | SemVer, compatibility, OrderPlacement v1/v2, sunset |
| 13 — API Management & Service Mesh | [Service Mesh](./13.%20API%20Management%20and%20Service%20Mesh/README.md) | Travelz, partner APIs, canary, Istio mTLS |
| 14 — Event-Driven Sentiment Analysis | [Event-driven analytics](./14.%20Event-Driven%20Sentiment%20Analysis/README.md) | Kafka, CloudEvents, Globex, PostgreSQL, InfluxDB/Grafana, Knative |
| 15 — CDC Legacy Modernization | [CDC modernization](./15.%20CDC%20Legacy%20Modernization/README.md) | PostgreSQL WAL, Debezium Kafka Connect, search and cashback projections |

**Chapter structure:** Open each module's **README**. For Modules 01–08, each chapter now follows the natural sequence **concept → current lab → validation**, instead of showing all labs before a separate old lecture. Concepts and illustrative examples from the original materials are retained, but obsolete duplicated execution instructions are not. The old `*-2026.md` URLs are compatibility pointers, not a second curriculum. For Modules 09–15, follow their README and linked labs.

## Lab setup and cross-module dependencies

| Dependency | What you must supply or verify |
|---|---|
| Virtual machines/host network | OS installation, unique hostnames, host IPs, hypervisor/VM capabilities and appropriate firewall |
| Workstation tools | `kubectl`, `helm`, `openssl`, `curl`, `sed`; optionally Minikube, kind, Vagrant, VirtualBox |
| Container registries & Helm charts | Working HTTPS/DNS and the upstream images referenced by the manifests; some historical third-party teaching images may cease to be published |
| NFS storage | A separate NFS server and exports for Modules 04/06; static NFS does **not** appear magically within a kubeadm cluster |
| Ingress | Matching F5 NGINX controller + IngressClass for its rewrite annotations; Traefik is an **alternative** only for the third-controller task |
| Kubernetes node credentials | Valid kubeconfig/current context, permissions to manage lab objects; only disposable labs sign client certificates with kubeadm's CA key |
| NodePorts | Reachable node IP and permitted TCP port, or an alternative local `kubectl port-forward` as documented |
| Quotas/metrics | Metrics Server before CPU HPA; adequate CPU/memory capacity for requested replicas |

These dependencies are **specified** in the relevant module guides. A fully self-contained written procedure does not mean a physical cluster can be conjured without hosts or that an upstream image is guaranteed to stay downloadable indefinitely.

**Resource collisions:** The labs often reuse namespace `homework` and NodePorts **30001, 31000, 32000, 32001 and 32002**. Clean up the previous lab before reserving them again. Use **fresh disposable clusters** for destructive etcd restore/upgrade work and optional alternate-CNI or Ingress configurations. Adapt node IPs and pod/service CIDRs when they overlap the real network.

## Safety and compatibility rules

- **Only one CNI per cluster.** Use Calico 3.33 for the main kubeadm learning track. Do **not** install historic Weave/Antrea/Flannel manifests on top of it. Optional Flannel uses a separate clean cluster.
- **Use supported Kubernetes APIs.** The old `PodSecurityPolicy`, `autoscaling/v2beta2` HPA and `gitRepo` volume driver no longer work on 1.37. Modern alternatives are identified in the relevant guides.
- **Distinguish ports.** NodePort on a Node, Service `port`, Service `targetPort` to a Pod and Ingress HTTPS listener 443 are different things.
- **Respect PV reclaim policy.** On static NFS, `Retain` preserves files when a PVC is deleted and requires manual reclamation of Released PVs. Do not wipe NFS directories while Pods still use them.
- **Keep lab clusters isolated.** The etcd restore and upgrade chapters use separate disposable clusters; a failed control plane is an intentional experiment, not a reason to damage a shared lab.
- **Do not execute raw 2021 author scripts.** Use the integrated 1.37 exercise sections in each module README. Preserve DOCX/ZIP/screenshots as historical examples, including the original multi-cluster exam; modern Exam 2026 uses three **logical namespaces** on one cluster instead.

## Standard lab verification

Before each module:

```bash
kubectl config current-context
kubectl version
kubectl get nodes -o wide
kubectl get pods -A
kubectl get tigerastatus
```

The **full acceptance** for each lab is inside that module's integrated README and covers:
1. **Preflight:** context, compatible versions, service/network/storage prerequisites and unused ports.
2. **Apply:** explicit paths to versioned, modern manifests or commands.
3. **Validate:** `kubectl get/describe`, rollout, status, endpoints, logs, HTTP tests and expected outputs.
4. **Troubleshoot:** distinguish image, CNI, permission, policy, storage and node connectivity faults.
5. **Cleanup:** reset the lab so a following task is not blocked by names, ports or released PVs.

A passing **static document audit** proves the instructions and source references are internally consistent to the extent checked. It does **not** claim a tested runtime success or permanently guarantee external resources.

## Historical exam vs modern simulation

Original `M8-Practice-Exam-Preparation-Simulation-Exam.docx` described three Debian 10 / Kubernetes 1.21.6 clusters; its attached ZIP has only part of the historic setup. The modern exam integrated into [Module 08 README](./08.%20Exam%20Preparation/README.md#kubernetes-137-integrated-labs) provides a current, reproducible **replacement simulation** covering the original skills, not a line-by-line migration or a literal three-cluster reproduction. Historical materials remain intact.

## Original learning material

The full original foundations lecture appears **below the course guide in this very README**. The original module theory and DOCX/PPTX/ZIP exercises also remain available for historical study. The historical 2021 three-cluster exam is **not** a drop-in Kubernetes 1.37 exercise; the modern Module 08 simulation deliberately uses three logical namespaces on one cluster.

## Source

Official [Kubernetes documentation](https://kubernetes.io/docs/home/), [Calico documentation](https://docs.tigera.io/calico/latest/), [Kustomize](https://kustomize.io/), [Helm](https://helm.sh/docs/) and [Traefik Helm chart](https://github.com/traefik/traefik-helm-chart).

---

## Original foundations lecture — historical reference

> **Original course content preserved without edits.** The following explanations of containerization, Docker, Kubernetes control-plane and worker components, `kubectl`, and resource types are retained from the original root README, including their diagrams and examples. **This is historical teaching material (2021)**, not the supported Kubernetes 1.37 executable setup. For running labs, use the integrated module READMEs linked above.

<!-- ORIGINAL_ROOT_README_PRESERVED_START -->
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

- **Container runtime** - CRI-compatible runtimes such as containerd or CRI-O; Docker Engine requires `cri-dockerd`
- **kubelet** - Communicates with the control plane
- **kube-proxy** - Network proxy

#### (Worker) Nodes: kubelet

- Main Kubernetes agent
- Registers node in the cluster
- Listens to the API Server
- Creates pods
- Reports back to the control plane
- Exposes the Kubelet HTTPS API on TCP `:10250` (with authentication/authorization)
- **NOTE (2026):** The historical unauthenticated read-only endpoint `:10255` (used for paths such as `/spec`, `/healthz`, `/pods`) is disabled by default in modern `KubeletConfiguration` (`readOnlyPort: 0`). Do not expose it in a current cluster.

#### (Worker) Nodes: Container Runtime

- Container management:
  - **Pulling** images
  - **Starting** and **stopping**
- It is **pluggable**
- **NOTE (2026):** Kubernetes has **no built-in default Docker runtime**. It uses the Container Runtime Interface (CRI); `kubeadm` detects an installed runtime or asks you to specify one. The built-in Docker integration (`dockershim`) was removed in Kubernetes **v1.24**. Use `containerd` (as in our [integrated 2026 setup lab](./02.%20Cluster%20Setup%20and%20Management/README.md#kubernetes-137-integrated-labs)), `CRI-O`, or Docker Engine with the separate `cri-dockerd` adapter.

#### (Worker) Nodes: kube-proxy

- Provides the **networking**
- Each pod has its **own address**
- All containers in a pod share the **same IP** address
- Offers **load balancing** across all pods in a **service**

### kubectl (kubernetes cli)

- Controls Kubernetes clusters
- Expects a file named **config** in the **$HOME/.kube** directory
- Other files can be specified by setting the **KUBECONFIG** environment variable or by setting the **--kubeconfig** flag

Its version should +/- 1 minor version compared to the cluster. For example, with kubectl version 1.22 we can work with clusters version 1.21, 1.22, and 1.23

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

> **NOTE (2026):** This resource table is a historical snapshot, not a current Kubernetes v1.37 API inventory. Run `kubectl api-resources` against your own cluster to see the resources it actually serves. In particular, the `PodSecurityPolicy` entry below was **removed in v1.25**.

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
| podsecuritypolicies             | psp        | policy                       | false      | PodSecurityPolicy (removed v1.25) |
| clusterrolebindings             |            | rbac.authorization.k8s.io    | false      | ClusterRoleBinding             |
| clusterroles                    |            | rbac.authorization.k8s.io    | false      | ClusterRole                    |
| rolebindings                    |            | rbac.authorization.k8s.io    | true       | RoleBinding                    |
| roles                           |            | rbac.authorization.k8s.io    | true       | Role                           |
| priorityclasses                 | pc         | scheduling.k8s.io            | false      | PriorityClass                  |
| csidrivers                      |            | storage.k8s.io               | false      | CSIDriver                      |
| csinodes                        |            | storage.k8s.io               | false      | CSINode                        |
| storageclasses                  | sc         | storage.k8s.io               | false      | StorageClass                   |
| volumeattachments               |            | storage.k8s.io               | false      | VolumeAttachment               |

**NOTE (2026) — PodSecurityPolicy → Pod Security Admission:** `PodSecurityPolicy` (PSP) was deprecated in Kubernetes v1.21 and removed in v1.25. The built-in **Pod Security Admission** controller enforces Pod Security Standards through **Namespace labels** (`privileged`, `baseline`, `restricted`) in `enforce`, `warn`, or `audit` modes. It is an admission controller, **not** a replacement resource type in the table above. PSP rules are not guaranteed to map one-to-one to these predefined standards.

Example for **a new disposable lab namespace** (Kubernetes v1.25+):

```bash
kubectl create namespace security-lab
kubectl label namespace security-lab \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/audit=restricted
kubectl get namespace security-lab --show-labels
# Clean up when finished:
kubectl delete namespace security-lab
```

With this example, Pods that violate the **baseline** standard are rejected; violations of **restricted** trigger warnings and audit annotations. Use the [official Pod Security Admission documentation](https://kubernetes.io/docs/concepts/security/pod-security-admission/) and [PodSecurityPolicy removal guide](https://kubernetes.io/docs/concepts/security/pod-security-policy/) for details.

#### Output options
  
| Output format                             | Description                                                                                           |
|-------------------------------------------|-------------------------------------------------------------------------------------------------------|
| ```-o custom-columns=<spec>```            | Print a table using a comma separated list of custom columns.                                         |
| ```-o custom-columns-file=<filename>```   | Print a table using the custom columns template in the <filename> file.                               |
| ```-o json```                             | Output a JSON formatted API object.                                                                   |
| ```-o jsonpath=<template>```              | Print the fields defined in a jsonpath expression.                                                    |
| ```-o jsonpath-file=<filename>```         | Print the fields defined by the jsonpath expression in the <filename> file.                           |
| ```-o name```                             | Print only the resource name and nothing else.                                                        |
| ```-o wide```                             | Output in the plain-text format with any additional information. For pods, the node name is included. |
| ```-o yaml```                             | Output a YAML formatted API object.                                                                   |
