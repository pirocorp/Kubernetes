# Using provided yaml create a template using **kustomize** with two variants – test and production with difference in the service port and number of replicas

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: homework
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: homework
  namespace: homework
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hw
  template:
    metadata:
      labels:
        app: hw
    spec:
      containers:
      - image: shekeriev/k8s-oracle
        name: homework
---
apiVersion: v1
kind: Service
metadata:
  labels:
    app: hw
  name: homework-svc
  namespace: homework
spec:
  ports:
  - port: 5000
    nodePort: 32000
    protocol: TCP
    targetPort: 5000
  selector:
    app: hw
  type: NodePort
```

## Solution:

Create this directory structure.

![image](https://user-images.githubusercontent.com/34960418/148067138-9203fbb1-0dfa-42ec-8edf-eaf57c8de10c.png)
