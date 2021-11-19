# Manifest files explanations (YAML)

## RoleBindings (jhon)

This manifest have two RoleBinding resources. 

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
