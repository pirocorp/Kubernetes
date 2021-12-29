# Basic Cluster Installation

Creation of simple yet working Kubernetes cluster.

[Requirements](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/#before-you-begin)

## Basic settings

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
