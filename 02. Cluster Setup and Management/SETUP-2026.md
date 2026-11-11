# Kubernetes 1.37 — modern kubeadm cluster setup (2026)

> **Scope:** New Linux lab clusters only. This is a companion to the original [Cluster Setup and Management notes](./README.md), which document the original Debian 10 / Kubernetes 1.21–1.22 exercises. Do **not** use those historical commands to install a new cluster.
>
> **Reference date:** 11 November 2026. **Status:** Documentation reviewed against upstream installation references; not executed against a live cluster.

## Target architecture

This guide modernizes the historical course with **Kubernetes 1.37**, **containerd 2.x**, **Calico 3.33**, VXLAN encapsulation, BGP disabled and NetworkPolicy support. Flannel is a **separate fresh-lab alternative**, never installed on the Calico cluster.

### Lab topology and choices

| Lab | Machines | Example hostnames / private IP addresses |
| --- | --- | --- |
| A — standard | 1 control plane + 2 workers | cp1: 192.168.56.11, wk1: .21, wk2: .22 |
| B — HA | 3 control planes + 3 workers + HAProxy | cp1: .11, cp2: .12, cp3: .13, wk1: .21, wk2: .22, wk3: .23, lb: .10 |

All addresses expand **192.168.56.**. Substitute the real IP addresses on your VM network. Lab B uses the DNS name **lb.k8s.lab** to point to HAProxy. **One HAProxy VM is a single point of failure**, even though etcd/control plane run in HA.

**Executable OS example:** Ubuntu Server **24.04 LTS**, on separate VMs or hosts with systemd and apt. Debian 12/13 are possible but require verifying distribution-specific package sources. The guide does not assume a particular hypervisor or physical subnet.

**Subnet choices:** Pod CIDR **10.244.0.0/16**, Service CIDR **10.96.0.0/12**; both must be distinct from physical/VPN networks. VXLAN between nodes requires **UDP 4789**; BGP is disabled.

### Provisioning the VMs

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

### Network access matrix

| Direction | Protocol/port | Purpose |
| --- | --- | --- |
| workstation/nodes → API endpoint | TCP 6443 | Kubernetes API |
| control-plane ↔ control-plane (Lab B) | TCP 2379–2380 | stacked etcd |
| control plane → nodes | TCP 10250 | kubelet |
| nodes ↔ nodes | UDP 4789 | Calico VXLAN |

Allow DNS, NTP, HTTPS image pulls and exercise-specific NodePorts as applicable. Use tight firewall rules rather than indiscriminately disabling host security. See the [Kubernetes port reference](https://kubernetes.io/docs/reference/networking/ports-and-protocols/).

### Lab execution order

1. **Lab A:** on cp1, wk1 and wk2, perform **sections 0–3**.
2. On cp1 initialize Kubernetes (**section 4**) and install Calico (**section 5**); then join workers (**section 6**) and verify (**section 7**).
3. Try workstation access, Headlamp, node maintenance, etcd backup and policy exercises (**sections 8–11 and 15–16**).
4. **etcd restore (section 12)** is destructive; use a disposable copy of Lab A, **not** the HA lab.
5. **Upgrade (section 13)** starts from an independent **1.36.x** cluster, not from an already installed 1.37 cluster.
6. **Lab B:** use freshly prepared VMs for 3 control planes + 3 workers + HAProxy, applying common sections 0–3 and then section 14.
7. **Flannel (section 17):** use a different fresh cluster. Never install it on top of Calico.

## 0. Preflight (all Kubernetes nodes)

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

## 1. Configure kernel networking (all nodes)

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

## 2. Install and configure containerd 2.x (all Kubernetes nodes)

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

## 3. Install kubeadm, kubelet and kubectl (all nodes)

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
## 4. Initialize the control plane (control-plane node only)

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

## 5. Install Calico v3.33.0 — VXLAN / BGP disabled (control-plane node only)

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

## 6. Join worker nodes

On the control-plane node, generate a fresh join command:

~~~bash
sudo kubeadm token create --print-join-command
~~~

Run the generated **kubeadm join** command on each prepared worker node with sudo. If multiple runtimes are installed, supply the appropriate **--cri-socket**.

Treat the bootstrap join token as a short-lived credential. Do not paste a real join command into this repository.

## 7. Verification

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

For further cluster administration (etcd snapshots, control-plane HA, upgrades, node drain), treat the [historical course notes](./README.md) as learning material and consult the current linked upstream instructions instead of copying their older commands.

## 8. Use kubectl from your workstation

**Goal:** control the cluster without logging into cp1 for every command.

On your workstation install kubectl with the same minor version as the cluster. For Linux, use the [official kubectl installation instructions](https://kubernetes.io/docs/tasks/tools/); for Windows/macOS, use the corresponding supported package instructions.

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

## 9. Web UI lab — Headlamp (replaces the archived Dashboard)

The original notes used Kubernetes Dashboard v2.4.0. **Kubernetes Dashboard is archived/unmaintained**; this lab uses [Headlamp](https://headlamp.dev/docs/latest/installation/in-cluster/) instead. Headlamp is a UI replacement, not the same implementation.

On your workstation with functioning kubectl, install [Helm 3](https://helm.sh/docs/intro/install/) and confirm:

~~~bash
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

### Create a restricted lab identity

Create a dedicated ServiceAccount and restrict its access to a lab namespace. **Do not create a permanent cluster-admin ServiceAccount.**

~~~bash
kubectl create namespace ui-lab
kubectl -n ui-lab create serviceaccount headlamp-viewer

kubectl -n ui-lab create rolebinding headlamp-viewer-readonly \
  --clusterrole=view \
  --serviceaccount=ui-lab:headlamp-viewer

kubectl -n ui-lab create token headlamp-viewer --duration=1h
~~~

Paste the short-lived bearer token into Headlamp's login prompt. Depending on the installed Headlamp version/UI authentication behavior, the UI may show limited namespace visibility or require another supported authentication method; consult its [authentication guide](https://headlamp.dev/docs/latest/installation/). The token can read resources allowed by its RBAC role in ui-lab, not administer the cluster.

**Exercise:** inspect namespaces, Pods, Events, Deployments, and confirm that writing to a different namespace is denied. To check authorization from kubectl:

~~~bash
kubectl auth can-i get pods -n ui-lab --as=system:serviceaccount:ui-lab:headlamp-viewer
kubectl auth can-i create deployments -n ui-lab --as=system:serviceaccount:ui-lab:headlamp-viewer
kubectl auth can-i get pods -n kube-system --as=system:serviceaccount:ui-lab:headlamp-viewer
~~~

Expected: yes / no / no for these checks (unless the cluster already grants this identity extra roles).

Cleanup after exercise:

~~~bash
kubectl delete namespace ui-lab
helm uninstall headlamp -n headlamp
kubectl delete namespace headlamp
~~~

## 10. Node maintenance exercises

Start only when all nodes show Ready and workloads can be rescheduled.

### 10.1 Cordon / uncordon

~~~bash
kubectl get nodes -o wide
kubectl cordon wk2.k8s.lab
kubectl get nodes
# Expect wk2 SchedulingDisabled; existing Pods need not move.
kubectl uncordon wk2.k8s.lab
kubectl get nodes
~~~

If your actual node name is wk2 rather than wk2.k8s.lab, use the name returned by kubectl get nodes.

### 10.2 Drain / uncordon

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

## 11. etcd backup — hands-on lab

**Scope:** the first example uses a single control-plane kubeadm node with local stacked etcd. etcd snapshots contain **sensitive cluster state**; do not store them in Git or in a public location.

### 11.1 Locate and inspect etcd

On **cp1**, using working kubectl:

~~~bash
kubectl -n kube-system get pods -l component=etcd -o wide
sudo grep -A4 -B4 "name: etcd-data" /etc/kubernetes/manifests/etcd.yaml
sudo grep "image:" /etc/kubernetes/manifests/etcd.yaml
~~~

The kubeadm static Pod normally mounts host /var/lib/etcd into the container and TLS certificates from /etc/kubernetes/pki/etcd. Use the **local** etcd Pod name returned on cp1, for example etcd-cp1.k8s.lab; do not assume it blindly.

### 11.2 Make a consistent snapshot

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

### 11.3 Install matching etcdutl and inspect the snapshot

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

## 12. etcd restore — isolated recovery exercise

**Destructive operation.** Restore overwrites cluster state, invalidates newer writes and can require clients/informers to reconnect. This procedure is **only for a disposable, single-control-plane kubeadm lab with local etcd** and a verified snapshot. Never use these single-node instructions on a 3-member stacked etcd cluster; multi-member restore requires a coordinated recovery process for **all members**. See [upstream recovery guidance](https://etcd.io/docs/v3.7/op-guide/recovery/).

### Before shutdown

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

### Shut down API and etcd static Pods

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

### Restore into a separate directory

~~~bash
sudo etcdutl snapshot restore \
  /var/backups/kubernetes/etcd-snapshot.db \
  --data-dir /var/lib/etcd-restore \
  --bump-revision 1000000000 \
  --mark-compacted

sudo ls -ld /var/lib/etcd-restore
~~~

**Expected:** etcdutl creates a new etcd data directory. The revision bump and compaction marker help invalidate stale Kubernetes watchers after restoring older state. Do not delete the original /var/lib/etcd during the lab; it is a fallback. Use this only on the disposable single-control-plane lab.

### Point static etcd at the restored directory

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

### Make kubeadm aware of the restored path

For a lasting restored setup, update the **etcd.local.dataDir** property in the cluster's kubeadm-config ConfigMap to /var/lib/etcd-restore; otherwise a later kubeadm upgrade can regenerate the etcd static Pod manifest with the old path. Use kubectl -n kube-system edit cm kubeadm-config and modify only the value in its embedded ClusterConfiguration YAML. Inspect the ConfigMap first and back it up before editing.

~~~bash
kubectl -n kube-system get cm kubeadm-config -o yaml > "$HOME/kubeadm-config-before-restore.yaml"
kubectl -n kube-system edit cm kubeadm-config
kubectl -n kube-system get cm kubeadm-config -o yaml
~~~

For real disaster recovery, follow upstream guidance on **revision bump / mark compacted** and restart relevant control-plane components so cached watches do not retain stale state. This instructional exercise does not claim to cover production restoration. Clean up local temporary files and recovery directories only after verifying success.

## 13. Kubernetes upgrade lab — kubeadm 1.36 → 1.37

This is a **separate lab**: it requires an existing **healthy Kubernetes 1.36.x** cluster. You **cannot** meaningfully perform a 1.36→1.37 upgrade on the v1.37 cluster installed above. To follow the original exercise, create a dedicated 1.36 lab first (adjust the versioned APT repo and the CNI release to ones compatible with 1.36), or carry out a **1.37.x patch upgrade** with the corresponding documented steps.

**No skipping minor releases.** Read [official kubeadm 1.36→1.37 instructions](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/) and release notes before upgrading.

### Preparation

On a healthy cluster:

~~~bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get pdb -A
kubectl version
~~~

Back up etcd (section 11), capture kubeadm configuration, check CNI compatibility, and confirm enough spare worker resources to drain nodes.

### Change the Kubernetes APT minor repository on all nodes

The repo installed for 1.36 includes **only** packages for that minor release. On each node, update the APT line to:

~~~text
deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.37/deb/ /
~~~

Then:

~~~bash
sudo apt-get update
apt-cache madison kubeadm
~~~

Choose the **exact latest 1.37 patch package** shown by the package manager; replace 1.37.x-* in the examples below with the actual available version string.

### First control-plane node (cp1)

~~~bash
sudo apt-mark unhold kubeadm
sudo apt-get install -y 'kubeadm=1.37.x-*'
sudo apt-mark hold kubeadm
kubeadm version

sudo kubeadm upgrade plan
# Only when the upgrade plan is healthy, substitute your selected patch:
sudo kubeadm upgrade apply v1.37.x
~~~

After successful control-plane upgrade, perform the node-local kubelet upgrade, ideally from a workstation whose kubectl can reach the API:

~~~bash
# On workstation:
kubectl drain cp1.k8s.lab --ignore-daemonsets

# On cp1:
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y 'kubelet=1.37.x-*' 'kubectl=1.37.x-*'
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# On workstation:
kubectl uncordon cp1.k8s.lab
kubectl get nodes
~~~

On **additional control-plane nodes in HA**, perform the kubeadm package upgrade **one at a time** but use **sudo kubeadm upgrade node** (not a second upgrade apply). Then drain, update kubelet/kubectl, restart kubelet, uncordon and verify the node before moving on.

### Worker nodes — one at a time

~~~bash
# Workstation:
kubectl drain wk1.k8s.lab --ignore-daemonsets

# On wk1:
sudo apt-mark unhold kubeadm kubectl
sudo apt-get install -y 'kubeadm=1.37.x-*' 'kubectl=1.37.x-*'
sudo apt-mark hold kubeadm kubectl
sudo kubeadm upgrade node

sudo apt-mark unhold kubelet
sudo apt-get install -y 'kubelet=1.37.x-*'
sudo apt-mark hold kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# Workstation:
kubectl uncordon wk1.k8s.lab
kubectl get nodes -o wide
~~~

Repeat for each worker. Verify API, DNS, workload networking, CNI pods, and application readiness at the end. For detailed draining caveats, version skew and patch upgrade variants, defer to the official 1.37 upgrade task.

## 14. High-availability lab — fresh cluster with stacked etcd

**This is an independent cluster build**, not the continuation of the 1 CP + 2 workers lab.

Topology: three control-plane VMs **cp1/cp2/cp3**, three worker VMs **wk1/wk2/wk3**, one **HAProxy** VM lb.k8s.lab (192.168.56.10 for this illustrative lab). Use the common OS, containerd, Kubernetes 1.37 and preflight steps (sections 0–3) on **all six Kubernetes nodes**. The HAProxy VM does not need kubeadm.

Each control plane runs its own etcd member (stacked topology). The Kubernetes API is available through **lb.k8s.lab:6443**. DNS or consistent hosts records must resolve this endpoint from **all nodes and the workstation**.

### 14.1 Set up HAProxy on the LB VM

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

**Important:** one HAProxy VM is a **single point of failure**. High availability of the full API endpoint additionally requires redundant load balancers and a VIP/failover or equivalent managed load balancer.

### 14.2 First control plane (cp1)

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

### 14.3 Join cp2 and cp3 — one at a time

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

### 14.4 Join the three workers

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

### 14.5 HA failure drill

Use an isolated lab and confirm the workload has multiple replicas across workers. Capture initial status, then stop **one** cp VM or temporarily stop its kubelet, not two etcd members at once. From the workstation:

~~~bash
kubectl get nodes -o wide
kubectl get --raw='/readyz'
kubectl -n kube-system get pods -l component=etcd -o wide
~~~

**Expected:** the API remains reachable through HAProxy and etcd retains a majority of 2/3 members. Restore the failed control plane and confirm the cluster returns to healthy 3-member state. This does not prove that HAProxy itself survives failure; that is a separate exercise.

**Do not** use the single-node etcd restore procedure from section 12 against this HA cluster. Plan coordinated snapshots and cluster-wide recovery using the [official HA](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/) and [etcd recovery](https://etcd.io/docs/v3.7/op-guide/recovery/) references.

## 15. Validate NetworkPolicy (Calico)

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

## 16. Troubleshooting reference

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

## 17. Optional alternative: fresh Flannel-only cluster

**Do not install Flannel on a cluster that already has Calico.** This optional appendix reproduces the historical networking choice on a **new** kubeadm cluster. Use a *separate clean set of VMs*, and make CNI selection **before** the first network plugin is installed.

The original lab used Flannel and the same 10.244.0.0/16 Pod CIDR. Complete sections 0–4 on fresh nodes but **skip section 5 entirely**. In kubeadm init use --pod-network-cidr=10.244.0.0/16. Then follow the [current official Flannel installation](https://github.com/flannel-io/flannel) for the selected, Kubernetes-compatible Flannel release and deployment method.

For a **networking-only** reproduction, use the vendor's official YAML manifest or Helm chart for the version you selected. Pin the version rather than fetching an uncontrolled latest/main branch. Verify the resulting CNI network ranges and node status.

For NetworkPolicy exercises **Flannel alone is insufficient**. Recent Flannel Helm charts have an optional additional kube-network-policies controller:

~~~bash
# Example Helm chart option on a new Flannel lab; see upstream chart
# repository and release docs for the exact install invocation:
helm install flannel flannel/flannel \
  --namespace kube-flannel \
  --set netpol.enabled=true
~~~

**Do not run this snippet without first adding the official Flannel Helm repository and creating/configuring its namespace according to the pinned release's instructions.** For a fully reproducible Flannel lab, follow and version-lock the current [Flannel Helm chart](https://github.com/flannel-io/flannel#deploying-flannel-with-helm). The supplemental controller adds moving parts; Calico remains our **primary course CNI**.

**Choice summary:** Default: **Calico 3.33 / VXLAN / BGP disabled / NetworkPolicy enabled**. Alternative: **Flannel** only on a fresh, separately prepared lab cluster. Never mix their full networking installations.

## 18. Course parity checklist

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


## 19. Operational follow-ups

- **Upgrades:** review release notes, take backups, then upgrade kubeadm/control-plane and worker nodes in the documented sequence. Do not skip minor versions.
- **etcd:** keep regular backups and a tested recovery procedure; production HA setups need additional planning.
- **Dashboard:** avoid the old v2.4.0 Dashboard + permanent cluster-admin setup from the historical course. Choose a currently supported UI and grant least-privilege access.
- **Hardening:** implement appropriate RBAC, Pod Security Admission, NetworkPolicies, audit logging, image version pinning and a secure supply chain.
- **Automation:** a future repo improvement can add lab provisioning and CI validation, but neither is a prerequisite for the documentation update.

## 20. Official references

- [Kubernetes release branches](https://kubernetes.io/releases/)
- [Installing kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [Container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
- [Operating etcd clusters](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [Calico on-premises installation](https://docs.tigera.io/calico/latest/getting-started/kubernetes/self-managed-onprem/onpremises)
- [Calico compatibility requirements](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)
