# Basic Cluster Installation

Creation of simple yet working Kubernetes cluster.

[Requirements](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/#before-you-begin)

# Debian 10 Based Kubernetes Template

Let’s assume that we have a virtual machine with **Debian 10** installed (basic / minimal). We will use it to prepare our golden image, that will be used for the creation of the cluster. Log on to the machine (we will assume that we are working with the **root** user)

Check if the **br_netfilter** module is loaded

```bash
lsmod | grep br_netfilter
```

If not, try to load it

```bash
modprobe br_netfilter
```

Then prepare a configuration file to load it on boot

```bash
cat << EOF | tee /etc/modules-load.d/k8s.conf
br_netfilter
EOF
```

Adjust a few more network-related settings

```bash
cat << EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
```

And then apply them

```bash
sysctl --system
```

Check which variant of **iptables** is in use

```bash
update-alternatives --query iptables
```

And switch it to the legacy version

```bash
update-alternatives --set iptables /usr/sbin/iptables-legacy
```
As a final general step, turn off the SWAP both for the session and in general

```bash
swapoff -a
sed -i '/swap/ s/^/#/' /etc/fstab
```

## Container runtime

Will use Docker and will follow the steps from the official [documentation](https://docs.docker.com/engine/install/debian/).

Update the repositories information

```bash
apt-get update
```

And install the required packages

```bash
apt-get install ca-certificates curl gnupg lsb-release
```

Download and install the key

```bash
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

Add the repository

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Install the required packages

```bash
apt-get update
apt-get install docker-ce docker-ce-cli containerd.io
```

## Container runtime configuration

Will refer to this [source](https://kubernetes.io/docs/setup/production-environment/container-runtimes/).

Create the configuration folder if does not exist

```bash
mkdir /etc/docker
```

Then create the configuration file with the following content

```bash
cat <<EOF | tee /etc/docker/daemon.json
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF
```

Reload and restart the service

```bash
systemctl enable docker
systemctl daemon-reload
systemctl restart docker
```

## Kubernetes components

Will refer to this [source](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/#installing-kubeadm-kubelet-and-kubectl). 

Install any packages that may be missing.

```bash
apt-get update
apt-get install -y apt-transport-https ca-certificates curl
```

Download and install the key

```bash
curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
```

Add the repository

```bash
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list
```

Update repositories information.

```bash
apt-get update
```

Check available versions of the packages.

```bash
apt-cache madison kubelet
```

Should we want to install the latest version, we may use (skip it for now).

```bash
apt-get install -y kubelet kubeadm kubectl
```

For a particular version we should use (execute this one)

```bash
apt-get install kubelet=1.21.6-00 kubeadm=1.21.6-00 kubectl=1.21.6-00
```

Then exclude the packages from being updated

```bash
apt-mark hold kubelet kubeadm kubectl
```

Turn off the machine

```bash
shutdown now
```

Using the virtualization solution techniques create a template of this machine or its virtual disk

# Cluster creation

Small cluster with three nodes. One will be part of the control plane and the rest will handle any work.

## Virtual infrastructure

Using the virtualization solution techniques create three identical virtual machines each with:
-	2 vCPU
-	2 GB+ RAM

Connect them in a way that will allow for Internet access and easier communication with and between them. External/bridged mode will be the best option
During the manual, will use 192.168.0.0/24. You should adjust the commands to match your setup.

## Preparation

Start all nodes

Log on the first one and set
-	Its IP address, for example 192.168.0.53/24
-	Ifs FQDN, for example node-1.k8s
-	Its /etc/hosts file:


edit /etc/network/interfaces with this values for example

iface eth0 inet static
        address 192.168.0.53/24
        gateway 192.168.0.1
        dns-nameservers 8.8.8.8

```bash
hostnamectl set-hostname node-1.k8s
```

```bash
echo "192.168.0.53  node-1.k8s  node-1" | tee -a /etc/hosts
echo "192.168.0.54  node-2.k8s  node-2" | tee -a /etc/hosts
echo "192.168.0.55  node-3.k8s  node-3" | tee -a /etc/hosts
```

Repeat the above steps on the other two machines.

## Cluster initialization (node-1)

Initialize the cluster with

```bash
kubeadm init --apiserver-advertise-address=192.168.0.53 --pod-network-cidr 10.244.0.0/16
```

Installation will finish relatively quickly. Copy somewhere the join command. To start using our cluster, we must execute the following.

```bash
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
```

Let's check our cluster nodes (just one so far)

```bash
kubectl get nodes
```

Note that it appears as **not ready**
Check the pods as well

```bash
kubectl get pods -n kube-system
```

Hm, most of the pods are operational, but there is one pair that is not (CoreDNS)
Let's check why the node is not ready

```bash
kubectl describe node node-1
```

Scroll to top and look for **Ready** and **KubeletNotReady** words.
It appears that there isn't any (POD) network plugin installed

We can check [here](https://kubernetes.io/docs/concepts/cluster-administration/addons/).
And get further details form [here](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/#pod-network).
Check here for a list of plugins [here](https://kubernetes.io/docs/concepts/cluster-administration/networking/#how-to-implement-the-kubernetes-networking-model).

It appears, that by installing a pod network plugin, we will solve both issues. Let's install a POD network plugin. For this demo, will use the [Flannel](https://github.com/flannel-io/flannel#flannel) plugin.

Install it

```bash
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```

Watch the progress with

```bash
kubectl get pods --all-namespaces -w
```

After a while both Flannel and CoreDNS will be fully operational
Press Ctrl + C to stop the monitoring
Check again the status of the node

```bash
kubectl get nodes
```

It should be operational and ready as well.

## Join nodes (node-2 and node-3)

Log on to node-2
Remember the join command that we copied earlier, now it is the time to use it
It should have the following structure: 

```bash
kubeadm join [IP]:6443 --token [TOKEN] --discovery-token-ca-cert-hash sha256:[HASH]
```

Join the node to the cluster (yours may be different).

```bash
kubeadm join 192.168.81.211:6443 --token 8qu2va.le6ndhtt9mdpbmow \
        --discovery-token-ca-cert-hash sha256:9d2642aeda7a1c210b26db639bbf0272e4bfa59b895904162b948c055cb39402
```

Repeat the same on node-3

Return on node-1
And check nodes

```bash
kubectl get nodes
```

Show cluster information

```bash
kubectl cluster-info
```

## Control our new cluster from our host.

- Close the session to node-1.
- Navigate to our home folder (on our host) and then to the **.kube** folder
- Copy the configuration file (use your actual master/node-1 IP address here)

```bash
scp root@192.168.0.53:/etc/kubernetes/admin.conf .
```

Backup the existing configuration if any

```bash
mv ~\.kube\config ~\.kube\config.bak
```

Make the copied file the active configuration

```bash
mv .\admin.conf ~\.kube\config
```

Ask for cluster information but this time from the host

```bash
kubectl cluster-info
```

Check version of our **kubectl**

```bash
kubectl version --client
```

And compare it with the one of the cluster

```bash
kubectl version
```

Note: +/-1 minor version is acceptable

# Dashboard Installation

Check the latest version and any installation instructions [here](https://github.com/kubernetes/dashboard)

Deploy the **Dashboard**

```yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.4.0/aio/deploy/recommended.yaml
```
Check the pods

```yaml
kubectl get pods --all-namespaces
```

Try to access the Dashboard

```yaml
kubectl proxy
```
Use this [URL](http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/) ```http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/```

We cannot log in as we do not have any valid way of doing it. Stop the Dashboard proxy with Ctrl + C. Create a file dashboard-admin-user.yml with the following content.


