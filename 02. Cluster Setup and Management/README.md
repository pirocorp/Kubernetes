# Basic Cluster Operations

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

Creation of simple yet working Kubernetes cluster. Small cluster with three nodes. One will be part of the control plane and the rest will handle any work.

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

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.4.0/aio/deploy/recommended.yaml
```
Check the pods

```bash
kubectl get pods --all-namespaces
```

Try to access the Dashboard

```bash
kubectl proxy
```
Use this [URL](http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/) ```http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/```

We cannot log in as we do not have any valid way of doing it. Stop the Dashboard proxy with Ctrl + C. Create a file dashboard-admin-user.yml with the following content.

Create a file ```dashboard-admin-user.yml``` with the following content

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
```

Create one more file ```dashboard-admin-role.yml``` with the following content

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
```

Apply both files

```bash
kubectl apply -f dashboard-admin-user.yml
kubectl apply -f dashboard-admin-role.yml
```

Now, we can list the available secrets

```bash
kubectl -n kubernetes-dashboard get secret 
```

Identify the one with name ```admin-user-token-xxxxx``` and ask for its details

```bash
kubectl -n kubernetes-dashboard describe secret admin-user-token-wtpbm 
```

Copy the token field data. Start the proxy again with.

```bash
kubectl proxy
```
Navigate to the same [URL](http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/) ```http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/```

Use the token from earlier. Explore the Dashboard. Once done, close the browser tab and stop the proxy with Ctrl + C.

# Nodes management

The gallant, way to remove a node from the cluster for maintenance. We can first mark the node as not schedulable, so it won't receive any new work.

```bash
kubectl cordon node-3.k8s
```

Check nodes

```bash
kubectl get nodes
```

Then check how the pods are distributed

```bash
kubectl get pods -o wide
```

As the cordon action is included in the drain action, we may continue or uncordon it first.

```bash
kubectl uncordon node-3.k8s
```

Next, we can drain the node. This will remove all work from it

```bash
kubectl drain node-3.k8s --ignore-errors --ignore-daemonsets --delete-local-data –force
```

And check what happened

```bash
kubectl get nodes
kubectl get pods -o wide
```

Now, we can safely do our maintenance tasks and once done, and the node is up and running, we can inform the cluster.

```bash
kubectl uncordon node-3.k8s
```

And again, check what is going on

```bash
kubectl get nodes
kubectl get pods -o wide
```

Hm, it seems that the workload is unbalanced. We will accept it for now, but will come back to it in a later module.

# Etcd backup

Let's create a snapshot of the etcd database. Log on to the control plane node. Execute the following to create a snapshot.

```bash
ETCDCTL_API=3 etcdctl snapshot save /tmp/etcd-snapshot.db
```

If the **etcdctl** binary appears to be missing, then install it. *For example, on **Debian/Ubuntu**, we can use the following*

```bash
apt-get update
apt-get install etcd-client
```

Then repeat the backup try.

```bash
ETCDCTL_API=3 etcdctl snapshot save /tmp/etcd-snapshot.db
```

If we receive an error again and if reads **"Error:  rpc error: code = Unavailable desc = transport is closing"** then we must authenticate first. For this, we must change the above command to. 

```bash
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=<trusted-ca-file> --cert=<cert-file> --key=<key-file> \
  snapshot save /tmp/etcd-snapshot.db
```
Where **trusted-ca-file**, **cert-file** and **key-file** can be obtained from the description of the **etcd** pod. We can get them from.

```bash
cat /etc/kubernetes/manifests/etcd.yaml
```

They are:
- ```--trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt```
- ```--cert-file=/etc/kubernetes/pki/etcd/server.crt```
- ```--key-file=/etc/kubernetes/pki/etcd/server.key```

Then, the final backup command becomes:

```bash
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-snapshot.db
```

Now, everything should work as expected. Check the snapshot.

```bash
ls -al /tmp/etcd*
```

**Etcd** holds the state of the cluster. If a change occurs, can bring everything back as it was at the time of the snapshot.

# Etcd restore

Restore the database using the snapshot made earlier.

```bash
ETCDCTL_API=3 etcdctl snapshot restore /tmp/etcd-snapshot.db --data-dir /var/lib/etcd-restore
```

Next, we must instruct the **etcd** to use the restored data.

Edit the **/etc/kubernetes/manifests/etcd.yaml** file and change the **etcd-data** volume to point to the new place (**/var/lib/etcd-restore**).

Save and close the file. Wait a while for the changes to take place.

Check again the pods.

```bash
kubectl get pods
```

The pods should be like they was in saved state.

# Upgrade a cluster

We will refer to these sources:

- [Cluster Upgrade](https://kubernetes.io/docs/tasks/administer-cluster/cluster-upgrade/)
- [Kubeadm Upgrade](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)

## Upgrade Control Plane nodes 

Will do one node at a time. Check the latest version.

```bash
apt update
apt-cache madison kubeadm
```

Have only one control plane node, so don’t have to choose. At the moment, the latest version is 1.22.3-00 so let’s use it.

```bash
apt-get update && \
apt-get install -y --allow-change-held-packages kubeadm=1.22.3-00
```

Check that the new version is here

```bash
kubeadm version
```

Ask for the upgrade plan

```bash
kubeadm upgrade plan
```

Should we see any errors (**not in production**), we may use the following

```bash
kubeadm upgrade plan --ignore-preflight-errors=true
```

Then initiate the actual upgrade

```bash
kubeadm upgrade apply v1.22.3
```

When asked for confirmation, do it

Nay need to upgrade CNI provider plugin (not in this case), so must consult with its documentation
**If had other control plane nodes, then must execute the following command on each one of them:**

```bash
kubeadm upgrade node
```

Drain the node

```bash
kubectl drain node-1.k8s --ignore-daemonsets
```

Or if we see any errors that the process cannot be finished, execute this

```bash
kubectl drain node-1.k8s --ignore-errors --ignore-daemonsets --delete-local-data --force
```

Upgrade the **kubelet** and **kubectl**. As at the moment, the latest version is 1.22.3-00, will execute this.

```bash
apt-get update && \
apt-get install -y --allow-change-held-packages kubelet=1.22.3-00 kubectl=1.22.3-00
```

Restart the **kubelet** service

```bash
systemctl daemon-reload
systemctl restart kubelet
```

Uncordon the node

```bash
kubectl uncordon node-1.k8s
```

Check the cluster status

```bash
kubectl get nodes
```

## Upgrade worker nodes

Will do one node at a time.

As at the moment, the latest version is **1.22.3-00**, we will execute.

```bash
apt-get update && \
apt-get install -y --allow-change-held-packages kubeadm=1.22.3-00
```

Then the upgrade

```bash
kubeadm upgrade node
```

Drain the node (from the control plane node)

```bash
kubectl drain node-2.k8s --ignore-daemonsets
```

Or if we see an error, execute

```bash
kubectl drain node-2.k8s --ignore-errors --ignore-daemonsets --delete-local-data --force
```

Return on the node. Upgrade the **kubelet** and **kubectl**.

```bash
apt-get update && \
apt-get install -y --allow-change-held-packages kubelet=1.22.3-00 kubectl=1.22.3-00
```

Then, restart the **kubelet** service.

```bash
systemctl daemon-reload
systemctl restart kubelet
```

And uncordon the node (from the control plane node).

```bash
kubectl uncordon node-2.k8s
```

While still on the control plane node, check the cluster status.

```bash
kubectl get nodes
```

Repeat the procedure on the other node(s). Cluster is upgraded 😊.

# Highly-available Cluster

Need three virtual machines for control plane nodes and one or more (in this case 3) for nodes members of the cluster. In addition, we will need a machine to act as a load balancer. The following sources are used:

- [Highly Available Control Plane](https://kubernetes.io/docs/tasks/administer-cluster/highly-available-control-plane/)
- [High Availability](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
- [HA Topology](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-topology/)
- [HA Considerations](https://github.com/kubernetes/kubeadm/blob/main/docs/ha-considerations.md)
