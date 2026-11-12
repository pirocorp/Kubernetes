# Module 02 — Cluster Setup and Management

> **Learning edition (Kubernetes 1.37).** A cluster is built, operated and recovered as a single progressive lesson. The 2021 Debian 10 / Kubernetes 1.21 installation and upgrade *commands* have been replaced by the fully documented Kubernetes 1.37 procedures. Core original explanations are retained at their relevant topics, while the original DOCX/ZIP remain available as historical artifacts (not executable setup instructions).

## Learning path and objectives

Build a working 1-control-plane / 2-worker Ubuntu 24.04 cluster with **containerd 2.x and Calico 3.33**, explore alternative learning environments, then learn maintenance, etcd backup/restore, upgrades and highly available architecture. Destructive labs require fresh disposable VMs. See the [course README](../README.md) for shared safety rules.

## Kubernetes 1.37 integrated labs

> Follow this chapter in order. Tasks are grouped with their concepts; legacy installation procedures are not duplicated later in the chapter.


<!-- PRESERVED_THEORY_BEGIN -->
## Cluster creation

Creation of simple yet working Kubernetes cluster. Small cluster with three nodes. One will be part of the control plane and the rest will handle any work.
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 0 -->
## Kubernetes 1.37 — modern kubeadm cluster setup (2026)

> **Scope:** New Linux lab clusters only. This **README is the complete supported lab**; historical Debian 10 / Kubernetes 1.21–1.22 procedures are no longer the execution path. Do **not** use historical commands to install a new cluster.
>
> **Reference date:** 11 November 2026. **Status:** Documentation reviewed against upstream installation references; not executed against a live cluster.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 1 -->
### Target architecture

This guide modernizes the historical course with **Kubernetes 1.37**, **containerd 2.x**, **Calico 3.33**, VXLAN encapsulation, BGP disabled and NetworkPolicy support. Flannel is a **separate fresh-lab alternative**, never installed on the Calico cluster.

#### Lab topology and choices

| Lab | Machines | Example hostnames / private IP addresses |
| --- | --- | --- |
| A — standard | 1 control plane + 2 workers | cp1: 192.168.56.11, wk1: .21, wk2: .22 |
| B — HA | 3 control planes + 3 workers + HAProxy | cp1: .11, cp2: .12, cp3: .13, wk1: .21, wk2: .22, wk3: .23, lb: .10 |

All addresses expand **192.168.56.**. Substitute the real IP addresses on your VM network. Lab B uses the DNS name **lb.k8s.lab** to point to HAProxy. **One HAProxy VM is a single point of failure**, even though etcd/control plane run in HA.

**Executable OS example:** Ubuntu Server **24.04 LTS**, on separate VMs or hosts with systemd and apt. Debian 12/13 are possible but require verifying distribution-specific package sources. The guide does not assume a particular hypervisor or physical subnet.

**Subnet choices:** Pod CIDR **10.244.0.0/16**, Service CIDR **10.96.0.0/12**; both must be distinct from physical/VPN networks. VXLAN between nodes requires **UDP 4789**; BGP is disabled.

#### Provisioning the VMs

Create the required VMs with your chosen hypervisor (e.g. bridged/routed virtual NICs), install Ubuntu Server 24.04, enable OpenSSH, give each a unique hostname, sudo-enabled admin account and IP reachable from the other nodes. For this lab, allocate at least **2 vCPU, 2 GiB RAM** plus adequate disk per Kubernetes node; more resources may be needed for workloads. Use a smaller separate VM for the HAProxy lab. IP configuration depends on your actual hypervisor, DHCP, gateway and NIC; configure static addressing or DHCP reservations *during provisioning*. Do not run example addresses on an unrelated real network.

On **each** node set its unique hostname; here is the cp1 example:

~~~bash
sudo hostnamectl set-hostname cp1.k8s.lab
hostnamectl
ip -brief addr
ip route
timedatectl
~~~

Use functioning DNS or put consistent mappings into **/etc/hosts on every node and your workstation**. Replace example addresses where necessary:

~~~text
192.168.56.10 lb.k8s.lab lb
192.168.56.11 cp1.k8s.lab cp1
192.168.56.12 cp2.k8s.lab cp2
192.168.56.13 cp3.k8s.lab cp3
192.168.56.21 wk1.k8s.lab wk1
192.168.56.22 wk2.k8s.lab wk2
192.168.56.23 wk3.k8s.lab wk3
~~~

Confirm on every relevant node:

~~~bash
getent hosts cp1.k8s.lab
ping -c 2 cp1.k8s.lab
# From your workstation, replacing user with your SSH account:
ssh user@cp1.k8s.lab
~~~

A node's actual kubelet name can differ from the short/FQDN form above; always get authoritative node names from **kubectl get nodes** and substitute them in the maintenance exercises.

#### Network access matrix

| Direction | Protocol/port | Purpose |
| --- | --- | --- |
| workstation/nodes → API endpoint | TCP 6443 | Kubernetes API |
| control-plane ↔ control-plane (Lab B) | TCP 2379–2380 | stacked etcd |
| control plane → nodes | TCP 10250 | kubelet |
| nodes ↔ nodes | UDP 4789 | Calico VXLAN |

Allow DNS, NTP, HTTPS image pulls and exercise-specific NodePorts as applicable. Use tight firewall rules rather than indiscriminately disabling host security. See the [Kubernetes port reference](https://kubernetes.io/docs/reference/networking/ports-and-protocols/).

#### Lab execution order

1. **Lab A:** on cp1, wk1 and wk2, perform **sections 0–3**.
2. On cp1 initialize Kubernetes (**section 4**) and install Calico (**section 5**); then join workers (**section 6**) and verify (**section 7**).
3. Try workstation access, Headlamp, node maintenance, etcd backup and policy exercises (**sections 8–11 and 15–16**).
4. **etcd restore (section 12)** is destructive; use a disposable copy of Lab A, **not** the HA lab.
5. **Upgrade (section 13)** starts from an independent **1.36.x** cluster, not from an already installed 1.37 cluster.
6. **Lab B:** use freshly prepared VMs for 3 control planes + 3 workers + HAProxy, applying common sections 0–3 and then section 14.
7. **Flannel (section 17):** use a different fresh cluster. Never install it on top of Calico.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 2 -->
### 0. Preflight (all Kubernetes nodes)

Check that the OS, subnet, routing, DNS, NTP, SSH, disk and RAM are ready, and that all nodes have unique names, VM IPs and machine IDs.

Kubernetes 1.37 expects modern cgroup behavior. **cgroup2fs** is the expected result for the cgroup version command below. The kubelet normally refuses to start on cgroup v1 with the current defaults.

~~~bash
uname -r
stat -fc %T /sys/fs/cgroup/
hostname -f
ip route
getent hosts cp1.k8s.lab
timedatectl status
free -h
df -h /
~~~

Disable swap on **each Kubernetes VM/node** (not on an unrelated Ubuntu homelab host):

~~~bash
sudo swapoff -a
swapon --show  # Expected: no output
~~~

Persist the change on these disposable VMs. Back up fstab and comment swap mounts (adjust other swap/zram managers separately if installed):

~~~bash
sudo cp -a /etc/fstab /etc/fstab.before-k8s-lab
sudo sed -i -E '/^[[:space:]]*[^#][^[:space:]]+[[:space:]]+[^[:space:]]+[[:space:]]+swap[[:space:]]/s/^/# disabled for kubeadm lab: /' /etc/fstab
grep -v '^#' /etc/fstab
~~~

After any reboot check **swapon --show** again. Do not apply these swap changes to a shared production host.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 3 -->
### 1. Configure kernel networking (all nodes)

~~~bash
sudo tee /etc/modules-load.d/k8s.conf >/dev/null <<'EOF'
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

sudo tee /etc/sysctl.d/99-kubernetes-cri.conf >/dev/null <<'EOF'
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system
sysctl net.ipv4.ip_forward
~~~

These are conventional bridge-networking settings for a lab; your CNI and host network setup may have additional requirements.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 4 -->
### 2. Install and configure containerd 2.x (all Kubernetes nodes)

The historical course used Docker Engine and its former built-in runtime integration. Kubernetes now uses **CRI-compatible runtimes**; install **containerd 2.x**, *not* Docker Engine. This procedure is for **fresh Ubuntu Server 24.04 LTS VMs** and adds Docker's **signed APT repository solely to install containerd.io** (without Docker Engine). For Debian, replace the repository with Docker's Debian repository after verifying distribution support.

~~~bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gpg
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<'EOF'
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: amd64 arm64
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
sudo apt-get install -y containerd.io
containerd --version
~~~

**Expected:** containerd 2.x is installed. If you have a different Ubuntu architecture, replace the Architectures line with the correct supported architecture before running apt update. If containerd is not 2.x, **stop and resolve the runtime installation** rather than guessing the matching TOML settings.

Generate a configuration for the **actually installed** containerd version. Enable systemd cgroups for runc (correct for a modern cgroup v2 + systemd host):

~~~bash
sudo install -m 0755 -d /etc/containerd
sudo containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
sudo sed -i -E 's/^([[:space:]]*SystemdCgroup[[:space:]]*=[[:space:]]*)false/\1true/' /etc/containerd/config.toml

grep -n 'SystemdCgroup = true' /etc/containerd/config.toml
grep -n 'disabled_plugins' /etc/containerd/config.toml
~~~

The matching containerd **2.x** table is [plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runc.options]. Confirm **SystemdCgroup = true**, and that the CRI plugins are not disabled. If the generated config is different, inspect the correct table instead of mixing 1.x and 2.x configuration fragments.

~~~bash
sudo systemctl enable --now containerd
sudo systemctl restart containerd
sudo systemctl is-active containerd
sudo ctr plugins ls | grep -i cri
~~~

**Expected:** service status is **active**, with no CRI plugin errors. Kubernetes uses the socket **unix:///run/containerd/containerd.sock**. A separate **cri-dockerd** adapter would be needed if choosing Docker Engine instead; we do not use it.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 5 -->
### 3. Install kubeadm, kubelet and kubectl (all nodes)

Kubernetes has a **different APT repository for each minor release**. The legacy apt.kubernetes.io repository is frozen and must not be used for v1.37.

~~~bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gpg apt-transport-https
sudo mkdir -p -m 755 /etc/apt/keyrings

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.37/deb/Release.key |
  sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.37/deb/ /' |
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
apt-cache madison kubeadm
K8S_PKG_VERSION="$(apt-cache madison kubeadm | awk '$3 ~ /^1[.]37[.]/ {print $3; exit}')"
test -n "$K8S_PKG_VERSION" || { echo "ERROR: no Kubernetes 1.37 package available"; return 1 2>/dev/null || exit 1; }
printf 'Chosen package: %s\n' "$K8S_PKG_VERSION"
sudo apt-get install -y "kubelet=$K8S_PKG_VERSION" "kubeadm=$K8S_PKG_VERSION" "kubectl=$K8S_PKG_VERSION"
sudo apt-mark hold kubelet kubeadm kubectl

kubeadm version
kubectl version --client
~~~

The APT commands above are for **new** nodes. When upgrading an existing cluster, follow the version-by-version [kubeadm upgrade procedure](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/) rather than jumping directly from an older release.


**Expected:** kubeadm and kubectl identify as v1.37.x. At the reference date, the upstream patch release is **1.37.1**; use the package that your verified repository offers and record the full version string (including the package suffix) for installing that *same version* on other nodes. Refresh it deliberately when upgrading — never allow unplanned version drift.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 6 -->
### 4. Initialize the control plane (control-plane node only)

This example uses **192.168.56.11** (Lab A's cp1). Replace it with your actual control-plane IP if different.

~~~bash
sudo kubeadm init \
  --apiserver-advertise-address=192.168.56.11 \
  --pod-network-cidr=10.244.0.0/16 \
  --cri-socket=unix:///run/containerd/containerd.sock
~~~

If you plan to expand this installation to a highly available control plane, plan a stable load-balancer endpoint and use **--control-plane-endpoint** from the beginning. Do not assume a single control-plane node is highly available.

Configure kubectl for your admin account on the control-plane node:

~~~bash
mkdir -p "$HOME/.kube"
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
chmod 600 "$HOME/.kube/config"

kubectl get nodes -o wide
~~~

At this stage, a **NotReady** node can be expected until a CNI plugin is installed. **Do not commit admin.conf, kubeconfig private keys, or bootstrap tokens to Git.**
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 7 -->
### 5. Install Calico v3.33.0 — VXLAN / BGP disabled (control-plane node only)

Our standard and HA labs both use **Calico Open Source v3.33.0 with VXLAN encapsulation**, with **BGP explicitly disabled**. Calico provides CNI connectivity and enforcement of standard Kubernetes NetworkPolicy, which is required by module 03 of the original course.

**Requirement:** nodes communicate bidirectionally over UDP 4789 (VXLAN). The CNI IP pool **10.244.0.0/16** matches --pod-network-cidr in kubeadm init and does not overlap with the Service subnet **10.96.0.0/12**. Allow Calico to manage its cali* and vxlan.calico interfaces (especially when NetworkManager is enabled).

The Tigera Operator is recommended because it manages the Calico lifecycle. As of Kubernetes 1.36+, Calico's native v3 API CRDs use the GA MutatingAdmissionPolicy API. These are the official pinned manifests from the 3.33.0 release:

~~~bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/v3_projectcalico_org.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/tigera-operator.yaml

kubectl get deployments -n tigera-operator
~~~

Rather than telling the reader to manually alter unknown fields in a downloaded sample, **create a complete Installation resource** with our agreed settings. On cp1, where kubectl has admin access:

~~~bash
cat > "$HOME/calico-installation.yaml" <<'EOF'
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    bgp: Disabled
    ipPools:
      - blockSize: 26
        cidr: 10.244.0.0/16
        encapsulation: VXLAN
        natOutgoing: Enabled
        nodeSelector: all()
EOF

kubectl apply -f "$HOME/calico-installation.yaml"
~~~

No BGP mesh is deployed. The operator sets up Calico networking and its related resources; it may take some time for images and Pods to start. **Do not install Flannel in the same cluster**.

~~~bash
kubectl get installation.operator.tigera.io default -o yaml
kubectl get tigerastatus
kubectl get pods -n tigera-operator
kubectl get pods -n calico-system -o wide
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
kubectl get nodes -o wide
~~~

**Expected:**
- Installation spec shows **bgp: Disabled**, **encapsulation: VXLAN**, Pod CIDR **10.244.0.0/16**.
- Operator/Tigera statuses show Available/healthy; Calico Pods reach Running/Ready.
- CoreDNS becomes Running/Ready, and cp1 becomes Ready.

If troubleshooting:

~~~bash
kubectl describe installation.operator.tigera.io default
kubectl get events -A --sort-by=.lastTimestamp
kubectl describe nodes
kubectl get pods -A -o wide
~~~

If the selected VM subnet overlaps 10.244.0.0/16, choose another non-overlapping Pod CIDR and update **both** kubeadm and the Installation resource *before creating the cluster*.

**Why changed from Flannel?** The original module 02 used Flannel as a simpler overlay. Calico's built-in NetworkPolicy support lets the same cluster complete module 03 without replacing the CNI. The optional Flannel-only install is in section 17.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 8 -->
### 6. Join worker nodes

On the control-plane node, generate a fresh join command:

~~~bash
sudo kubeadm token create --print-join-command
~~~

Run the generated **kubeadm join** command on each prepared worker node with sudo. If multiple runtimes are installed, supply the appropriate **--cri-socket**.

Treat the bootstrap join token as a short-lived credential. Do not paste a real join command into this repository.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 9 -->
### 7. Verification

~~~bash
kubectl get nodes -o wide
kubectl get pods --all-namespaces
kubectl get tigerastatus
kubectl cluster-info
~~~

Check:
1. All required nodes have **Ready** status.
2. **CoreDNS** is running and Pod networking works between nodes.
3. Calico reports **Available=True** for its installed components.
4. The Kubernetes version and installed runtime match the intended configuration.
5. Cluster-admin access is limited to trusted administrators.

For further cluster administration (etcd snapshots, control-plane HA, upgrades, node drain), continue with the **current node maintenance, etcd, upgrade and HA exercises further down this README**, and consult the current upstream references listed in section 20.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 10 -->
### 8. Use kubectl from your workstation

**Goal:** control the cluster without logging into cp1 for every command.

On the workstation install **kubectl 1.37.x** with the same minor version as the server. For a Linux workstation that also runs Ubuntu 24.04, you may reuse the signed Kubernetes APT repository and kubectl installation from **section 3** (only install the kubectl package). For **Windows 11/PowerShell**, the commands below use Windows Package Manager, with OpenSSH Client already installed:


~~~powershell
winget install --id Kubernetes.kubectl --exact
kubectl version --client
New-Item -ItemType Directory -Force "$HOME\.kube" | Out-Null
~~~

Windows users can securely copy the config with the OpenSSH scp executable after preparing the transfer file on cp1 as instructed below:

~~~powershell
scp user@192.168.56.11:admin.conf "$HOME\.kube\config"
kubectl config current-context
kubectl get nodes -o wide
~~~

Use the actual username/address, and store the kubeconfig only in your private profile folder (do not share it or commit it). The kubeconfig contains cluster-admin authentication material. On Windows, restrict its ACL to the account that will use it.

On cp1, the file /etc/kubernetes/admin.conf contains cluster-admin credentials and a client private key. Transfer it only over a secure connection to your **own trusted workstation** (the historical course uses this method for local learning). From the workstation, for example:

~~~bash
mkdir -p "$HOME/.kube"
chmod 700 "$HOME/.kube"

# SSH user and cp1 IP must be adjusted. The file must be readable by that user;
# prefer a secure temporary copy with correct permissions rather than enabling
# broad remote read access to /etc/kubernetes/admin.conf.
scp user@192.168.56.11:~/admin.conf "$HOME/.kube/config"
chmod 600 "$HOME/.kube/config"

kubectl config current-context
kubectl cluster-info
kubectl get nodes -o wide
~~~

**On cp1 first**, prepare the temporary transfer file, remove it immediately after a successful transfer:

~~~bash
sudo cp /etc/kubernetes/admin.conf "$HOME/admin.conf"
sudo chown "$(id -u):$(id -g)" "$HOME/admin.conf"
chmod 600 "$HOME/admin.conf"
# After secure workstation transfer:
rm -f "$HOME/admin.conf"
~~~

If the API endpoint in the transferred config is **127.0.0.1**, a private name unknown to the workstation, or unreachable, update **only the workstation copy** to the correct endpoint using kubectl config set-cluster (inspect kubectl config view --minify first). For the HA lab use lb.k8s.lab:6443. Do not change security settings or ignore TLS verification to make an invalid endpoint work.

**Expected:** kubectl get nodes on the workstation shows the same nodes as on cp1. Keep kubeconfig out of Git and never send it to an untrusted machine.
<!-- MODERN_LAB_END -->


## Alternative local clusters and Vagrant homework

> After the default kubeadm cluster is working, compare Minikube, kind and Vagrant on **separate** disposable environments. The exercises here are independent of the HA/etcd recovery drills below.


<!-- MODERN_LAB_BEGIN HOMEWORK-2026.md 0 -->
## Module 02 homework — Kubernetes 1.37 (Minikube, kind, Vagrant/vanilla)

> **NOTE (2026):** The original `M2-Practice` DOCX and author Vagrant scripts are **Kubernetes 1.21–1.22 / Debian 10** historical artifacts. Do **not** execute them on a fresh 1.37 lab. This guide completes all three optional homework tasks on 1.37 using actual, versioned images/tools, with validation and cleanup. The full vanilla cluster procedure is [SETUP-2026.md](./SETUP-2026.md).
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN HOMEWORK-2026.md 1 -->
### Before starting

1. Install `kubectl` and verify its 1.36–1.38 compatible client version; have Docker Engine available for the first two tasks, with enough CPU/RAM (at least 8 GiB free memory for the multi-node local clusters). Follow the official [minikube installation](https://minikube.sigs.k8s.io/docs/start/) and [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/) for your host OS.
2. Use an isolated cluster for **each** task. The homework image `shekeriev/k8s-oracle` is third-party; the sample app requires image pull availability. Both examples reuse the multi-document [Module 01 Task 3A.yaml](../01.%20Core%20Concepts/Homework/Task%203/Task%203A.yaml) with Namespace, Pods and Service.
3. The application uses **NodePort 32000**, Service/Pod port **5000**, selector `app=hw`. Clear any pre-existing workload using that NodePort on the chosen cluster.
4. Always run `kubectl config current-context` before applying resources so you do not modify the wrong cluster. NodePort exposure differs by driver; follow the methods below.

From repository root:

```bash
kubectl version --client
docker version
```
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN HOMEWORK-2026.md 2 -->
### Task 1 — 2-node Minikube cluster

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
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN HOMEWORK-2026.md 3 -->
### Task 2 — 3-node kind cluster

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
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN HOMEWORK-2026.md 4 -->
### Task 3 — three-node vanilla cluster with Vagrant-managed VMs

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
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN HOMEWORK-2026.md 5 -->
### Troubleshooting and scope

| Symptom | Static checks / next action |
|---|---|
| Wrong cluster/context | `kubectl config current-context`; switch to `m02` or `kind-m02` as needed |
| Nodes not Ready | `kubectl describe node`; inspect `kube-system`, CNI and containerd |
| Pods not Ready | `kubectl describe pod -n homework`; investigate third-party image pull and node resources |
| NodePort not reachable | `kubectl get svc -n homework`, endpoints, host port mapping/firewall; Minikube `service --url`; try port-forward |
| Vagrant box unavailable | Confirm VirtualBox version and pinned `bento/ubuntu-24.04` box availability/provider/CPU architecture; choose an equivalent Ubuntu 24.04 box if required |
| kubeadm packages unavailable | Use the `pkgs.k8s.io` versioned sources in `SETUP-2026.md`; **never** the old `apt.kubernetes.io` repo |

Historical M2 DOCX/ZIP/author scripts remain available **for comparison**, but following this integrated README (sections 0–8 for setup) is the supported Kubernetes 1.37 path. The two Helm/CNI stacks (kind/minikube vs kubeadm/Calico) are different environments and should not be mixed.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 11 -->
### 9. Web UI lab — Headlamp (replaces the archived Dashboard)

The original notes used Kubernetes Dashboard v2.4.0. **Kubernetes Dashboard is archived/unmaintained**; this lab uses [Headlamp](https://headlamp.dev/docs/latest/installation/in-cluster/) instead. Headlamp is a UI replacement, not the same implementation.

On your workstation with functioning kubectl, install **Helm 3** (if not already installed). Download and **inspect** the official installer script before executing it:

~~~bash
curl -fsSLo "$HOME/get-helm-3" https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
less "$HOME/get-helm-3"
bash "$HOME/get-helm-3"
helm version
kubectl get nodes
helm repo add headlamp https://kubernetes-sigs.github.io/headlamp/
helm repo update
kubectl create namespace headlamp
helm install headlamp headlamp/headlamp --namespace headlamp --wait
kubectl get pods -n headlamp
kubectl get svc -n headlamp
~~~

**Expected:** Headlamp Pods are Running/Ready and the Service is visible. Forward the service port **from your workstation**:

~~~bash
kubectl port-forward -n headlamp svc/headlamp 8080:80
~~~

Open http://localhost:8080 locally. Keep the terminal open during the lab; Ctrl+C stops the port-forward.

#### Create a read-only identity for the UI

The historical Dashboard used a permanent cluster-admin ServiceAccount, giving excessive access to a browser UI. Instead, use a **short-lived token** with the built-in read-only ClusterRole **view**. It can inspect common workload resources across namespaces but **cannot write Deployments or read Secrets**. This provides a usable cluster-wide UI for the course without granting admin operations.

~~~bash
kubectl create namespace ui-lab
kubectl -n ui-lab create serviceaccount headlamp-viewer

kubectl create clusterrolebinding headlamp-lab-view \
  --clusterrole=view \
  --serviceaccount=ui-lab:headlamp-viewer

kubectl -n ui-lab create token headlamp-viewer --duration=1h
~~~

Paste the printed short-lived token into Headlamp's login prompt. Do not commit or share the token. Depending on the installed chart and Headlamp version, you may need to refresh the token when it expires.

**Exercise:** inspect the namespaces you can access, Pods, Events and Deployments. Some cluster-scoped resources (such as Nodes) may remain unavailable to the built-in view role. Verify rights with kubectl:

~~~bash
kubectl auth can-i get pods -n ui-lab --as=system:serviceaccount:ui-lab:headlamp-viewer
kubectl auth can-i create deployments -n ui-lab --as=system:serviceaccount:ui-lab:headlamp-viewer
kubectl auth can-i get pods -n kube-system --as=system:serviceaccount:ui-lab:headlamp-viewer
kubectl auth can-i get secrets -n kube-system --as=system:serviceaccount:ui-lab:headlamp-viewer
~~~

**Expected:** yes / no / yes / no, respectively, unless other permissions were granted. This lab intentionally demonstrates **view**, not the original Dashboard's unsafe permanent cluster-admin role. Perform write/administrative operations with trusted kubectl credentials.

Cleanup after the UI exercise:

~~~bash
kubectl delete clusterrolebinding headlamp-lab-view
kubectl delete namespace ui-lab
helm uninstall headlamp -n headlamp
kubectl delete namespace headlamp
~~~
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Nodes Maintenance

- Make the node unavailable for new work (**cordon**)
- Initiate workload migration (**drain**)
- All pods are **evicted** and recreated on other nodes 
- Node is ready for maintenance
- Declare the node ready for accepting work (**uncordon**)

The gallant, way to remove a node from the cluster for maintenance. We can first mark the node as not schedulable, so it won't receive any new work.
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 12 -->
### 10. Node maintenance exercises

Start only when all nodes show Ready and workloads can be rescheduled.

#### 10.1 Cordon / uncordon

~~~bash
kubectl get nodes -o wide
kubectl cordon wk2.k8s.lab
kubectl get nodes
# Expect wk2 SchedulingDisabled; existing Pods need not move.
kubectl uncordon wk2.k8s.lab
kubectl get nodes
~~~

If your actual node name is wk2 rather than wk2.k8s.lab, use the name returned by kubectl get nodes.

#### 10.2 Drain / uncordon

**Caution:** drain evicts Pods; it may block on PodDisruptionBudgets, local data, or unmanaged Pods. Do not use force or delete-emptydir-data unless you understand the consequences.

Create a simple replicable Deployment:

~~~bash
kubectl create namespace ops-lab
kubectl -n ops-lab create deployment web --image=nginx:stable --replicas=3
kubectl -n ops-lab rollout status deployment/web
kubectl -n ops-lab get pods -o wide

kubectl drain wk2.k8s.lab --ignore-daemonsets
kubectl get nodes
kubectl -n ops-lab get pods -o wide

kubectl uncordon wk2.k8s.lab
kubectl delete namespace ops-lab
~~~

**Expected:** drained node becomes SchedulingDisabled and eligible controller-managed Pods are rescheduled to other nodes. Draining does **not** imply that every workload can be moved (PVC constraints, resource availability, affinity, disruption budgets). Use describe/events to investigate if drain cannot finish.
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Etcd backup

- **etcd** is the default database for storing the cluster state.
- It runs on the control plane node(s).
- Use the **etcdctl** command to control it.
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 13 -->
### 11. etcd backup — hands-on lab

**Scope:** the first example uses a single control-plane kubeadm node with local stacked etcd. etcd snapshots contain **sensitive cluster state**; do not store them in Git or in a public location.

#### 11.1 Locate and inspect etcd

On **cp1**, using working kubectl:

~~~bash
kubectl -n kube-system get pods -l component=etcd -o wide
sudo grep -A4 -B4 "name: etcd-data" /etc/kubernetes/manifests/etcd.yaml
sudo grep "image:" /etc/kubernetes/manifests/etcd.yaml
~~~

The kubeadm static Pod normally mounts host /var/lib/etcd into the container and TLS certificates from /etc/kubernetes/pki/etcd. Use the **local** etcd Pod name returned on cp1, for example etcd-cp1.k8s.lab; do not assume it blindly.

#### 11.2 Make a consistent snapshot

~~~bash
# On cp1: replace the pod name with the local etcd Pod shown above.
ETCD_POD=etcd-cp1.k8s.lab

kubectl -n kube-system exec "$ETCD_POD" -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt \
  --key=/etc/kubernetes/pki/etcd/healthcheck-client.key \
  snapshot save /var/lib/etcd/etcd-snapshot.db

# For this kubeadm configuration, the path above is a hostPath mount:
sudo mkdir -p -m 700 /var/backups/kubernetes
sudo mv /var/lib/etcd/etcd-snapshot.db /var/backups/kubernetes/etcd-snapshot.db
sudo chmod 600 /var/backups/kubernetes/etcd-snapshot.db
sudo ls -lh /var/backups/kubernetes/etcd-snapshot.db
~~~

**Expected:** etcdctl reports a saved snapshot, and a non-empty local snapshot file exists. Test restoring snapshots only in disposable or dedicated recovery environments. Copy backups to encrypted/off-node storage with an established retention policy.

#### 11.3 Install matching etcdutl and inspect the snapshot

**etcdctl** takes network snapshots; **etcdutl** validates and restores local snapshot files. The original course used etcdctl restore, which is deprecated. Download the **matching etcd version** for this kubeadm cluster, identified from its static etcd Pod's image, directly from an official etcd release. Perform this step on **cp1** before any destructive restore.

~~~bash
ETCD_POD="$(kubectl -n kube-system get pods -l component=etcd -o jsonpath='{.items[0].metadata.name}')"
ETCD_IMAGE="$(kubectl -n kube-system get pod "$ETCD_POD" -o jsonpath='{.spec.containers[0].image}')"
printf 'etcd image: %s\n' "$ETCD_IMAGE"

# Example: registry.k8s.io/etcd:3.6.5-0 -> v3.6.5
ETCD_VER="v$(printf '%s' "$ETCD_IMAGE" | awk -F: '{print $NF}' | cut -d- -f1)"
case "$(uname -m)" in
  x86_64)  ETCD_ARCH=amd64 ;;
  aarch64) ETCD_ARCH=arm64 ;;
  *) echo "Unsupported lab CPU architecture; select correct upstream release manually"; exit 1 ;;
esac

printf 'Downloading etcd version %s for %s\n' "$ETCD_VER" "$ETCD_ARCH"
curl -fL --retry 3 \
  "https://github.com/etcd-io/etcd/releases/download/$ETCD_VER/etcd-$ETCD_VER-linux-$ETCD_ARCH.tar.gz" \
  -o "$HOME/etcd-tools.tar.gz"
mkdir -p "$HOME/etcd-tools"
tar -xzf "$HOME/etcd-tools.tar.gz" -C "$HOME/etcd-tools" --strip-components=1
sudo install -m 0755 "$HOME/etcd-tools/etcdutl" /usr/local/bin/etcdutl

etcdutl version
sudo etcdutl snapshot status /var/backups/kubernetes/etcd-snapshot.db -w table
~~~

**Expected:** etcdutl reports the version extracted from the live etcd image, and snapshot status displays revision, key count and size. If the image tag does not match an official release archive, inspect the image version and use a matching compatible etcdutl release. Verify downloaded release artifacts/checksums as appropriate for your environment. Keep the snapshot on secure storage; it contains cluster state and secrets.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 14 -->
### 12. etcd restore — isolated recovery exercise

**Destructive operation.** Restore overwrites cluster state, invalidates newer writes and can require clients/informers to reconnect. This procedure is **only for a disposable, single-control-plane kubeadm lab with local etcd** and a verified snapshot. Never use these single-node instructions on a 3-member stacked etcd cluster; multi-member restore requires a coordinated recovery process for **all members**. See [upstream recovery guidance](https://etcd.io/docs/v3.7/op-guide/recovery/).

#### Before shutdown

On cp1, check that the snapshot is available, consistent and from the same cluster, and that a compatible etcdutl binary is installed:

~~~bash
sudo etcdutl snapshot status /var/backups/kubernetes/etcd-snapshot.db -w table
sudo test -f /etc/kubernetes/manifests/kube-apiserver.yaml
sudo test -f /etc/kubernetes/manifests/etcd.yaml
sudo test -d /var/lib/etcd
~~~

Create a small temporary Kubernetes object **before** stopping services, to demonstrate rollback:

~~~bash
kubectl create namespace restore-demo
kubectl get namespace restore-demo
~~~

#### Shut down API and etcd static Pods

Back up the manifests, move them **outside** the staticPodPath directory, and confirm the containers stop. The kubelet watches /etc/kubernetes/manifests (including files with backup-like suffixes), so never leave backup YAMLs there.

~~~bash
sudo mkdir -p -m 700 /root/k8s-disabled-manifests
sudo cp -a /etc/kubernetes/manifests /root/k8s-manifests-pre-restore
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /root/k8s-disabled-manifests/
sudo mv /etc/kubernetes/manifests/etcd.yaml /root/k8s-disabled-manifests/

# Wait for the kubelet to terminate both static Pods; verify:
sudo crictl --runtime-endpoint unix:///run/containerd/containerd.sock ps
~~~

Only proceed when the original kube-apiserver and etcd containers are actually stopped. Restoring while they run can corrupt the recovery process.

#### Restore into a separate directory

~~~bash
sudo etcdutl snapshot restore \
  /var/backups/kubernetes/etcd-snapshot.db \
  --data-dir /var/lib/etcd-restore \
  --bump-revision 1000000000 \
  --mark-compacted

sudo ls -ld /var/lib/etcd-restore
~~~

**Expected:** etcdutl creates a new etcd data directory. The revision bump and compaction marker help invalidate stale Kubernetes watchers after restoring older state. Do not delete the original /var/lib/etcd during the lab; it is a fallback. Use this only on the disposable single-control-plane lab.

#### Point static etcd at the restored directory

In **/root/k8s-disabled-manifests/etcd.yaml**, find the **hostPath.path** for the volume named etcd-data and change its host-side value from /var/lib/etcd to **/var/lib/etcd-restore**; leave the container mountPath untouched. Check the volume specification carefully.

~~~bash
sudo grep -A5 -B5 'name: etcd-data' /root/k8s-disabled-manifests/etcd.yaml
# Edit only the relevant hostPath.path (editor of choice):
sudoedit /root/k8s-disabled-manifests/etcd.yaml

sudo mv /root/k8s-disabled-manifests/etcd.yaml /etc/kubernetes/manifests/
# Verify the restored etcd container becomes healthy before continuing:
sudo crictl --runtime-endpoint unix:///run/containerd/containerd.sock ps
~~~

Once etcd is healthy, restore the API server manifest:

~~~bash
sudo mv /root/k8s-disabled-manifests/kube-apiserver.yaml /etc/kubernetes/manifests/
kubectl get nodes
kubectl get namespaces
~~~

**Expected:** the API returns and the test namespace restore-demo, which was created *after* the snapshot, is **absent**. The control plane may take time to reconcile. Investigate static Pod logs and kubelet logs if it does not recover.

#### Make kubeadm aware of the restored path

For a lasting restored setup, update the **etcd.local.dataDir** property in the cluster's kubeadm-config ConfigMap to /var/lib/etcd-restore; otherwise a later kubeadm upgrade can regenerate the etcd static Pod manifest with the old path. Use kubectl -n kube-system edit cm kubeadm-config and modify only the value in its embedded ClusterConfiguration YAML. Inspect the ConfigMap first and back it up before editing.

~~~bash
kubectl -n kube-system get cm kubeadm-config -o yaml > "$HOME/kubeadm-config-before-restore.yaml"
kubectl -n kube-system edit cm kubeadm-config
kubectl -n kube-system get cm kubeadm-config -o yaml
~~~

For real disaster recovery, follow upstream guidance on **revision bump / mark compacted** and restart relevant control-plane components so cached watches do not retain stale state. This instructional exercise does not claim to cover production restoration. Clean up local temporary files and recovery directories only after verifying success.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 15 -->
### 13. Kubernetes upgrade lab — v1.36.x → v1.37.x

**This is a separate lab with an existing healthy v1.36.x cluster.** You cannot upgrade a v1.37 cluster *to the same minor version* and call that a v1.36→v1.37 exercise. Kubernetes does not support skipping minor versions.

#### 13.1 Prepare the source 1.36 lab (clean VMs)

Use **fresh cp1/wk1/wk2 VMs**, following the OS, addressing, swap, cgroup and containerd instructions in sections 0–2. For this *source lab only*, install Kubernetes 1.36 packages, not 1.37. Configure the v1.36 APT repository below on **all three** nodes:

~~~bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gpg
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key |
  sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' |
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
apt-cache madison kubeadm
K8S_SRC_PKG="$(apt-cache madison kubeadm | awk '$3 ~ /^1[.]36[.]/ {print $3; exit}')"
test -n "$K8S_SRC_PKG" || { echo "No 1.36 package found"; exit 1; }
sudo apt-get install -y "kubeadm=$K8S_SRC_PKG" "kubelet=$K8S_SRC_PKG" "kubectl=$K8S_SRC_PKG"
sudo apt-mark hold kubeadm kubelet kubectl
~~~

Use the *same source package patch* across the three machines. On cp1 initialize Kubernetes as in **section 4**, install **Calico 3.33 / VXLAN / BGP Disabled** exactly as in **section 5** (Calico 3.33 is tested against Kubernetes 1.36), join workers as in **section 6**, and verify in section 7. Now you have an actual source cluster ready for the following upgrade.

#### 13.2 Preparation and backup

Run on cp1 or a trusted workstation:

~~~bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get pdb -A
kubectl version
kubectl get tigerastatus
~~~

Verify every node is Ready and the API is healthy. Complete the **etcd backup (section 11)**; record a copy of the **kubeadm-config ConfigMap**, the Calico version and the current versions. Ensure workloads have enough remaining capacity for drain.

#### 13.3 Switch the APT repo to 1.37 on each node

Perform on cp1, wk1 and wk2, before their individual package upgrade, without yet replacing the 1.36 packages:

~~~bash
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.37/deb/ /' |
  sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
apt-cache madison kubeadm

K8S_TARGET_PKG="$(apt-cache madison kubeadm | awk '$3 ~ /^1[.]37[.]/ {print $3; exit}')"
test -n "$K8S_TARGET_PKG" || { echo "No 1.37 package found"; exit 1; }
K8S_TARGET_VER="$(printf '%s' "$K8S_TARGET_PKG" | cut -d- -f1)"
printf 'Chosen target package: %s / release v%s\n' "$K8S_TARGET_PKG" "$K8S_TARGET_VER"
~~~

**Record one target K8S_TARGET_PKG** from cp1. Verify it is available from apt on *all* nodes and assign the exact same version on each terminal (the package version suffix varies by repository). The variables are session-local: re-run the selection before each procedure or explicitly export the recorded value.

#### 13.4 Upgrade the first control plane cp1

On **cp1**, with the variables above set:

~~~bash
sudo apt-mark unhold kubeadm
sudo apt-get install -y "kubeadm=$K8S_TARGET_PKG"
sudo apt-mark hold kubeadm
kubeadm version

sudo kubeadm upgrade plan
sudo kubeadm upgrade apply "v$K8S_TARGET_VER"
~~~

**Expected:** kubeadm reports a successful v1.37.x control-plane upgrade. **Only after** this succeeds, move to the kubelet on cp1.

From the workstation with cluster-admin kubectl:

~~~bash
kubectl drain cp1.k8s.lab --ignore-daemonsets
~~~

On cp1:

~~~bash
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y "kubelet=$K8S_TARGET_PKG" "kubectl=$K8S_TARGET_PKG"
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet
~~~

Back on workstation:

~~~bash
kubectl uncordon cp1.k8s.lab
kubectl get nodes -o wide
kubectl get pods -A
~~~

**Expected:** cp1 returns Ready at the selected target version; check component health before proceeding.

#### 13.5 Additional control planes (if running this lab on the HA topology)

For **cp2**, then **cp3**, do the following *one node at a time*. This differs from cp1 because additional control planes run **kubeadm upgrade node**, not kubeadm upgrade apply.

On a workstation, drain the selected control plane:

~~~bash
kubectl drain cp2.k8s.lab --ignore-daemonsets
~~~

On cp2 (ensure 1.37 repository, K8S_TARGET_PKG variable and chosen patch are set):

~~~bash
sudo apt-mark unhold kubeadm
sudo apt-get install -y "kubeadm=$K8S_TARGET_PKG"
sudo apt-mark hold kubeadm
sudo kubeadm upgrade node
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y "kubelet=$K8S_TARGET_PKG" "kubectl=$K8S_TARGET_PKG"
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet
~~~

On workstation:

~~~bash
kubectl uncordon cp2.k8s.lab
kubectl get nodes -o wide
kubectl -n kube-system get pods -l component=etcd -o wide
~~~

**Expected:** cp2 Ready, etcd quorum retained. Repeat with cp3 by replacing **cp2** with **cp3**. Never drain two of the three control planes simultaneously.

#### 13.6 Upgrade workers — wk1, then wk2 (and wk3 in HA lab)

From workstation:

~~~bash
kubectl drain wk1.k8s.lab --ignore-daemonsets
~~~

On wk1 (K8S_TARGET_PKG set from 13.3):

~~~bash
sudo apt-mark unhold kubeadm
sudo apt-get install -y "kubeadm=$K8S_TARGET_PKG"
sudo apt-mark hold kubeadm
sudo kubeadm upgrade node

sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y "kubelet=$K8S_TARGET_PKG" "kubectl=$K8S_TARGET_PKG"
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet
~~~

From workstation:

~~~bash
kubectl uncordon wk1.k8s.lab
kubectl get nodes -o wide
~~~

Repeat on wk2 (and wk3 for the HA scenario), one node at a time, using actual names from kubectl get nodes. If drain blocks due to PodDisruptionBudgets or local data, **resolve the constraint**, do not add --force or --delete-emptydir-data blindly.

#### 13.7 Verify the upgrade

~~~bash
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get tigerastatus
kubectl get --raw='/readyz'
kubectl version
~~~

**Expected:** all control planes and workers Ready on 1.37.x, with healthy Calico and CoreDNS. Review any deprecated APIs and changed defaults from the [1.37 upgrade guidance](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/). Keep an etcd backup and a documented recovery path before upgrading any non-lab cluster.
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Highly-available Cluster

Need three virtual machines for control plane nodes and one or more (in this case 3) for nodes members of the cluster. In addition, we will need a machine to act as a load balancer. The following sources are used:

- [Highly Available Control Plane](https://kubernetes.io/docs/tasks/administer-cluster/highly-available-control-plane/)
- [High Availability](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
- [HA Topology](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-topology/)
- [HA Considerations](https://github.com/kubernetes/kubeadm/blob/main/docs/ha-considerations.md)
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 16 -->
### 14. High-availability lab — fresh cluster with stacked etcd

**This is an independent cluster build**, not the continuation of the 1 CP + 2 workers lab.

Topology: three control-plane VMs **cp1/cp2/cp3**, three worker VMs **wk1/wk2/wk3**, one **HAProxy** VM lb.k8s.lab (192.168.56.10 for this illustrative lab). Use the common OS, containerd, Kubernetes 1.37 and preflight steps (sections 0–3) on **all six Kubernetes nodes**. The HAProxy VM does not need kubeadm.

Each control plane runs its own etcd member (stacked topology). The Kubernetes API is available through **lb.k8s.lab:6443**. DNS or consistent hosts records must resolve this endpoint from **all nodes and the workstation**.

#### 14.1 Set up HAProxy on the LB VM

On the separate **LB VM** (Ubuntu/Debian):

~~~bash
sudo apt-get update
sudo apt-get install -y haproxy
sudo cp -a /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.orig
~~~

Append the following **distinct frontend/backend names** to /etc/haproxy/haproxy.cfg. Replace all IPs with your lab's real addresses. Check for duplicate port 6443 listeners before restarting.

~~~haproxy
frontend k8s_api_front
    bind *:6443
    mode tcp
    option tcplog
    default_backend k8s_api_back

backend k8s_api_back
    mode tcp
    balance roundrobin
    option tcp-check
    server cp1 192.168.56.11:6443 check
    server cp2 192.168.56.12:6443 check
    server cp3 192.168.56.13:6443 check

# Historical course parity: local-only HAProxy statistics page.
# Use an SSH port forward rather than publishing this dashboard to the LAN.
listen k8s_api_stats
    bind 127.0.0.1:8404
    mode http
    stats enable
    stats uri /stats
~~~

Apply after validating the configuration:

~~~bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
sudo systemctl enable --now haproxy
sudo systemctl restart haproxy
sudo systemctl status haproxy --no-pager
sudo ss -lntp | grep ':6443'
~~~

**Expected:** HAProxy listens on TCP 6443. Before kubeadm init the backends are down and an API request may get connection refused; after cp1 starts, it should forward API traffic.

**Optional exercise — HAProxy stats (as in the historical course):** from your workstation, use an SSH tunnel to the LB VM and open http://127.0.0.1:8404/stats in the workstation's browser:

~~~bash
ssh -L 8404:127.0.0.1:8404 user@lb.k8s.lab
~~~

Replace user with the LB VM SSH account. The HAProxy stats listener is bound only to LB loopback; no public statistics port is needed. You should see the three backend servers change status as control planes become available.

**Important:** one HAProxy VM is a **single point of failure**. High availability of the full API endpoint additionally requires redundant load balancers and a VIP/failover or equivalent managed load balancer.

#### 14.2 First control plane (cp1)

On cp1, after completing common steps 0–3:

~~~bash
getent hosts lb.k8s.lab
getent hosts cp1.k8s.lab

sudo kubeadm init \
  --control-plane-endpoint=lb.k8s.lab:6443 \
  --apiserver-advertise-address=192.168.56.11 \
  --pod-network-cidr=10.244.0.0/16 \
  --upload-certs \
  --cri-socket=unix:///run/containerd/containerd.sock
~~~

**Expected:** kubeadm prints a worker join command, a control-plane join command containing **--control-plane**, and a short-lived **--certificate-key**. Capture them securely. The uploaded certificates key expires after two hours by default; regenerate using kubeadm init phase upload-certs --upload-certs if necessary. Do not commit join tokens or certificates.

Configure the cp1 admin kubectl as in section 4. Then install **exactly the same Calico operator and custom-resources.yaml with VXLAN + BGP Disabled** as section 5. Verify the first node, CoreDNS and Calico before joining other control planes.

#### 14.3 Join cp2 and cp3 — one at a time

On cp2, after OS/runtime/kubeadm preparation, run the **control-plane join command printed by kubeadm**, with its current token, discovery CA cert hash, certificate key and the control-plane flag. Example **structure only** (not an executable token):

~~~bash
sudo kubeadm join lb.k8s.lab:6443 \
  --token <GENERATED_TOKEN> \
  --discovery-token-ca-cert-hash sha256:<GENERATED_CA_HASH> \
  --control-plane \
  --certificate-key <GENERATED_CERTIFICATE_KEY> \
  --cri-socket=unix:///run/containerd/containerd.sock
~~~

On cp1, wait for cp2 to join and become Ready, then run the same generated control-plane join command on cp3. Do not initialize a new cluster on cp2 or cp3.

~~~bash
kubectl get nodes -o wide
kubectl -n kube-system get pods -l component=etcd -o wide
kubectl get tigerastatus
~~~

**Expected:** three control-plane nodes Ready, three etcd Pods on separate control planes, Calico available. Verify quorum and API health; a single lost control plane should not stop the API when HAProxy remains available and the other two etcd members are healthy.

#### 14.4 Join the three workers

On cp1 generate a fresh command:

~~~bash
sudo kubeadm token create --print-join-command
~~~

Run the worker join command on **wk1, wk2, wk3**, with matching --cri-socket if needed. Do **not** append --control-plane to worker joins. Validate:

~~~bash
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get tigerastatus
kubectl cluster-info
~~~

**Expected:** 6 Ready Kubernetes nodes: 3 control planes plus 3 workers. HAProxy is external and is **not** a Kubernetes node.

#### 14.5 HA failure drill

Use an isolated lab and confirm the workload has multiple replicas across workers. Capture initial status, then stop **one** cp VM or temporarily stop its kubelet, not two etcd members at once. From the workstation:

~~~bash
kubectl get nodes -o wide
kubectl get --raw='/readyz'
kubectl -n kube-system get pods -l component=etcd -o wide
~~~

**Expected:** the API remains reachable through HAProxy and etcd retains a majority of 2/3 members. Restore the failed control plane and confirm the cluster returns to healthy 3-member state. This does not prove that HAProxy itself survives failure; that is a separate exercise.

**Do not** use the single-node etcd restore procedure from section 12 against this HA cluster. Plan coordinated snapshots and cluster-wide recovery using the [official HA](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/) and [etcd recovery](https://etcd.io/docs/v3.7/op-guide/recovery/) references.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 17 -->
### 15. Validate NetworkPolicy (Calico)

This exercise intentionally proves why the default course CNI is Calico rather than basic Flannel.

~~~bash
kubectl create namespace policy-lab
kubectl -n policy-lab create deployment web --image=nginx:stable
kubectl -n policy-lab expose deployment web --port=80
kubectl -n policy-lab run allowed --image=busybox:1.36 --labels=access=granted --restart=Never -- sleep 3600
kubectl -n policy-lab run blocked --image=busybox:1.36 --labels=access=none --restart=Never -- sleep 3600
kubectl -n policy-lab wait --for=condition=Ready pod/allowed pod/blocked --timeout=180s
kubectl -n policy-lab rollout status deployment/web
~~~

Apply this namespaced **Ingress** policy. It targets the NGINX Pods and allows connections only from same-namespace Pods labelled access=granted, to TCP port 80.

~~~bash
cat > "$HOME/policy-lab.yaml" <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-from-granted
  namespace: policy-lab
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              access: granted
      ports:
        - protocol: TCP
          port: 80
EOF

kubectl apply -f "$HOME/policy-lab.yaml"
kubectl -n policy-lab get networkpolicy
kubectl -n policy-lab exec allowed -- wget -qO- -T 3 http://web
kubectl -n policy-lab exec blocked -- wget -qO- -T 3 http://web
~~~

**Expected:** allowed receives the NGINX HTML response; blocked times out/fails. The initial state without this policy allows both. If results differ, check labels, Service endpoints, Calico status, and pre-existing policies rather than assuming the CNI is broken.

~~~bash
kubectl delete namespace policy-lab
~~~
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 18 -->
### 16. Troubleshooting reference

| Symptom | First commands | Investigate |
| --- | --- | --- |
| Node NotReady | kubectl describe node NODE; journalctl -u kubelet -xe | CNI, runtime, swap, resources |
| Calico unavailable | kubectl get tigerastatus; kubectl get pods -n calico-system | pool CIDR, BGP setting, VXLAN UDP 4789, host firewall |
| CoreDNS Pending/NotReady | kubectl -n kube-system describe pod POD | CNI and Pod networking |
| kubeadm init fails | sudo journalctl -u kubelet; sudo crictl ps -a | CRI socket, cgroups, port conflicts |
| Worker join times out | getent hosts lb.k8s.lab; nc -zv lb.k8s.lab 6443 | DNS, network ACLs, HAProxy |
| HAProxy API unavailable | sudo haproxy -c -f /etc/haproxy/haproxy.cfg; systemctl status haproxy | backend reachability, API readiness |
| Drain blocks | kubectl get pdb -A; kubectl describe pod POD | PDB, local storage, unmanaged Pods |
| etcd restore fails | journalctl -u kubelet; crictl logs CONTAINER_ID | wrong data directory, manifests, certificates |

Use real Kubernetes object names from kubectl outputs; NODE, POD and CONTAINER_ID above are placeholders. Helpful baseline commands:

~~~bash
kubectl get events -A --sort-by=.lastTimestamp
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl describe node cp1.k8s.lab
sudo systemctl status kubelet containerd --no-pager
sudo journalctl -u kubelet -n 100 --no-pager
sudo crictl --runtime-endpoint unix:///run/containerd/containerd.sock ps -a
~~~
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 19 -->
### 17. Optional alternative: Flannel v0.28.10 on a fresh cluster

This appendix preserves the course's original CNI option. **Do not run it on Calico nodes.** Install Flannel **instead of** section 5 on an entirely new disposable lab.

#### 17.1 Create fresh VMs and base cluster

Repeat the standard Lab A topology (cp1 + wk1 + wk2), run common setup **sections 0–3**, and on cp1 run **section 4** exactly as written (including --pod-network-cidr=10.244.0.0/16). **Skip section 5 entirely.** Before deploying Flannel, the control-plane node will normally be NotReady due to missing CNI.

Flannel uses VXLAN over UDP 8472 by default (**different from Calico's UDP 4789**). Open node-to-node UDP 8472 in your lab firewall.

#### 17.2 Install CNI plugins on all three nodes

The Flannel Helm chart uses standard CNI binaries including portmap. Install a known plugin archive on **cp1, wk1, wk2** (amd64 and arm64 examples):

~~~bash
case "$(uname -m)" in
  x86_64)  CNI_ARCH=amd64 ;;
  aarch64) CNI_ARCH=arm64 ;;
  *) echo "Set CNI_ARCH for your CPU before continuing"; exit 1 ;;
esac
sudo mkdir -p /opt/cni/bin
curl -fL --retry 3 -o "$HOME/cni-plugins.tgz" \
  "https://github.com/containernetworking/plugins/releases/download/v1.7.1/cni-plugins-linux-$CNI_ARCH-v1.7.1.tgz"
sudo tar -C /opt/cni/bin -xzf "$HOME/cni-plugins.tgz"
test -x /opt/cni/bin/portmap && echo "portmap plugin ready"
~~~

#### 17.3 Install Helm (control-plane admin account)

If Helm has not yet been installed, use the official Helm 3 installer after inspecting the downloaded script. **This lab does not install Helm by silently running unchecked remote shell code.**

~~~bash
curl -fsSLo "$HOME/get-helm-3" https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
less "$HOME/get-helm-3"  # Inspect the script; press q to exit.
bash "$HOME/get-helm-3"
helm version
~~~

Use Helm on cp1 with working admin kubectl, or on a trusted workstation configured as in section 8.

#### 17.4 Deploy Flannel (control-plane admin account)

~~~bash
kubectl create namespace kube-flannel
kubectl label --overwrite namespace kube-flannel pod-security.kubernetes.io/enforce=privileged

helm repo add flannel https://flannel-io.github.io/flannel/
helm repo update
helm search repo flannel/flannel --versions

FLANNEL_CHART_VERSION="$(helm search repo flannel/flannel --versions | awk 'NR==2 {print $2}')"
test -n "$FLANNEL_CHART_VERSION" || { echo "No Flannel chart version found"; exit 1; }
printf 'Selected Helm chart version: %s\n' "$FLANNEL_CHART_VERSION"

helm install flannel flannel/flannel \
  --namespace kube-flannel \
  --version "$FLANNEL_CHART_VERSION" \
  --set podCidr=10.244.0.0/16 \
  --set flannel.image.tag=v0.28.10 \
  --set flannel_cni.image.tag=v1.9.1-flannel3 \
  --wait
~~~

**Expected:** Flannel chart is installed with image version **v0.28.10**, Pod CIDR **10.244.0.0/16**, and namespace Pod Security Admission set appropriately for the plugin. **Record the printed chart version** to reproduce this specific chart in the future. If the chart changes its values API, inspect the chart with helm show values and adjust before installing. No Calico operator or Installation resource is used in this lab.

~~~bash
kubectl get pods -n kube-flannel -o wide
kubectl get nodes -o wide
kubectl get pods -n kube-system -l k8s-app=kube-dns
helm status flannel -n kube-flannel
~~~

After Flannel is Ready and CoreDNS works, run the worker join procedure **section 6** on wk1 and wk2, then run section 7.

#### 17.5 Optional NetworkPolicy controller for Flannel

Flannel **alone** provides pod networking but does not enforce standard Kubernetes NetworkPolicy. Its recent Helm chart can deploy the **kube-network-policies** controller through the **netpol.enabled** option. Use the same installed chart/version (do not install a second CNI):

~~~bash
helm upgrade flannel flannel/flannel \
  --namespace kube-flannel \
  --version "$FLANNEL_CHART_VERSION" \
  --reuse-values \
  --set netpol.enabled=true \
  --wait
kubectl get pods -n kube-flannel -o wide
helm get values flannel -n kube-flannel
~~~

**Expected:** a NetworkPolicy-related additional container/controller is present. You may now try the **section 15** NetworkPolicy lab on this independent Flannel cluster. To test Flannel *without* policy support, omit this optional subsection.

**Comparison:** Calico remains the main course recommendation because it has integrated policy enforcement and richer networking controls. Flannel is the simpler historical alternative with an optional extra controller. Neither is to be installed into a cluster already managed by the other CNI.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 20 -->
### 18. Course parity checklist

| Historical 2021–22 lab topic | Modern counterpart |
| --- | --- |
| Debian template and VMs | Lab topology, VM checklist, steps 0–3 |
| Single control plane and two workers | Steps 4–7 |
| Flannel Pod network | Calico VXLAN, step 5; optional Flannel in step 17 |
| Remote kubectl on PC | Step 8 |
| Kubernetes Dashboard | Headlamp, step 9 |
| Node cordon/drain/uncordon | Step 10 |
| etcd snapshot | Step 11 |
| etcd restore | Step 12 (**single-node lab only**) |
| Upgrade control plane and workers | Step 13 (separate source-version lab) |
| HAProxy, 3 CP and 3 workers | Step 14 (HA lab, with single-LB caveat) |
| Security / NetworkPolicy follow-on | Step 15 and original module 03 |

This is a **documentation procedure** aligned with upstream references, not a record of a completed end-to-end test. Some destructive/upgrade exercises require **fresh separate VMs** and are intentionally not run one after another on the same cluster.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 21 -->
### 19. Operational follow-ups

- **Upgrades:** review release notes, take backups, then upgrade kubeadm/control-plane and worker nodes in the documented sequence. Do not skip minor versions.
- **etcd:** keep regular backups and a tested recovery procedure; production HA setups need additional planning.
- **Dashboard:** avoid the old v2.4.0 Dashboard + permanent cluster-admin setup from the historical course. Choose a currently supported UI and grant least-privilege access.
- **Hardening:** implement appropriate RBAC, Pod Security Admission, NetworkPolicies, audit logging, image version pinning and a secure supply chain.
- **Automation:** a future repo improvement can add lab provisioning and CI validation, but neither is a prerequisite for the documentation update.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SETUP-2026.md 22 -->
### 20. Official references

- [Kubernetes release branches](https://kubernetes.io/releases/)
- [Installing kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [Container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
- [Operating etcd clusters](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [Calico on-premises installation](https://docs.tigera.io/calico/latest/getting-started/kubernetes/self-managed-onprem/onpremises)
- [Calico compatibility requirements](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)
<!-- MODERN_LAB_END -->

