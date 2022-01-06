# Security and Policies

# Default Cluster User

Log on to the control plane node. Check the cluster configuration file.

```bash
cat ~/.kube/config
```

We can see that there are several notable sections – clusters, contexts, current-context, and users. Clusters section contains currently registered clusters with their certificate authority data, control plane and name. Contexts section contains list of currently registered contexts that combine clusters with users. Current context specifies against which context our commands will be fired by default and without the need to explicitly specifying it. Users section contains the list of registered users with their name, certificate and key. Should we want to control more than one cluster or interact as different users, then we must alter this file or use another copy.

# Additional Cluster Users

Utilizing the option for using X.509 client certificates for cluster authentication.

Create the **pirocorp** OS user

```bash
useradd -m -s /bin/bash pirocorp
```
Switch to its home folder

```bash
cd /home/pirocorp
```

Create a folder for the certificate related files and change to it

```bash
mkdir .certs && cd .certs
```

Create a private key

```bash
openssl genrsa -out pirocorp.key 2048
```

Create a certificate signing request

```bash
openssl req -new -key pirocorp.key -out pirocorp.csr -subj "/CN=pirocorp"
```

Sign the **CSR** with the **Kubernetes CA** certificate

```bash
openssl x509 -req -in pirocorp.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out pirocorp.crt -days 365
```

Return to the home folder. Create the user in **Kubernetes**.

```bash
kubectl config set-credentials pirocorp --client-certificate=/home/pirocorp/.certs/pirocorp.crt --client-key=/home/pirocorp/.certs/pirocorp.key
```

Create context for the user as well

```bash
kubectl config set-context pirocorp-context --cluster=kubernetes --user=pirocorp
```

Create a folder to store the user configuration

```bash
mkdir /home/pirocorp/.kube
```

And create a file config there with the following content (most of it is skipped but borrowed from **/etc/kubernetes/admin.conf**). Everithumg up to ```contexts``` is borrowed.

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM1ekNDQWMrZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJeE1URXhNekUwTlRrME1Wb1hEVE14TVRFeE1URTBOVGswTVZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTkIwClIvUi9lYkJkVVRteUxuMVBzb2tLQ2JaQU16TXBKMHRKS1prZlVxb0Jqa0dRVC9FUmVPK1krOS81MHZKTTNBUnoKTGMwR21MTGROVXdzeXFTb0xCUW5zWUVGaHBKNHhGSkhOU2hRb2EwYXdoZ3dWUUdwNEJaeHhNVE8zWkJIM2U3WQorZzZ1dlhSaFNmMWNNNURsRmtFcjhwTVFBS0hQdVFFMnRscWZBSzRQT0t3OWk5dHZ4SmpJbE1oNmVSQmRJOXFOCmh0c3dta0F0NFQ4MThPZVdOeXdGRWdyQjF0R1MwbnhDWENmMlZDbFJkejZEcVdRa1lGUElhN2NmTWlvMXh3MWQKdXNWekhEMW1rSDB2L1hkek1asdZ4Q3AwYTBTODZxdHA0aGo0d2tnb3RsSHhmeW14YWpmRUhiKzc5UWlFSFpJeQpFN0NYdlRyNXQ0Tlh1RXVKekZzQ0F3RUFBYU5DTUVBd0RnWURWUjBQQVFIL0JBUURBZ0trasdasdExVWRFd0VCCi93UUZNQU1CQWY4d0hRWURWUjBPQkJZRUZEazQ5Z094YXpoT2J0NUxOOWlJem9OTndkM3FNQTBHQ1NxR1NJYjMKRFFFQkN3VUFBNElCQVFDT0Z1eEd5SkgyVHNDaTkvN1ROTFNyVE1CNDU4c3JUdzB5d3d3WEpSYm5PNFQ2eDROdwpjOGF5ZUxybjFYQ1pSMGc1RVZTVHIrT3FqR0ZLM1lmRko0YjZ6V21zZ0ZKZm1JSStMWUZSMi9UaWhYZkI5cnNzCjZWb3lrdVdjbVVOZGNrYkhzSnk3MVFhS0FxQnFiSzdub2FEUlJiaHI4ZVpvTFpwOHRYa011cko4VzFIeFY1ODcKeml0REFCZW9wRG4wYStmVk9Vam9NYWJzNnRPTGJ6QXhIVGdpdlJLMk5HcURwQUUvRGRpdGtKcjk4Q0ZFK3U1LwpWMzJhekthUmJuS1N1aGFiWHhLSjlmM29LY2tYQWgyM3ZjaHNkb2ZPdGxRVHYybk9HMGUxcjc3emowRWk4SDl4CkZMV3hiajU0QkNGNzNPbWlVa2ZoWDJoV0RWYVpQNUtpV2MzWQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    server: https://192.168.0.53:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: pirocorp
  name: pirocorp-context
current-context: pirocorp-context
kind: Config
preferences: {}
users:
- name: pirocorp
  user:
    client-certificate: /home/pirocorp/.certs/pirocorp.crt
    client-key: /home/pirocorp/.certs/pirocorp.key
```

Save and close the file.

*Note that in the above example we are using **client-certificate** and **client-key** and not **client-certificate-data** and **client-key-data** as with the **admin.conf** file. We may go with the second pair, but then we must first encode using **base64** the content of both files and then use the result here.*


Change the ownership of the files

```bash
chown -R pirocorp: /home/pirocorp/
```

# Bind Cluster User to Role (RoleBinding)

- First rolebinding allows ```pirocorp``` to ```edit``` objects in ```demo-prod``` namespace.
- Second rolebinding allows ```pirocorp``` to ```view``` objects in ```demo-dev``` namespace.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: demo-prod-edit
  namespace: demo-prod
# Subcects (multiple) for which rolebinding is applied.
subjects:
- kind: User
  name: pirocorp
  apiGroup: rbac.authorization.k8s.io
# Role which will be bound to subjects
roleRef:
  # Role type (resource type) 
  kind: ClusterRole
  name: edit
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: demo-dev-view
  namespace: demo-dev
subjects:
- kind: User
  name: pirocorp
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

Save and close the file and push it to the cluster.

```bash
kubectl apply -f role-bindings.yaml
```

# Permission Check

Check for current user or ```as``` other user.

```bash
kubectl auth can-i [command] [type] [flags]
kubectl auth can-i create pods
kubectl auth can-i create pods -n demo-prod
kubectl auth can-i create pods -n demo-prod --as pirocorp
```

Furthermore, instead of asking for individual actions, we can ask for everything one can do in a namespace

```bash
kubectl auth can-i --list --namespace demo-dev --as pirocorp
```

# Extend Service Account Permitions

The **default** service account doesn’t have any permissions granted by default.

![image](https://user-images.githubusercontent.com/34960418/147775473-ff572e21-4805-48a6-aa44-7156db592829.png)

Create Service Account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: demo-sa
  namespace: rbac-ns
```

Save and close the file. Send the **Service Account** to the cluster.

```bash
kubectl apply -f service-account.yaml
```

Create Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
# Metadata specifies role name and in which namespace role is defined
metadata:
  name: demo-role
  namespace: rbac-ns
# Role can have multiple resources (resource types) with different access rights (verbs)
rules:
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
  - list
  - create
  - delete
- apiGroups:
  - ""
  resources:
  - services
  verbs:
  - get
  - list
  - create
```

Save and close the file. Send the **Role** to the cluster.

```bash
kubectl apply -f role.yaml
```

Then create a **RoleBinding** for the Service Account and Role.

```bash
kubectl create rolebinding demo-role-binding --role=demo-role --serviceaccount=rbac-ns:demo-sa --namespace=rbac-ns
```

or send this yaml to cluster

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
# Specifies binding name and namespace
metadata:
  name: demo-role-binding
  namespace: rbac-ns
# Subjects (objects) which will be bound to the role
subjects:
- kind: ServiceAccount
  name: demo-sa
  namespace: rbac-ns
# Role to which objects are bound
roleRef:
  kind: Role
  name: demo-role
  apiGroup: rbac.authorization.k8s.io
```

Check that it got some of the permissions that we wanted to grant

```bash
kubectl auth can-i get pods --namespace rbac-ns --as system:serviceaccount:rbac-ns:demo-sa
kubectl auth can-i get services --namespace rbac-ns --as system:serviceaccount:rbac-ns:demo-sa
kubectl auth can-i delete pods --namespace rbac-ns --as system:serviceaccount:rbac-ns:demo-sa
kubectl auth can-i delete services --namespace rbac-ns --as system:serviceaccount:rbac-ns:demo-sa
```

Now, let’s start a new pod that will use this service account and check from there

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: demo-pod
  namespace: rbac-ns
spec:
  containers:
  - image: shekeriev/k8s-oracle
    name: demo-pod
  # Explisit specification of service account for this pod
  serviceAccount: demo-sa
  serviceAccountName: demo-sa
```

Save and close the file. Send the **Pod** to the cluster.

```bash
kubectl apply -f pod.yaml
```

Now, open a session to the pod


```bash
kubectl exec -it demo-pod -n rbac-ns -- bash
```

Install the missing curl command

```bash
apt-get update && apt-get install -y curl
```

Prepare a set of environment variables

```bash
APISERVER=https://kubernetes.default.svc
SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount
NAMESPACE=$(cat ${SERVICEACCOUNT}/namespace)
TOKEN=$(cat ${SERVICEACCOUNT}/token)
CACERT=${SERVICEACCOUNT}/ca.crt
```

Let’s check for the pods

```bash
curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" \
-X GET ${APISERVER}/api/v1/namespaces/rbac-ns/pods
```

Let’s check for the services

```bash
curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" \
-X GET ${APISERVER}/api/v1/namespaces/rbac-ns/services
```

# Requests and Limits

When you specify a **Pod**, you can optionally specify how much of each resource a **container** needs. The most common resources to specify are CPU and memory (RAM); there are others.

When you specify the resource **request** for containers in a Pod, the kube-scheduler uses this information to decide which node to place the Pod on. When you specify a resource **limit** for a container, the kubelet enforces those limits so that the running container is not allowed to use more of that resource than the limit you set. The kubelet also **reserves** at least the request amount of that system resource specifically for that container to use.

If the node where a Pod is running has enough of a resource available, it's possible (and allowed) for a container to use more resource than its **request** for that resource specifies. However, a container is not allowed to use more than its resource **limit**.

*Note: If a container specifies its own memory limit, but does not specify a memory request, Kubernetes automatically assigns a memory request that matches the limit. Similarly, if a container specifies its own CPU limit, but does not specify a CPU request, Kubernetes automatically assigns a CPU request that matches the limit.*

## Check the available resources on the nodes

Focus on the sections **Capacity**, **Allocatable**, **Non-terminated Pods**, and **Allocated resources**

![image](https://user-images.githubusercontent.com/34960418/147819663-cff90f05-477c-40ea-86eb-8ae5d03e5812.png)

```bash
kubectl describe nodes
```

## Pod with Requests and Limits

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-3a
  namespace: reslim
spec:
  containers:
  - image: busybox
    command: ["dd", "if=/dev/zero", "of=/dev/null", "bs=64M"]
    name: main
    # Manage resource on container level
    resources:
      # Resources reserved for container in order for container to run. If there are no such free (unreserved) resources the container won't start.
      requests:
        cpu: 250m
        memory: 16Mi
      # limits the container how many resources it can consume. If pod overconsume resources (ex. Memory leak in app) kubernetes will kill it and start a new instance.
      limits:
        cpu: 500m
        memory: 128Mi
```

# Limit Ranges

- Enforce minimum and maximum compute resources usage per Pod or Container in a namespace.
- Enforce minimum and maximum storage request per PersistentVolumeClaim in a namespace.
- Enforce a ratio between request and limit for a resource in a namespace.
- Set default request/limit for compute resources in a namespace and automatically inject them to Containers at runtime.
- The LimitRanger admission controller enforces defaults and limits for all Pods and Containers that do not set compute resource requirements and tracks usage to ensure it does not exceed resource minimum, maximum and ratio defined in any LimitRange present in the namespace.
- LimitRange validations occurs only at Pod Admission stage, not on Running Pods.

LimitRangeis for managing constraints at a pod and container level within the project. LimitRanges can specify and requests (reservations).

- defaultRequest — is **how much CPU/Memory will be reserved** to Container, if it doesn't specify it's own value.
- default — is **default limit** for amount of CPU/Memory for Container, if it doesn't specify it's own value
- max — is maximum limit for amount of CPU/Memory that Container/Pod can ask for. I.e. it **can't set it's own limit more than that**
- min — is minimum limit amount of CPU/Memory that Container/Pod can ask for. I.e. it **can't set it's own limit less than that**

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: limits
  namespace: reslim
spec:
  limits:
  # limits on pod level
  - type: Pod
    max:
      cpu: 1
      memory: 1Gi
    min:
      cpu: 100m
      memory: 16Mi
  # limist on container level
  - type: Container
    defaultRequest:
      cpu: 100m
      memory: 16Mi
    default:
      cpu: 200m
      memory: 32Mi
    max:
      cpu: 1
      memory: 1Gi
    min:
      cpu: 100m
      memory: 16Mi
```

# Resource Quotas

Resource quotas are a tool for administrators to address the need of sharing cluster resources between teams of users. They are defined by the **ResourceQuota** object. Provide constraints that limit **aggregate resource consumption per namespace**. Limit the **quantity of objects** that can be created in a namespace by type. Limit the **total amount of compute resources** that may be consumed by resources.

ResourceQuota is for limiting the total resource consumption of a namespace.

An individual Pod or Container that requests resources outside of these LimitRange constraints will be rejected, whereas a ResourceQuota only applies to all of the namespace/project's objects in aggregate.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quota
  namespace: reslim
spec:
  hard:
    pods: 3
    requests.cpu: 1
    requests.memory: 1Gi
    limits.cpu: 2
    limits.memory: 2Gi
```

# [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)

Make sure that our cluster is using a **Network plugin** that supports **Network Policies**. Partial list of them can be found [here](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/) (**Flannel** plugin does not support network policies).

## Instalation of [Antrea](https://github.com/antrea-io/antrea/blob/main/docs/getting-started.md) plugin

Assuming that cluster is created with 

```bash
kubeadm init --apiserver-advertise-address=<cp-address> --pod-network-cidr 172.16.0.0/16
```

Then the **Antrea** plugin can be installed with

```bash
kubectl apply -f https://raw.githubusercontent.com/antrea-io/antrea/main/build/yamls/antrea.yml
```


## Instalation of [Calico](https://docs.projectcalico.org/getting-started/kubernetes/quickstart )


Assuming that cluster is created with 

```bash
kubeadm init --apiserver-advertise-address=<cp-address> --pod-network-cidr 172.16.0.0/16
```

Then the Calico plugin can be installed with

```bash
kubectl apply -f https://docs.projectcalico.org/manifests/tigera-operator.yaml
```

Then download the custom resources manifest

```bash
curl https://docs.projectcalico.org/manifests/custom-resources.yaml -O
```

Adjust the configuration if needed by editing the **custom-resources.yaml** manifest (especially if you used something different than 192.168.0.0/16 for pod network). Then apply it.

```bash
kubectl apply -f custom-resources.yaml
```

## Instalation of [Weave Net](https://github.com/weaveworks/weave)

Assuming that we created our cluster with

```bash
kubeadm init --apiserver-advertise-address=<cp-address> --pod-network-cidr 10.32.0.0/12
```

Then the Weave Net plugin can be installed with

```bash
kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"
```

Should we want to change the configuration, for example the pod network addresses, we ca change it to

```bash
kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d 'n')&env.IPALLOC_RANGE=10.200.0.0/16"
```

## Network policy example

Network policies are defined on namespace level

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: access-oracle
  namespace: basicnp
spec:
  # which pods will be affected by this policy in the namespace.
  podSelector:
    matchLabels:
      app: oracle
  # policy type (ingress - incomming communication, egress outgoing communication)
  ingress:
  # in egress policy section will be `to` (not from)
  - from:
    - podSelector:
        matchLabels:
          access: "true"
      namespaceSelector: {}
  # ports:
  # - protocol: TCP
  #   port: 6379  
```

***Note***: NetworkPolicy includes a ```podSelector``` which selects the grouping of Pods to which the policy applies. You can see this policy selects Pods with the label ```app=oracle```. An empty ```podSelector``` selects all pods in the namespace.

## Behavior of ```to``` and ```from``` selectors

There are four kinds of selectors that can be specified in an ```ingress``` ```from``` section or ```egress``` ```to``` section:

***podSelector*** - This selects particular Pods in the same namespace as the NetworkPolicy which should be allowed as ingress sources or egress destinations.

***namespaceSelector*** - This selects particular namespaces for which all Pods should be allowed as ingress sources or egress destinations.

***namespaceSelector*** and ***podSelector*** - A single ```to```/```from``` entry that specifies both ```namespaceSelector``` and ```podSelector``` selects particular Pods within particular namespaces. Be careful to use correct YAML syntax.

Example: 

Contains a single from element allowing connections ```from``` Pods with the label ```role=client``` in namespaces with the label ```user=alice```

```yaml
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          user: alice
      podSelector:
        matchLabels:
          role: client
```

Contains two elements in the ```from``` array, and allows connections from Pods in the local Namespace with the label ```role=client```, or from any Pod in any namespace with the label ```user=alice```.

```yaml
ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          user: alice
    - podSelector:
        matchLabels:
          role: client
```

When in doubt, use kubectl describe to see how Kubernetes has interpreted the policy.

## Default policies

By default, if no policies exist in a namespace, then all ingress and egress traffic is allowed to and from pods in that namespace. The following examples let you change the default behavior in that namespace.


### Deny all ingress traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

### Allow all ingress traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-ingress
spec:
  podSelector: {}
  ingress:
  - {}
  policyTypes:
  - Ingress
```

### Deny all egress traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
```

### Allow all egress traffic 

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-egress
spec:
  podSelector: {}
  egress:
  - {}
  policyTypes:
  - Egress
```

### Deny all ingress and all egress traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```
