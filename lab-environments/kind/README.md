# Disposable Kubernetes 1.37 lab on Ubuntu (kind + Calico)

**Goal:** an actual Kubernetes API, control plane, containerd, kubelet and **three Kubernetes Node objects** running as Docker containers, built and destroyed from code. This is the **fast application-lab profile** of the [Kubernetes/OpenShift course](../../README.md), not a replacement for the Module 02 VM/kubeadm operating-system labs. No production HA or physical fault isolation is claimed.

| Pinned component | Version/configuration |
|---|---|
| [kind](https://kind.sigs.k8s.io/) | **v0.33.0** |
| Kubernetes node image | **v1.37.0**, exact SHA-256 digest in `kind-config.yaml` |
| Topology | **1 Control Plane + 2 Workers** |
| Runtime inside nodes | containerd, managed by kind/kubeadm |
| CNI | [Calico OSS](https://docs.tigera.io/calico/latest/getting-started/kubernetes/kind) **3.33.0**, VXLAN, BGP disabled |
| Pod CIDR / Service CIDR | `10.244.0.0/16` / `10.96.0.0/12` |
| Cluster name / kubectl context | `course-lab` / `kind-course-lab` |
| Host access | Published NodePorts on **Ubuntu 127.0.0.1 only** |

The **only** permanent parts are this versioned configuration, scripts, optional Docker image cache, and your checked-in source/manifests. **Kubernetes workload state, etcd state, local PVC data and any uncommitted in-cluster work are deliberately destroyed by `make down`.** Do not use this lab for data you cannot lose.

## 1. Ubuntu host: one-time prerequisites

Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) from official instructions (not snap Docker), [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/) and **kind v0.33.0**. Examples for Ubuntu x86-64 (for ARM64 use the matching ARM64 binary):

```bash
# Install Docker Engine by its official Ubuntu procedure first.
docker version
docker info

# kind: deliberately pinned CLI, aligned with its official Kubernetes 1.37.0 node image.
curl -fsSLo /tmp/kind https://kind.sigs.k8s.io/dl/v0.33.0/kind-linux-amd64
chmod +x /tmp/kind
sudo install -m 0755 /tmp/kind /usr/local/bin/kind
kind version

# kubectl (use the same minor as Kubernetes; see official docs for verified signatures):
curl -fsSLo /tmp/kubectl https://dl.k8s.io/release/v1.37.0/bin/linux/amd64/kubectl
chmod +x /tmp/kubectl
sudo install -m 0755 /tmp/kubectl /usr/local/bin/kubectl
kubectl version --client

sudo apt-get update && sudo apt-get install -y make curl
```

**Security:** Docker daemon access is root-equivalent; prefer a dedicated Ubuntu lab machine or account. The lab scripts **never** use `sudo` to provision workloads, never modify your host network/firewall, and never invoke `kubectl` without explicit `--context kind-course-lab`. Access to Docker, registry.k8s.io, quay.io and upstream Calico manifest URLs is required. If you are running Ubuntu behind a VPN, verify there is **no subnet overlap** with the cluster Pod/Service CIDRs or Docker's bridge; if you change the Pod CIDR, update **both** YAML files.

**Host capacity planning (guidance, not an enforced requirement):** reserve roughly **8–12 GiB free RAM**, several CPUs and 15–25 GB free disk for a three-node lab plus image cache; actual needs vary by workloads. Heavy Kafka/DB exercises require more. kind does not add capacity — all nodes share your Ubuntu host's kernel.

## 2. Everything else is infrastructure as code

From the repository root:

```bash
cd lab-environments/kind

make tools       # Verify host prerequisites; no changes
make up          # Create/reuse 3 Docker node containers; bootstrap Calico
make verify      # Confirm 3 Ready nodes, Kubernetes 1.37, Calico VXLAN, CoreDNS
make status      # List cluster nodes and running Pods

# Now perform course exercises in the same kind-course-lab context:
kubectl --context kind-course-lab get pods -A

make down        # Delete ONLY course-lab: workloads/etcd/volumes are disposable
make up          # Rebuild from the SAME files, on the same pinned versions
```

`make up` is idempotent for an **existing healthy** cluster. It does not overwrite your work or silently update its node image/config. After changing `kind-config.yaml`, use **`make reset`**, which is equivalent to deleting and recreating the whole lab and **loses all in-cluster state**.

- [`kind-config.yaml`](./kind-config.yaml) is the node topology, pinning, Docker networking and localhost port-forward mappings.
- [`calico-installation.yaml`](./calico-installation.yaml) is the exact desired Calico VXLAN/BGP/CIDR configuration.
- [`scripts/lab.sh`](./scripts/lab.sh) manages creation, Calico/operator provisioning, safe validation and deletion.
- [`Makefile`](./Makefile) exposes the short `make up`/`make down` developer workflow.

To load **your own** .NET application image into all Kubernetes nodes without a registry push:

```bash
docker build -t myapi:dev ./path/to/api
make load IMAGE=myapi:dev
# In your Pod/Deployment use image: myapi:dev; imagePullPolicy: IfNotPresent
```

Each recreated cluster starts clean. Docker's host image cache remains available; internal images/workloads must be reloaded/redeployed.

## 3. Networking and accessing applications from Ubuntu

NodePort examples in the original modules use ports **30001, 31000, 32000, 32001, 32002**. These are mapped 1:1 from the kind control-plane node container to the **Ubuntu loopback**. The Service must actually declare that `nodePort`. Do not confuse the Service's `port` with `nodePort`. Multiple exercises may reuse a fixed NodePort; clean up the previous lab first.

```bash
kubectl --context kind-course-lab get svc -A
curl http://127.0.0.1:30001/   # only after creating a Service with nodePort: 30001
```

For **Module 05 F5 NGINX Ingress**, install with the same chart used in that module, but explicitly set its NodePorts and `externalTrafficPolicy=Cluster`; otherwise NodePort traffic forwarded to the control-plane container may not reach an Ingress controller Pod running on a worker:

```bash
helm upgrade --install nginx-ingress oci://ghcr.io/nginx/charts/nginx-ingress \
  --version 2.8.1 \
  --namespace nginx-ingress --create-namespace \
  --set controller.service.type=NodePort \
  --set controller.service.externalTrafficPolicy=Cluster \
  --set controller.ingressClass.name=nginx \
  --set controller.service.httpPort.nodePort=30080 \
  --set controller.service.httpsPort.nodePort=30443

kubectl --context kind-course-lab get svc -n nginx-ingress
# After completing the Module 05 TLS Secret and Ingress setup:
curl -k --resolve 'demo.lab:18443:127.0.0.1' https://demo.lab:18443/service1
```

**Host mapping:** Ubuntu `localhost:18080` → NodePort 30080 (HTTP), `localhost:18443` → NodePort 30443 (HTTPS). **Helm uses the current kubeconfig context**: run `kubectl config current-context` and confirm it is `kind-course-lab` first; or pass `--kube-context kind-course-lab` to the Helm command (recommended). The example above uses the latter only if you add that flag yourself. **Do not use this installation command before the original Module 05 exercise**: the profile supplies ports, not the application workload or TLS Secret.

If Ubuntu is remote and you work from Windows/another machine, use **SSH forwarding**, not a public listen address, e.g. `ssh -L 18443:127.0.0.1:18443 ubuntu-host` for HTTPS. For remote `kubectl` access, use a properly configured SSH API-server tunnel or run the CLI on Ubuntu; the created API endpoint is intentionally bound to localhost.

## 4. Course coverage and realism

| Module | Real Kubernetes in kind? | Limitation or addition |
|---|---|---|
| **01 Core Concepts** | **Yes** | Same Pod/Namespace/Service/NodePort APIs; optional image pulls remain external |
| **02 Cluster Setup** | **Partly** | kind calls kubeadm internally, but **does not teach Ubuntu OS preparation, manual kubeadm init/join, real node upgrade or disaster recovery**; use the [VM track](../../02.%20Cluster%20Setup%20and%20Management/README.md) |
| **03 Security / NetworkPolicy** | **Yes** | Real X.509/RBAC/ResourceQuota/Calico policies; Docker host remains shared |
| **04 Storage** | **Partly** | ConfigMaps, Secrets, PVCs work; **NFS lessons require an NFS server reachable by the kind containers**, and PV behavior depends on provisioner |
| **05 Advanced / Ingress / HPA** | **Yes, after add-ons** | Module 05 installs pinned F5 NGINX and Metrics Server; host ingress needs above pinned NodePorts |
| **06 Observability** | **Mostly** | Probes, logs and application failures are real; NFS exercise needs the external NFS service |
| **07 Helm/Kustomize** | **Yes** | Standard Kubernetes/Helm behavior |
| **08 Exam simulation** | **Yes** | Namespace-based practice exam; excludes actual multiple physical cluster infrastructure |
| **09–15 OpenShift** | **No — not OpenShift** | A kind cluster has Kubernetes, **not OpenShift Routes, BuildConfigs, Operators or SCC**; use the [OpenShift environment profiles](../../docs/OPENSHIFT-LAB-PROFILES.md) |

**Kubernetes API fidelity:** Pods, Deployments, Services, CNI and NetworkPolicy are real — not mocked. **Node/OS fidelity:** Docker node images run their own containerized init and kubelet atop the Ubuntu host kernel, so OS-level services and failure isolation differ. Not all kernel, hardware and cloud/load-balancer behaviors are equivalent. [kind explicitly treats node image internals as implementation details](https://kind.sigs.k8s.io/docs/design/node-image/).

For a future **real OpenShift** lab on the same Ubuntu host, use a **separate provider**, e.g. [CRC / OpenShift Local](https://crc.dev/docs/using/) or a dedicated OKD/OpenShift installation. CRC starts an OpenShift-compatible VM, **not OpenShift components inside these kind Docker nodes**. It requires hardware virtualization and significantly more resources; do not claim the kind cluster becomes OpenShift by swapping container images. A future `lab-environments/openshift-local/` profile can expose a similar `up / verify / down` interface.

## 5. Troubleshooting

| Symptom | Diagnose | Response |
|---|---|---|
| Docker denied | `docker info` | Configure Docker Engine/user permissions once; Docker group is root-equivalent |
| Cannot bind port | `docker ps`, `ss -ltn` | Stop unrelated listener or change the hostPort mapping and `make reset` |
| Nodes NotReady initially | `kubectl --context kind-course-lab get nodes` | This is **expected before Calico**; `make up` must install Calico |
| Calico operator / CNI stuck | `kubectl --context kind-course-lab -n tigera-operator logs deployment/tigera-operator`; `kubectl --context kind-course-lab -n calico-system get pods` | Check manifest/registry reachability; diagnose then use `make reset` for a disposable clean environment |
| NetworkPolicy has no effect | `kubectl --context kind-course-lab get installation default -o yaml` | Verify Calico Installed, BGP Disabled/VXLAN and selectors; do not install a second CNI |
| API/Service unreachable remotely | `kubectl --context kind-course-lab get svc -A` | Use Ubuntu localhost or SSH tunnel; NodePort mapping must match actual Service.nodePort |
| Pods Pending due to storage | `kubectl --context kind-course-lab get pvc,sc` | Inspect StorageClass/claim binding; NFS lab still needs reachable NFS |
| Host system issues | `kind export logs --name course-lab` | Review kubelet/docker logs; try fresh `make reset` after fixing host prerequisites |

**Scope and verification:** The YAML/scripts are statically checked in GitHub Actions; the optional live CI workflow attempts to boot and destroy a real three-node kind cluster. That is independent of the VM/kubeadm and OpenShift platform labs. Never describe an unexecuted exercise as passed.
