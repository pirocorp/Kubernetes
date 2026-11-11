# Kubernetes 1.37 — modern kubeadm cluster setup (2026)

> **Scope:** New Linux lab clusters only. This is a companion to the original [Cluster Setup and Management notes](./README.md), which document the original Debian 10 / Kubernetes 1.21–1.22 exercises. Do **not** use those historical commands to install a new cluster.
>
> **Reference date:** 11 November 2026. **Status:** Documentation reviewed against upstream installation references; not executed against a live cluster.

## Target architecture

- One control-plane node and one or more worker nodes, on separate Linux VMs or hosts.
- Debian 12/13 or Ubuntu 24.04 LTS as examples of modern Linux distributions. Check your actual OS, kernel, runtime and CNI support before use.
- Kubernetes **v1.37** installed using the versioned **pkgs.k8s.io** repository.
- A Kubernetes CRI-compatible runtime: **containerd** (prefer a supported 2.x release).
- **Calico v3.33.0** for Pod networking and NetworkPolicy, installed through the Tigera Operator.
- One non-overlapping Pod CIDR: **10.244.0.0/16** for this example, adjusted to your actual LAN/VPN/service networks as necessary.

The example builds a **lab cluster, not a production HA deployment**. For production, add HA control plane, stable endpoint/load balancer, backups, monitoring, network hardening and a documented upgrade plan.

## 0. Preflight (all nodes)

Check:
- Unique hostnames, IP addresses, MAC addresses and machine IDs; working DNS/hosts resolution and time synchronization.
- Network connectivity among nodes and the required [Kubernetes ports](https://kubernetes.io/docs/reference/networking/ports-and-protocols/), plus ports required by your selected CNI.
- A supported CPU architecture, adequate memory and disk capacity, and a routable node-to-node network.
- The Pod CIDR and Kubernetes Service CIDR do **not** overlap physical, VPN or other routed networks.
- Kubernetes 1.37 expects a compatible CRI implementation and modern Linux cgroup configuration.

Kubelet normally refuses to start when swap is enabled, unless explicitly configured to support it. For a simple lab, disable swap on **each Kubernetes VM/node** (not necessarily on a separate homelab host):

~~~bash
sudo swapoff -a
swapon --show
~~~

Make the swap change persistent using the actual distribution's configuration (for example, the relevant /etc/fstab entry or systemd swap units). Verify after reboot.

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

## 2. Install and configure containerd (all nodes)

Install **containerd**, not the Docker Engine + built-in dockershim combination used in the historical guide. Docker Engine requires a separate **cri-dockerd** adapter when used as a Kubernetes runtime.

Example for Debian/Ubuntu using distribution packages:

~~~bash
sudo apt-get update
sudo apt-get install -y containerd
containerd --version
sudo mkdir -p /etc/containerd
sudo containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
~~~

**Review the installed containerd version before continuing.** Prefer a supported 2.x version. If the OS package supplies 1.x, consult the [containerd installation guide](https://github.com/containerd/containerd/blob/main/docs/getting-started.md) to choose a supported version appropriate to your OS.

Edit **/etc/containerd/config.toml** and ensure:
- The Kubernetes CRI integration is **enabled** (no CRI entry in disabled_plugins).
- The runc runtime uses **SystemdCgroup = true**.
- The configuration section matches the installed version:

~~~toml
# containerd 2.x (fragment only; edit the generated config)
[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runc.options]
  SystemdCgroup = true
~~~

For containerd 1.x the corresponding path is:

~~~toml
# containerd 1.x (fragment only)
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true
~~~

Do not blindly paste both fragments into the file. Keep the other required defaults from the generated configuration.

~~~bash
sudo systemctl enable --now containerd
sudo systemctl restart containerd
sudo systemctl status containerd --no-pager
~~~

Check that the container runtime uses a CRI-compatible socket (the usual containerd endpoint is **unix:///run/containerd/containerd.sock**). For details see [Kubernetes container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/).

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
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

kubeadm version
kubectl version --client
~~~

The APT commands above are for **new** nodes. When upgrading an existing cluster, follow the version-by-version [kubeadm upgrade procedure](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/) rather than jumping directly from an older release.

## 4. Initialize the control plane (control-plane node only)

Choose and verify the actual **private IP** of your control-plane node. Replace the placeholder below; do not run it literally.

~~~bash
sudo kubeadm init \
  --apiserver-advertise-address=<CONTROL_PLANE_PRIVATE_IP> \
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

## 5. Install Calico networking (control-plane node only)

For this v1.37 example we use the vendor's **Calico v3.33.0 operator installation**, which is tested against Kubernetes v1.37. Review the current [official Calico on-premises procedure](https://docs.tigera.io/calico/latest/getting-started/kubernetes/self-managed-onprem/onpremises) before deployment.

~~~bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/v3_projectcalico_org.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/tigera-operator.yaml

curl -fLO https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/custom-resources.yaml
~~~

**Important:** before applying the downloaded custom-resources.yaml, inspect its **Installation.spec.calicoNetwork.ipPools[].cidr**. Set it to **10.244.0.0/16** to match the Pod CIDR used in kubeadm init. The downloaded example may default to another subnet; do not apply it unchanged with a conflicting CIDR.

~~~bash
# Inspect and edit custom-resources.yaml so the pool matches 10.244.0.0/16.
grep -n "cidr:" custom-resources.yaml
# After editing and reviewing the file:
kubectl create -f custom-resources.yaml
kubectl get tigerastatus
kubectl get pods -A
~~~

Wait for the network components, CoreDNS and the node to become healthy. Do not install a second unrelated CNI on the same cluster.

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

## 8. Operational follow-ups

- **Upgrades:** review release notes, take backups, then upgrade kubeadm/control-plane and worker nodes in the documented sequence. Do not skip minor versions.
- **etcd:** keep regular backups and a tested recovery procedure; production HA setups need additional planning.
- **Dashboard:** avoid the old v2.4.0 Dashboard + permanent cluster-admin setup from the historical course. Choose a currently supported UI and grant least-privilege access.
- **Hardening:** implement appropriate RBAC, Pod Security Admission, NetworkPolicies, audit logging, image version pinning and a secure supply chain.
- **Automation:** a future repo improvement can add lab provisioning and CI validation, but neither is a prerequisite for the documentation update.

## Official references

- [Kubernetes release branches](https://kubernetes.io/releases/)
- [Installing kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [Container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
- [Operating etcd clusters](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [Calico on-premises installation](https://docs.tigera.io/calico/latest/getting-started/kubernetes/self-managed-onprem/onpremises)
- [Calico compatibility requirements](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)
