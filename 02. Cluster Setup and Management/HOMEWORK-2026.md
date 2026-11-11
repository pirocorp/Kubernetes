# Module 02 homework — Kubernetes 1.37 (Minikube, kind, Vagrant/vanilla)

> **NOTE (2026):** The original `M2-Practice` DOCX and author Vagrant scripts are **Kubernetes 1.21–1.22 / Debian 10** historical artifacts. Do **not** execute them on a fresh 1.37 lab. This guide completes all three optional homework tasks on 1.37 using actual, versioned images/tools, with validation and cleanup. The full vanilla cluster procedure is [SETUP-2026.md](./SETUP-2026.md).

## Before starting

1. Install `kubectl` and verify its 1.36–1.38 compatible client version; have Docker Engine available for the first two tasks, with enough CPU/RAM (at least 8 GiB free memory for the multi-node local clusters). Follow the official [minikube installation](https://minikube.sigs.k8s.io/docs/start/) and [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/) for your host OS.
2. Use an isolated cluster for **each** task. The homework image `shekeriev/k8s-oracle` is third-party; the sample app requires image pull availability. Both examples reuse the multi-document [Module 01 Task 3A.yaml](../01.%20Core%20Concepts/Homework/Task%203/Task%203A.yaml) with Namespace, Pods and Service.
3. The application uses **NodePort 32000**, Service/Pod port **5000**, selector `app=hw`. Clear any pre-existing workload using that NodePort on the chosen cluster.
4. Always run `kubectl config current-context` before applying resources so you do not modify the wrong cluster. NodePort exposure differs by driver; follow the methods below.

From repository root:

```bash
kubectl version --client
docker version
```

## Task 1 — 2-node Minikube cluster

Requires Minikube **1.39.0+** (supports Kubernetes 1.37), Docker driver, access to node-image registries.

```bash
minikube start -p m02 --driver=docker --nodes=2 --kubernetes-version=v1.37.0 --container-runtime=containerd
minikube -p m02 status
kubectl config use-context m02
kubectl get nodes -o wide
kubectl version
kubectl apply -f "01. Core Concepts/Homework/Task 3/Task 3A.yaml"
kubectl wait -n homework --for=condition=Ready pod/homework-1 pod/homework-2 --timeout=180s
kubectl get pods,svc -n homework -o wide
minikube service homework-svc -n homework -p m02 --url
```

**Expected:** 2 Ready nodes, two Ready app Pods, a NodePort Service **32000**. Open the **actual URL printed by `minikube service --url`** (it may use a tunnel, particularly with the Docker driver on macOS/Windows; keep that command running while testing). Check HTTP response from the app.

```bash
kubectl delete namespace homework
minikube delete -p m02
```

## Task 2 — 3-node kind cluster

Requires `kind` version **0.33.0+**, and Docker Engine. Official kind v0.33.0 node image is pinned to Kubernetes 1.37.0.

Create `kind-m02.yaml` from the repository root:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 32000
    hostPort: 8080
    listenAddress: "127.0.0.1"
    protocol: TCP
- role: worker
- role: worker
```

```bash
kind create cluster --name m02 --config kind-m02.yaml \
  --image kindest/node:v1.37.0@sha256:a1ed56cfb0e7b93589bdf97c8cd566405a265939e3620fc4f5de89adff580ae5
kubectl config use-context kind-m02
kubectl get nodes -o wide
kubectl version
kubectl apply -f "01. Core Concepts/Homework/Task 3/Task 3A.yaml"
kubectl wait -n homework --for=condition=Ready pod/homework-1 pod/homework-2 --timeout=180s
kubectl get pods,svc -n homework -o wide
curl -fsS http://localhost:8080/
```

**Expected:** 3 Ready nodes, Service `homework-svc` NodePort **32000** forwarded to localhost **8080**, and an HTTP reply. The `kind` NodePort mapping is valid only if `containerPort` equals the Service's `nodePort`. Ensure host TCP **8080** is free. If the image cannot be pulled, inspect `kubectl describe pod -n homework`.

```bash
kubectl delete namespace homework
kind delete cluster --name m02
rm -f kind-m02.yaml
```

## Task 3 — three-node vanilla cluster with Vagrant-managed VMs

Unlike the **historical Vagrantfile** embedded in `Exercise/Author Solution/README.md`, the new [Vagrant-2026/Vagrantfile](./Exercise/Vagrant-2026/Vagrantfile) uses **Ubuntu 24.04** (Bento box, pinned version) and prepares three machines' hostnames, host-only IPs, swap and kernel networking settings.

Prerequisites: current Vagrant, VirtualBox, hardware virtualization, at least **9 GiB RAM + headroom**, enough disk, and internet for box + Kubernetes packages/images. **Replace** the sample private IPs in the Vagrantfile if your host-only network differs. The example IPs correspond to the **standard Lab A topology** of SETUP-2026.md.

```bash
cd "02. Cluster Setup and Management/Exercise/Vagrant-2026"
vagrant up --provider=virtualbox
vagrant status
vagrant ssh cp1
# Inside cp1: hostname; ip -brief addr; getent hosts wk1.k8s.lab
# exit to host; repeat e.g. vagrant ssh wk1 / wk2
```

Next, follow the **executable** [SETUP-2026.md](./SETUP-2026.md) **in order** (not the old Debian 10 README): common OS / containerd / Kubernetes package preparation **sections 0–3** on cp1, wk1, wk2; `kubeadm init` **section 4** on cp1; Calico Operator **section 5** once on cp1, with **VXLAN** and **BGP disabled**, Pod CIDR `10.244.0.0/16`; join workers **section 6**; verify **section 7**; workstation kubectl access **section 8**. Vagrant performs **VM provisioning**, while the documented `kubeadm` steps complete Kubernetes provisioning. Do not install Flannel on top of Calico.

**Expected:** one Ready control-plane and two Ready workers; containerd active; Calico status healthy; CoreDNS Ready.

On your kubectl-equipped workstation, now from the **repository root**:

```bash
kubectl config current-context
kubectl get nodes -o wide
kubectl get tigerastatus
kubectl apply -f "01. Core Concepts/Homework/Task 3/Task 3A.yaml"
kubectl wait -n homework --for=condition=Ready pod/homework-1 pod/homework-2 --timeout=180s
kubectl get pods,svc -n homework
# Replace <reachable-node-ip> with a real worker/control-plane node address.
curl http://<reachable-node-ip>:32000/
kubectl delete namespace homework
```

Make sure firewall permits **NodePort 32000/TCP** from the workstation. If it does not, validate with `kubectl port-forward -n homework svc/homework-svc 8080:5000` and curl localhost:8080 from another terminal.

**Cleanup** (irreversibly deletes the three disposable VMs):

```bash
cd "02. Cluster Setup and Management/Exercise/Vagrant-2026"
vagrant destroy -f
```

## Troubleshooting and scope

| Symptom | Static checks / next action |
|---|---|
| Wrong cluster/context | `kubectl config current-context`; switch to `m02` or `kind-m02` as needed |
| Nodes not Ready | `kubectl describe node`; inspect `kube-system`, CNI and containerd |
| Pods not Ready | `kubectl describe pod -n homework`; investigate third-party image pull and node resources |
| NodePort not reachable | `kubectl get svc -n homework`, endpoints, host port mapping/firewall; Minikube `service --url`; try port-forward |
| Vagrant box unavailable | Confirm VirtualBox version and pinned `bento/ubuntu-24.04` box availability/provider/CPU architecture; choose an equivalent Ubuntu 24.04 box if required |
| kubeadm packages unavailable | Use the `pkgs.k8s.io` versioned sources in `SETUP-2026.md`; **never** the old `apt.kubernetes.io` repo |

Historical M2 DOCX/ZIP/author scripts remain available **for comparison**, but following this guide plus the linked SETUP-2026.md is the supported 1.37 path. The two Helm/CNI stacks (kind/minikube vs kubeadm/Calico) are different environments and should not be mixed.
