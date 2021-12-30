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




# Manifest files explanations (YAML)

## Part 1

### RoleBindings (jhon and jane)

This manifest (john's role bindings) have two RoleBinding resources. Jhon have role edit in namespace demo-prod and role view in namespace demo-dev.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
# Metadata describes for which user (name) in which (namespace) role binding is set
metadata:
  name: john
  namespace: demo-prod
# Subcects (multiple) for which rolebinding is applied.
subjects:
- kind: User
  name: john
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
  name: john
  namespace: demo-dev
subjects:
- kind: User
  name: john
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

This manifest (jane's role bindings) have two RoleBinding resources. Jane have role view in namespace demo-prod and role edit is namespace demo-dev.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jane
  namespace: demo-prod
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jane
  namespace: demo-dev
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: edit
  apiGroup: rbac.authorization.k8s.io
```

### Demo Role 

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

### Demo Service Acount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: demo-sa
  namespace: rbac-ns
```

### Demo Role RoleBinding

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

### Demo Pod

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

## Part 2

### Demo Pod (pod-2)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-2
  namespace: reslim
spec:
  containers:
  - image: busybox
    command: ["dd", "if=/dev/zero", "of=/dev/null", "bs=32M"]
    name: main
    # Manage resource on container (pod) level
    resources:
      # Resources reserved for pod in order for pod to run. If there are no such free (unreserved) resources the pod won't start
      requests:
        cpu: 250m
        memory: 16Mi
```

### (pod-3a)

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
    resources:
      requests:
        cpu: 250m
        memory: 16Mi
      # limits the container (pod) how many resources it can consume. If pod overconsume resources (ex. Memory leak in app) kubernetes will kill it and start a new instance.
      limits:
        cpu: 500m
        memory: 128Mi
```

### LimitRange

LimitRangeis for managing constraints at a pod and container level within the project. LimitRanges can specify and requests (reservations).

- defaultRequest — is **how much CPU/Memory will be reserved** to Container, if it doesn't specify it's own value
- default — is **default limit** for amount of CPU/Memory for Container, if it doesn't specify it's own value
- max — is maximum limit for amount of CPU/Memory that Container can ask for. I.e. it **can't set it's own limit more than that**
- min — is minimum limit amount of CPU/Memory that Container can ask for. I.e. it **can't set it's own limit less than that**

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
    # default reserved resources
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

### Quotas

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

## Part 3

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
