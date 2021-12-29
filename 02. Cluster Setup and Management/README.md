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

Will use Docker and will follow the steps from the official [documentation](https://docs.docker.com/engine/install/debian/):

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
