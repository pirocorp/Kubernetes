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
