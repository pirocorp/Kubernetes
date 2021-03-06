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


# Create a Helm chart 

Create a **Helm** chart  that spins a **NGINX**-based deployment with **3 replicas** by default. It must mount a default **index.html** (with a **text** and a **picture**) page from a **ConfigMap**. The web server should be exposed via NodePort service on port **31000** by default. At least the **text of the default page, number of replicas**, and **service port** should be parametrized.

## Solution

Create this directory structure.

![image](https://user-images.githubusercontent.com/34960418/148069783-80a078bc-1d48-4e53-9d36-dcce9b6b2b31.png)

webchart/Chart.yaml

```yaml
apiVersion: v2
name: webchart
description: A simple Nginx-based Helm chart for Kubernetes
# Chart type. A chart can be either an 'application' or a 'library' chart
type: application
# Version of the chart
version: 0.1.0
# Version of the application. In our case - Nginx 1.21.4
appVersion: "1.21.4"
```

webchart/values.yaml

```yaml
replicasCount: 3
greetingMessage: Hello from NGINX chart :)
nodePort: 31000
```

webchart/templates/svc.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-svc
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: {{ .Values.nodePort }}
    protocol: TCP
  selector:
    app: {{ .Release.Name }}
```

webchart/templates/cm.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-cm
data:
  index.html: <h1>{{ .Values.greetingMessage }}</h1><img src="https://www.linuxadictos.com/wp-content/uploads/nginx-1.jpg" alt="nginx logo">
```

webchart/templates/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment
spec:
  replicas: {{ .Values.replicasCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
      - name: main
        image: nginx
        ports:
        - containerPort: 80
        volumeMounts:
        - name: html
          mountPath: /usr/share/nginx/html
      volumes:
      - name: html
        configMap:
          name: {{ .Release.Name }}-cm
```

Can deploy the chart with (for example with one replica instead of three)

```bash
helm install homework hwchart --set replicaCount=1
```

Check the deployed resources

```bash
kubectl get pods,svc,cm,deploy
```

Open a browser tab and navigate to ```http://<cluster-ip>:31000```. App should be there and working. 

Clean Up

```bash
helm uninstall homework
```
