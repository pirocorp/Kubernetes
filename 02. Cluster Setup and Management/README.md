# Basic Cluster Installation

creation of simple yet working Kubernetes cluster

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

