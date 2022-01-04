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


base/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: homework
commonLabels:
  app: hw
resources:
- homework.yaml
```

overlays/production/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namePrefix: production-
commonLabels:
  variant: production
  org: pirocorp
resources:
- ../../base
patchesStrategicMerge:
- deployment.yaml
- service.yaml
```

overlays/test/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namePrefix: test-
commonLabels:
  variant: test
  org: pirocorp
resources:
- ../../base
patchesStrategicMerge:
- deployment.yaml
- service.yaml
```

overlays/production/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: homework
  namespace: homework
spec:
  replicas: 3
```

overlays/test/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: homework
  namespace: homework
spec:
  replicas: 1
```

overlays/production/service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: homework-svc
  namespace: homework
spec:
  ports:
  - port: 5000
    nodePort: 30001
    protocol: TCP
```


overlays/test/service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: homework-svc
  namespace: homework
spec:
  ports:
  - port: 5000
    nodePort: 32002
    protocol: TCP
    targetPort: 5000
```

Now, test both variants

```bash
kustomize build out/overlays/production/
kustomize build out/overlays/test/
```

Everything seems to be fine. We can start both variants with.

```bash
kubectl apply -k out/overlays/production/
kubectl apply -k out/overlays/test/
```

We can check the resources that were created with

```bash
kubectl get all -n homework
```

Everything seems to be fine. Let’s check the details of the namespace

```bash
kubectl get ns homework --show-labels
```

Open two browser tabs and navigate to

-	```http://<cluster-ip>:30001``` for production.
-	```http://<cluster-ip>:32002``` for test.

Clean Up

```bash
kubectl delete ns homework
```
