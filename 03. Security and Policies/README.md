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
