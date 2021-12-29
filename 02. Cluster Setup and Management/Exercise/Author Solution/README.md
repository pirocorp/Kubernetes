# Task 1

Create a two node **Minikube**-based **Kubernetes** cluster and deploy a simple app on it. For example, shekeriev/k8s-oracle from the previous HW.

Solution:

To create a **minikube**-based two node **Kubernetes** cluster we must execute the following command.

Adjust the **--driver** option to match your situation. You can select one of the following **virtualbox**, **vmwarefusion**, **hyperv**, **vmware**, **docker**, or **ssh**. If not specified, the most suitable option will be auto detected and selected.

```bash
minikube start --driver=hyperv --nodes=2
```

Now, that we have our cluster, we can check if it is reachable

```bash
kubectl cluster-info
kubectl get nodes -o wide
```

Next, we can deploy a simple application on it (using the files from the previous HW)

```bash
kubectl apply -f homework.yaml
```

Then check the deployed resources
```bash
kubectl get pods,svc -n homework -o wide
```

And try to reach the application on ```http://<minikube-ip>:32000```
**Minikube IP** address can be retrieved with

```bash
minikube ip
```
Or directly the service **URL** with

```bash
minikube service list
```
Once done, clean up the application with

```bash
kubectl delete -f homework.yaml
```

And then the **minikube** cluster with

```bash
minikube delete
```

# Task 2

Create a three node **KIND**-based **Kubernetes** cluster and deploy a simple app on it. For example, ```shekeriev/k8s-oracle``` from the previous HW 

Solution:

kind-cluster.yaml

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 32000
    hostPort: 8080
- role: worker
- role: worker
```

Then start the cluster with

```bash
kind create cluster --name hw --config kind-cluster.yaml
```

Finally, switch the context to the new cluster

```bash
kubectl config use-context kind-hw
```

Ask for some information about the cluster

```bash
kubectl cluster-info
kubectl get nodes -o wide
```

Then spin up the application

```bash
kubectl apply -f homework.yaml
```

And check its components

```bash
kubectl get pods,svc -n homework -o wide
```

Try to reach the application on ```http://localhost:8080```
Once done exploring, remove the application with

```bash
kubectl delete -f homework.yaml
```

And finally, remove the cluster with

```bash
kind delete cluster --name hw
```

# Task 3

Create a three-node vanilla **Kubernetes** cluster in a virtualization solution of your choice. You are free to use **Debian** or any other (from the same or another family) **Linux** distribution. Use **Vagrant** or a similar tool to do it in as much automated fashion as possible.

Solution:

Please note, that this solution requires access to a supported local virtualization solution. VirtualBox is the one selected for this. Also, you must have Vagrant installed.

```Vagrantfile
# -*- mode: ruby -*-
# vi: set ft=ruby :

$common = <<SCRIPT

# Set it to a particular version (for example, 1.21.6-00) or latest (to install the latest available)
# For example, K8SVER='1.21.6-00' or K8SVER='latest'
K8SVER='1.21.6-00'
echo $K8SVER > /tmp/k8s-version

echo '* Load br_netfilter on boot ...'
modprobe br_netfilter
echo br_netfilter >> /etc/modules-load.d/k8s.conf

echo '* Adjust network-related settings and apply them ...'
cat << EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sysctl --system

echo '* Install iptables and switch it iptables to legacy version ...'
apt-get update && apt-get install -y iptables
update-alternatives --set iptables /usr/sbin/iptables-legacy

echo '* Turn off the swap ...'
swapoff -a
sed -i '/swap/ s/^/#/' /etc/fstab

echo '* Add hosts ...'
echo '192.168.99.101 node1.k8s.lab node1' >> /etc/hosts
echo '192.168.99.102 node2.k8s.lab node2' >> /etc/hosts
echo '192.168.99.103 node3.k8s.lab node3' >> /etc/hosts

echo '* Install other required packages ...'
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

echo '* Download and install the Docker repository key ...'
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo '* Add the Docker repository ...'
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

echo '* Install the required container runtime packages ...'
apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io

echo '* Adjust container runtime configuration ...'
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
systemctl daemon-reload
systemctl enable --now docker
systemctl restart docker

echo '* Add vagrant user to docker group ...'
usermod -aG docker vagrant

echo '* Download and install the Kubernetes repository key ...'
curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg

echo '* Add the Kubernetes repository ...'
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list

echo "* Install the selected ($K8SVER) version ..."
apt-get update
if [ $K8SVER != 'latest' ]; then 
  apt-get install -y kubelet=$K8SVER kubeadm=$K8SVER kubectl=$K8SVER
else
  apt-get install -y kubelet kubeadm kubectl
fi

echo '* Exclude the Kubernetes packages from being updated ...'
apt-mark hold kubelet kubeadm kubectl

SCRIPT


$k8scp = <<SCRIPT 

K8SVER=$(cut -d - -f 1 /tmp/k8s-version)

echo "* Initialize Kubernetes cluster ..."
if [ $K8SVER != 'latest' ]; then
  kubeadm init --kubernetes-version=$K8SVER --apiserver-advertise-address=192.168.99.101 --pod-network-cidr 10.244.0.0/16 --token abcdef.0123456789abcdef
else 
  kubeadm init --apiserver-advertise-address=192.168.99.101 --pod-network-cidr 10.244.0.0/16 --token abcdef.0123456789abcdef
fi

echo "* Save the hash to a file ..."
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //' > /vagrant/hash.txt

echo "* Copy configuration for root ..."
mkdir -p /root/.kube
cp -i /etc/kubernetes/admin.conf /root/.kube/config
chown -R root:root /root/.kube

echo "* Copy configuration for vagrant ..."
mkdir -p /home/vagrant/.kube
cp -i /etc/kubernetes/admin.conf /home/vagrant/.kube/config
chown -R vagrant:vagrant /home/vagrant/.kube

# Pod Network plugin - comment/uncomment one of the following blocks
# Currently set to Calico

# echo "* Install Pod Network plugin (Flannel) ..."
# wget -q https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml -O /tmp/kube-flannel.yaml
# sed -i '/--kube-subnet-mgr/ a CHANGEME' /tmp/kube-flannel.yaml
# sed -i "s/CHANGEME/        - --iface=$(ip a | grep 192.168.99.101 | tr -s ' ' | cut -d ' ' -f 8)/" /tmp/kube-flannel.yaml 
# kubectl apply -f /tmp/kube-flannel.yaml

echo "* Install Pod Network plugin (Calico) ..."
kubectl create -f https://docs.projectcalico.org/manifests/tigera-operator.yaml
wget -q https://docs.projectcalico.org/manifests/custom-resources.yaml -O /tmp/custom-resources.yaml
sed -i 's/192.168.0.0/10.244.0.0/g' /tmp/custom-resources.yaml
kubectl create -f /tmp/custom-resources.yaml

SCRIPT

$k8swk = <<SCRIPT

echo "* Join the worker node ..."
kubeadm join 192.168.99.101:6443 --token abcdef.0123456789abcdef --discovery-token-ca-cert-hash sha256:`cat /vagrant/hash.txt`

SCRIPT

Vagrant.configure(2) do |config|
    
  config.ssh.insert_key = false

  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
    v.cpus = 2
  end

  config.vm.define "node1" do |node1|
    node1.vm.box = "shekeriev/debian-10"
    node1.vm.hostname = "node1.k8s.lab"
    node1.vm.network "private_network", ip: "192.168.99.101"
    node1.vm.synced_folder "vagrant/", "/vagrant"
    node1.vm.provision "shell", inline: $common
    node1.vm.provision "shell", inline: $k8scp
  end

  config.vm.define "node2" do |node2|
    node2.vm.box = "shekeriev/debian-10"
    node2.vm.hostname = "node2.k8s.lab"
    node2.vm.network "private_network", ip: "192.168.99.102"
    node2.vm.synced_folder "vagrant/", "/vagrant"
    node2.vm.provision "shell", inline: $common
    node2.vm.provision "shell", inline: $k8swk
  end

  config.vm.define "node3" do |node3|
    node3.vm.box = "shekeriev/debian-10"
    node3.vm.hostname = "node3.k8s.lab"
    node3.vm.network "private_network", ip: "192.168.99.103"
    node3.vm.synced_folder "vagrant/", "/vagrant"
    node3.vm.provision "shell", inline: $common
    node3.vm.provision "shell", inline: $k8swk
  end
end
```
